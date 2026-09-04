import json
import unittest
from pathlib import Path

import lkt_hardware_pricing


class LktHardwarePricingTests(unittest.TestCase):
    def report(self, **overrides):
        values = {
            "hardware_cost_cny": "2100",
            "cny_per_usd": "7",
            "price_usd": "498",
            "other_variable_cost_usd": "60",
            "payment_fee_percent": "4",
            "payment_fee_fixed_usd": "0.30",
            "target_margin_percent": "35",
        }
        values.update(overrides)
        return lkt_hardware_pricing.build_report(**values)

    def test_quote_below_margin_floor_fails_closed(self):
        report = self.report()
        self.assertEqual(report["economics"]["hardware_cost_usd"], "300.00")
        self.assertEqual(report["economics"]["contribution_usd"], "117.78")
        self.assertEqual(report["economics"]["contribution_margin_percent"], "23.65")
        self.assertEqual(report["economics"]["minimum_target_price_usd"], "590.66")
        self.assertFalse(report["economics"]["meets_target_margin"])
        self.assertFalse(report["public_offer_ready"])

    def test_quote_stays_gated_until_costs_and_terms_are_confirmed(self):
        report = self.report(price_usd="748")
        self.assertTrue(report["economics"]["meets_target_margin"])
        self.assertFalse(report["public_offer_ready"])
        self.assertEqual(len(report["readiness_failures"]), 2)

        ready = self.report(
            price_usd="748",
            costs_confirmed=True,
            commercial_terms_reviewed=True,
        )
        self.assertTrue(ready["public_offer_ready"])
        self.assertEqual(ready["readiness_failures"], [])
        self.assertFalse(ready["policy"]["publishes_or_changes_price"])

    def test_report_has_no_payment_or_supplier_identifier_field(self):
        serialized = json.dumps(self.report())
        self.assertNotIn("supplier_name", serialized)
        self.assertNotIn("supplier_url", serialized)
        self.assertNotIn("account", serialized)
        self.assertFalse(self.report()["policy"]["customer_payment_created"])
        self.assertFalse(self.report()["policy"]["private_supplier_quote_persisted"])

    def test_invalid_rates_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "leave no room"):
            self.report(payment_fee_percent="20", target_margin_percent="80")

    def test_documented_device_floor_stays_non_public(self):
        body = (Path(__file__).parents[1] / "docs" / "lkt-hardware-pricing.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Do not advertise the earlier USD 498 device idea", body)
        self.assertIn("USD 798 is therefore a **proposed internal floor**", body)
        self.assertIn("minimum 25%-margin price is USD 768.56", body)


if __name__ == "__main__":
    unittest.main()
