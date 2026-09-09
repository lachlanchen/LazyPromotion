#!/usr/bin/env python3
"""Report sent applications that are due for a human reply check."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CAMPAIGNS_DIR = ROOT / "campaigns"
DEFAULT_REVIEW_DAYS = 7


def parse_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO date: {value}") from exc


def sent_day(value: object) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError as exc:
        raise ValueError(f"invalid sent_at timestamp: {value}") from exc


def nested_review_after(application: dict) -> object:
    direct = application.get("review_after") or application.get("follow_up_not_before")
    if direct:
        return direct
    follow_up_gate = application.get("follow_up_gate")
    if isinstance(follow_up_gate, dict) and follow_up_gate.get("review_not_before"):
        return follow_up_gate["review_not_before"]
    fallback = application.get("fallback")
    if isinstance(fallback, dict) and fallback.get("review_after"):
        return fallback["review_after"]
    return None


def is_awaiting_reply(state: str) -> bool:
    words = state.casefold()
    tokens = set(words.split("_"))
    was_submitted = bool(tokens & {"sent", "submitted"})
    return was_submitted and ("awaiting" in tokens or "pending_reply" in words)


def application_record(payload: dict, *, source_file: Path, on: date) -> dict | None:
    application = payload.get("application")
    if not isinstance(application, dict):
        return None
    state = str(application.get("state") or "").strip()
    if not is_awaiting_reply(state):
        return None

    explicit_review = nested_review_after(application)
    sent = sent_day(application.get("sent_at") or application.get("submitted_at"))
    if explicit_review:
        review_after = parse_day(str(explicit_review))
        schedule_source = "campaign"
    elif sent:
        review_after = sent + timedelta(days=DEFAULT_REVIEW_DAYS)
        schedule_source = "default_7_days_after_sent"
    else:
        review_after = None
        schedule_source = "missing"

    campaign_id = str(payload.get("id") or source_file.stem).strip()
    return {
        "campaign_id": campaign_id,
        "state": state,
        "review_after": review_after.isoformat() if review_after else None,
        "due_for_human_review": bool(review_after and review_after <= on),
        "schedule_source": schedule_source,
        "source_url": str(payload.get("source_need", {}).get("url") or ""),
    }


def additional_application_records(
    payload: dict, *, source_file: Path, on: date
) -> list[dict]:
    campaign_id = str(payload.get("id") or source_file.stem).strip()
    records = []
    outreach = payload.get("additional_outreach")
    if not isinstance(outreach, list):
        return records
    for index, item in enumerate(outreach, start=1):
        if not isinstance(item, dict):
            continue
        state = str(item.get("application_state") or "").strip()
        if not is_awaiting_reply(state):
            continue
        normalized = dict(item)
        normalized["state"] = state
        record = application_record(
            {
                "id": f"{campaign_id}:additional_outreach:{index}",
                "source_need": {"url": str(item.get("source_url") or "")},
                "application": normalized,
            },
            source_file=source_file,
            on=on,
        )
        if record:
            record["parent_campaign_id"] = campaign_id
            records.append(record)
    return records


def build_report(
    *, campaigns_dir: Path = CAMPAIGNS_DIR, on: date | None = None
) -> dict:
    on = on or datetime.now(timezone.utc).date()
    records = []
    for path in sorted(campaigns_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"could not read campaign: {path.name}") from exc
        if not isinstance(payload, dict):
            raise RuntimeError(f"campaign is not an object: {path.name}")
        record = application_record(payload, source_file=path, on=on)
        if record:
            records.append(record)
        records.extend(additional_application_records(payload, source_file=path, on=on))

    records.sort(
        key=lambda item: (
            item["review_after"] is None,
            item["review_after"] or "9999-12-31",
            item["campaign_id"],
        )
    )
    return {
        "checked_on": on.isoformat(),
        "applications": records,
        "summary": {
            "awaiting_human_reply": len(records),
            "due_for_human_review": sum(
                1 for item in records if item["due_for_human_review"]
            ),
            "missing_review_schedule": sum(
                1 for item in records if item["review_after"] is None
            ),
        },
        "policy": {
            "mail_opened": False,
            "automatic_follow_up": False,
            "application_is_not_a_lead": True,
            "due_review_action": (
                "Check aggregate outreach counts first; inspect a reply visibly only "
                "when evidence changes."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--on", type=parse_day, help="Evaluate against an ISO date.")
    args = parser.parse_args()
    print(
        json.dumps(
            build_report(on=args.on), ensure_ascii=False, indent=2, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
