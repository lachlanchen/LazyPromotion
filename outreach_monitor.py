#!/usr/bin/env python3
"""Monitor a private business-outreach folder badge without opening mail."""

from __future__ import annotations

import argparse
import fcntl
import json
import re
import sqlite3
import time
from pathlib import Path

import browser
import inbound_monitor


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local"
CONFIG_PATH = RUNTIME / "private" / "outreach-monitor.json"
DB_PATH = RUNTIME / "outreach-monitor.sqlite3"
STATUS_PATH = RUNTIME / "outreach-monitor-status.json"
LOG_PATH = RUNTIME / "outreach-monitor.jsonl"
LOCK_PATH = RUNTIME / "outreach-monitor.lock"
BADGE_RE = re.compile(r"^(\d+)(?:\+)?$")


def load_config(path: Path = CONFIG_PATH) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("the private outreach monitor configuration is unavailable") from exc
    folder_name = str(payload.get("folder_name") or "").strip()
    public_label = str(payload.get("public_label") or "").strip()
    if not folder_name or not public_label:
        raise RuntimeError("the private outreach monitor configuration is incomplete")
    if "@" in public_label or len(public_label) > 80:
        raise RuntimeError("the outreach monitor public label is unsafe")
    return {"folder_name": folder_name, "public_label": public_label}


def unread_badge_expression(folder_name: str) -> str:
    """Return JavaScript that reads only numeric descendants of one folder row."""
    encoded_name = json.dumps(folder_name, ensure_ascii=False)
    return f"""(() => {{
      const name = {encoded_name};
      const folder = Array.from(document.querySelectorAll('[role="option"][aria-label]'))
        .find((item) => item.getAttribute('aria-label') === name);
      if (!folder) return {{folderFound: false, badgeTexts: []}};
      const numeric = /^(\\d+)(?:\\+)?$/;
      const badgeTexts = Array.from(folder.querySelectorAll('*'))
        .map((item) => (item.innerText || '').replace(/\\s+/g, ' ').trim())
        .filter((text) => numeric.test(text));
      return {{
        folderFound: true,
        folderSelected: folder.getAttribute('aria-selected') === 'true',
        badgeTexts: Array.from(new Set(badgeTexts)),
      }};
    }})()"""


def parse_badge_texts(values: object) -> int:
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise ValueError("iCloud exposed an invalid folder badge")
    counts = set()
    for value in values:
        match = BADGE_RE.fullmatch(value.strip())
        if not match:
            raise ValueError("iCloud exposed an invalid folder badge")
        counts.add(int(match.group(1)))
    if not counts:
        return 0
    if len(counts) != 1:
        raise ValueError("iCloud exposed conflicting folder badges")
    return counts.pop()


def read_unread_badge(*, cdp: str, folder_name: str) -> int:
    """Read one folder's unread badge without selecting it or opening messages."""
    with browser.browser_operation_lock():
        target = inbound_monitor.icloud_mail_target(inbound_monitor.load_cdp_targets(cdp))
        with inbound_monitor.open_cdp_target(
            str(target["webSocketDebuggerUrl"])
        ) as connection:
            tree = connection.command("Page.getFrameTree").get("frameTree")
            if not isinstance(tree, dict):
                raise RuntimeError("the iCloud Mail frame tree is unavailable")
            frame = inbound_monitor.find_mail_app_frame(tree)
            frame_id = frame.get("id")
            if not frame_id:
                raise RuntimeError("the iCloud Mail application frame is unavailable")
            isolated = connection.command(
                "Page.createIsolatedWorld",
                {
                    "frameId": frame_id,
                    "worldName": "lazypromotion-outreach-badge",
                    "grantUniveralAccess": False,
                },
            )
            context_id = isolated.get("executionContextId")
            if not context_id:
                raise RuntimeError("the outreach badge context is unavailable")
            evaluated = connection.command(
                "Runtime.evaluate",
                {
                    "contextId": context_id,
                    "expression": unread_badge_expression(folder_name),
                    "returnByValue": True,
                    "awaitPromise": False,
                },
            )
        if evaluated.get("exceptionDetails"):
            raise RuntimeError("iCloud did not expose the outreach folder badge")
        payload = evaluated.get("result", {}).get("value")
        if not isinstance(payload, dict) or not payload.get("folderFound"):
            raise RuntimeError("the configured outreach folder is unavailable")
        return parse_badge_texts(payload.get("badgeTexts"))


def open_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS outreach_unread_observations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          observed_at TEXT NOT NULL,
          public_label TEXT NOT NULL,
          unread_count INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS outreach_unread_observations_latest
          ON outreach_unread_observations(public_label, id DESC);
        """
    )
    return db


def record_observation(
    unread_count: int,
    *,
    public_label: str,
    db_path: Path = DB_PATH,
    status_path: Path = STATUS_PATH,
    observed_at: str | None = None,
) -> dict:
    if unread_count < 0:
        raise ValueError("the unread count cannot be negative")
    if not public_label or "@" in public_label:
        raise ValueError("the public folder label is unsafe")
    observed_at = observed_at or inbound_monitor.utc_now()
    db = open_db(db_path)
    try:
        previous = db.execute(
            """
            SELECT unread_count FROM outreach_unread_observations
            WHERE public_label=? ORDER BY id DESC LIMIT 1
            """,
            (public_label,),
        ).fetchone()
        alerts = []
        if previous and unread_count > int(previous["unread_count"]):
            alerts.append(
                {
                    "kind": "outreach_unread_increased",
                    "unread_delta": unread_count - int(previous["unread_count"]),
                    "action": "Review the business outreach folder visibly before changing funnel state.",
                }
            )
        db.execute(
            """
            INSERT INTO outreach_unread_observations
              (observed_at, public_label, unread_count)
            VALUES (?, ?, ?)
            """,
            (observed_at, public_label, unread_count),
        )
        db.commit()
    finally:
        db.close()
    report = {
        "checked_at": observed_at,
        "folder": public_label,
        "unread_count": unread_count,
        "alerts": alerts,
        "policy": {
            "message_content_opened": False,
            "message_metadata_persisted": False,
            "unread_increase_is_not_a_qualified_lead": True,
            "automatic_reply": False,
        },
    }
    inbound_monitor.atomic_write_json(status_path, report)
    return report


def monitor_once(*, config_path: Path = CONFIG_PATH) -> dict:
    config = load_config(config_path)
    unread_count = read_unread_badge(
        cdp=browser.DEFAULT_CDP,
        folder_name=config["folder_name"],
    )
    return record_observation(unread_count, public_label=config["public_label"])


def loop(interval_minutes: int) -> None:
    if interval_minutes < 5:
        raise ValueError("interval must be at least five minutes")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("outreach monitor is already running") from exc
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
    commands.add_parser("once", help="Read and record one aggregate unread badge.")
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
