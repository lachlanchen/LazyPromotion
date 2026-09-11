import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PaidWriterRouteTests(unittest.TestCase):
    def load(self, name):
        path = ROOT / "campaigns" / name
        serialized = path.read_text(encoding="utf-8")
        return serialized, json.loads(serialized)

    def test_knowledgeowl_pitch_is_sent_without_inflating_outcome(self):
        serialized, campaign = self.load("knowledgeowl-source-ledger-writer-pitch.json")
        self.assertEqual(campaign["version"], 1)
        self.assertEqual(
            campaign["source_need"]["published_compensation"],
            "USD 250 per published article, or the writer's established higher rate.",
        )
        self.assertEqual(campaign["application"]["state"], "sent_awaiting_editorial_reply")
        self.assertEqual(
            campaign["application"]["quoted_rate"],
            "USD 250 for one 1,200 to 1,600 word article",
        )
        self.assertEqual(len(campaign["fit"]["public_samples"]), 3)
        self.assertFalse(campaign["funnel"]["human_reply_observed"])
        self.assertFalse(campaign["funnel"]["payment_confirmed"])
        self.assertEqual(campaign["funnel"]["received_revenue_usd"], 0)
        self.assertIsNone(
            re.search(
                r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
                serialized,
                re.IGNORECASE,
            )
        )

    def test_percona_pitch_is_code_bound_and_not_a_production_claim(self):
        serialized, campaign = self.load("percona-microquant-writer-pitch.json")
        self.assertEqual(campaign["version"], 1)
        self.assertEqual(
            campaign["source_need"]["published_compensation"],
            "USD 350 after publication.",
        )
        self.assertIn(
            "prohibits AI-generated",
            campaign["source_need"]["published_ai_policy"],
        )
        self.assertEqual(
            campaign["fit"]["repository_revision_checked"],
            "10fb3047cbd44609945a8e8b4617e7c002e230f6",
        )
        self.assertIn(
            "ON CONFLICT DO UPDATE",
            " ".join(campaign["fit"]["supported_now"]),
        )
        self.assertIn(
            "production incident",
            " ".join(campaign["fit"]["not_claimed"]),
        )
        self.assertEqual(
            campaign["application"]["state"],
            "submitted_awaiting_editorial_reply",
        )
        self.assertFalse(campaign["funnel"]["qualified_lead_observed"])
        self.assertFalse(campaign["funnel"]["payment_confirmed"])
        self.assertEqual(campaign["funnel"]["received_revenue_usd"], 0)
        self.assertIsNone(
            re.search(
                r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
                serialized,
                re.IGNORECASE,
            )
        )

    def test_technically_application_is_paid_and_does_not_inflate_revenue(self):
        serialized, campaign = self.load("technically-contributor-program.json")
        self.assertEqual(campaign["version"], 2)
        self.assertEqual(
            campaign["source_need"]["published_compensation"],
            "USD 500 per contribution. Technically says the first contribution is paid even if it does not reach the publication bar.",
        )
        self.assertEqual(
            campaign["fit"]["first_topic"],
            "What an MCP server actually does—and why tool permissions matter",
        )
        self.assertEqual(len(campaign["fit"]["public_samples"]), 3)
        self.assertEqual(
            campaign["application"]["state"], "submitted_awaiting_human_reply"
        )
        self.assertFalse(campaign["application"]["linkedin_profile_sent"])
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
                serialized,
                re.IGNORECASE,
            )
        )


if __name__ == "__main__":
    unittest.main()
