#!/usr/bin/env python3
"""Monitor one submitted Freelancer bid without opening messages or replying."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

import browser as browser_tools


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local"
STATE_PATH = RUNTIME / "freelancer-inbound-state.json"
STATUS_PATH = RUNTIME / "freelancer-inbound-monitor-status.json"
LOG_PATH = RUNTIME / "freelancer-inbound-monitor.jsonl"
LOCK_PATH = RUNTIME / "freelancer-inbound-monitor.lock"
DEFAULT_CDP = "http://127.0.0.1:9436"
HOST = "www.freelancer.com"
PROJECT_SLUG = "Playwright-Python-Regression-Suite"
PROJECT_PATH_SUFFIX = f"/{PROJECT_SLUG}/proposals"
EXPECTED_USERNAME = "@lachlanchen"
RANK_PATTERN = re.compile(r"You are ranked\s+(\d+)\s+out of\s+(\d+)\s+proposals", re.I)


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


def bid_state(body_text: str) -> str:
    normalized = " ".join(body_text.split()).casefold()
    if "project has been awarded" in normalized or "you have been awarded" in normalized:
        return "awarded_review_required"
    if "project is closed" in normalized or "bidding has ended" in normalized:
        return "closed"
    if "your proposal" in normalized and "retract" in normalized and "edit" in normalized:
        return "active_submitted"
    return "unknown"


def summarize_observation(
    *,
    authenticated: bool,
    current_bid_state: str,
    message_badge_count: int,
    rank: int | None,
    proposal_count: int | None,
    previous: dict | None,
    checked_at: str,
) -> tuple[dict, dict]:
    if current_bid_state not in {
        "active_submitted",
        "awarded_review_required",
        "closed",
        "unknown",
    }:
        raise ValueError("invalid bid state")
    if message_badge_count < 0:
        raise ValueError("message badge count must be non-negative")
    if (rank is None) != (proposal_count is None):
        raise ValueError("rank and proposal count must be present together")
    baseline_created = previous is None
    previous_count = int((previous or {}).get("message_badge_count", 0))
    previous_state = (previous or {}).get("bid_state")
    new_message_signal = not baseline_created and message_badge_count > previous_count
    bid_state_changed = (
        not baseline_created
        and isinstance(previous_state, str)
        and current_bid_state != previous_state
    )
    review_required = (
        new_message_signal
        or bid_state_changed
        or current_bid_state in {"awarded_review_required", "unknown"}
    )
    status = {
        "checked_at": checked_at,
        "available": True,
        "authenticated": authenticated,
        "bid_state": current_bid_state,
        "message_badge_count": message_badge_count,
        "new_message_signal": new_message_signal,
        "rank": rank,
        "proposal_count": proposal_count,
        "baseline_created": baseline_created,
        "bid_state_changed": bid_state_changed,
        "review_required": review_required,
        "message_opened": False,
        "automatic_reply": False,
        "action": (
            "Review the Freelancer bid visibly; do not reply or accept automatically."
            if review_required
            else "No Freelancer review is required."
        ),
    }
    state = {
        "checked_at": checked_at,
        "bid_state": current_bid_state,
        "message_badge_count": message_badge_count,
        "rank": rank,
        "proposal_count": proposal_count,
    }
    return status, state


def collect_visible_status(*, cdp: str) -> dict:
    with browser_tools.browser_operation_lock():
        with sync_playwright() as playwright:
            connected = playwright.chromium.connect_over_cdp(cdp)
            candidates = []
            for context in connected.contexts:
                for page in context.pages:
                    parsed = urlsplit(page.url)
                    if parsed.hostname == HOST and parsed.path.endswith(PROJECT_PATH_SUFFIX):
                        candidates.append(page)
            if len(candidates) != 1:
                raise RuntimeError(
                    "exactly one authenticated Freelancer proposal tab must be open"
                )
            page = candidates[0]
            page.bring_to_front()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(800)
            observed = page.evaluate(
                """() => {
                  const bodyText = document.body ? document.body.innerText : '';
                  const buttons = Array.from(document.querySelectorAll('button[aria-label="Messages"]'))
                    .filter((button) => {
                      const style = getComputedStyle(button);
                      const rect = button.getBoundingClientRect();
                      return style.visibility !== 'hidden' && style.display !== 'none' &&
                        rect.width > 0 && rect.height > 0;
                    });
                  const digits = buttons.flatMap((button) =>
                    ((button.innerText || '').match(/\d+/g) || []).map(Number));
                  return {
                    bodyText,
                    messageBadgeCount: digits.length ? Math.max(...digits) : 0,
                    authenticated: bodyText.includes('@lachlanchen') &&
                      !document.querySelector('input[type="password"]')
                  };
                }"""
            )
            if not isinstance(observed, dict):
                raise RuntimeError("Freelancer exposed an invalid proposal state")
            body_text = str(observed.get("bodyText") or "")
            rank_match = RANK_PATTERN.search(body_text)
            return {
                "authenticated": bool(observed.get("authenticated")),
                "bid_state": bid_state(body_text),
                "message_badge_count": int(observed.get("messageBadgeCount") or 0),
                "rank": int(rank_match.group(1)) if rank_match else None,
                "proposal_count": int(rank_match.group(2)) if rank_match else None,
            }


def monitor_once(
    *,
    cdp: str = DEFAULT_CDP,
    state_path: Path = STATE_PATH,
    status_path: Path = STATUS_PATH,
    log_path: Path = LOG_PATH,
) -> dict:
    checked_at = utc_now()
    observed = collect_visible_status(cdp=cdp)
    if not observed["authenticated"]:
        raise RuntimeError("the dedicated Freelancer session is not authenticated")
    previous = None
    if state_path.is_file() and not state_path.is_symlink():
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError("the private Freelancer monitor state is invalid") from exc
    status, state = summarize_observation(
        authenticated=observed["authenticated"],
        current_bid_state=observed["bid_state"],
        message_badge_count=observed["message_badge_count"],
        rank=observed["rank"],
        proposal_count=observed["proposal_count"],
        previous=previous,
        checked_at=checked_at,
    )
    if status["review_required"]:
        evidence = RUNTIME / "evidence" / f"{checked_at.replace(':', '')}-freelancer-bid.png"
        with browser_tools.browser_operation_lock():
            with sync_playwright() as playwright:
                connected = playwright.chromium.connect_over_cdp(cdp)
                pages = [page for context in connected.contexts for page in context.pages]
                target = next(
                    page
                    for page in pages
                    if urlsplit(page.url).hostname == HOST
                    and urlsplit(page.url).path.endswith(PROJECT_PATH_SUFFIX)
                )
                evidence.parent.mkdir(parents=True, exist_ok=True)
                target.screenshot(path=str(evidence), full_page=False)
                os.chmod(evidence, 0o600)
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
    return payload


def loop(*, cdp: str, interval_minutes: int) -> None:
    if interval_minutes < 15:
        raise ValueError("interval must be at least 15 minutes")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Freelancer inbound monitor is already running") from exc
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
    if args.command == "once":
        print(json.dumps(monitor_once(cdp=args.cdp), sort_keys=True))
    elif args.command == "status":
        print(json.dumps(status_summary(), sort_keys=True))
    else:
        loop(cdp=args.cdp, interval_minutes=args.interval_minutes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
