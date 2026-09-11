#!/usr/bin/env python3
"""Watch live Stripe charges without persisting customer or payment details."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sqlite3
import stat
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from payment_readiness import load_env


ROOT = Path(__file__).resolve().parent
DEFAULT_ENV = (ROOT.parent / "Stripe" / ".env").resolve()
RUNTIME = ROOT / ".local"
DEFAULT_DB = RUNTIME / "stripe-revenue-monitor.sqlite3"
DEFAULT_STATUS = RUNTIME / "stripe-revenue-monitor-status.json"
DEFAULT_LOG = RUNTIME / "stripe-revenue-monitor.jsonl"
DEFAULT_LOCK = RUNTIME / "stripe-revenue-monitor.lock"
DEFAULT_SINCE = "2026-08-31T00:00:00Z"
SAFE_METADATA_KEYS = frozenset(
    {
        "brand",
        "fit_check_required",
        "offer_type",
        "product_slug",
        "scope_version",
        "site",
    }
)
SAFE_METADATA_VALUE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,79}")


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_since(value: str) -> tuple[str, int]:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("--since must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("--since must include a timezone")
    parsed = parsed.astimezone(timezone.utc).replace(microsecond=0)
    return parsed.isoformat().replace("+00:00", "Z"), int(parsed.timestamp())


def inspect_live_key(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Stripe environment path must be a regular file")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o600:
        raise ValueError("Stripe environment file must have mode 600")
    key = load_env(path).get("STRIPE_SECRET_KEY", "")
    if not key.startswith("sk_live_"):
        raise ValueError("Stripe revenue monitoring requires a live secret key")
    return key


def stripe_get(
    path: str,
    params: list[tuple[str, str]],
    secret_key: str,
    *,
    opener=urlopen,
) -> dict[str, Any]:
    url = f"https://api.stripe.com{path}?{urlencode(params)}"
    request = Request(url, headers={"Authorization": f"Bearer {secret_key}"})
    try:
        with opener(request, timeout=20) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Stripe read failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("Stripe read could not reach the API") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Stripe returned an invalid response")
    return payload


def fetch_charges(
    secret_key: str,
    since_epoch: int,
    *,
    opener=urlopen,
    max_pages: int = 20,
) -> list[dict[str, Any]]:
    charges: list[dict[str, Any]] = []
    starting_after = ""
    for _ in range(max_pages):
        params = [("created[gte]", str(since_epoch)), ("limit", "100")]
        if starting_after:
            params.append(("starting_after", starting_after))
        payload = stripe_get("/v1/charges", params, secret_key, opener=opener)
        page = payload.get("data")
        if not isinstance(page, list):
            raise RuntimeError("Stripe charge response has no data list")
        rows = [row for row in page if isinstance(row, dict)]
        charges.extend(rows)
        if not payload.get("has_more"):
            return charges
        if not rows or not str(rows[-1].get("id") or ""):
            raise RuntimeError("Stripe charge pagination cannot advance")
        starting_after = str(rows[-1]["id"])
    raise RuntimeError("Stripe charge pagination exceeded the safety limit")


def sanitized_charge(row: dict[str, Any]) -> dict[str, Any] | None:
    charge_id = str(row.get("id") or "")
    currency = str(row.get("currency") or "").lower()
    if (
        row.get("object") != "charge"
        or not charge_id
        or row.get("livemode") is not True
        or row.get("paid") is not True
        or row.get("status") != "succeeded"
        or len(currency) != 3
        or not currency.isalpha()
    ):
        return None
    amount = row.get("amount")
    refunded = row.get("amount_refunded", 0)
    created = row.get("created")
    if (
        isinstance(amount, bool)
        or not isinstance(amount, int)
        or amount <= 0
        or isinstance(refunded, bool)
        or not isinstance(refunded, int)
        or refunded < 0
        or refunded > amount
        or isinstance(created, bool)
        or not isinstance(created, int)
        or created <= 0
    ):
        return None
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    safe_metadata = {}
    for key, value in metadata.items():
        text = str(value).strip()
        if key in SAFE_METADATA_KEYS and SAFE_METADATA_VALUE.fullmatch(text):
            safe_metadata[key] = text
    return {
        "charge_key": hashlib.sha256(charge_id.encode("utf-8")).hexdigest(),
        "created_at": datetime.fromtimestamp(created, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "currency": currency.upper(),
        "amount_minor": amount,
        "amount_refunded_minor": refunded,
        "disputed": bool(row.get("disputed")),
        "refunded": bool(row.get("refunded")) or refunded == amount,
        "safe_metadata": safe_metadata,
    }


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS monitor_meta (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stripe_charge_observations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          observed_at TEXT NOT NULL,
          charge_key TEXT NOT NULL,
          created_at TEXT NOT NULL,
          currency TEXT NOT NULL,
          amount_minor INTEGER NOT NULL,
          amount_refunded_minor INTEGER NOT NULL,
          disputed INTEGER NOT NULL,
          refunded INTEGER NOT NULL,
          safe_metadata_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS stripe_charge_observations_charge
          ON stripe_charge_observations(charge_key, id DESC);
        """
    )
    os.chmod(path, 0o600)
    return db


def previous_observation(db: sqlite3.Connection, charge_key: str) -> dict | None:
    row = db.execute(
        """
        SELECT * FROM stripe_charge_observations
        WHERE charge_key=? ORDER BY id DESC LIMIT 1
        """,
        (charge_key,),
    ).fetchone()
    return dict(row) if row else None


def monitor_initialized(db: sqlite3.Connection) -> bool:
    return (
        db.execute("SELECT 1 FROM monitor_meta WHERE key='initialized'").fetchone()
        is not None
    )


def remember_charge(db: sqlite3.Connection, checked_at: str, charge: dict) -> None:
    db.execute(
        """
        INSERT INTO stripe_charge_observations
          (observed_at, charge_key, created_at, currency, amount_minor,
           amount_refunded_minor, disputed, refunded, safe_metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            checked_at,
            charge["charge_key"],
            charge["created_at"],
            charge["currency"],
            charge["amount_minor"],
            charge["amount_refunded_minor"],
            int(charge["disputed"]),
            int(charge["refunded"]),
            json.dumps(charge["safe_metadata"], sort_keys=True),
        ),
    )


def changed(previous: dict, current: dict) -> bool:
    return any(
        previous[field] != current[field]
        for field in (
            "amount_minor",
            "amount_refunded_minor",
            "disputed",
            "refunded",
        )
    ) or previous["safe_metadata_json"] != json.dumps(
        current["safe_metadata"], sort_keys=True
    )


def summarize(charges: list[dict]) -> dict[str, Any]:
    currencies: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "successful_charge_count": 0,
            "gross_minor": 0,
            "refunded_minor": 0,
            "net_minor_before_fees_and_disputes": 0,
            "disputed_charge_count": 0,
        }
    )
    for charge in charges:
        bucket = currencies[charge["currency"]]
        bucket["successful_charge_count"] += 1
        bucket["gross_minor"] += charge["amount_minor"]
        bucket["refunded_minor"] += charge["amount_refunded_minor"]
        bucket["net_minor_before_fees_and_disputes"] += (
            charge["amount_minor"] - charge["amount_refunded_minor"]
        )
        bucket["disputed_charge_count"] += int(charge["disputed"])
    return {
        "successful_charge_count": len(charges),
        "currencies": dict(sorted(currencies.items())),
    }


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def append_log(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, sort_keys=True) + "\n")
    os.chmod(path, 0o600)


def build_report(
    *,
    env_path: Path = DEFAULT_ENV,
    db_path: Path = DEFAULT_DB,
    status_path: Path = DEFAULT_STATUS,
    log_path: Path = DEFAULT_LOG,
    since: str = DEFAULT_SINCE,
    opener=urlopen,
) -> dict[str, Any]:
    since_iso, since_epoch = parse_since(since)
    secret_key = inspect_live_key(env_path)
    raw = fetch_charges(secret_key, since_epoch, opener=opener)
    charges = [charge for row in raw if (charge := sanitized_charge(row))]
    charges.sort(key=lambda charge: (charge["created_at"], charge["charge_key"]))
    checked_at = utc_now()
    db = open_db(db_path)
    try:
        initialized = monitor_initialized(db)
        alerts: list[dict[str, Any]] = []
        for charge in charges:
            previous = previous_observation(db, charge["charge_key"])
            if previous is None:
                remember_charge(db, checked_at, charge)
                if initialized:
                    alerts.append(
                        {
                            "kind": "new_successful_charge",
                            **charge,
                            "review_required": True,
                        }
                    )
            elif changed(previous, charge):
                remember_charge(db, checked_at, charge)
                alerts.append(
                    {
                        "kind": "charge_state_changed",
                        **charge,
                        "previous_amount_refunded_minor": previous[
                            "amount_refunded_minor"
                        ],
                        "previous_disputed": bool(previous["disputed"]),
                        "previous_refunded": bool(previous["refunded"]),
                        "review_required": True,
                    }
                )
        if not initialized:
            db.execute(
                "INSERT INTO monitor_meta (key, value) VALUES ('initialized', ?)",
                (checked_at,),
            )
        db.commit()
    finally:
        db.close()

    report = {
        "version": 1,
        "checked_at": checked_at,
        "since": since_iso,
        "initialized_before_check": initialized,
        "summary": summarize(charges),
        "alerts": alerts,
        "policy": {
            "stripe_mutations_performed": False,
            "customer_or_payment_details_persisted": False,
            "raw_stripe_ids_persisted": False,
            "automatic_revenue_records": False,
            "classification_required": (
                "A successful charge must be matched to its accepted scope or "
                "donation context before metrics.py records revenue."
            ),
        },
    }
    atomic_write_json(status_path, report)
    append_log(log_path, report)
    return report


def acquire_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+", encoding="utf-8")
    os.chmod(path, 0o600)
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        stream.close()
        raise RuntimeError("Stripe revenue monitor is already running") from exc
    return stream


def load_status(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Stripe revenue monitor has no status yet")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("once", "loop", "status"))
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--status-file", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--since", default=DEFAULT_SINCE)
    parser.add_argument("--interval-minutes", type=int, default=30)
    parser.add_argument("--confirm-private-financial-read", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "status":
        print(json.dumps(load_status(args.status_file), indent=2, sort_keys=True))
        return 0
    if not args.confirm_private_financial_read:
        raise SystemExit(
            "Stripe monitoring requires --confirm-private-financial-read"
        )
    if args.command == "loop" and args.interval_minutes < 15:
        raise SystemExit("--interval-minutes must be at least 15")

    lock = acquire_lock(args.lock)
    try:
        if args.command == "once":
            print(
                json.dumps(
                    build_report(
                        env_path=args.env,
                        db_path=args.db,
                        status_path=args.status_file,
                        log_path=args.log,
                        since=args.since,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        while True:
            try:
                report = build_report(
                    env_path=args.env,
                    db_path=args.db,
                    status_path=args.status_file,
                    log_path=args.log,
                    since=args.since,
                )
                print(json.dumps(report, sort_keys=True), flush=True)
            except Exception as exc:  # keep the long-running watcher alive
                error = {
                    "checked_at": utc_now(),
                    "error": type(exc).__name__,
                    "customer_or_payment_details_persisted": False,
                }
                print(json.dumps(error, sort_keys=True), flush=True)
            time.sleep(args.interval_minutes * 60)
    finally:
        lock.close()


if __name__ == "__main__":
    raise SystemExit(main())
