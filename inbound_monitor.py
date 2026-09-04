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
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import websocket

import browser


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local"
DB_PATH = RUNTIME / "inbound-monitor.sqlite3"
STATUS_PATH = RUNTIME / "inbound-monitor-status.json"
LOG_PATH = RUNTIME / "inbound-monitor.jsonl"
LOCK_PATH = RUNTIME / "inbound-monitor.lock"
FOLDER_NAME = "LKT Fit Checks"
STATUS_RE = re.compile(
    r"^\s*(\d+)\s+Messages?(?:\s*,\s*(\d+)\s+unread)?\s*$",
    re.IGNORECASE,
)
CDP_HTTP_TIMEOUT_SECONDS = 5
CDP_COMMAND_TIMEOUT_SECONDS = 10
MAIL_PAGE_HOST = "www.icloud.com"
MAIL_APP_FRAME_PATH = "/applications/mail2/"


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
    # iCloud omits the unread clause entirely when its value is zero.
    return int(match.group(1)), int(match.group(2) or 0)


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


def cdp_http_url(endpoint: str, path: str) -> str:
    parsed = urlsplit(str(endpoint or ""))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("CDP endpoint must be an HTTP(S) URL")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def load_cdp_targets(
    endpoint: str,
    *,
    timeout_seconds: float = CDP_HTTP_TIMEOUT_SECONDS,
) -> list[dict]:
    """Load target metadata without attaching Playwright to every open tab."""
    try:
        with urllib.request.urlopen(
            cdp_http_url(endpoint, "/json/list"),
            timeout=timeout_seconds,
        ) as response:
            targets = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError("the project CDP endpoint is unavailable") from exc
    if not isinstance(targets, list):
        raise RuntimeError("the project CDP endpoint returned an invalid target list")
    return [item for item in targets if isinstance(item, dict)]


def icloud_mail_target(targets: list[dict]) -> dict:
    for target in targets:
        if target.get("type") != "page":
            continue
        parsed = urlsplit(str(target.get("url") or ""))
        if parsed.hostname == MAIL_PAGE_HOST and parsed.path.startswith("/mail"):
            if target.get("webSocketDebuggerUrl"):
                return target
    raise RuntimeError("the authenticated iCloud Mail page is not open")


class CdpConnection:
    """Small synchronous CDP client for one already-open browser target."""

    def __init__(self, websocket_url: str, *, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds
        self.sequence = 0
        try:
            self.socket = websocket.create_connection(
                websocket_url,
                timeout=timeout_seconds,
                suppress_origin=True,
            )
        except (OSError, websocket.WebSocketException) as exc:
            raise RuntimeError("could not attach to the iCloud Mail browser target") from exc

    def close(self) -> None:
        self.socket.close()

    def command(self, method: str, params: dict | None = None) -> dict:
        self.sequence += 1
        command_id = self.sequence
        message = {"id": command_id, "method": method}
        if params:
            message["params"] = params
        try:
            self.socket.send(json.dumps(message))
            deadline = time.monotonic() + self.timeout_seconds
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError
                self.socket.settimeout(remaining)
                reply = json.loads(self.socket.recv())
                if reply.get("id") != command_id:
                    continue
                if reply.get("error"):
                    raise RuntimeError(f"CDP command failed: {method}")
                result = reply.get("result")
                if not isinstance(result, dict):
                    raise RuntimeError(f"CDP returned an invalid result: {method}")
                return result
        except (OSError, TimeoutError, ValueError, websocket.WebSocketException) as exc:
            raise RuntimeError(f"CDP command did not complete: {method}") from exc


@contextmanager
def open_cdp_target(
    websocket_url: str,
    *,
    timeout_seconds: float = CDP_COMMAND_TIMEOUT_SECONDS,
):
    connection = CdpConnection(websocket_url, timeout_seconds=timeout_seconds)
    try:
        yield connection
    finally:
        connection.close()


def find_mail_app_frame(frame_tree: dict) -> dict:
    """Find the mailbox application frame, excluding its message-body frame."""
    pending = [frame_tree]
    while pending:
        node = pending.pop(0)
        frame = node.get("frame") if isinstance(node, dict) else None
        if isinstance(frame, dict):
            parsed = urlsplit(str(frame.get("url") or ""))
            if parsed.path.startswith(MAIL_APP_FRAME_PATH):
                return frame
        children = node.get("childFrames", []) if isinstance(node, dict) else []
        pending.extend(item for item in children if isinstance(item, dict))
    raise RuntimeError("the iCloud Mail application frame is unavailable")


def aggregate_status_expression(folder_name: str) -> str:
    """Return JavaScript that exposes only the named folder's aggregate status."""
    encoded_name = json.dumps(folder_name, ensure_ascii=False)
    return f"""(() => {{
      const name = {encoded_name};
      const exact = (selector) => Array.from(document.querySelectorAll(selector))
        .find((item) => item.getAttribute('aria-label') === name);
      const folder = exact('[role="option"][aria-label]');
      const heading = exact('h2[aria-label]');
      const status = heading && heading.parentElement
        ? heading.parentElement.querySelector('h3')
        : null;
      return {{
        folderFound: Boolean(folder),
        folderSelected: folder ? folder.getAttribute('aria-selected') === 'true' : false,
        status: status ? status.innerText : null,
      }};
    }})()"""


def read_folder_counts(
    *,
    cdp: str = browser.DEFAULT_CDP,
    folder_name: str = FOLDER_NAME,
) -> tuple[int, int]:
    """Read only the selected folder's aggregate status without changing the UI."""
    with browser.browser_operation_lock():
        target = icloud_mail_target(load_cdp_targets(cdp))
        with open_cdp_target(str(target["webSocketDebuggerUrl"])) as connection:
            tree = connection.command("Page.getFrameTree").get("frameTree")
            if not isinstance(tree, dict):
                raise RuntimeError("the iCloud Mail frame tree is unavailable")
            frame = find_mail_app_frame(tree)
            frame_id = frame.get("id")
            if not frame_id:
                raise RuntimeError("the iCloud Mail application frame is unavailable")
            isolated = connection.command(
                "Page.createIsolatedWorld",
                {
                    "frameId": frame_id,
                    "worldName": "lazypromotion-inbound-counts",
                    "grantUniveralAccess": False,
                },
            )
            context_id = isolated.get("executionContextId")
            if not context_id:
                raise RuntimeError("the aggregate-count context is unavailable")
            evaluated = connection.command(
                "Runtime.evaluate",
                {
                    "contextId": context_id,
                    "expression": aggregate_status_expression(folder_name),
                    "returnByValue": True,
                    "awaitPromise": False,
                },
            )
        if evaluated.get("exceptionDetails"):
            raise RuntimeError("iCloud did not expose the folder aggregate status")
        payload = evaluated.get("result", {}).get("value")
        if not isinstance(payload, dict) or not payload.get("folderFound"):
            raise RuntimeError("the dedicated LKT intake folder is unavailable")
        if not payload.get("folderSelected"):
            raise RuntimeError("the dedicated LKT intake folder is not selected")
        return parse_folder_status(payload.get("status"))


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
