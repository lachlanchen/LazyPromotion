import json
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "apify-content-writer-opportunity.json"


class ApifyContentWriterCampaignTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_published_payment_requires_review_ready_article(self):
        source = self.payload["source_need"]
        self.assertIn("USD 500", source["published_rate"])
        self.assertIn("working code", source["published_rate"])
        self.assertIn("reviewed", source["published_rate"])

    def test_account_gate_was_not_bypassed(self):
        application = self.payload["application"]
        self.assertFalse(application["discord_joined"])
        self.assertFalse(application["discord_submission_sent"])
        self.assertFalse(application["account_created"])
        self.assertFalse(application["complete_article_sent"])
        self.assertIn(
            "No account was created", self.payload["source_need"]["account_boundary"]
        )

    def test_fallback_question_is_not_acceptance_or_revenue(self):
        application = self.payload["application"]
        funnel = self.payload["funnel"]
        self.assertEqual(
            application["state"], "email_fallback_sent_awaiting_human_reply"
        )
        self.assertTrue(funnel["delivery_observed"])
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["topic_confirmed"])
        self.assertFalse(funnel["article_accepted"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_public_record_has_no_contact_or_browser_secrets(self):
        serialized = CAMPAIGN.read_text(encoding="utf-8").casefold()
        for forbidden in (
            "hello@",
            "@gmail.com",
            "cookie",
            "browser profile",
            "message id",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_application_watch_schedules_one_nonautomatic_review(self):
        record = application_watch.application_record(
            self.payload,
            source_file=CAMPAIGN,
            on=application_watch.parse_day("2026-09-09"),
        )
        self.assertIsNotNone(record)
        self.assertFalse(record["due_for_human_review"])
        self.assertEqual(record["review_after"], "2026-09-16")
        self.assertFalse(self.payload["application"]["automatic_follow_up"])


if __name__ == "__main__":
    unittest.main()
