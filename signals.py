#!/usr/bin/env python3
"""Import private first-party demand evidence without inventing sales."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import promotion


ALLOWED_DELTA_UNITS = {"", "absolute", "percent"}


def signal_id(*, source: str, period: str, signal_kind: str, subject: str, url: str, metric: str) -> str:
    identity = "\n".join((source, period, signal_kind, subject, url, metric))
    return "sig_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]


def compact_required(value: object, name: str) -> str:
    result = promotion.compact(str(value or ""))
    if not result:
        raise ValueError(f"{name} is required")
    return result


def finite_number(value: object, name: str, *, nullable: bool = False) -> float | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def validate_evidence_path(value: object) -> str:
    path = promotion.compact(str(value or ""))
    if not path:
        return ""
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("evidence_path must be a safe repository-relative path")
    if candidate.parts[:2] != (".local", "evidence"):
        raise ValueError("evidence_path must stay under .local/evidence")
    return candidate.as_posix()


def normalize_signal(payload: dict, defaults: dict) -> dict:
    source = compact_required(payload.get("source", defaults.get("source")), "source")
    period = compact_required(payload.get("period", defaults.get("period")), "period")
    observed_at = compact_required(
        payload.get("observed_at", defaults.get("observed_at")), "observed_at"
    )
    signal_kind = compact_required(payload.get("signal_kind"), "signal_kind")
    subject = compact_required(payload.get("subject"), "subject")
    metric = compact_required(payload.get("metric"), "metric")
    value = finite_number(payload.get("value"), "value")
    if value is not None and value < 0:
        raise ValueError("value cannot be negative")
    delta_value = finite_number(payload.get("delta_value"), "delta_value", nullable=True)
    delta_unit = promotion.compact(str(payload.get("delta_unit") or "")).casefold()
    if delta_unit not in ALLOWED_DELTA_UNITS:
        raise ValueError(f"unsupported delta_unit: {delta_unit}")
    if delta_value is None and delta_unit:
        raise ValueError("delta_unit requires delta_value")
    if delta_value is not None and not delta_unit:
        raise ValueError("delta_value requires delta_unit")

    url = promotion.compact(str(payload.get("url") or ""))
    if url:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an absolute HTTP(S) URL")
    project_id = promotion.compact(str(payload.get("project_id") or ""))
    if project_id:
        promotion.project_by_id(project_id)
    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")
    evidence_path = validate_evidence_path(
        payload.get("evidence_path", defaults.get("evidence_path"))
    )
    return {
        "id": signal_id(
            source=source,
            period=period,
            signal_kind=signal_kind,
            subject=subject,
            url=url,
            metric=metric,
        ),
        "source": source,
        "signal_kind": signal_kind,
        "subject": subject,
        "url": url,
        "project_id": project_id,
        "metric": metric,
        "value": value,
        "delta_value": delta_value,
        "delta_unit": delta_unit,
        "period": period,
        "observed_at": observed_at,
        "evidence_path": evidence_path,
        "metadata_json": json.dumps(metadata, ensure_ascii=False, sort_keys=True),
    }


def import_payload(db, payload: dict) -> dict:
    if payload.get("version") != 1:
        raise ValueError("signal import version must be 1")
    records = payload.get("signals")
    if not isinstance(records, list) or not records:
        raise ValueError("signals must be a non-empty list")
    defaults = {
        "source": payload.get("source"),
        "period": payload.get("period"),
        "observed_at": payload.get("observed_at"),
        "evidence_path": payload.get("evidence_path"),
    }
    normalized = [normalize_signal(record, defaults) for record in records]
    if len({record["id"] for record in normalized}) != len(normalized):
        raise ValueError("signal import contains duplicate identities")

    now = promotion.utc_now()
    for record in normalized:
        db.execute(
            """
            INSERT INTO demand_signals
              (id, source, signal_kind, subject, url, project_id, metric, value,
               delta_value, delta_unit, period, observed_at, evidence_path,
               metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              project_id=excluded.project_id, value=excluded.value,
              delta_value=excluded.delta_value, delta_unit=excluded.delta_unit,
              observed_at=excluded.observed_at,
              evidence_path=excluded.evidence_path,
              metadata_json=excluded.metadata_json, updated_at=excluded.updated_at
            """,
            (
                record["id"], record["source"], record["signal_kind"],
                record["subject"], record["url"], record["project_id"],
                record["metric"], record["value"], record["delta_value"],
                record["delta_unit"], record["period"], record["observed_at"],
                record["evidence_path"], record["metadata_json"], now, now,
            ),
        )
    db.commit()
    return {
        "source": defaults["source"],
        "period": defaults["period"],
        "imported": len(normalized),
        "ids": [record["id"] for record in normalized],
    }


def signal_report(db, *, source: str = "", period: str = "", limit: int = 20) -> dict:
    clauses = []
    params: list[object] = []
    if source:
        clauses.append("source=?")
        params.append(source)
    if period:
        clauses.append("period=?")
        params.append(period)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = [
        dict(row)
        for row in db.execute(
            f"""
            SELECT source, signal_kind, subject, url, project_id, metric, value,
                   delta_value, delta_unit, period, observed_at
            FROM demand_signals{where}
            ORDER BY metric, value DESC, subject
            """,
            params,
        )
    ]
    kinds = Counter(row["signal_kind"] for row in rows)
    metrics = Counter(row["metric"] for row in rows)
    return {
        "signals": len(rows),
        "by_kind": dict(sorted(kinds.items())),
        "by_metric": dict(sorted(metrics.items())),
        "top": rows[: max(1, min(limit, 100))],
        "interpretation_guard": (
            "Demand evidence can prioritize work; it is not a lead, order, donation, or sale."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=promotion.DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)
    importing = sub.add_parser("import-json")
    importing.add_argument("path", type=Path)
    importing.add_argument("--confirm-private-first-party-data", action="store_true")
    report = sub.add_parser("report")
    report.add_argument("--source", default="")
    report.add_argument("--period", default="")
    report.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    db = promotion.open_db(args.db)
    if args.command == "import-json":
        if not args.confirm_private_first_party_data:
            raise SystemExit("import requires --confirm-private-first-party-data")
        payload = json.loads(args.path.read_text(encoding="utf-8"))
        result = import_payload(db, payload)
    else:
        result = signal_report(
            db,
            source=promotion.compact(args.source),
            period=promotion.compact(args.period),
            limit=args.limit,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
