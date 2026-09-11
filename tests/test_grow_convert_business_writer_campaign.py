import json
import re
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]


class GrowConvertBusinessWriterCampaignTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "campaigns" / "grow-convert-business-writer.json"
        self.serialized = self.path.read_text(encoding="utf-8")
        self.campaign = json.loads(self.serialized)

    def test_application_is_recorded_without_inflating_outcome(self):
        campaign = self.campaign
        self.assertEqual(campaign["version"], 1)
        self.assertEqual(
            campaign["source_need"]["published_compensation"].split()[0], "USD"
        )
        self.assertEqual(len(campaign["fit"]["public_samples"]), 3)
        self.assertLessEqual(
            campaign["fit"]["application_exercise"]["word_count"], 300
        )
        self.assertEqual(
            campaign["application"]["state"], "submitted_awaiting_human_reply"
        )
        self.assertFalse(campaign["application"]["account_required"])
        self.assertIn(
            "must not impersonate", campaign["application"]["operator_dependency"]
        )
        self.assertTrue(campaign["funnel"]["delivery_observed"])
        self.assertFalse(campaign["funnel"]["human_reply_observed"])
        self.assertFalse(campaign["funnel"]["payment_confirmed"])
        self.assertEqual(campaign["funnel"]["received_revenue_usd"], 0)
        inbound = campaign["application"]["inbound_monitor"]
        self.assertEqual(inbound["state"], "automatic_receipt_reviewed")
        self.assertEqual(inbound["matching_thread_count"], 1)
        self.assertEqual(inbound["unread_matching_thread_count"], 0)
        self.assertTrue(inbound["mail_opened"])
        self.assertTrue(inbound["message_preview_read"])
        receipt = campaign["application"]["automated_acknowledgement"]
        self.assertEqual(receipt["state"], "automatic_form_receipt_reviewed")
        self.assertFalse(receipt["human_reply"])
        self.assertIn("one month", receipt["published_wait"])
        self.assertIsNone(
            re.search(
                r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
                self.serialized,
                re.IGNORECASE,
            )
        )

    def test_application_watch_uses_the_explicit_review_date(self):
        record = application_watch.application_record(
            self.campaign,
            source_file=self.path,
            on=application_watch.parse_day("2026-09-11"),
        )
        self.assertIsNotNone(record)
        self.assertEqual(record["review_after"], "2026-10-11")
        self.assertFalse(record["due_for_human_review"])


if __name__ == "__main__":
    unittest.main()
