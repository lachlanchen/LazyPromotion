import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import payment_readiness


def valid_config() -> dict:
    return {
        "slug": "local-knowledge-terminal-collection-fit-sprint",
        "quantity": 1,
        "adjustableQuantity": {"enabled": False},
        "shippingCountries": [],
        "allowPromotionCodes": False,
        "billingAddressCollection": "required",
        "requiresFulfillmentReview": True,
        "fulfillmentReviewNotes": [f"review {index}" for index in range(7)],
        "variants": [{"currency": "usd", "unitAmount": 25000}],
        "metadata": {"fit_check_required": "true"},
    }


def valid_manuscript_config() -> dict:
    config = valid_config()
    config["slug"] = "manuscript-build-redline-sprint"
    config["fulfillmentReviewNotes"].append("review 7")
    return config


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class PaymentReadinessTests(unittest.TestCase):
    def helper(
        self,
        root: Path,
        config: dict | None = None,
        *,
        config_name: str = "local-knowledge-terminal-sprint.json",
    ) -> Path:
        (root / "config").mkdir()
        (root / "config" / config_name).write_text(
            json.dumps(config or valid_config()), encoding="utf-8"
        )
        env = root / ".env"
        env.write_text("STRIPE_SECRET_KEY=sk_live_private_test_value\n", encoding="utf-8")
        env.chmod(0o600)
        return root

    def test_local_report_is_sanitized_and_does_not_claim_account_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = payment_readiness.build_report(self.helper(Path(tmp)))
        serialized = json.dumps(report)
        self.assertTrue(report["config"]["config_ready"])
        self.assertTrue(report["local_live_configuration_ready"])
        self.assertIsNone(report["ready_for_reviewed_live_request"])
        self.assertFalse(report["account_checked"])
        self.assertNotIn("sk_live_private_test_value", serialized)
        self.assertFalse(report["mutates_stripe"])

    def test_manuscript_report_uses_its_exact_guarded_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            helper = self.helper(
                Path(tmp),
                valid_manuscript_config(),
                config_name="manuscript-build-redline-sprint.json",
            )
            report = payment_readiness.build_report(helper, offer="manuscript")
        serialized = json.dumps(report)
        self.assertEqual(report["offer"], "manuscript")
        self.assertEqual(report["config"]["offer"], "manuscript")
        self.assertEqual(
            report["config"]["product_slug"],
            "manuscript-build-redline-sprint",
        )
        self.assertEqual(report["config"]["display_price"], "USD 250")
        self.assertEqual(report["config"]["fulfillment_review_notes"], 8)
        self.assertTrue(report["local_live_configuration_ready"])
        self.assertFalse(report["mutates_stripe"])
        self.assertNotIn("sk_live_private_test_value", serialized)

    def test_wrong_amount_fails_closed(self):
        config = valid_config()
        config["variants"][0]["unitAmount"] = 24999
        with tempfile.TemporaryDirectory() as tmp:
            report = payment_readiness.build_report(self.helper(Path(tmp), config))
        self.assertFalse(report["config"]["config_ready"])
        self.assertIn("the checkout amount is not USD 250", report["config"]["failures"])
        self.assertFalse(report["local_live_configuration_ready"])

    def test_read_only_account_result_can_prove_readiness_without_identifiers(self):
        payload = {
            "id": "acct_private_identifier",
            "object": "account",
            "charges_enabled": True,
            "payouts_enabled": True,
            "details_submitted": True,
            "requirements": {"currently_due": [], "eventually_due": []},
        }

        def opener(_request, timeout):
            self.assertEqual(timeout, 20)
            return FakeResponse(payload)

        with tempfile.TemporaryDirectory() as tmp:
            report = payment_readiness.build_report(
                self.helper(Path(tmp)), check_live_account=True, opener=opener
            )
        serialized = json.dumps(report)
        self.assertTrue(report["ready_for_reviewed_live_request"])
        self.assertNotIn("acct_private_identifier", serialized)
        self.assertFalse(report["mutates_stripe"])

    def test_cli_requires_explicit_confirmation_for_account_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            helper = self.helper(Path(tmp))
            with self.assertRaisesRegex(SystemExit, "confirm-private-financial-read"):
                with redirect_stdout(io.StringIO()):
                    payment_readiness.main(
                        ["--helper-root", str(helper), "--check-account"]
                    )


if __name__ == "__main__":
    unittest.main()
