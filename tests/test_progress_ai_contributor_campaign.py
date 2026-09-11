import json
import re
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]


class ProgressAiContributorCampaignTests(unittest.TestCase):
    def setUp(self):
        self.path = (
            ROOT / "campaigns" / "progress-ai-thought-leadership-contributor.json"
        )
        self.serialized = self.path.read_text(encoding="utf-8")
        self.campaign = json.loads(self.serialized)

    def test_application_is_delivered_without_inflating_revenue(self):
        source = self.campaign["source_need"]
        self.assertEqual(
            source["published_compensation"][
                "written_content_usd_per_published_piece"
            ],
            500,
        )
        self.assertEqual(len(self.campaign["fit"]["publications"]), 3)
        application = self.campaign["application"]
        self.assertEqual(application["state"], "submitted_awaiting_human_reply")
        self.assertEqual(application["content_types_selected"], ["Blogs"])
        self.assertFalse(application["partner_selected"])
        self.assertFalse(application["employee_selected"])
        self.assertEqual(application["submission_attempts"], 1)
        self.assertTrue(self.campaign["funnel"]["delivery_observed"])
        self.assertFalse(self.campaign["funnel"]["human_reply_observed"])
        self.assertFalse(self.campaign["funnel"]["payment_confirmed"])
        self.assertEqual(self.campaign["funnel"]["received_revenue_usd"], 0)
        self.assertIsNone(
            re.search(
                r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
                self.serialized,
                re.IGNORECASE,
            )
        )

    def test_application_watch_uses_one_review_date(self):
        record = application_watch.application_record(
            self.campaign,
            source_file=self.path,
            on=application_watch.parse_day("2026-09-11"),
        )
        self.assertIsNotNone(record)
        self.assertEqual(record["review_after"], "2026-09-18")
        self.assertFalse(record["due_for_human_review"])
        self.assertFalse(self.campaign["application"]["automatic_follow_up"])


if __name__ == "__main__":
    unittest.main()
