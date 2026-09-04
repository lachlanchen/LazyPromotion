#!/usr/bin/env python3
"""Evaluate an LKT hardware quote without changing the USD 250 service offer."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from typing import Sequence


CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def as_decimal(value: object, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be a decimal number") from exc
    if not result.is_finite():
        raise ValueError(f"{label} must be finite")
    return result


def money(value: Decimal) -> str:
    return str(value.quantize(CENT, rounding=ROUND_CEILING))


def build_report(
    *,
    hardware_cost_cny: object,
    cny_per_usd: object,
    price_usd: object,
    other_variable_cost_usd: object,
    payment_fee_percent: object,
    payment_fee_fixed_usd: object,
    target_margin_percent: object,
    costs_confirmed: bool = False,
    commercial_terms_reviewed: bool = False,
) -> dict[str, object]:
    hardware_cny = as_decimal(hardware_cost_cny, "hardware cost")
    exchange_rate = as_decimal(cny_per_usd, "CNY per USD")
    price = as_decimal(price_usd, "price")
    other_cost = as_decimal(other_variable_cost_usd, "other variable cost")
    fee_rate = as_decimal(payment_fee_percent, "payment fee percent") / HUNDRED
    fee_fixed = as_decimal(payment_fee_fixed_usd, "fixed payment fee")
    target_margin = as_decimal(target_margin_percent, "target margin percent") / HUNDRED

    if hardware_cny <= 0 or exchange_rate <= 0 or price <= 0:
        raise ValueError("hardware cost, exchange rate, and price must be positive")
    if other_cost < 0 or fee_fixed < 0:
        raise ValueError("variable costs and fixed payment fee cannot be negative")
    if fee_rate < 0 or fee_rate >= 1:
        raise ValueError("payment fee percent must be at least zero and below 100")
    if target_margin < 0 or target_margin >= 1:
        raise ValueError("target margin percent must be at least zero and below 100")
    if fee_rate + target_margin >= 1:
        raise ValueError("payment fee and target margin leave no room for costs")

    hardware_usd = hardware_cny / exchange_rate
    variable_cost = hardware_usd + other_cost
    payment_fee = (price * fee_rate) + fee_fixed
    contribution = price - payment_fee - variable_cost
    contribution_margin = contribution / price
    break_even = (variable_cost + fee_fixed) / (Decimal("1") - fee_rate)
    minimum = (variable_cost + fee_fixed) / (
        Decimal("1") - fee_rate - target_margin
    )
    meets_target = price >= minimum
    readiness_failures: list[str] = []
    if not costs_confirmed:
        readiness_failures.append("landed BOM and all variable costs are not confirmed")
    if not commercial_terms_reviewed:
        readiness_failures.append(
            "shipping, tax, cancellation, return, warranty, and support terms are not reviewed"
        )
    if not meets_target:
        readiness_failures.append("the quote is below the selected contribution-margin floor")

    return {
        "scope": "LKT supplied-device economics; the USD 250 collection-fit service is separate",
        "inputs": {
            "hardware_cost_cny": money(hardware_cny),
            "cny_per_usd": str(exchange_rate),
            "price_usd": money(price),
            "other_variable_cost_usd": money(other_cost),
            "payment_fee_percent": str(fee_rate * HUNDRED),
            "payment_fee_fixed_usd": money(fee_fixed),
            "target_margin_percent": str(target_margin * HUNDRED),
        },
        "economics": {
            "hardware_cost_usd": money(hardware_usd),
            "total_variable_cost_usd": money(variable_cost),
            "payment_fee_usd": money(payment_fee),
            "contribution_usd": money(contribution),
            "contribution_margin_percent": str(
                (contribution_margin * HUNDRED).quantize(CENT)
            ),
            "break_even_price_usd": money(break_even),
            "minimum_target_price_usd": money(minimum),
            "meets_target_margin": meets_target,
        },
        "public_offer_ready": not readiness_failures,
        "readiness_failures": readiness_failures,
        "policy": {
            "publishes_or_changes_price": False,
            "shipping_must_be_in_cost_or_charged_separately": True,
            "customer_payment_created": False,
            "private_supplier_quote_persisted": False,
        },
    }


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--hardware-cost-cny", required=True)
    command.add_argument("--cny-per-usd", required=True)
    command.add_argument("--price-usd", required=True)
    command.add_argument("--other-variable-cost-usd", required=True)
    command.add_argument("--payment-fee-percent", required=True)
    command.add_argument("--payment-fee-fixed-usd", required=True)
    command.add_argument("--target-margin-percent", required=True)
    command.add_argument("--costs-confirmed", action="store_true")
    command.add_argument("--commercial-terms-reviewed", action="store_true")
    return command


def main(argv: Sequence[str] | None = None) -> None:
    args = parser().parse_args(argv)
    report = build_report(
        hardware_cost_cny=args.hardware_cost_cny,
        cny_per_usd=args.cny_per_usd,
        price_usd=args.price_usd,
        other_variable_cost_usd=args.other_variable_cost_usd,
        payment_fee_percent=args.payment_fee_percent,
        payment_fee_fixed_usd=args.payment_fee_fixed_usd,
        target_margin_percent=args.target_margin_percent,
        costs_confirmed=args.costs_confirmed,
        commercial_terms_reviewed=args.commercial_terms_reviewed,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
