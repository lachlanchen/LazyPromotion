import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "amezmo-technical-writer.json"


class AmezmoTechnicalWriterCampaignTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_current_pay_is_not_acceptance_or_revenue(self):
        source = self.payload["source_need"]

        self.assertEqual(source["published_pay"], "USD 300 per 2,000-word article")
        self.assertIn("not topic acceptance", source["boundary"])
        self.assertEqual(self.payload["funnel"]["received_revenue_usd"], 0)

    def test_exact_proof_and_gaps_remain_visible(self):
        fit = self.payload["fit"]
        gaps = " ".join(fit["not_proven"])

        self.assertIn("LazyEdge", fit["projects"])
        self.assertIn("outbound SSH", fit["proposed_topic"])
        self.assertIn("Amezmo-specific", gaps)
        self.assertIn("PHP runtime", gaps)
        self.assertIn("rights or license", gaps)

    def test_cloudflare_gate_was_not_bypassed(self):
        application = self.payload["application"]

        self.assertEqual(
            application["state"], "not_submitted_official_form_access_blocked"
        )
        self.assertFalse(application["application_submitted"])
        self.assertFalse(application["bypass_attempted"])
        self.assertFalse(application["alternate_contact_used"])
        self.assertFalse(application["full_article_drafted"])
        self.assertEqual(application["next_review_not_before"], "2026-09-19")


if __name__ == "__main__":
    unittest.main()
