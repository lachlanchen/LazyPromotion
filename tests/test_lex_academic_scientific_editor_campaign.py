import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LexAcademicScientificEditorCampaignTests(unittest.TestCase):
    def test_prepared_application_keeps_claims_and_revenue_bounded(self):
        campaign = json.loads(
            (
                ROOT
                / "campaigns"
                / "lex-academic-scientific-editor-opportunity.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            campaign["source_need"]["state"],
            "official_current_freelance_recruitment",
        )
        self.assertIsNone(campaign["source_need"]["published_rate"])
        self.assertIn("paper-revision-skill", campaign["fit"]["projects"])
        self.assertIn("paid scientific-editing", campaign["fit"]["not_proven"][0])
        application = campaign["application"]
        self.assertEqual(application["state"], "sent_awaiting_human_reply")
        self.assertEqual(application["attachments_sent"], 1)
        self.assertFalse(application["client_credits_claimed"])
        self.assertEqual(
            application["automated_acknowledgement"]["state"],
            "automatic_reply_reviewed",
        )
        self.assertFalse(application["automated_acknowledgement"]["human_reply"])
        self.assertIn(
            "10 days", application["automated_acknowledgement"]["published_wait"]
        )
        self.assertEqual(application["review_after"], "2026-09-19")
        self.assertFalse(application["automatic_follow_up"])
        funnel = campaign["funnel"]
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertTrue(funnel["delivery_observed"])
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["contract_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
