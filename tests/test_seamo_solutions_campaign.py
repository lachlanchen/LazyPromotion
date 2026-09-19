from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SeamoSolutionsCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(
            (ROOT / "campaigns/seamo-solutions-freelancer.json").read_text()
        )

    def test_bid_math_and_delivery_are_bounded(self):
        app = self.campaign["application"]
        self.assertEqual(app["proposed_bid_inr"], sum(app["milestones_inr"]))
        self.assertEqual(
            app["proposed_bid_inr"] - app["platform_fee_at_proposed_bid_inr"],
            app["proposed_net_before_other_deductions_inr"],
        )
        self.assertEqual(app["proposed_question_cap"], 25)
        self.assertEqual(app["proposed_revision_rounds"], 1)
        self.assertEqual(app["first_draft_days"], 7)
        self.assertEqual(app["proposed_delivery_days"], 10)

    def test_submission_does_not_claim_funding_or_olympiad_experience(self):
        app = self.campaign["application"]
        funnel = self.campaign["funnel"]
        self.assertTrue(app["bid_submitted"])
        self.assertFalse(app["paid_upgrade_selected"])
        self.assertFalse(app["automatic_follow_up"])
        self.assertIn(".local/private/", app["proposal"])
        self.assertNotIn("proposal_text", app)
        self.assertIn("funded milestones before accepting", app["policy"])
        self.assertIn("Olympiad credential", self.campaign["fit"]["boundary"])
        for key in (
            "buyer_reply_observed", "qualified_lead_observed", "scope_accepted",
            "contract_observed", "payment_confirmed", "delivered",
        ):
            self.assertFalse(funnel[key])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
