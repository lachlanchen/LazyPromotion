#!/usr/bin/env python3
"""Verify a fit-gated LazyingArt Stripe path without creating Stripe objects."""

from __future__ import annotations

import argparse
import json
import stat
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
DEFAULT_HELPER_ROOT = (ROOT.parent / "Stripe").resolve()
OFFER_CONTRACTS = {
    "lkt": {
        "config_relative": Path("config/local-knowledge-terminal-sprint.json"),
        "slug": "local-knowledge-terminal-collection-fit-sprint",
        "minimum_review_notes": 7,
    },
    "manuscript": {
        "config_relative": Path("config/manuscript-build-redline-sprint.json"),
        "slug": "manuscript-build-redline-sprint",
        "minimum_review_notes": 8,
    },
}


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def inspect_config(path: Path, *, offer: str = "lkt") -> dict[str, object]:
    contract = OFFER_CONTRACTS.get(offer)
    if not contract:
        raise ValueError(f"unknown offer: {offer}")
    config = json.loads(path.read_text(encoding="utf-8"))
    variants = config.get("variants")
    notes = config.get("fulfillmentReviewNotes")
    failures: list[str] = []

    if config.get("slug") != contract["slug"]:
        failures.append("unexpected product slug")
    if config.get("requiresFulfillmentReview") is not True:
        failures.append("fulfillment review is not required")
    if (
        not isinstance(notes, list)
        or len(notes) < int(contract["minimum_review_notes"])
        or not all(str(note).strip() for note in notes)
    ):
        failures.append("the full fulfillment review checklist is missing")
    if config.get("quantity") != 1:
        failures.append("quantity is not fixed at one")
    if config.get("adjustableQuantity", {}).get("enabled") is not False:
        failures.append("adjustable quantity is enabled")
    if config.get("allowPromotionCodes") is not False:
        failures.append("promotion codes are enabled")
    if config.get("shippingCountries") != []:
        failures.append("shipping collection is enabled for a service")
    if config.get("billingAddressCollection") != "required":
        failures.append("billing address collection is not required")
    if not isinstance(variants, list) or len(variants) != 1:
        failures.append("the offer must have exactly one checkout variant")
        variant: dict[str, object] = {}
    else:
        variant = variants[0]
        if str(variant.get("currency", "")).lower() != "usd":
            failures.append("the checkout currency is not USD")
        if variant.get("unitAmount") != 25_000:
            failures.append("the checkout amount is not USD 250")
    if config.get("metadata", {}).get("fit_check_required") != "true":
        failures.append("fit-check metadata is missing")

    return {
        "offer": offer,
        "config_ready": not failures,
        "failures": failures,
        "product_slug": config.get("slug", ""),
        "currency": str(variant.get("currency", "")).upper(),
        "unit_amount_minor": variant.get("unitAmount"),
        "display_price": "USD 250" if variant.get("unitAmount") == 25_000 else "",
        "quantity": config.get("quantity"),
        "fulfillment_review_required": config.get("requiresFulfillmentReview") is True,
        "fulfillment_review_notes": len(notes) if isinstance(notes, list) else 0,
        "public_export_allowed": False,
    }


def inspect_private_key(path: Path) -> tuple[dict[str, object], str]:
    mode = stat.S_IMODE(path.stat().st_mode)
    key = load_env(path).get("STRIPE_SECRET_KEY", "")
    key_mode = "live" if key.startswith("sk_live_") else "test" if key.startswith("sk_test_") else "unknown"
    status = {
        "env_file_present": True,
        "env_file_mode": f"{mode:03o}",
        "env_file_private": mode == 0o600,
        "secret_key_present": bool(key),
        "secret_key_format_valid": key_mode in {"live", "test"},
        "key_mode": key_mode,
    }
    return status, key


def check_account(secret_key: str, *, opener=urlopen) -> dict[str, object]:
    request = Request(
        "https://api.stripe.com/v1/account",
        headers={"Authorization": f"Bearer {secret_key}"},
    )
    try:
        with opener(request, timeout=20) as response:
            account = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Stripe account authentication failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("Stripe account check could not reach the API") from exc

    requirements = account.get("requirements") or {}
    currently_due = requirements.get("currently_due")
    eventually_due = requirements.get("eventually_due")
    return {
        "authenticated": account.get("object") == "account",
        "charges_enabled": bool(account.get("charges_enabled")),
        "payouts_enabled": bool(account.get("payouts_enabled")),
        "details_submitted": bool(account.get("details_submitted")),
        "currently_due_count": len(currently_due) if isinstance(currently_due, list) else None,
        "eventually_due_count": len(eventually_due) if isinstance(eventually_due, list) else None,
    }


def build_report(
    helper_root: Path,
    *,
    offer: str = "lkt",
    check_live_account: bool = False,
    opener=urlopen,
) -> dict[str, object]:
    helper_root = helper_root.resolve()
    contract = OFFER_CONTRACTS.get(offer)
    if not contract:
        raise ValueError(f"unknown offer: {offer}")
    config_status = inspect_config(
        helper_root / contract["config_relative"],
        offer=offer,
    )
    key_status, secret_key = inspect_private_key(helper_root / ".env")
    account_status = check_account(secret_key, opener=opener) if check_live_account else None
    account_ready = bool(
        account_status
        and account_status["authenticated"]
        and account_status["charges_enabled"]
        and account_status["payouts_enabled"]
        and account_status["details_submitted"]
    )
    local_ready = bool(
        config_status["config_ready"]
        and key_status["env_file_private"]
        and key_status["secret_key_format_valid"]
        and key_status["key_mode"] == "live"
    )
    return {
        "offer": offer,
        "mutates_stripe": False,
        "helper_root": str(helper_root),
        "config": config_status,
        "private_key": key_status,
        "account_checked": check_live_account,
        "account": account_status,
        "local_live_configuration_ready": local_ready,
        "ready_for_reviewed_live_request": local_ready and account_ready if check_live_account else None,
        "remaining_gate": (
            "A real customer must pass the free fit check and accept the written scope. "
            "Review every fulfillment note before separately running the Stripe creation command; "
            "this readiness check never creates a Product, Price, Payment Link, charge, or payout."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper-root", type=Path, default=DEFAULT_HELPER_ROOT)
    parser.add_argument("--offer", choices=sorted(OFFER_CONTRACTS), default="lkt")
    parser.add_argument("--check-account", action="store_true")
    parser.add_argument("--confirm-private-financial-read", action="store_true")
    args = parser.parse_args(argv)

    if args.check_account and not args.confirm_private_financial_read:
        raise SystemExit("--check-account requires --confirm-private-financial-read")
    report = build_report(
        args.helper_root,
        offer=args.offer,
        check_live_account=args.check_account,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
