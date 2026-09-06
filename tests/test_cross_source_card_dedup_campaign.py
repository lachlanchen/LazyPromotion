import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "cross-source-card-dedup.json"


class CrossSourceCardDedupCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_live_article_has_one_bounded_offer_path(self):
        lazyblog = self.campaign["channels"]["lazyblog"]
        conversion = lazyblog["conversion_path"]

        self.assertEqual(self.campaign["version"], 2)
        self.assertIn("48adb6a", lazyblog["blog_commits"])
        self.assertIn("USD 250", conversion["offer"])
        self.assertIn("12 source units", conversion["offer"])
        self.assertIn("20 test questions", conversion["offer"])
        self.assertEqual(
            conversion["fit_check"],
            "https://lazying.art/lkt/fit-check/?utm_source=lazyblog&utm_medium=article&utm_campaign=card_dedup&utm_content=fit_check",
        )
        self.assertFalse(conversion["automatic_form_submission"])
        self.assertIn("HTTP 200", conversion["live_review"])

    def test_publication_and_attention_do_not_inflate_revenue(self):
        funnel = self.campaign["funnel"]
        self.assertEqual(funnel["state"], "attention")
        self.assertFalse(funnel["fit_inquiry_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
