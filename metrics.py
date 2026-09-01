#!/usr/bin/env python3
"""Record verified private outcomes and report the truthful promotion funnel."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import secrets
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

import promotion


ROOT = Path(__file__).resolve().parent
CAMPAIGNS = ROOT / "campaigns"
USD_GOAL_MINOR = 100_000
EINK_USD_MINOR = 12_800
LKT_SPRINT_USD_MINOR = 25_000

OUTCOME_KINDS = {
    "affiliate_commission_received",
    "affiliate_commission_reversed",
    "affiliate_referral_confirmed",
    "reply_received",
    "qualified_lead",
    "checkout_started",
    "sale_confirmed",
    "donation_received",
    "sponsor_received",
    "refund_confirmed",
}
REVENUE_KINDS = {
    "affiliate_commission_received",
    "sale_confirmed",
    "donation_received",
    "sponsor_received",
}
REVERSAL_KINDS = {"affiliate_commission_reversed", "refund_confirmed"}
MONEY_KINDS = REVENUE_KINDS | REVERSAL_KINDS
REFERENCE_KINDS = MONEY_KINDS | {"affiliate_referral_confirmed"}


def money_to_minor(value: str) -> int:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("amount must be a decimal number") from exc
    if amount <= 0 or amount.as_tuple().exponent < -2:
        raise ValueError("amount must be positive with at most two decimal places")
    return int(amount * 100)


def known_campaign(campaign_id: str) -> bool:
    for path in CAMPAIGNS.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("id") == campaign_id:
            return True
    return False


def record_outcome(
    db,
    *,
    kind: str,
    candidate_id: str = "",
    draft_id: str = "",
    campaign_id: str = "",
    project_id: str = "",
    amount: str = "0",
    currency: str = "",
    reference: str = "",
    evidence_url: str = "",
    note: str = "",
    occurred_at: str = "",
) -> dict:
    if kind not in OUTCOME_KINDS:
        raise ValueError(f"unknown outcome kind: {kind}")
    if not any((candidate_id, draft_id, campaign_id, project_id)):
        raise ValueError("an outcome must be attached to a candidate, draft, campaign, or project")
    if candidate_id:
        candidate = db.execute(
            "SELECT id FROM candidates WHERE id=?", (candidate_id,)
        ).fetchone()
        if not candidate:
            raise ValueError("candidate does not exist")
    if draft_id:
        draft = db.execute(
            "SELECT candidate_id FROM drafts WHERE id=?", (draft_id,)
        ).fetchone()
        if not draft:
            raise ValueError("draft does not exist")
        if candidate_id and draft["candidate_id"] != candidate_id:
            raise ValueError("draft is not bound to the supplied candidate")
    if project_id:
        promotion.project_by_id(project_id)
    if campaign_id and not known_campaign(campaign_id):
        raise ValueError("campaign does not exist")
    if evidence_url:
        parsed = urlparse(evidence_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("evidence URL must be an absolute HTTP(S) URL")

    currency = promotion.compact(currency).upper()
    reference = promotion.compact(reference)
    if kind in MONEY_KINDS:
        amount_minor = money_to_minor(amount)
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("money outcomes require a three-letter currency code")
    else:
        try:
            non_money_amount = Decimal(amount)
        except InvalidOperation as exc:
            raise ValueError("amount must be zero for a non-money outcome") from exc
        if non_money_amount != 0 or currency:
            raise ValueError("non-money outcomes cannot record an amount or currency")
        amount_minor = 0

    if kind in REFERENCE_KINDS:
        if not reference:
            if kind == "affiliate_referral_confirmed":
                raise ValueError(
                    "confirmed affiliate referrals require a private conversion reference"
                )
            raise ValueError("money outcomes require a private order or receipt reference")
        reference_hash = hashlib.sha256(reference.encode("utf-8")).hexdigest()
        if db.execute(
            "SELECT 1 FROM outcomes WHERE kind=? AND reference_hash=?",
            (kind, reference_hash),
        ).fetchone():
            raise ValueError("this outcome reference was already recorded")
    else:
        reference_hash = ""
        if candidate_id and db.execute(
            "SELECT 1 FROM outcomes WHERE kind=? AND candidate_id=?",
            (kind, candidate_id),
        ).fetchone():
            raise ValueError("this candidate outcome was already recorded")

    occurred_at = promotion.compact(occurred_at) or promotion.utc_now()
    created_at = promotion.utc_now()
    identity = "\n".join(
        (
            kind,
            candidate_id,
            draft_id,
            campaign_id,
            project_id,
            str(amount_minor),
            currency,
            reference_hash,
            evidence_url,
            occurred_at,
            secrets.token_hex(8),
        )
    )
    outcome_id = "out_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
    db.execute(
        """
        INSERT INTO outcomes
          (id, kind, candidate_id, draft_id, campaign_id, project_id,
           amount_minor, currency, reference_hash, evidence_url, note,
           occurred_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            outcome_id,
            kind,
            candidate_id,
            draft_id,
            campaign_id,
            project_id,
            amount_minor,
            currency,
            reference_hash,
            evidence_url,
            promotion.compact(note),
            occurred_at,
            created_at,
        ),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM outcomes WHERE id=?", (outcome_id,)).fetchone())


def funnel_report(db) -> dict:
    candidates = Counter(row[0] for row in db.execute("SELECT status FROM candidates"))
    drafts = Counter(row[0] for row in db.execute("SELECT status FROM drafts"))
    outcomes = Counter(row[0] for row in db.execute("SELECT kind FROM outcomes"))
    gross_by_currency: dict[str, int] = defaultdict(int)
    refunds_by_currency: dict[str, int] = defaultdict(int)
    reversals_by_currency: dict[str, int] = defaultdict(int)
    for kind, amount_minor, currency in db.execute(
        "SELECT kind, amount_minor, currency FROM outcomes WHERE currency != ''"
    ):
        if kind in REVENUE_KINDS:
            gross_by_currency[currency] += amount_minor
        elif kind in REVERSAL_KINDS:
            reversals_by_currency[currency] += amount_minor
            if kind == "refund_confirmed":
                refunds_by_currency[currency] += amount_minor
    net_by_currency = {
        currency: gross_by_currency[currency] - reversals_by_currency[currency]
        for currency in sorted(set(gross_by_currency) | set(reversals_by_currency))
    }
    usd_gross = gross_by_currency.get("USD", 0)
    remaining = max(0, USD_GOAL_MINOR - usd_gross)
    return {
        "candidates": dict(sorted(candidates.items())),
        "drafts": dict(sorted(drafts.items())),
        "outcomes": dict(sorted(outcomes.items())),
        "gross_revenue_minor_by_currency": dict(sorted(gross_by_currency.items())),
        "refunds_minor_by_currency": dict(sorted(refunds_by_currency.items())),
        "reversals_minor_by_currency": dict(sorted(reversals_by_currency.items())),
        "net_revenue_minor_by_currency": net_by_currency,
        "usd_1000_gross_goal": {
            "target_minor": USD_GOAL_MINOR,
            "confirmed_minor": usd_gross,
            "progress_percent": round(100 * usd_gross / USD_GOAL_MINOR, 2),
            "remaining_minor": remaining,
            "additional_250_usd_sprints_needed": math.ceil(
                remaining / LKT_SPRINT_USD_MINOR
            ),
            "additional_128_usd_orders_needed": math.ceil(remaining / EINK_USD_MINOR),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=promotion.DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("report")
    record = sub.add_parser("record")
    record.add_argument("--kind", required=True, choices=sorted(OUTCOME_KINDS))
    record.add_argument("--candidate-id", default="")
    record.add_argument("--draft-id", default="")
    record.add_argument("--campaign-id", default="")
    record.add_argument("--project-id", default="")
    record.add_argument("--amount", default="0")
    record.add_argument("--currency", default="")
    record.add_argument(
        "--reference",
        default="",
        help=(
            "private order, receipt, payout, reversal, or affiliate conversion "
            "reference; only its SHA-256 hash is stored"
        ),
    )
    record.add_argument("--evidence-url", default="")
    record.add_argument("--note", default="")
    record.add_argument("--occurred-at", default="")
    record.add_argument("--confirm-verified-outcome", action="store_true")
    args = parser.parse_args()
    db = promotion.open_db(args.db)
    if args.command == "report":
        result = funnel_report(db)
    else:
        if not args.confirm_verified_outcome:
            raise SystemExit("recording requires --confirm-verified-outcome")
        result = record_outcome(
            db,
            kind=args.kind,
            candidate_id=args.candidate_id,
            draft_id=args.draft_id,
            campaign_id=args.campaign_id,
            project_id=args.project_id,
            amount=args.amount,
            currency=args.currency,
            reference=args.reference,
            evidence_url=args.evidence_url,
            note=args.note,
            occurred_at=args.occurred_at,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
