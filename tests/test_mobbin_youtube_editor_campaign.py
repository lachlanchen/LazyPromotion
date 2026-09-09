import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "mobbin-youtube-editor-opportunity.json"


class MobbinYouTubeEditorCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = CAMPAIGN.read_text(encoding="utf-8")
        cls.campaign = json.loads(cls.raw)

    def test_current_first_party_source_is_pinned(self):
        source = self.campaign["source_need"]
        self.assertEqual(self.campaign["version"], 1)
        self.assertEqual(source["state"], "first_party_role_listed")
        self.assertEqual(source["published_compensation"].split()[0], "No")
        self.assertTrue(source["official_posting"].startswith("https://jobs.ashbyhq.com/"))
        self.assertTrue(source["official_application"].endswith("/application"))
        self.assertIn("two to four videos", source["engagement"].casefold())

    def test_proof_and_gaps_are_not_blurred(self):
        fit = self.campaign["fit"]
        urls = [sample["url"] for sample in fit["public_samples"]]
        self.assertIn("https://www.youtube.com/watch?v=9FjVTAgD9QE", urls)
        self.assertIn("https://lazying.art/video/", urls)
        gaps = " ".join(fit["not_proven"]).casefold()
        self.assertIn("paid client", gaps)
        self.assertIn("retention", gaps)
        self.assertIn("premiere pro", gaps)
        self.assertIn("do not call them client work", fit["claim_boundary"].casefold())

    def test_application_stays_guarded(self):
        application = self.campaign["application"]
        self.assertEqual(
            application["state"], "prepared_personal_fact_confirmation_required"
        )
        self.assertIn("must not be inferred", application["blocking_personal_fact"])
        self.assertIn("SGD 2,400", application["pricing_position"]["expected_rate"])
        self.assertFalse(application["submitted"])
        self.assertFalse(application["automatic_follow_up"])
        self.assertNotIn("@", json.dumps(application))

    def test_attention_is_not_revenue(self):
        funnel = self.campaign["funnel"]
        self.assertEqual(funnel["state"], "attention")
        self.assertFalse(funnel["buyer_reply_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
