#!/usr/bin/env python3
"""Report sent applications that are due for a human reply check."""

from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CAMPAIGNS_DIR = ROOT / "campaigns"
DEFAULT_REVIEW_DAYS = 7
SOURCE_REVIEWS_DB = ROOT / ".local" / "lazypromotion.sqlite3"


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


def attach_source_reviews(report: dict, *, db_path: Path = SOURCE_REVIEWS_DB) -> dict:
    """Add stored private context, never reschedule or infer a provider result."""
    # Keep the default report and the running publication monitor independent
    # of the private graph. Import only for an explicitly requested review.
    import network

    result = deepcopy(report)
    urls = []
    for item in result["applications"]:
        url = item["source_url"]
        context = {"state": "source_url_missing", "matches": []}
        if url:
            try:
                network.screening_url_key(url)
            except ValueError:
                context["state"] = "source_url_invalid"
            else:
                if url not in urls:
                    urls.append(url)
                context["state"] = "not_recorded"
        item["stored_source_review"] = context

    # Do not call promotion.open_db: even a missing file must not be created or
    # migrated by an operator's read-only review command.
    with closing(sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        by_url = {}
        for start in range(0, len(urls), 20):
            lookup = network.lookup_sources(db, urls[start:start + 20])
            by_url.update({item["url"]: item for item in lookup["sources"]})
        for item in result["applications"]:
            stored = by_url.get(item["source_url"])
            if stored is not None:
                item["stored_source_review"] = {
                    "state": stored["state"], "matches": stored["matches"],
                }

    result["private_context"] = True
    result["source_review_policy"] = {
        "read_only": True,
        "provider_checked": False,
        "campaign_dates_unchanged": True,
        "automatic_follow_up": False,
        "notice": (
            "Campaign due dates are not new activity or permission to recheck. "
            "Read stored source decisions and their evidence before acting. "
            "URL matches may concern another application to the same source; "
            "missing, conflicting or unreadable records need review, not an "
            "eligibility inference. Graph timestamps are not provider checks. "
            "This private output must not be committed or published."
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--on", type=parse_day, help="Evaluate against an ISO date.")
    parser.add_argument(
        "--with-source-reviews", action="store_true",
        help="Include private stored source decisions; never opens a provider or changes due dates.",
    )
    parser.add_argument("--db", type=Path, help="Existing private graph; requires --with-source-reviews.")
    args = parser.parse_args()
    if args.db is not None and not args.with_source_reviews:
        parser.error("--db requires --with-source-reviews")
    report = build_report(on=args.on)
    if args.with_source_reviews:
        try:
            report = attach_source_reviews(report, db_path=args.db or SOURCE_REVIEWS_DB)
        except (OSError, sqlite3.Error, ValueError):
            parser.error("stored source reviews could not be read; no provider state is inferred")
    print(
        json.dumps(
            report, ensure_ascii=False, indent=2, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
