#!/usr/bin/env python3
"""Durable, local-only review state for already received fit requests."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
from pathlib import Path

import lkt_inbox


INBOX_DIR = lkt_inbox.INBOX_DIR
LEDGER_PATH = INBOX_DIR.parent / "intake-review.json"
RECEIPT_RE = re.compile(r"[a-f0-9]{32}\Z")
HASH_RE = re.compile(r"[a-f0-9]{64}\Z")
NAME_RE = re.compile(r"lkt-([a-f0-9]{32})\.inquiry\.json\Z")
STATES = frozenset({"needs_action", "closed", "synthetic_test"})


def private_directory(path: Path) -> None:
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_mode & 0o077:
        raise ValueError("private directory required")


def read_private(path: Path, maximum: int) -> bytes:
    private_directory(path.parent)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
            raise ValueError("private regular file required")
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("private file exceeds limit")
    return data


def read_ledger(path: Path) -> dict:
    private_directory(path.parent)
    try:
        data = read_private(path, 1024 * 1024)
    except FileNotFoundError:
        if path.is_symlink():
            raise ValueError("invalid ledger")
        return {}
    ledger = lkt_inbox.strict_json_object(data, maximum=1024 * 1024)
    if (
        set(ledger) != {"version", "reviews"}
        or type(ledger["version"]) is not int
        or ledger["version"] != 1
    ):
        raise ValueError("invalid ledger")
    reviews = ledger["reviews"]
    if not isinstance(reviews, dict):
        raise ValueError("invalid reviews")
    for receipt, review in reviews.items():
        if not RECEIPT_RE.fullmatch(receipt) or not isinstance(review, dict):
            raise ValueError("invalid review")
        if set(review) != {"sha256", "state", "reviewed_at"}:
            raise ValueError("invalid review fields")
        if (
            not isinstance(review["sha256"], str)
            or not HASH_RE.fullmatch(review["sha256"])
            or not isinstance(review["state"], str)
            or review["state"] not in STATES
        ):
            raise ValueError("invalid review state")
        lkt_inbox.validate_utc_seconds(review["reviewed_at"])
    return reviews


def inspect_requests(directory: Path = INBOX_DIR, ledger_path: Path = LEDGER_PATH) -> list[dict]:
    """Private operator metadata only; never return contact or message fields."""
    private_directory(directory)
    reviews = read_ledger(ledger_path)
    rows = []
    for path in sorted(directory.iterdir()):
        match = NAME_RE.fullmatch(path.name)
        if not match:
            if path.name.endswith(".inquiry.json"):
                raise ValueError("unexpected inquiry filename")
            continue
        data = read_private(path, lkt_inbox.MAX_CIPHERTEXT_BYTES)
        record = lkt_inbox.strict_json_object(data, maximum=lkt_inbox.MAX_CIPHERTEXT_BYTES)
        lkt_inbox.validate_record(record, created_at=record.get("received_at"))
        receipt = match[1]
        digest = hashlib.sha256(data).hexdigest()
        review = reviews.get(receipt, {})
        state = (
            review.get("state", "pending_review")
            if review.get("sha256") == digest else "pending_review"
        )
        rows.append({
            "receipt": receipt,
            "sha256": digest,
            "received_at": record["received_at"],
            "offer": record["payload"].get("offer", "lkt"),
            "state": state,
        })
    if set(reviews) - {row["receipt"] for row in rows}:
        raise ValueError("reviewed inquiry is missing")
    return rows


def status_summary(directory: Path = INBOX_DIR, ledger_path: Path = LEDGER_PATH) -> dict:
    try:
        rows = inspect_requests(directory, ledger_path)
    except (OSError, ValueError, TypeError, KeyError, lkt_inbox.InboxError):
        return {"available": False, "review_required": True, "error": "private_intake_state_unavailable"}
    counts = {state: sum(row["state"] == state for row in rows) for state in sorted(STATES | {"pending_review"})}
    return {
        "available": True,
        "retained_requests": len(rows),
        **counts,
        "review_required": bool(counts["pending_review"] or counts["needs_action"]),
        "automatic_reply": False,
    }


def record_review(
    receipt: str, expected_hash: str, state: str,
    *, directory: Path = INBOX_DIR, ledger_path: Path = LEDGER_PATH,
) -> None:
    if not RECEIPT_RE.fullmatch(receipt) or not HASH_RE.fullmatch(expected_hash) or state not in STATES:
        raise ValueError("invalid review request")
    private_directory(ledger_path.parent)
    lock_path = ledger_path.with_suffix(".lock")
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    with os.fdopen(descriptor, "r+b") as lock:
        metadata = os.fstat(lock.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
            raise ValueError("invalid review lock")
        fcntl.flock(lock, fcntl.LOCK_EX)
        row = next((row for row in inspect_requests(directory, ledger_path) if row["receipt"] == receipt), None)
        if row is None or row["sha256"] != expected_hash:
            raise ValueError("inquiry changed or is missing; review again")
        reviews = read_ledger(ledger_path)
        reviews[receipt] = {"sha256": expected_hash, "state": state, "reviewed_at": lkt_inbox.utc_now()}
        lkt_inbox.private_atomic_write(
            ledger_path, lkt_inbox.canonical_json({"version": 1, "reviews": reviews}), replace=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Aggregate counts only.")
    commands.add_parser("inspect", help="Private receipt metadata for deliberate review.")
    review = commands.add_parser("review", help="Record local review only; sends nothing.")
    review.add_argument("receipt")
    review.add_argument("--sha256", required=True)
    review.add_argument("--state", choices=sorted(STATES), required=True)
    review.add_argument("--confirm-reviewed", action="store_true", required=True)
    args = parser.parse_args()
    try:
        if args.command == "review":
            record_review(args.receipt, args.sha256, args.state)
        result = inspect_requests() if args.command == "inspect" else status_summary()
    except (OSError, ValueError, TypeError, KeyError, lkt_inbox.InboxError):
        parser.exit(1, "Private intake state unavailable; inspect locally.\n")
    print(json.dumps(result, sort_keys=True))
    if isinstance(result, dict) and not result["available"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
