#!/usr/bin/env python3
"""Monitor social inbox badges and allowlisted campaign participants without reading messages."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import Locator, Page, sync_playwright

import browser as browser_tools
import inbound_monitor


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local"
CONFIG_PATH = RUNTIME / "private" / "social-inbox-monitor.json"
STATE_PATH = RUNTIME / "social-inbox-monitor-state.json"
STATUS_PATH = RUNTIME / "social-inbox-monitor-status.json"
LOG_PATH = RUNTIME / "social-inbox-monitor.jsonl"
LOCK_PATH = RUNTIME / "social-inbox-monitor.lock"
DEFAULT_CDP = "http://127.0.0.1:9436"
PLATFORMS = {"instagram", "reddit"}
CAMPAIGN_ID = re.compile(r"^[a-z0-9][a-z0-9:_-]{1,99}$")
PARTICIPANT = re.compile(r"^[A-Za-z0-9_.-]{2,64}$")


def validate_config(payload: object) -> dict:
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("the social inbox configuration is invalid")
    raw_campaigns = payload.get("campaigns")
    if not isinstance(raw_campaigns, list) or not raw_campaigns:
        raise ValueError("the social inbox campaign list is invalid")
    campaigns = []
    seen: set[str] = set()
    for raw in raw_campaigns:
        if not isinstance(raw, dict):
            raise ValueError("the social inbox campaign is invalid")
        campaign_id = str(raw.get("campaign_id") or "").strip()
        platform = str(raw.get("platform") or "").strip().casefold()
        participant = str(raw.get("participant") or "").strip()
        source_url = str(raw.get("source_url") or "").strip()
        if not CAMPAIGN_ID.fullmatch(campaign_id) or campaign_id in seen:
            raise ValueError("the social inbox campaign id is invalid")
        if platform not in PLATFORMS:
            raise ValueError("the social inbox platform is invalid")
        if platform == "instagram":
            if not PARTICIPANT.fullmatch(participant) or source_url:
                raise ValueError("the Instagram participant is invalid")
        else:
            parsed = urlsplit(source_url)
            parts = [part for part in parsed.path.split("/") if part]
            if (
                participant
                or parsed.scheme != "https"
                or parsed.hostname != "www.reddit.com"
                or len(parts) < 4
                or parts[0] != "r"
                or parts[2] != "comments"
            ):
                raise ValueError("the Reddit source URL is invalid")
        seen.add(campaign_id)
        campaigns.append(
            {
                "campaign_id": campaign_id,
                "platform": platform,
                "participant": participant,
                "source_url": source_url,
            }
        )
    return {"version": 1, "campaigns": campaigns}


def load_config(path: Path = CONFIG_PATH) -> dict:
    try:
        return validate_config(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError("the private social inbox configuration is unavailable") from exc


def badge_numbers(locator: Locator) -> list[int]:
    numbers: list[int] = []
    for index in range(min(locator.count(), 30)):
        item = locator.nth(index)
        values = [item.get_attribute("aria-label") or "", item.get_attribute("title") or ""]
        if item.is_visible():
            values.append(item.inner_text(timeout=1_000))
        for value in values:
            if re.fullmatch(r"\s*\d{1,3}\s*", value):
                numbers.append(int(value.strip()))
            else:
                numbers.extend(
                    int(match)
                    for match in re.findall(r"(?i)(?:unread|new)\D{0,12}(\d{1,3})", value)
                )
    return numbers


def platform_page(context, hosts: set[str]) -> Page:
    candidates = [
        page for page in context.pages if urlsplit(page.url).hostname in hosts
    ]
    return candidates[0] if candidates else context.new_page()


def reddit_chat_badge_count(page: Page) -> int | None:
    """Read the homepage chat counter, never the chat list or its previews."""
    badge = page.locator("#header-action-item-chat-button-badge")
    if badge.count() != 1:
        return None
    numbers = [
        *badge_numbers(badge),
        *badge_numbers(badge.locator("span, [aria-label]")),
    ]
    initial = badge.get_attribute("initial-count") or ""
    if re.fullmatch(r"\d{1,6}", initial):
        numbers.append(int(initial))
    return max(numbers) if numbers else None


REDDIT_NOTIFICATION_COUNTER_SCRIPT = r"""element => {
  // The hydrated count can differ from the original HTML attribute.
  if (element.count !== undefined) {
    return Number.isSafeInteger(element.count) && element.count >= 0
      ? element.count : null;
  }
  const initial = element.getAttribute('initial-count');
  return /^\d{1,6}$/.test(initial || '') ? Number(initial) : null;
}"""

REDDIT_NOTIFICATION_EMPTY_SCRIPT = r"""navigation => {
  // A fresh server render omits the badge when this explicit count is zero.
  const tracker = navigation.closest('faceplate-tracker[noun="inbox"]');
  try {
    const context = JSON.parse(tracker?.getAttribute('data-faceplate-tracking-context') || 'null');
    const count = context?.inbox?.badgeCount;
    return count === 0 || count === '0' ? 0 : null;
  } catch (_) {
    return null;
  }
}"""


def reddit_notification_badge_count(page: Page) -> int | None:
    """Read the bell's sibling badge, without opening notification content."""
    badge = page.locator('dynamic-badge[data-id="notification-count-element"]')
    count = badge.count()
    if count > 1:
        return None
    navigation = page.locator("#notifications-inbox-button")
    if navigation.count() != 1 or not navigation.is_visible():
        return None
    if count == 0:
        return navigation.evaluate(REDDIT_NOTIFICATION_EMPTY_SCRIPT)
    # The badge itself has a zero-size box at count=0; that is not a failure.
    return badge.evaluate(REDDIT_NOTIFICATION_COUNTER_SCRIPT)


def exact_term_present(page: Page, term: str) -> bool:
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    locator = page.get_by_text(pattern)
    if any(locator.nth(index).is_visible() for index in range(min(locator.count(), 20))):
        return True
    return bool(
        page.locator("html").evaluate(
            "(el, value) => el.outerHTML.toLowerCase().includes(value.toLowerCase())",
            term,
        )
    )


def resolve_reddit_author(page: Page, source_url: str) -> str:
    page.goto(source_url, wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(3_000)
    post = page.locator("shreddit-post[author]").first
    author = (post.get_attribute("author") or "").strip() if post.count() else ""
    if not PARTICIPANT.fullmatch(author):
        raise RuntimeError("Reddit did not expose the allowlisted public post author")
    return author


def collect_observation(config: dict, *, cdp: str = DEFAULT_CDP) -> dict:
    campaigns = config["campaigns"]
    with browser_tools.browser_operation_lock(), sync_playwright() as playwright:
        connected = playwright.chromium.connect_over_cdp(cdp)
        if len(connected.contexts) != 1:
            raise RuntimeError("expected one project browser context")
        context = connected.contexts[0]

        instagram_page = platform_page(context, {"instagram.com", "www.instagram.com"})
        instagram_page.bring_to_front()
        instagram_page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30_000)
        instagram_page.wait_for_timeout(3_000)
        instagram_nav = instagram_page.locator('a[href="/direct/inbox/"], a[href^="/direct/"]')
        instagram_login = instagram_page.locator('input[name="username"], input[name="password"]')
        instagram_numbers = badge_numbers(
            instagram_page.locator(
                'a[href="/direct/inbox/"] [aria-label*="unread" i], '
                'a[href="/direct/inbox/"] [aria-label*="new message" i], '
                'a[href="/direct/inbox/"] span'
            )
        )
        instagram = {
            "authenticated": instagram_login.count() == 0 and instagram_nav.count() > 0,
            "navigation_available": instagram_nav.count() > 0,
            "unread_badge_total": max(instagram_numbers, default=0),
        }
        instagram_page.goto(
            "https://www.instagram.com/direct/inbox/",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        instagram_page.wait_for_timeout(3_000)

        reddit_page = platform_page(context, {"reddit.com", "www.reddit.com"})
        reddit_authors = {
            item["campaign_id"]: resolve_reddit_author(reddit_page, item["source_url"])
            for item in campaigns
            if item["platform"] == "reddit"
        }
        reddit_page.goto("https://www.reddit.com/", wait_until="domcontentloaded", timeout=30_000)
        reddit_page.wait_for_timeout(3_000)
        reddit_nav = reddit_page.locator(
            'a[href*="/message"], a[href*="/notifications"], '
            'button[aria-label*="message" i], button[aria-label*="notification" i]'
        )
        reddit_login = reddit_page.locator('a[href*="/login"], button:has-text("Log In")')
        reddit_numbers = badge_numbers(
            reddit_page.locator(
                'a[href*="/message"] [aria-label], a[href*="/message"] faceplate-number, '
                'a[href*="/message"] span, button[aria-label*="message" i] span, '
                'a[href*="/notifications"] faceplate-number'
            )
        )
        reddit = {
            "authenticated": reddit_login.count() == 0 and reddit_nav.count() > 0,
            "navigation_available": reddit_nav.count() > 0,
            "unread_badge_total": max(reddit_numbers, default=0),
            "chat_navigation_available": reddit_page.locator(
                "#header-action-item-chat-button"
            ).count() == 1,
            "chat_unread_badge_total": reddit_chat_badge_count(reddit_page),
            "notification_navigation_available": reddit_page.locator(
                "#notifications-inbox-button"
            ).count() == 1,
            "notification_unread_badge_total": reddit_notification_badge_count(reddit_page),
        }
        reddit_page.goto(
            "https://www.reddit.com/message/inbox/",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        reddit_page.wait_for_timeout(3_000)

        matched = []
        for item in campaigns:
            page = instagram_page if item["platform"] == "instagram" else reddit_page
            term = (
                item["participant"]
                if item["platform"] == "instagram"
                else reddit_authors[item["campaign_id"]]
            )
            matched.append(
                {
                    "campaign_id": item["campaign_id"],
                    "platform": item["platform"],
                    "known_participant_present": exact_term_present(page, term),
                }
            )
        connected.close()

    return {
        "checked_at": inbound_monitor.utc_now(),
        "platforms": {"instagram": instagram, "reddit": reddit},
        "campaigns": matched,
    }


def summarize_observation(observed: dict, previous: dict | None) -> tuple[dict, dict]:
    platforms = observed.get("platforms")
    campaigns = observed.get("campaigns")
    if not isinstance(platforms, dict) or not isinstance(campaigns, list):
        raise ValueError("the social inbox observation is invalid")
    prior_platforms = (previous or {}).get("platforms", {})
    prior_campaigns = {
        item.get("campaign_id"): item
        for item in (previous or {}).get("campaigns", [])
        if isinstance(item, dict)
    }
    alerts = []
    safe_platforms = {}
    state_platforms = {}
    for platform in sorted(PLATFORMS):
        item = platforms.get(platform)
        if not isinstance(item, dict):
            raise ValueError("the social inbox platform observation is invalid")
        unread = item.get("unread_badge_total")
        if isinstance(unread, bool) or not isinstance(unread, int) or unread < 0:
            raise ValueError("the social inbox unread count is invalid")
        authenticated = bool(item.get("authenticated"))
        navigation = bool(item.get("navigation_available"))
        prior_unread = prior_platforms.get(platform, {}).get("unread_badge_total")
        if isinstance(prior_unread, int) and unread > prior_unread:
            alerts.append(
                {
                    "kind": "social_inbox_unread_increased",
                    "platform": platform,
                    "unread_delta": unread - prior_unread,
                }
            )
        safe_platforms[platform] = {
            "authenticated": authenticated,
            "navigation_available": navigation,
            "unread_badge_total": unread,
            "layout_unknown": authenticated and not navigation,
        }
        state_platforms[platform] = {"unread_badge_total": unread}
        for counter in ("chat", "notification") if platform == "reddit" else ():
            count_key = f"{counter}_unread_badge_total"
            navigation_key = f"{counter}_navigation_available"
            if count_key not in item:
                continue
            count = item[count_key]
            if count is not None and (
                isinstance(count, bool)
                or not isinstance(count, int)
                or count < 0
            ):
                raise ValueError(f"the Reddit {counter} unread count is invalid")
            counter_navigation = bool(item.get(navigation_key))
            prior_count = prior_platforms.get(platform, {}).get(count_key)
            if isinstance(count, int) and count > 0 and (
                not isinstance(prior_count, int) or count > prior_count
            ):
                alerts.append(
                    {
                        "kind": f"reddit_{counter}_unread_detected",
                        "platform": "reddit",
                        "unread_badge_total": count,
                    }
                )
            safe_platforms[platform].update({
                navigation_key: counter_navigation,
                count_key: count,
                "layout_unknown": safe_platforms[platform]["layout_unknown"]
                or (authenticated and (not counter_navigation or count is None)),
            })
            # An unavailable badge is not evidence that the inbox became empty.
            state_platforms[platform][count_key] = (
                count if count is not None else prior_count
            )

    safe_campaigns = []
    state_campaigns = []
    for item in campaigns:
        if not isinstance(item, dict):
            raise ValueError("the social inbox campaign observation is invalid")
        campaign_id = str(item.get("campaign_id") or "")
        platform = str(item.get("platform") or "")
        present = bool(item.get("known_participant_present"))
        if not CAMPAIGN_ID.fullmatch(campaign_id) or platform not in PLATFORMS:
            raise ValueError("the social inbox campaign observation is invalid")
        previous_present = bool(prior_campaigns.get(campaign_id, {}).get("known_participant_present"))
        if previous is not None and present and not previous_present:
            alerts.append(
                {
                    "kind": "known_campaign_participant_appeared",
                    "campaign_id": campaign_id,
                    "platform": platform,
                }
            )
        record = {
            "campaign_id": campaign_id,
            "platform": platform,
            "known_participant_present": present,
        }
        safe_campaigns.append(record)
        state_campaigns.append(record)

    status = {
        "checked_at": str(observed.get("checked_at") or inbound_monitor.utc_now()),
        "available": True,
        "baseline_created": previous is None,
        "platforms": safe_platforms,
        "campaigns": safe_campaigns,
        "alerts": alerts,
        "review_required": bool(alerts) or any(
            item["layout_unknown"] for item in safe_platforms.values()
        ),
        "policy": {
            "conversation_opened": False,
            "message_body_or_preview_collected": False,
            "participant_persisted": False,
            "automatic_reply": False,
            "activity_is_not_a_lead_or_revenue": True,
        },
    }
    state = {
        "checked_at": status["checked_at"],
        "platforms": state_platforms,
        "campaigns": state_campaigns,
    }
    return status, state


def read_json(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("the social inbox state is invalid") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("the social inbox state is invalid")
    return payload


def monitor_once(
    *,
    config_path: Path = CONFIG_PATH,
    state_path: Path = STATE_PATH,
    status_path: Path = STATUS_PATH,
    log_path: Path = LOG_PATH,
    cdp: str = DEFAULT_CDP,
) -> dict:
    observed = collect_observation(load_config(config_path), cdp=cdp)
    status, state = summarize_observation(observed, read_json(state_path))
    inbound_monitor.atomic_write_json(state_path, state)
    inbound_monitor.atomic_write_json(status_path, status)
    inbound_monitor.append_log(log_path, status)
    return status


def status_summary(path: Path = STATUS_PATH) -> dict:
    payload = read_json(path)
    if payload is None:
        return {"available": False, "review_required": False}
    return {
        "available": bool(payload.get("available")),
        "checked_at": payload.get("checked_at"),
        "baseline_created": bool(payload.get("baseline_created")),
        "review_required": bool(payload.get("review_required")),
        "alert_count": len(payload.get("alerts", [])),
        "platforms": payload.get("platforms", {}),
        "campaigns": payload.get("campaigns", []),
        "policy": payload.get("policy", {}),
    }


def loop(interval_minutes: int) -> None:
    if interval_minutes < 15:
        raise ValueError("interval must be at least fifteen minutes")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("social inbox monitor is already running") from exc
        while True:
            try:
                monitor_once()
            except Exception as exc:
                failure = {
                    "checked_at": inbound_monitor.utc_now(),
                    "available": False,
                    "review_required": True,
                    "error": str(exc),
                    "policy": {"automatic_reply": False},
                }
                inbound_monitor.atomic_write_json(STATUS_PATH, failure)
                inbound_monitor.append_log(LOG_PATH, failure)
            time.sleep(interval_minutes * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("once", help="Run one visible, read-only aggregate observation.")
    subparsers.add_parser("status", help="Print the privacy-limited last status.")
    loop_parser = subparsers.add_parser("loop", help="Repeat while the isolated browser remains active.")
    loop_parser.add_argument("--interval-minutes", type=int, default=15)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "once":
        report = monitor_once()
    elif args.command == "status":
        report = status_summary()
    else:
        loop(args.interval_minutes)
        return
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
