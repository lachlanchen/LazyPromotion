import json
import re
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]


class HygraphCreatorCampaignTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "campaigns" / "hygraph-creator-program.json"
        self.serialized = self.path.read_text(encoding="utf-8")
        self.campaign = json.loads(self.serialized)

    def test_application_is_submitted_without_inflating_outcome(self):
        campaign = self.campaign
        self.assertEqual(campaign["version"], 1)
        self.assertIn("Hygraph MCP", campaign["source_need"]["published_scope"])
        self.assertIn("rights-cleared", campaign["fit"]["proposal"])
        self.assertEqual(
            campaign["application"]["state"], "submitted_awaiting_human_reply"
        )
        self.assertFalse(campaign["application"]["account_created"])
        self.assertFalse(campaign["application"]["credential_created"])
        self.assertTrue(campaign["funnel"]["delivery_observed"])
        self.assertFalse(campaign["funnel"]["human_reply_observed"])
        self.assertFalse(campaign["funnel"]["payment_confirmed"])
        self.assertEqual(campaign["funnel"]["received_revenue_usd"], 0)
        self.assertIsNone(
            re.search(
                r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
                self.serialized,
                re.IGNORECASE,
            )
        )

    def test_application_watch_uses_the_published_reply_window(self):
        record = application_watch.application_record(
            self.campaign,
            source_file=self.path,
            on=application_watch.parse_day("2026-09-11"),
        )
        self.assertIsNotNone(record)
        self.assertEqual(record["review_after"], "2026-09-18")
        self.assertFalse(record["due_for_human_review"])


if __name__ == "__main__":
    unittest.main()
