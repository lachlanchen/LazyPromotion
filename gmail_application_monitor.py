#!/usr/bin/env python3
"""Observe configured Gmail application searches without opening messages."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import time
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote_plus, urlsplit

from playwright.sync_api import sync_playwright

import browser


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / ".local/private/gmail-application-monitor.json"
STATUS = ROOT / ".local/gmail-application-monitor-status.json"
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DOMAIN_RE = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,63}\Z")
EMAIL_RE = re.compile(r"[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}\Z")
OPAQUE_RE = re.compile(r"[A-Za-z0-9_:#-]{1,160}\Z")
POLICY = {
    "exact_configured_searches_only": True,
    "complete_mailbox_claimed": False,
    "messages_opened": False,
    "previews_or_bodies_read": False,
    "contacts_subjects_or_message_ids_persisted": False,
    "automatic_reply": False,
}
SESSION_REASONS = {
    "ambiguous Gmail browser context": "ambiguous_context",
    "ambiguous project Gmail tab": "ambiguous_tab",
    "Gmail needs account review": "origin_changed",
    "Gmail account binding unavailable": "account_binding_unavailable",
}


class GmailSessionUnavailable(RuntimeError):
    pass


def validate_config(value: dict) -> dict:
    if not isinstance(value, dict) or set(value) != {"account_email", "campaigns"}:
        raise ValueError("invalid Gmail configuration")
    account = value["account_email"]
    rules = value["campaigns"]
    if not isinstance(account, str) or not EMAIL_RE.fullmatch(account):
        raise ValueError("invalid Gmail account binding")
    if not isinstance(rules, list) or not 1 <= len(rules) <= 4:
        raise ValueError("Gmail requires one to four bounded campaign searches")
    result, seen = [], set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"campaign_id", "subject", "sender_domain", "after"}:
            raise ValueError("invalid Gmail campaign rule")
        cid, subject, domain, after = (rule[k] for k in ("campaign_id", "subject", "sender_domain", "after"))
        if not isinstance(cid, str) or len(cid) > 100 or not ID_RE.fullmatch(cid) or cid in seen:
            raise ValueError("invalid or duplicate Gmail campaign")
        if not isinstance(subject, str) or not 8 <= len(subject) <= 180 or any(c in subject for c in '\r\n"{}()') or not subject.isprintable():
            raise ValueError("invalid Gmail subject boundary")
        if not isinstance(domain, str) or len(domain) > 253 or not DOMAIN_RE.fullmatch(domain):
            raise ValueError("invalid Gmail sender domain")
        if not isinstance(after, str) or date.fromisoformat(after).isoformat() != after:
            raise ValueError("invalid Gmail date boundary")
        seen.add(cid)
        result.append(dict(rule))
    return {"account_email": account.casefold(), "campaigns": result}


def load_config(path: Path = CONFIG) -> dict:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Gmail configuration must be an owned private regular file")
    return validate_config(json.loads(path.read_text(encoding="utf-8")))


def search_query(rule: dict) -> str:
    return f'in:anywhere after:{rule["after"].replace("-", "/")} from:{rule["sender_domain"]} subject:"{rule["subject"]}"'


def normalized_subject(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).strip()
    value = re.sub(r"^(?:(?:re|fw|fwd)\s*:\s*)+", "", value, flags=re.I)
    return " ".join(value.casefold().split())


# Only result metadata is inspected. Never read a row's innerText/textContent:
# it contains the message preview. The two subject spans are duplicate links.
SNAPSHOT_JS = r"""() => {
    const visible = e => !!e.getClientRects().length;
    const mains = [...document.querySelectorAll('[role="main"]')].filter(visible);
    if (mains.length !== 1) return null;
    const main = mains[0];
    if ([...main.querySelectorAll('.a3s, [contenteditable="true"]')].some(visible)) return null;
    const rows = [...main.querySelectorAll('tr.zA')].filter(visible);
    if (!rows.length) {
        const empty = [...main.querySelectorAll('div.LeCudf')].filter(e => visible(e)
            && e.querySelector('b')?.textContent === 'No matches'
            && /^No matches\s*Try a different search$/.test(e.textContent.trim()));
        if (empty.length !== 1) return null;
        return {empty: true, complete: true, rows: []};
    }
    const pagers = [...document.querySelectorAll('.Dj')].filter(visible).map(e => e.textContent.trim());
    const complete = pagers.some(t => {
        const m = t.match(/^1\s*[–-]\s*(\d+)\s+of\s+(\d+)$/);
        return m && Number(m[1]) === rows.length && Number(m[2]) === rows.length;
    });
    const data = rows.map(row => {
        const nodes = [...row.querySelectorAll('[data-thread-id]')];
        const records = nodes.map(n => ({thread_id: n.getAttribute('data-thread-id'),
            last_message_id: n.getAttribute('data-legacy-last-non-draft-message-id'),
            subject: n.textContent.trim()}));
        if (!records.length || records.some(r => JSON.stringify(r) !== JSON.stringify(records[0]))) return null;
        const unread = row.classList.contains('zE'), read = row.classList.contains('yO');
        if (unread === read) return null;
        return {...records[0], unread};
    });
    return {empty: false, complete, rows: data};
}"""


def validate_snapshot(value: dict, rule: dict) -> dict:
    if not isinstance(value, dict) or set(value) != {"empty", "complete", "rows"} or value["complete"] is not True:
        raise ValueError("Gmail results are unavailable or incomplete")
    rows = value["rows"]
    if type(value["empty"]) is not bool or not isinstance(rows, list) or len(rows) > 50 or value["empty"] != (len(rows) == 0):
        raise ValueError("invalid Gmail result boundary")
    identities, unread = [], 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"thread_id", "last_message_id", "subject", "unread"}:
            raise ValueError("incomplete Gmail row metadata")
        if any(not isinstance(row[k], str) or not OPAQUE_RE.fullmatch(row[k]) for k in ("thread_id", "last_message_id")):
            raise ValueError("invalid Gmail row identity")
        if not isinstance(row["subject"], str) or normalized_subject(row["subject"]) != normalized_subject(rule["subject"]) or type(row["unread"]) is not bool:
            raise ValueError("Gmail row does not match the configured conversation")
        if row["thread_id"] in {identity[0] for identity in identities}:
            raise ValueError("duplicate Gmail thread")
        identities.append((row["thread_id"], row["last_message_id"], row["unread"]))
        unread += int(row["unread"])
    digest = hashlib.sha256(json.dumps(sorted(identities)).encode()).hexdigest()
    return {"campaign_id": rule["campaign_id"], "matching_thread_count": len(rows),
            "unread_matching_thread_count": unread, "snapshot_digest": digest}


def account_matches(page, account: str) -> bool:
    if urlsplit(page.url).hostname != "mail.google.com":
        return False
    marker = page.locator('a[aria-label^="Google Account:"]').filter(visible=True)
    return (marker.count() == 1 and f"({account})" in (marker.get_attribute("aria-label", timeout=1000) or "").casefold()
            and f" - {account} - Gmail".casefold() in page.title().casefold())


def wait_for_account(page, account: str, *, deadline: float) -> None:
    """Allow existing sign-in redirects to settle; never operate a login form."""
    while time.monotonic() < deadline:
        if urlsplit(page.url).hostname not in {"mail.google.com", "accounts.google.com"}:
            raise GmailSessionUnavailable("Gmail needs account review")
        if account_matches(page, account):
            return
        page.wait_for_timeout(250)
    raise GmailSessionUnavailable("Gmail account binding unavailable")


def collect_counts(config: dict) -> list[dict]:
    config = validate_config(config)
    with browser.browser_operation_lock(timeout_seconds=5), sync_playwright() as pw:
        overall_deadline = time.monotonic() + 60

        def remaining_timeout():
            remaining = int((overall_deadline - time.monotonic()) * 1000)
            if remaining < 1:
                raise RuntimeError("bounded Gmail check timed out")
            return min(15_000, remaining)

        connected = pw.chromium.connect_over_cdp(browser.DEFAULT_CDP, no_defaults=True, timeout=10_000)
        if len(connected.contexts) != 1:
            raise GmailSessionUnavailable("ambiguous Gmail browser context")
        context = connected.contexts[0]
        pages = [p for p in context.pages if urlsplit(p.url).hostname == "mail.google.com"]
        if len(pages) > 1:
            raise GmailSessionUnavailable("ambiguous project Gmail tab")
        page = pages[0] if pages else context.new_page()
        results = []
        for rule in config["campaigns"]:
            query = search_query(rule)
            destination = "https://mail.google.com/mail/u/0/#search/" + quote(query, safe="")
            page.bring_to_front()
            page.goto(destination, wait_until="domcontentloaded", timeout=remaining_timeout())
            # On a fresh tab, Gmail can still be completing its existing-sign-in
            # redirect after DOMContentLoaded. Do not interrupt that with reload.
            wait_for_account(page, config["account_email"],
                             deadline=min(overall_deadline, time.monotonic() + 20))
            # A document reload prevents the preceding SPA search's cached rows
            # or empty marker from satisfying the new query's observation.
            page.reload(wait_until="domcontentloaded", timeout=remaining_timeout())
            deadline, previous, stable = min(overall_deadline, time.monotonic() + 15), None, 0
            while time.monotonic() < deadline:
                if urlsplit(page.url).hostname != "mail.google.com":
                    raise GmailSessionUnavailable("Gmail needs account review")
                field = page.locator('input[placeholder="Search mail"]').filter(visible=True)
                fragment = unquote_plus(urlsplit(page.url).fragment)
                if account_matches(page, config["account_email"]) and field.count() == 1 and field.input_value(timeout=1000).strip() == query and fragment == "search/" + query:
                    try:
                        observed = validate_snapshot(page.evaluate(SNAPSHOT_JS), rule)
                    except ValueError:
                        observed = None
                    if observed is not None:
                        stable = stable + 1 if observed == previous else 1
                        previous = observed
                        if stable >= 3:
                            results.append(observed)
                            break
                    else:
                        previous, stable = None, 0
                else:
                    previous, stable = None, 0
                page.wait_for_timeout(400)
            else:
                if not account_matches(page, config["account_email"]):
                    raise GmailSessionUnavailable("Gmail account binding unavailable")
                raise RuntimeError("Gmail result observation did not stabilize")
        return results


def private_json(path: Path, value: dict) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("unsafe Gmail status path")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def validated_success(value: object) -> dict | None:
    if not isinstance(value, dict) or set(value) != {"checked_at", "config_fingerprint", "campaigns"}:
        return None
    try:
        stamp = datetime.fromisoformat(value["checked_at"].replace("Z", "+00:00"))
        if stamp.tzinfo is None or not re.fullmatch(r"[a-f0-9]{64}", value["config_fingerprint"]):
            return None
        rows = value["campaigns"]
        if not isinstance(rows, list) or not 1 <= len(rows) <= 4:
            return None
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"campaign_id", "matching_thread_count", "unread_matching_thread_count", "snapshot_digest"}:
                return None
            if not ID_RE.fullmatch(row["campaign_id"]) or row["campaign_id"] in seen or not re.fullmatch(r"[a-f0-9]{64}", row["snapshot_digest"]):
                return None
            if any(type(row[k]) is not int for k in ("matching_thread_count", "unread_matching_thread_count")) or not 0 <= row["unread_matching_thread_count"] <= row["matching_thread_count"] <= 50:
                return None
            seen.add(row["campaign_id"])
    except (KeyError, AttributeError, TypeError, ValueError):
        return None
    return value


def record_observation(config: dict, rows: list[dict], previous: dict, checked_at: str) -> dict:
    config = validate_config(config)
    fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    success = {"checked_at": checked_at, "config_fingerprint": fingerprint, "campaigns": rows}
    if validated_success(success) is None or {r["campaign_id"] for r in rows} != {r["campaign_id"] for r in config["campaigns"]}:
        raise ValueError("invalid Gmail observation rows")
    prior = validated_success(previous.get("last_success")) or {}
    if prior.get("config_fingerprint") != fingerprint:
        prior = {}
    known = {r["campaign_id"]: r for r in prior.get("campaigns", [])}
    pending = set()
    if prior:
        for alert in previous.get("alerts", []) if isinstance(previous.get("alerts"), list) else []:
            if isinstance(alert, dict) and set(alert) == {"campaign_id", "kind"} and alert.get("kind") == "gmail_application_activity" and alert.get("campaign_id") in known:
                pending.add(alert["campaign_id"])
    for row in rows:
        before = known.get(row["campaign_id"])
        if (before is None and row["matching_thread_count"] > 0) or (before is not None and before != row):
            pending.add(row["campaign_id"])
    alerts = [{"campaign_id": cid, "kind": "gmail_application_activity"} for cid in sorted(pending)]
    return {"state": "checked", "checked_at": checked_at, "last_success": success,
            "alerts": alerts, "policy": dict(POLICY)}


def validated_summary(value: dict) -> dict:
    if not isinstance(value, dict) or value.get("state") not in {"not_configured", "checked", "session_unavailable", "observation_failed"}:
        raise ValueError("invalid Gmail summary")
    fields = {"state"}
    if value["state"] == "checked":
        fields |= {"campaign_count", "matching_thread_count", "unread_matching_thread_count", "review_required"}
        if any(type(value.get(k)) is not int or value[k] < 0 for k in fields - {"state", "review_required"}):
            raise ValueError("invalid Gmail summary count")
        if not 1 <= value["campaign_count"] <= 4 or value["unread_matching_thread_count"] > value["matching_thread_count"] or type(value.get("review_required")) is not bool:
            raise ValueError("inconsistent Gmail summary")
    if set(value) != fields:
        raise ValueError("unexpected Gmail summary fields")
    return dict(value)


def check_optional(config_path: Path = CONFIG, status_path: Path = STATUS) -> dict:
    if not config_path.exists() and not config_path.is_symlink():
        return {"state": "not_configured"}
    previous = {}
    if status_path.exists() and not status_path.is_symlink():
        try:
            previous = json.loads(status_path.read_text())
            if not isinstance(previous, dict):
                previous = {}
        except (OSError, ValueError):
            pass
    checked_at = datetime.now(timezone.utc).isoformat()
    try:
        config = load_config(config_path)
        rows = collect_counts(config)
        checked_at = datetime.now(timezone.utc).isoformat()
        record = record_observation(config, rows, previous, checked_at)
        summary = {"state": "checked", "campaign_count": len(rows),
                   "matching_thread_count": sum(r["matching_thread_count"] for r in rows),
                   "unread_matching_thread_count": sum(r["unread_matching_thread_count"] for r in rows),
                   "review_required": bool(record["alerts"])}
    except Exception as error:
        state = "session_unavailable" if isinstance(error, GmailSessionUnavailable) else "observation_failed"
        last_success = validated_success(previous.get("last_success"))
        known_ids = {r["campaign_id"] for r in last_success["campaigns"]} if last_success else set()
        pending = previous.get("alerts", [])
        alerts = [a for a in pending if isinstance(a, dict) and set(a) == {"campaign_id", "kind"}
                  and a.get("kind") == "gmail_application_activity" and a.get("campaign_id") in known_ids] if isinstance(pending, list) else []
        record = {"state": state, "checked_at": checked_at, "last_success": last_success,
                  "alerts": alerts, "policy": dict(POLICY)}
        record["failure_reason"] = SESSION_REASONS.get(str(error), "unavailable_or_incomplete")
        summary = {"state": state}
    private_json(status_path, record)
    return validated_summary(summary)
