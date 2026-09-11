from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PlaywrightRegressionCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(
            (ROOT / "campaigns" / "playwright-regression-contract.json").read_text(
                encoding="utf-8"
            )
        )

    def test_live_need_and_scope_boundary_are_explicit(self):
        need = self.campaign["source_need"]
        self.assertEqual(need["state"], "active_open")
        self.assertEqual(need["project_id"], 40704383)
        self.assertIn("manual checklist and application size", need["scope_unknowns"])
        self.assertIn("funded first milestone", need["policy"])

    def test_executed_proof_does_not_invent_buyer_coverage(self):
        specimen = self.campaign["fit"]["executed_specimen"]
        self.assertEqual(specimen["state"], "three_consecutive_runs_passed")
        self.assertEqual(specimen["tests_per_run"], 2)
        self.assertIn("Project-owned login fixture", specimen["boundary"])
        self.assertIn(
            "three clean runs against the buyer's environment",
            self.campaign["fit"]["not_proven"],
        )

    def test_bid_has_no_paid_upgrade_or_revenue_claim(self):
        application = self.campaign["application"]
        funnel = self.campaign["funnel"]
        self.assertEqual(application["state"], "submitted_once_visible_confirmation")
        self.assertTrue(application["bid_submitted"])
        self.assertFalse(application["paid_upgrade_selected"])
        self.assertTrue(funnel["application_submitted"])
        self.assertEqual(application["milestones_inr"], [11250, 22500, 16875, 5625])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_portfolio_card_stops_at_phone_gate(self):
        item = self.campaign["marketplace_account"]["portfolio_item"]
        self.assertEqual(
            item["state"], "prepared_not_published_phone_verification_required"
        )
        self.assertFalse(item["phone_verification_requested"])
        self.assertRegex(item["image_sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
