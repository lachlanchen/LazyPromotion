import json
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "draftdev-cybersecurity-writer-opportunity.json"


class DraftDevCybersecurityWriterCampaignTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_rate_is_third_party_and_not_an_accepted_contract(self):
        source = self.payload["source_need"]
        listing = source["current_listing"]
        self.assertEqual(source["url"], "https://draft.dev/write")
        self.assertIn("USD 315", listing["published_rate"])
        self.assertIn("third-party", listing["boundary"])
        self.assertIn("Confirm", listing["boundary"])
        self.assertIn("does not publish a rate", source["official_scope"])

    def test_application_is_one_submission_not_revenue(self):
        application = self.payload["application"]
        funnel = self.payload["funnel"]
        self.assertEqual(application["state"], "sent_awaiting_human_reply")
        self.assertEqual(application["review_after"], "2026-10-09")
        self.assertEqual(application["public_sample_links_sent"], 3)
        self.assertEqual(application["skill_topics_selected"], 8)
        self.assertFalse(application["resume_sent"])
        self.assertFalse(application["photo_sent"])
        self.assertFalse(application["automatic_follow_up"])
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_public_campaign_has_no_private_contact_or_browser_data(self):
        serialized = CAMPAIGN.read_text(encoding="utf-8").casefold()
        for forbidden in (
            "lach@",
            "cookie",
            "browser profile",
            "airtable response id",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_application_watch_waits_for_stated_thirty_day_window(self):
        record = application_watch.application_record(
            self.payload,
            source_file=CAMPAIGN,
            on=application_watch.parse_day("2026-09-09"),
        )
        self.assertIsNotNone(record)
        self.assertFalse(record["due_for_human_review"])
        self.assertEqual(record["review_after"], "2026-10-09")


if __name__ == "__main__":
    unittest.main()
