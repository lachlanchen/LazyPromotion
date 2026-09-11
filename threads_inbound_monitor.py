#!/usr/bin/env python3
"""Detect new Threads reply activity without opening or answering a reply."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

import browser as browser_tools


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local"
STATE_PATH = RUNTIME / "threads-inbound-state.json"
STATUS_PATH = RUNTIME / "threads-inbound-monitor-status.json"
LOG_PATH = RUNTIME / "threads-inbound-monitor.jsonl"
LOCK_PATH = RUNTIME / "threads-inbound-monitor.lock"
DEFAULT_CDP = "http://127.0.0.1:9436"
ACTIVITY_HOSTS = {"threads.com", "www.threads.com"}
ACTIVITY_PATH = "/activity/replies"
PROFILE_PATH = "/@lazying.art"


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def append_log(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, sort_keys=True) + "\n")
    os.chmod(path, 0o600)


def reply_fingerprints(paths: list[str]) -> list[str]:
    """Create opaque stable keys while retaining duplicate notification rows."""
    occurrences: dict[str, int] = {}
    fingerprints = []
    for value in paths:
        parsed = urlsplit(str(value or ""))
        if parsed.hostname not in ACTIVITY_HOSTS:
            continue
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 3 or not parts[0].startswith("@") or parts[1] != "post":
            continue
        canonical = "/" + "/".join(parts)
        occurrences[canonical] = occurrences.get(canonical, 0) + 1
        identity = f"{canonical}\n{occurrences[canonical]}"
        fingerprints.append(hashlib.sha256(identity.encode("utf-8")).hexdigest())
    return fingerprints


def summarize_observation(
    *,
    current_fingerprints: list[str],
    previous_fingerprints: list[str] | None,
    current_profile_fingerprints: list[str] | None = None,
    previous_profile_fingerprints: list[str] | None = None,
    profile_available: bool = False,
    empty_message_visible: bool,
    authenticated: bool,
    checked_at: str,
) -> tuple[dict, dict]:
    current = list(dict.fromkeys(current_fingerprints))
    previous = list(dict.fromkeys(previous_fingerprints or []))
    current_profile = list(dict.fromkeys(current_profile_fingerprints or []))
    previous_profile = list(dict.fromkeys(previous_profile_fingerprints or []))
    profile_tracking = current_profile_fingerprints is not None
    activity_baseline_created = previous_fingerprints is None
    profile_baseline_created = profile_tracking and previous_profile_fingerprints is None
    baseline_created = activity_baseline_created and (
        not profile_tracking or profile_baseline_created
    )
    new_keys = (
        sorted(set(current) - set(previous))
        if not activity_baseline_created
        else []
    )
    count_delta = (
        max(0, len(current) - len(previous))
        if not activity_baseline_created
        else 0
    )
    new_profile_keys = (
        sorted(set(current_profile) - set(previous_profile))
        if profile_tracking and not profile_baseline_created
        else []
    )
    profile_count_delta = (
        max(0, len(current_profile) - len(previous_profile))
        if profile_tracking and not profile_baseline_created
        else 0
    )
    new_reply_item_count = max(
        len(new_keys),
        count_delta,
        len(new_profile_keys),
        profile_count_delta,
    )
    layout_unknown = (
        authenticated
        and not current
        and not empty_message_visible
        and not profile_available
    )
    review_required = bool(new_reply_item_count or layout_unknown)
    status = {
        "checked_at": checked_at,
        "available": True,
        "authenticated": authenticated,
        "reply_item_count": max(len(current), len(current_profile)),
        "activity_reply_item_count": len(current),
        "profile_reply_item_count": len(current_profile),
        "profile_available": profile_available,
        "profile_baseline_created": profile_baseline_created,
        "new_reply_item_count": new_reply_item_count,
        "baseline_created": baseline_created,
        "layout_unknown": layout_unknown,
        "review_required": review_required,
        "content_opened": False,
        "automatic_reply": False,
        "action": (
            "Review Threads activity visibly; do not reply automatically."
            if review_required
            else "No reply review is required."
        ),
    }
    state = {
        "checked_at": checked_at,
        "fingerprints": current,
        "profile_fingerprints": current_profile,
    }
    return status, state


def collect_visible_activity(*, cdp: str) -> dict:
    """Read reply links and owned-card counts from already-open Threads tabs."""
    with browser_tools.browser_operation_lock():
        with sync_playwright() as playwright:
            connected = playwright.chromium.connect_over_cdp(cdp)
            candidates = []
            for context in connected.contexts:
                for page in context.pages:
                    parsed = urlsplit(page.url)
                    if parsed.hostname in ACTIVITY_HOSTS and parsed.path == ACTIVITY_PATH:
                        candidates.append(page)
            if len(candidates) != 1:
                raise RuntimeError(
                    "exactly one dedicated Threads replies activity tab must be open"
                )
            page = candidates[0]
            page.bring_to_front()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
            observed = page.evaluate(
                r"""() => {
                  const hrefs = Array.from(document.querySelectorAll('a[href]'))
                    .map((anchor) => anchor.href)
                    .filter((href) => /threads\.com\/@[^/]+\/post\/[^/?#]+/.test(href));
                  const bodyText = document.body ? document.body.innerText : '';
                  const profile = Array.from(document.querySelectorAll('a[href]'))
                    .some((anchor) => /threads\.com\/@lazying\.art\/?$/.test(anchor.href));
                  return {
                    hrefs,
                    emptyMessageVisible: /No activity yet\.?/i.test(bodyText),
                    authenticated: profile && !document.querySelector('input[type=password]')
                  };
                }"""
            )
            if not isinstance(observed, dict):
                raise RuntimeError("Threads exposed an invalid activity state")

            profiles = []
            for context in connected.contexts:
                for candidate in context.pages:
                    parsed = urlsplit(candidate.url)
                    if (
                        parsed.hostname in ACTIVITY_HOSTS
                        and parsed.path.rstrip("/") == PROFILE_PATH
                    ):
                        profiles.append(candidate)
            if len(profiles) != 1:
                raise RuntimeError(
                    "exactly one dedicated Threads profile tab must be open"
                )
            profile = profiles[0]
            profile.bring_to_front()
            profile.wait_for_load_state("domcontentloaded")
            profile.wait_for_timeout(500)
            profile_observed = profile.evaluate(
                r"""() => {
                  const rows = [];
                  const cards = Array.from(
                    document.querySelectorAll('[data-pressable-container="true"]')
                  );
                  for (const card of cards) {
                    const anchor = Array.from(card.querySelectorAll('a[href]')).find(
                      (item) => /threads\.com\/@lazying\.art\/post\/[^/?#]+/.test(item.href)
                    );
                    const icon = card.querySelector('svg[aria-label="Reply"]');
                    if (!anchor || !icon) continue;
                    const text = (icon.parentElement?.innerText || '').trim();
                    const match = text.replaceAll(',', '').match(/^(\d+)$/);
                    rows.push({href: anchor.href, count: match ? Number(match[1]) : 0});
                  }
                  return {
                    profileFound:
                      location.pathname.replace(/\/$/, '') === '/@lazying.art',
                    rows,
                  };
                }"""
            )
            if not isinstance(profile_observed, dict):
                raise RuntimeError("Threads exposed an invalid profile state")
            profile_paths = []
            for row in profile_observed.get("rows") or []:
                if not isinstance(row, dict):
                    continue
                count = row.get("count")
                if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                    continue
                profile_paths.extend([str(row.get("href") or "")] * count)
            return {
                "fingerprints": reply_fingerprints(list(observed.get("hrefs") or [])),
                "profile_fingerprints": reply_fingerprints(profile_paths),
                "profile_available": bool(profile_observed.get("profileFound")),
                "empty_message_visible": bool(observed.get("emptyMessageVisible")),
                "authenticated": bool(observed.get("authenticated")),
            }


def capture_visible_evidence(*, cdp: str, path: Path) -> None:
    """Capture activity and profile views without following a notification."""
    with browser_tools.browser_operation_lock():
        with sync_playwright() as playwright:
            connected = playwright.chromium.connect_over_cdp(cdp)
            candidates = [
                page
                for context in connected.contexts
                for page in context.pages
                if urlsplit(page.url).hostname in ACTIVITY_HOSTS
                and urlsplit(page.url).path == ACTIVITY_PATH
            ]
            if len(candidates) != 1:
                raise RuntimeError(
                    "exactly one dedicated Threads replies activity tab must be open"
                )
            candidates[0].bring_to_front()
            path.parent.mkdir(parents=True, exist_ok=True)
            candidates[0].screenshot(path=str(path), full_page=False)
            os.chmod(path, 0o600)
            profiles = [
                page
                for context in connected.contexts
                for page in context.pages
                if urlsplit(page.url).hostname in ACTIVITY_HOSTS
                and urlsplit(page.url).path.rstrip("/") == PROFILE_PATH
            ]
            if len(profiles) != 1:
                raise RuntimeError(
                    "exactly one dedicated Threads profile tab must be open"
                )
            profile_path = path.with_name(path.stem + "-profile" + path.suffix)
            profiles[0].bring_to_front()
            profiles[0].screenshot(path=str(profile_path), full_page=False)
            os.chmod(profile_path, 0o600)


def monitor_once(
    *,
    cdp: str = DEFAULT_CDP,
    state_path: Path = STATE_PATH,
    status_path: Path = STATUS_PATH,
    log_path: Path = LOG_PATH,
) -> dict:
    checked_at = utc_now()
    observed = collect_visible_activity(cdp=cdp)
    if state_path.is_file() and not state_path.is_symlink():
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8"))
            previous_fingerprints = list(previous.get("fingerprints") or [])
            previous_profile_fingerprints = (
                list(previous.get("profile_fingerprints") or [])
                if "profile_fingerprints" in previous
                else None
            )
        except (OSError, json.JSONDecodeError, AttributeError, TypeError):
            raise RuntimeError("the private Threads monitor state is invalid")
    else:
        previous_fingerprints = None
        previous_profile_fingerprints = None
    status, state = summarize_observation(
        current_fingerprints=observed["fingerprints"],
        previous_fingerprints=previous_fingerprints,
        current_profile_fingerprints=observed["profile_fingerprints"],
        previous_profile_fingerprints=previous_profile_fingerprints,
        profile_available=observed["profile_available"],
        empty_message_visible=observed["empty_message_visible"],
        authenticated=observed["authenticated"],
        checked_at=checked_at,
    )
    if not status["authenticated"]:
        raise RuntimeError("the dedicated Threads profile is not authenticated")
    if status["review_required"]:
        evidence = RUNTIME / "evidence" / f"{checked_at.replace(':', '')}-threads-replies.png"
        capture_visible_evidence(cdp=cdp, path=evidence)
        status["private_evidence_saved"] = True
    else:
        status["private_evidence_saved"] = False
    atomic_write_json(state_path, state)
    atomic_write_json(status_path, status)
    append_log(log_path, status)
    return status


def status_summary(path: Path = STATUS_PATH) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"available": False}
    allowed = {
        "checked_at",
        "available",
        "authenticated",
        "reply_item_count",
        "activity_reply_item_count",
        "profile_reply_item_count",
        "profile_available",
        "profile_baseline_created",
        "new_reply_item_count",
        "baseline_created",
        "layout_unknown",
        "review_required",
        "content_opened",
        "automatic_reply",
        "action",
        "private_evidence_saved",
    }
    return {key: payload[key] for key in allowed if key in payload}


def loop(*, cdp: str, interval_minutes: int) -> None:
    if interval_minutes < 15:
        raise ValueError("interval must be at least 15 minutes")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Threads inbound monitor is already running") from exc
        while True:
            try:
                monitor_once(cdp=cdp)
            except Exception as exc:
                failure = {"checked_at": utc_now(), "available": False, "error": str(exc)}
                atomic_write_json(STATUS_PATH, failure)
                append_log(LOG_PATH, failure)
            time.sleep(interval_minutes * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("once", "loop", "status"))
    parser.add_argument("--cdp", default=DEFAULT_CDP)
    parser.add_argument("--interval-minutes", type=int, default=30)
    args = parser.parse_args()
    if args.command == "status":
        print(json.dumps(status_summary(), sort_keys=True))
    elif args.command == "once":
        print(json.dumps(monitor_once(cdp=args.cdp), sort_keys=True))
    else:
        loop(cdp=args.cdp, interval_minutes=args.interval_minutes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
