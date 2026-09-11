#!/usr/bin/env python3
"""Poll Bounty's agent API without commenting, claiming, messaging, or submitting."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import stat
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
API_URL = "https://api.trybounty.ai/v1/agent/bounties"
DEFAULT_CREDENTIALS = ROOT / ".local" / "private" / "CREDENTIALS.md"
DEFAULT_STATE = ROOT / ".local" / "bounty-marketplace-monitor-status.json"
DEFAULT_LOCK = ROOT / ".local" / "bounty-marketplace-monitor.lock"
MINIMUM_INTERVAL_MINUTES = 5
MAX_PAGES = 100
KEY_PATTERN = re.compile(r"^ak_[A-Za-z0-9_-]{20,}$")
Opener = Callable[..., Any]


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _safe_private_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    metadata = path.stat()
    if stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1:
        raise ValueError(f"{label} must be private and singly linked")
    return path


def load_api_key(path: Path = DEFAULT_CREDENTIALS) -> str:
    """Read the Bounty API key without returning any other credential data."""
    path = _safe_private_file(path, "credential file")
    section = re.search(
        r"(?ms)^## Bounty agent API\n(.*?)(?=^## |\Z)",
        path.read_text(encoding="utf-8"),
    )
    if not section:
        raise ValueError("Bounty agent API credential section is missing")
    match = re.search(r"(?m)^- API key: `?([^`\s]+)`?\s*$", section.group(1))
    if not match or not KEY_PATTERN.fullmatch(match.group(1)):
        raise ValueError("Bounty agent API key is missing or invalid")
    return match.group(1)


def _api_page(
    api_key: str,
    *,
    cursor: str | None = None,
    opener: Opener = urlopen,
) -> dict[str, Any]:
    if not KEY_PATTERN.fullmatch(api_key):
        raise ValueError("Bounty API key is invalid")
    url = API_URL
    if cursor:
        url += "?" + urlencode({"cursor": cursor})
    request = Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with opener(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Bounty read failed with HTTP {exc.code}") from exc
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise RuntimeError("Bounty read did not return valid JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Bounty returned an invalid response")
    return payload


def _summary(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RuntimeError("Bounty returned an invalid work summary")
    bounty_id = raw.get("_id") or raw.get("id")
    version = raw.get("version")
    if not isinstance(bounty_id, str) or not bounty_id.strip():
        raise RuntimeError("Bounty work summary has no ID")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise RuntimeError("Bounty work summary has no valid version")
    return {"bounty_id": bounty_id.strip(), "version": version}


def fetch_available_bounties(
    api_key: str,
    *,
    opener: Opener = urlopen,
    max_pages: int = MAX_PAGES,
) -> dict[str, Any]:
    """Read every available page. Listing work never creates a Claim."""
    if max_pages < 1:
        raise ValueError("max_pages must be positive")
    cursor: str | None = None
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for page_number in range(1, max_pages + 1):
        payload = _api_page(api_key, cursor=cursor, opener=opener)
        raw_rows = payload.get("bounties")
        is_done = payload.get("is_done")
        next_cursor = payload.get("next_cursor")
        if not isinstance(raw_rows, list) or not isinstance(is_done, bool):
            raise RuntimeError("Bounty returned an invalid page")
        for raw in raw_rows:
            row = _summary(raw)
            if row["bounty_id"] in seen_ids:
                raise RuntimeError("Bounty returned a duplicate work summary")
            seen_ids.add(row["bounty_id"])
            rows.append(row)
        if is_done:
            rows.sort(key=lambda row: (row["bounty_id"], row["version"]))
            return {"bounties": rows, "pages_read": page_number}
        if not isinstance(next_cursor, str) or not next_cursor or next_cursor == cursor:
            raise RuntimeError("Bounty pagination cannot advance")
        cursor = next_cursor
    raise RuntimeError("Bounty pagination exceeded the safety limit")


def validate_local_path(path: Path, *, root: Path = ROOT, suffix: str) -> Path:
    root = root.resolve()
    candidate = Path(os.path.abspath(os.fspath(path)))
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("runtime path must stay inside the repository") from exc
    if len(relative.parts) < 2 or relative.parts[0] != ".local":
        raise ValueError("runtime path must be below .local")
    if candidate.suffix != suffix:
        raise ValueError(f"runtime path must end in {suffix}")
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError("runtime path must not contain symbolic links")
    return candidate


def load_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    path = _safe_private_file(path, "monitor state")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("monitor state is invalid") from exc
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("monitor state is invalid")
    seen = payload.get("seen_bounty_versions")
    if not isinstance(seen, dict) or any(
        not isinstance(key, str)
        or not key
        or isinstance(version, bool)
        or not isinstance(version, int)
        or version < 1
        for key, version in seen.items()
    ):
        raise ValueError("monitor state contains invalid seen work")
    return payload


def write_private_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists() and (path.is_symlink() or not path.is_file()):
            raise ValueError("refusing unsafe monitor state path")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def build_state(
    observation: dict[str, Any],
    previous: dict[str, Any] | None,
    *,
    checked_at: str | None = None,
) -> dict[str, Any]:
    rows = observation.get("bounties")
    pages_read = observation.get("pages_read")
    if not isinstance(rows, list) or not isinstance(pages_read, int) or pages_read < 1:
        raise ValueError("Bounty observation is invalid")
    current = {row["bounty_id"]: row["version"] for row in rows}
    if len(current) != len(rows):
        raise ValueError("Bounty observation contains duplicate IDs")
    previous_seen = dict(previous["seen_bounty_versions"]) if previous else {}
    alerts = []
    if previous is not None:
        for row in rows:
            old_version = previous_seen.get(row["bounty_id"])
            if old_version is None or row["version"] > old_version:
                alerts.append(
                    {
                        "kind": "available_bounty_changed"
                        if old_version
                        else "new_available_bounty",
                        **row,
                        "action": (
                            "Open the current terms and attachments for private fit review; "
                            "do not comment, claim, message, or submit automatically."
                        ),
                    }
                )
    seen = dict(previous_seen)
    for bounty_id, version in current.items():
        seen[bounty_id] = max(version, seen.get(bounty_id, 0))
    return {
        "version": 1,
        "initialized": True,
        "checked_at": checked_at or utc_now(),
        "baseline_created": previous is None,
        "available_bounties": rows,
        "seen_bounty_versions": dict(sorted(seen.items())),
        "alerts": alerts,
        "summary": {
            "available_bounties": len(rows),
            "new_or_updated_alerts": len(alerts),
            "pages_read": pages_read,
        },
        "policy": {
            "http_method": "GET",
            "api_credentials_persisted_in_state": False,
            "raw_attachments_requested": False,
            "comments_or_messages_written": False,
            "claims_created": False,
            "submissions_created": False,
            "available_work_is_not_a_lead": True,
            "available_work_is_not_revenue": True,
        },
    }


def monitor_once(
    *,
    credentials_path: Path = DEFAULT_CREDENTIALS,
    state_path: Path = DEFAULT_STATE,
    root: Path = ROOT,
    opener: Opener = urlopen,
    checked_at: str | None = None,
) -> dict[str, Any]:
    state_path = validate_local_path(state_path, root=root, suffix=".json")
    previous = load_state(state_path)
    api_key = load_api_key(credentials_path)
    observation = fetch_available_bounties(api_key, opener=opener)
    report = build_state(observation, previous, checked_at=checked_at)
    write_private_json(state_path, report)
    return report


@contextmanager
def monitor_lock(path: Path = DEFAULT_LOCK):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    os.chmod(path, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Bounty marketplace monitor is already running") from exc
        yield
    finally:
        os.close(descriptor)


def monitor_loop(interval_minutes: int, **kwargs: Any) -> None:
    if interval_minutes < MINIMUM_INTERVAL_MINUTES:
        raise ValueError(
            f"Bounty marketplace interval must be at least {MINIMUM_INTERVAL_MINUTES} minutes"
        )
    with monitor_lock():
        while True:
            try:
                report = monitor_once(**kwargs)
                print(
                    json.dumps(report, ensure_ascii=False, sort_keys=True), flush=True
                )
            except Exception:
                print(
                    json.dumps(
                        {
                            "checked_at": utc_now(),
                            "error": "Bounty marketplace read failed",
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
            time.sleep(interval_minutes * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    once = subparsers.add_parser("once")
    once.add_argument("--credentials", type=Path, default=DEFAULT_CREDENTIALS)
    once.add_argument("--state", type=Path, default=DEFAULT_STATE)
    loop = subparsers.add_parser("loop")
    loop.add_argument("--credentials", type=Path, default=DEFAULT_CREDENTIALS)
    loop.add_argument("--state", type=Path, default=DEFAULT_STATE)
    loop.add_argument("--interval-minutes", type=int, default=MINIMUM_INTERVAL_MINUTES)
    status = subparsers.add_parser("status")
    status.add_argument("--state", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args()
    if args.command == "once":
        print(
            json.dumps(
                monitor_once(credentials_path=args.credentials, state_path=args.state),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "loop":
        monitor_loop(
            args.interval_minutes,
            credentials_path=args.credentials,
            state_path=args.state,
        )
        return 0
    state_path = validate_local_path(args.state, suffix=".json")
    payload = load_state(state_path)
    if payload is None:
        raise SystemExit("Bounty marketplace monitor has no state yet")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
