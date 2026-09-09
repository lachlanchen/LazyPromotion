import json
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "neverinstall-technical-writer-opportunity.json"


class NeverinstallTechnicalWriterCampaignTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_live_route_keeps_old_program_page_and_payment_trigger_visible(self):
        source = self.payload["source_need"]
        self.assertEqual(source["program_page_published_at"], "2022-08-01T12:31:00Z")
        self.assertIn("USD 100–250", source["published_rate"])
        self.assertIn("approves for publication", source["published_rate"])
        self.assertIn("potentially unattended", source["freshness_boundary"])
        self.assertIn("do not explicitly guarantee Hong Kong", source["eligibility_boundary"])

    def test_application_is_one_bounded_submission_not_revenue(self):
        application = self.payload["application"]
        funnel = self.payload["funnel"]
        self.assertEqual(application["state"], "sent_awaiting_human_reply")
        self.assertEqual(application["review_after"], "2026-09-16")
        self.assertEqual(application["portfolio_articles_visible"], 3)
        self.assertFalse(application["resume_sent"])
        self.assertFalse(application["video_sent"])
        self.assertFalse(application["draft_sent"])
        self.assertFalse(application["account_created"])
        self.assertFalse(application["automatic_follow_up"])
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_public_campaign_has_no_contact_or_private_browser_data(self):
        serialized = CAMPAIGN.read_text(encoding="utf-8").casefold()
        for forbidden in (
            "lach@",
            "cookie",
            "websocket",
            "browser profile",
            "typeform response id",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertIn("https://lazying.art/work/", serialized)
        self.assertIn("https://github.com/lachlanchen/lazyedge", serialized)
        self.assertIn("https://github.com/lachlanchen/lazytunnel", serialized)

    def test_application_watch_schedules_one_human_review_without_follow_up(self):
        record = application_watch.application_record(
            self.payload,
            source_file=CAMPAIGN,
            on=application_watch.parse_day("2026-09-09"),
        )
        self.assertIsNotNone(record)
        self.assertFalse(record["due_for_human_review"])
        self.assertEqual(record["review_after"], "2026-09-16")


if __name__ == "__main__":
    unittest.main()

