#!/usr/bin/env python3
"""Monitor one open LinkedIn outreach thread by aggregate event count only."""

from __future__ import annotations

import argparse
import fcntl
import json
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlsplit

import browser
import inbound_monitor


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local"
CONFIG_PATH = RUNTIME / "private" / "linkedin-reply-monitor.json"
DB_PATH = RUNTIME / "linkedin-reply-monitor.sqlite3"
STATUS_PATH = RUNTIME / "linkedin-reply-monitor-status.json"
LOG_PATH = RUNTIME / "linkedin-reply-monitor.jsonl"
LOCK_PATH = RUNTIME / "linkedin-reply-monitor.lock"
LINKEDIN_HOST = "www.linkedin.com"
THREAD_PATH_PREFIX = "/messaging/thread/"


def validate_thread_url(value: str) -> str:
    thread_url = str(value or "").strip()
    parsed = urlsplit(thread_url)
    path = parsed.path.rstrip("/") + "/"
    if (
        parsed.scheme != "https"
        or parsed.hostname != LINKEDIN_HOST
        or not path.startswith(THREAD_PATH_PREFIX)
        or path == THREAD_PATH_PREFIX
    ):
        raise ValueError("the private LinkedIn thread URL is invalid")
    return thread_url


def load_config(path: Path = CONFIG_PATH) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("the private LinkedIn monitor configuration is unavailable") from exc
    thread_url = validate_thread_url(payload.get("thread_url"))
    public_label = str(payload.get("public_label") or "").strip()
    minimum_event_count = payload.get("minimum_event_count", 1)
    if not public_label or "@" in public_label or len(public_label) > 80:
        raise RuntimeError("the LinkedIn monitor public label is unsafe")
    if (
        isinstance(minimum_event_count, bool)
        or not isinstance(minimum_event_count, int)
        or minimum_event_count < 1
    ):
        raise RuntimeError("the LinkedIn monitor minimum event count is invalid")
    return {
        "thread_url": thread_url,
        "public_label": public_label,
        "minimum_event_count": minimum_event_count,
    }


def linkedin_thread_target(targets: list[dict], thread_url: str) -> dict:
    expected = urlsplit(validate_thread_url(thread_url))
    expected_path = expected.path.rstrip("/")
    matches = []
    for target in targets:
        if target.get("type") != "page" or not target.get("webSocketDebuggerUrl"):
            continue
        parsed = urlsplit(str(target.get("url") or ""))
        if parsed.hostname == LINKEDIN_HOST and parsed.path.rstrip("/") == expected_path:
            matches.append(target)
    if len(matches) != 1:
        raise RuntimeError("the configured LinkedIn conversation is not open exactly once")
    return matches[0]


def event_count_expression() -> str:
    """Return JavaScript that exposes no message text or sender metadata."""
    return """(() => ({
      conversationFound: Boolean(document.querySelector('main')),
      eventCount: document.querySelectorAll('li.msg-s-message-list__event').length,
    }))()"""


def parse_event_count(payload: object, *, minimum_event_count: int) -> int:
    if not isinstance(payload, dict) or not payload.get("conversationFound"):
        raise RuntimeError("LinkedIn did not expose the open conversation")
    count = payload.get("eventCount")
    if isinstance(count, bool) or not isinstance(count, int) or count < minimum_event_count:
        raise RuntimeError("LinkedIn did not expose the expected aggregate event count")
    return count


def read_event_count(
    *,
    cdp: str,
    thread_url: str,
    minimum_event_count: int,
) -> int:
    """Read an exact already-open thread without focus, navigation, or message access."""
    with browser.browser_operation_lock():
        target = linkedin_thread_target(
            inbound_monitor.load_cdp_targets(cdp),
            thread_url,
        )
        with inbound_monitor.open_cdp_target(
            str(target["webSocketDebuggerUrl"])
        ) as connection:
            tree = connection.command("Page.getFrameTree").get("frameTree")
            if not isinstance(tree, dict):
                raise RuntimeError("the LinkedIn conversation frame is unavailable")
            frame_id = tree.get("frame", {}).get("id")
            if not frame_id:
                raise RuntimeError("the LinkedIn conversation frame is unavailable")
            isolated = connection.command(
                "Page.createIsolatedWorld",
                {
                    "frameId": frame_id,
                    "worldName": "lazypromotion-linkedin-event-count",
                    "grantUniveralAccess": False,
                },
            )
            context_id = isolated.get("executionContextId")
            if not context_id:
                raise RuntimeError("the LinkedIn aggregate-count context is unavailable")
            evaluated = connection.command(
                "Runtime.evaluate",
                {
                    "contextId": context_id,
                    "expression": event_count_expression(),
                    "returnByValue": True,
                    "awaitPromise": False,
                },
            )
        if evaluated.get("exceptionDetails"):
            raise RuntimeError("LinkedIn did not expose the aggregate event count")
        return parse_event_count(
            evaluated.get("result", {}).get("value"),
            minimum_event_count=minimum_event_count,
        )


def open_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS linkedin_event_observations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          observed_at TEXT NOT NULL,
          public_label TEXT NOT NULL,
          event_count INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS linkedin_event_observations_latest
          ON linkedin_event_observations(public_label, id DESC);
        """
    )
    return db


def record_observation(
    event_count: int,
    *,
    public_label: str,
    db_path: Path = DB_PATH,
    status_path: Path = STATUS_PATH,
    observed_at: str | None = None,
) -> dict:
    if isinstance(event_count, bool) or not isinstance(event_count, int) or event_count < 1:
        raise ValueError("the LinkedIn event count is invalid")
    if not public_label or "@" in public_label or len(public_label) > 80:
        raise ValueError("the LinkedIn monitor public label is unsafe")
    observed_at = observed_at or inbound_monitor.utc_now()
    db = open_db(db_path)
    try:
        previous = db.execute(
            """
            SELECT event_count FROM linkedin_event_observations
            WHERE public_label=? ORDER BY id DESC LIMIT 1
            """,
            (public_label,),
        ).fetchone()
        if previous and event_count < int(previous["event_count"]):
            raise RuntimeError("the LinkedIn aggregate event count decreased")
        alerts = []
        if previous and event_count > int(previous["event_count"]):
            alerts.append(
                {
                    "kind": "linkedin_conversation_event_count_increased",
                    "event_delta": event_count - int(previous["event_count"]),
                    "action": (
                        "Review the exact conversation visibly before recording a reply, "
                        "qualified lead, scope acceptance, or sale."
                    ),
                }
            )
        db.execute(
            """
            INSERT INTO linkedin_event_observations
              (observed_at, public_label, event_count)
            VALUES (?, ?, ?)
            """,
            (observed_at, public_label, event_count),
        )
        db.commit()
    finally:
        db.close()

    report = {
        "checked_at": observed_at,
        "conversation": public_label,
        "event_count": event_count,
        "alerts": alerts,
        "policy": {
            "message_content_read": False,
            "sender_metadata_persisted": False,
            "event_increase_is_not_a_reply_or_lead": True,
            "automatic_reply": False,
        },
    }
    inbound_monitor.atomic_write_json(status_path, report)
    return report


def monitor_once(*, config_path: Path = CONFIG_PATH) -> dict:
    config = load_config(config_path)
    event_count = read_event_count(
        cdp=browser.DEFAULT_CDP,
        thread_url=config["thread_url"],
        minimum_event_count=config["minimum_event_count"],
    )
    return record_observation(event_count, public_label=config["public_label"])


def loop(interval_minutes: int) -> None:
    if interval_minutes < 5:
        raise ValueError("interval must be at least five minutes")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("LinkedIn reply monitor is already running") from exc
        while True:
            try:
                report = monitor_once()
                inbound_monitor.append_log(LOG_PATH, report)
            except Exception as exc:
                failure = {"checked_at": inbound_monitor.utc_now(), "error": str(exc)}
                inbound_monitor.atomic_write_json(STATUS_PATH, failure)
                inbound_monitor.append_log(LOG_PATH, failure)
            time.sleep(interval_minutes * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("once", help="Read and record one aggregate conversation count.")
    continuous = commands.add_parser("loop", help="Repeat aggregate observations.")
    continuous.add_argument("--interval-minutes", type=int, default=15)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "once":
        print(json.dumps(monitor_once(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        loop(args.interval_minutes)


if __name__ == "__main__":
    main()
