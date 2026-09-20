import json
import re
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]


class AppSignalTechnicalWriterCampaignTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "campaigns" / "appsignal-technical-writer-program.json"
        self.serialized = self.path.read_text(encoding="utf-8")
        self.campaign = json.loads(self.serialized)

    def test_application_is_submitted_without_inflating_outcome(self):
        campaign = self.campaign
        self.assertEqual(campaign["version"], 3)
        self.assertEqual(campaign["fit"]["selected_language"], "Node.js")
        self.assertEqual(campaign["fit"]["selected_topic"], "Observability")
        self.assertEqual(len(campaign["fit"]["public_samples"]), 3)
        self.assertEqual(
            campaign["application"]["state"], "submitted_awaiting_human_reply"
        )
        self.assertFalse(campaign["application"]["account_required"])
        self.assertFalse(campaign["application"]["rate_claimed"])
        inbound = campaign["application"]["inbound_monitor"]
        self.assertEqual(inbound["state"], "baseline_initialized")
        self.assertEqual(inbound["matching_thread_count"], 0)
        self.assertFalse(inbound["mail_opened"])
        self.assertFalse(inbound["message_preview_read"])
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

    def test_application_watch_uses_the_explicit_review_date(self):
        record = application_watch.application_record(
            self.campaign,
            source_file=self.path,
            on=application_watch.parse_day("2026-09-11"),
        )
        self.assertIsNotNone(record)
        self.assertEqual(record["review_after"], "2026-09-18")
        self.assertFalse(record["due_for_human_review"])

    def test_follow_up_retains_delivery_uncertainty_and_no_retry(self):
        follow_up = self.campaign["application"]["follow_up"]
        self.assertEqual(follow_up["state"], "send_attempted_delivery_unverified")
        self.assertEqual(follow_up["send_attempts"], 1)
        self.assertFalse(follow_up["sent_copy_verified"])
        self.assertFalse(follow_up["automatic_retry"])
        self.assertIn("not confirmed delivery", follow_up["verification_policy"])
        proof = self.campaign["fit"]["bounded_article_angle"]
        self.assertEqual(proof["focused_tests_run"], 2)
        self.assertEqual(proof["focused_tests_passed"], 2)
        self.assertIn(proof["proof_revision"], proof["proof_url"])
        self.assertTrue(proof["public_remote_revision_verified"])
        self.assertFalse(proof["article_or_outline_written"])


if __name__ == "__main__":
    unittest.main()
