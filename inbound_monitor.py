#!/usr/bin/env python3
"""Monitor the dedicated LKT intake folder without opening or copying mail."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

import browser


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local"
DB_PATH = RUNTIME / "inbound-monitor.sqlite3"
STATUS_PATH = RUNTIME / "inbound-monitor-status.json"
LOG_PATH = RUNTIME / "inbound-monitor.jsonl"
LOCK_PATH = RUNTIME / "inbound-monitor.lock"
FOLDER_NAME = "LKT Fit Checks"
STATUS_RE = re.compile(
    r"^\s*(\d+)\s+Messages?\s*,\s*(\d+)\s+unread\s*$",
    re.IGNORECASE,
)


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_folder_status(value: str) -> tuple[int, int]:
    match = STATUS_RE.fullmatch(str(value or ""))
    if not match:
        raise ValueError("iCloud did not expose the expected folder count status")
    return int(match.group(1)), int(match.group(2))


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def append_log(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def open_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS inbound_count_observations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          observed_at TEXT NOT NULL,
          folder_name TEXT NOT NULL,
          message_count INTEGER NOT NULL,
          unread_count INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS inbound_count_observations_latest
          ON inbound_count_observations(folder_name, id DESC);
        """
    )
    return db


def previous_counts(db: sqlite3.Connection, folder_name: str) -> dict | None:
    row = db.execute(
        """
        SELECT message_count, unread_count FROM inbound_count_observations
        WHERE folder_name=? ORDER BY id DESC LIMIT 1
        """,
        (folder_name,),
    ).fetchone()
    return dict(row) if row else None


def read_folder_counts(
    *,
    cdp: str = browser.DEFAULT_CDP,
    folder_name: str = FOLDER_NAME,
) -> tuple[int, int]:
    """Read only the exact folder's aggregate status from visible iCloud Mail."""
    with browser.browser_operation_lock(), sync_playwright() as playwright:
        connected = playwright.chromium.connect_over_cdp(cdp)
        pages = [page for context in connected.contexts for page in context.pages]
        page = next((item for item in pages if "icloud.com/mail" in item.url), None)
        if page is None:
            raise RuntimeError("the authenticated iCloud Mail page is not open")
        page.bring_to_front()
        frame = next(
            (item for item in page.frames if "/applications/mail2/" in item.url),
            None,
        )
        if frame is None:
            raise RuntimeError("the iCloud Mail application frame is unavailable")

        folder = frame.locator(
            f'[role="option"][aria-label="{folder_name}"]'
        ).first
        if not folder.count() or not folder.is_visible():
            raise RuntimeError("the dedicated LKT intake folder is unavailable")
        if folder.get_attribute("aria-selected") != "true":
            folder.click()

        heading = frame.locator(f'h2[aria-label="{folder_name}"]').first
        heading.wait_for(state="visible", timeout=10000)
        status = heading.locator("xpath=..").locator("h3").first
        status.wait_for(state="visible", timeout=10000)
        counts = parse_folder_status(status.inner_text())
        return counts


def record_observation(
    message_count: int,
    unread_count: int,
    *,
    db_path: Path = DB_PATH,
    status_path: Path = STATUS_PATH,
    folder_name: str = FOLDER_NAME,
    observed_at: str | None = None,
) -> dict:
    if message_count < 0 or unread_count < 0 or unread_count > message_count:
        raise ValueError("mailbox counts are invalid")
    observed_at = observed_at or utc_now()
    db = open_db(db_path)
    try:
        previous = previous_counts(db, folder_name)
        alerts = []
        if previous and message_count > int(previous["message_count"]):
            alerts.append(
                {
                    "kind": "inbound_count_increased",
                    "message_delta": message_count - int(previous["message_count"]),
                    "action": (
                        "Inspect only the dedicated folder in the visible browser; "
                        "review fit before recording a qualified lead or sale."
                    ),
                }
            )
        db.execute(
            """
            INSERT INTO inbound_count_observations
              (observed_at, folder_name, message_count, unread_count)
            VALUES (?, ?, ?, ?)
            """,
            (observed_at, folder_name, message_count, unread_count),
        )
        db.commit()
    finally:
        db.close()

    report = {
        "checked_at": observed_at,
        "folder": folder_name,
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
    atomic_write_json(status_path, report)
    return report


def monitor_once() -> dict:
    message_count, unread_count = read_folder_counts()
    return record_observation(message_count, unread_count)


def loop(interval_minutes: int) -> None:
    if interval_minutes < 5:
        raise ValueError("interval must be at least five minutes")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("inbound monitor is already running") from exc
        while True:
            try:
                report = monitor_once()
                append_log(LOG_PATH, report)
            except Exception as exc:  # keep account and message details out of errors
                failure = {"checked_at": utc_now(), "error": str(exc)}
                atomic_write_json(STATUS_PATH, failure)
                append_log(LOG_PATH, failure)
            time.sleep(interval_minutes * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("once", help="Read and record one aggregate folder count.")
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
