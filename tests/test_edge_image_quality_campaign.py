import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "edge-image-quality-contract.json"


class EdgeImageQualityCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_current_need_and_budget_are_pinned(self):
        source = self.campaign["source_need"]
        self.assertEqual(source["state"], "public_listing_visible")
        self.assertEqual(source["eligibility"], "Worldwide")
        self.assertIn("1,800–2,500", source["published_budget"])
        self.assertIn("50-plus proposals", source["activity_when_checked"])
        self.assertIn("not escrow", source["policy"])

    def test_proof_and_medical_gaps_stay_separate(self):
        fit = self.campaign["fit"]
        urls = [item["url"] for item in fit["public_evidence"]]
        self.assertIn("https://github.com/lachlanchen/OpenHI", urls)
        self.assertTrue(any("edge-image-quality" in url for url in urls))
        gaps = " ".join(fit["not_proven"]).casefold()
        self.assertIn("medical images", gaps)
        self.assertIn("incorrect view", gaps)
        self.assertIn("customer work", fit["claim_boundary"].casefold())

    def test_application_stays_guarded_and_bounded(self):
        application = self.campaign["application"]
        self.assertEqual(application["state"], "prepared_login_required")
        self.assertEqual(application["proposed_fixed_price"], "USD 2,200")
        self.assertEqual(len(application["milestones"]), 3)
        self.assertEqual(application["connects_spent"], 0)
        self.assertFalse(application["application_submitted"])
        self.assertIn("spend Connects", application["policy"])

    def test_attention_is_not_revenue(self):
        funnel = self.campaign["funnel"]
        self.assertEqual(funnel["state"], "buyer_intent_identified")
        self.assertFalse(funnel["buyer_reply_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
