import json
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "digitalocean-ripple-writer-pitch.json"


class DigitalOceanRippleWriterCampaignTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_payment_trigger_and_form_failure_are_not_conflated(self):
        source = self.payload["source_need"]
        self.assertIn("USD 500", source["published_rate"])
        self.assertIn("published", source["published_rate"])
        self.assertIn("vendor onboarding", source["published_rate"])
        self.assertIn("You need access", source["form_boundary"])
        self.assertFalse(self.payload["application"]["form_submitted"])
        self.assertFalse(self.payload["application"]["access_request_sent"])

    def test_fallback_pitch_is_delivered_but_not_a_lead_or_revenue(self):
        application = self.payload["application"]
        funnel = self.payload["funnel"]
        self.assertEqual(
            application["state"], "email_fallback_sent_awaiting_human_reply"
        )
        self.assertTrue(funnel["delivery_observed"])
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["pitch_accepted"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_claim_boundary_keeps_future_build_unproven(self):
        fit = self.payload["fit"]
        self.assertIn("remain future work", fit["claim_boundary"])
        self.assertIn("DigitalOcean-specific implementation results", fit["not_proven"])
        self.assertIn("https://github.com/lazyingart/AgInTiFlow", fit["public_proof"])
        self.assertIn("https://github.com/lachlanchen/LazyEdge", fit["public_proof"])

    def test_public_record_excludes_contact_and_private_browser_data(self):
        serialized = CAMPAIGN.read_text(encoding="utf-8").casefold()
        for forbidden in (
            "@digitalocean.com",
            "@gmail.com",
            "cookie",
            "browser profile",
            "message id",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_application_watch_schedules_review_after_published_window(self):
        record = application_watch.application_record(
            self.payload,
            source_file=CAMPAIGN,
            on=application_watch.parse_day("2026-09-09"),
        )
        self.assertIsNotNone(record)
        self.assertFalse(record["due_for_human_review"])
        self.assertEqual(self.payload["application"]["initial_review_after"], "2026-09-18")
        self.assertEqual(record["review_after"], "2026-09-27")

    def test_one_follow_up_is_not_a_second_application_or_assignment(self):
        follow_up = self.payload["application"]["follow_up"]
        self.assertEqual(follow_up["state"], "sent_once_awaiting_human_reply")
        self.assertFalse(follow_up["automatic_follow_up"])
        self.assertTrue(follow_up["ai_assistance_disclosed"])
        self.assertIn("not an accepted fee", follow_up["policy"])
        channel = self.payload["channels"]["direct_email"]
        self.assertEqual(channel["outbound_messages"], 2)
        self.assertEqual(channel["unique_applications"], 1)
        self.assertEqual(channel["fees_spent_usd"], 0)
        self.assertEqual(self.payload["funnel"]["outbound_application_count"], 1)
        self.assertFalse(self.payload["funnel"]["pitch_accepted"])

    def test_gmail_thread_is_not_reported_as_covered_by_icloud(self):
        coverage = self.payload["application"]["inbound_coverage"]
        self.assertEqual(coverage["provider"], "gmail")
        self.assertFalse(coverage["automatic_check_enabled"])
        self.assertFalse(coverage["human_reply_observed"])
        self.assertIn("outside the existing iCloud", coverage["policy"])


if __name__ == "__main__":
    unittest.main()
