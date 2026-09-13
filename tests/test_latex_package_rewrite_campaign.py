import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LatexPackageRewriteCampaignTests(unittest.TestCase):
    def test_declined_application_is_closed_without_lead_or_revenue(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "latex-package-rewrite.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(campaign["version"], 3)
        self.assertEqual(campaign["source_need"]["state"], "public_explicit_paid_request")
        self.assertEqual(campaign["source_need"]["budget"], "USD 50-100")
        self.assertEqual(campaign["fit"]["project"], "paperagent")
        self.assertTrue(
            all(url.startswith("https://") for url in campaign["fit"]["public_proof"])
        )
        self.assertEqual(campaign["application"]["state"], "closed_not_selected")
        self.assertIn("closed_at", campaign["application"])
        self.assertNotIn("follow_up_not_before", campaign["application"])
        self.assertFalse(campaign["application"]["automatic_follow_up"])
        self.assertFalse(campaign["application"]["future_agent_contact"])
        self.assertIn(
            "Rule 10",
            campaign["application"]["community_policy_observation"]["rule"],
        )
        self.assertTrue(campaign["funnel"]["buyer_reply_observed"])
        self.assertFalse(campaign["funnel"]["qualified_lead_observed"])
        self.assertFalse(campaign["funnel"]["payment_confirmed"])
        self.assertEqual(campaign["funnel"]["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
