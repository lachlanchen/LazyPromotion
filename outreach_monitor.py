#!/usr/bin/env python3
"""Monitor private business-outreach folder counts without opening mail."""

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
CONFIG_PATH = RUNTIME / "private" / "outreach-monitor.json"
DB_PATH = RUNTIME / "outreach-monitor.sqlite3"
STATUS_PATH = RUNTIME / "outreach-monitor-status.json"
LOG_PATH = RUNTIME / "outreach-monitor.jsonl"
LOCK_PATH = RUNTIME / "outreach-monitor.lock"


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


def icloud_mail_targets(targets: list[dict]) -> list[dict]:
    """Return every attachable top-level iCloud Mail page target."""
    matches = []
    for target in targets:
        if target.get("type") != "page":
            continue
        parsed = urlsplit(str(target.get("url") or ""))
        if (
            parsed.hostname == inbound_monitor.MAIL_PAGE_HOST
            and parsed.path.startswith("/mail")
            and target.get("webSocketDebuggerUrl")
        ):
            matches.append(target)
    if not matches:
        raise RuntimeError("the authenticated iCloud Mail page is not open")
    return matches


def read_folder_status(connection, *, folder_name: str, world_number: int) -> dict:
    """Inspect one Mail tab for only the configured folder's aggregate status."""
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
            "worldName": f"lazypromotion-outreach-counts-{world_number}",
            "grantUniveralAccess": False,
        },
    )
    context_id = isolated.get("executionContextId")
    if not context_id:
        raise RuntimeError("the outreach aggregate-count context is unavailable")
    evaluated = connection.command(
        "Runtime.evaluate",
        {
            "contextId": context_id,
            "expression": inbound_monitor.aggregate_status_expression(folder_name),
            "returnByValue": True,
            "awaitPromise": False,
        },
    )
    if evaluated.get("exceptionDetails"):
        raise RuntimeError("iCloud did not expose the outreach folder aggregate status")
    payload = evaluated.get("result", {}).get("value")
    if not isinstance(payload, dict):
        raise RuntimeError("iCloud exposed an invalid outreach folder status")
    if payload.get("folderSelected") and not payload.get("folderFound"):
        raise RuntimeError("iCloud exposed an inconsistent outreach folder status")
    return payload


def read_folder_counts(*, cdp: str, folder_name: str) -> tuple[int, int]:
    """Read aggregate counts from exactly one already-selected outreach folder."""
    with browser.browser_operation_lock():
        targets = icloud_mail_targets(inbound_monitor.load_cdp_targets(cdp))
        selected = []
        for index, target in enumerate(targets):
            with inbound_monitor.open_cdp_target(
                str(target["webSocketDebuggerUrl"])
            ) as connection:
                payload = read_folder_status(
                    connection,
                    folder_name=folder_name,
                    world_number=index,
                )
            if payload.get("folderFound") and payload.get("folderSelected"):
                selected.append(payload)

        if len(selected) != 1:
            raise RuntimeError(
                "exactly one iCloud Mail tab must have the outreach folder selected"
            )
        return inbound_monitor.parse_folder_status(selected[0].get("status"))


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
        CREATE TABLE IF NOT EXISTS outreach_count_observations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          observed_at TEXT NOT NULL,
          public_label TEXT NOT NULL,
          message_count INTEGER NOT NULL,
          unread_count INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS outreach_count_observations_latest
          ON outreach_count_observations(public_label, id DESC);
        """
    )
    return db


def record_observation(
    message_count: int,
    unread_count: int,
    *,
    public_label: str,
    db_path: Path = DB_PATH,
    status_path: Path = STATUS_PATH,
    observed_at: str | None = None,
) -> dict:
    if message_count < 0 or unread_count < 0 or unread_count > message_count:
        raise ValueError("the outreach folder counts are invalid")
    if not public_label or "@" in public_label:
        raise ValueError("the public folder label is unsafe")
    observed_at = observed_at or inbound_monitor.utc_now()
    db = open_db(db_path)
    try:
        previous = db.execute(
            """
            SELECT message_count, unread_count FROM outreach_count_observations
            WHERE public_label=? ORDER BY id DESC LIMIT 1
            """,
            (public_label,),
        ).fetchone()
        alerts = []
        if previous and message_count > int(previous["message_count"]):
            alerts.append(
                {
                    "kind": "outreach_count_increased",
                    "message_delta": message_count - int(previous["message_count"]),
                    "action": "Review the business outreach folder visibly before changing funnel state.",
                }
            )
        db.execute(
            """
            INSERT INTO outreach_count_observations
              (observed_at, public_label, message_count, unread_count)
            VALUES (?, ?, ?, ?)
            """,
            (observed_at, public_label, message_count, unread_count),
        )
        db.commit()
    finally:
        db.close()
    report = {
        "checked_at": observed_at,
        "folder": public_label,
        "message_count": message_count,
        "unread_count": unread_count,
        "alerts": alerts,
        "policy": {
            "message_content_opened": False,
            "message_metadata_persisted": False,
            "count_increase_is_not_a_qualified_lead": True,
            "automatic_reply": False,
        },
    }
    inbound_monitor.atomic_write_json(status_path, report)
    return report


def monitor_once(*, config_path: Path = CONFIG_PATH) -> dict:
    config = load_config(config_path)
    message_count, unread_count = read_folder_counts(
        cdp=browser.DEFAULT_CDP,
        folder_name=config["folder_name"],
    )
    return record_observation(
        message_count,
        unread_count,
        public_label=config["public_label"],
    )


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
    commands.add_parser("once", help="Read and record aggregate folder counts.")
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
