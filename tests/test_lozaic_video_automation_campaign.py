import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "campaigns" / "lozaic-video-automation.json"


class LozaicVideoAutomationCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))

    def test_first_milestone_is_bounded_below_the_full_public_budget(self):
        application = self.campaign["application"]
        self.assertIn("USD 750", application["proposed_first_milestone"])
        self.assertIn("actual prototype", application["remaining_scope_policy"])
        self.assertIn("acceptance tests", application["remaining_scope_policy"])

    def test_unproven_product_claims_are_explicit(self):
        gaps = " ".join(self.campaign["fit"]["not_proven"]).casefold()
        for phrase in (
            "electron",
            "premiere pro",
            "style detection",
            "multi-user",
            "customer outcome",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, gaps)

    def test_marketplace_and_revenue_states_fail_closed(self):
        application = self.campaign["application"]
        upwork = self.campaign["channels"]["upwork"]
        funnel = self.campaign["funnel"]
        self.assertEqual(application["state"], "prepared_login_required")
        self.assertFalse(application["application_submitted"])
        self.assertEqual(application["connects_spent"], 0)
        self.assertEqual(upwork["state"], "prepared_login_required")
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["contract_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
