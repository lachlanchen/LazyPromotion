from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SourceBoundedEducationalPromptCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(
            (ROOT / "campaigns" / "source-bounded-educational-prompt.json").read_text(
                encoding="utf-8"
            )
        )

    def test_current_need_and_buyer_gate_are_recorded(self):
        need = self.campaign["source_need"]
        self.assertEqual(need["project_id"], 40703686)
        self.assertEqual(need["state"], "active_open_bidding_gated")
        self.assertIn("identity", need["buyer_state"])
        self.assertIn("no reviews", need["buyer_state"])

    def test_public_proof_stays_inside_its_evidence_boundary(self):
        specimen = self.campaign["fit"]["executed_specimen"]
        self.assertEqual(specimen["repository_commit"], "d863a41")
        self.assertIn("not a customer result", specimen["boundary"])
        self.assertIn(
            "paid educational-prompt delivery",
            self.campaign["fit"]["not_proven"],
        )

    def test_paid_bid_gate_was_not_crossed(self):
        check = self.campaign["marketplace_check"]
        self.assertEqual(check["state"], "not_submitted_minimum_balance_gate")
        self.assertFalse(check["funds_added"])
        self.assertFalse(check["paid_upgrade_selected"])
        self.assertFalse(check["application_submitted"])
        self.assertIn("Do not fund", check["policy"])

    def test_proof_is_not_recorded_as_revenue(self):
        funnel = self.campaign["funnel"]
        self.assertFalse(funnel["application_submitted"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
