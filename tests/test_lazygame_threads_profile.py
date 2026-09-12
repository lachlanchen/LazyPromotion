import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LazyGameThreadsProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(
            (ROOT / "campaigns" / "lazygame-teaching-explainer.json").read_text(
                encoding="utf-8"
            )
        )

    def test_reply_stays_helpful_and_profile_supplies_quiet_context(self):
        threads = self.campaign["channels"]["threads"]
        profile = threads["profile_context"]

        self.assertEqual(self.campaign["version"], 4)
        self.assertEqual(threads["state"], "one_direct_answer_sent")
        self.assertFalse(threads["linked_project"])
        self.assertEqual(profile["state"], "live_verified")
        self.assertEqual(profile["profile_url"], "https://www.threads.com/@lazying.art")
        self.assertEqual(profile["link_url"], "https://lazying.art")
        self.assertEqual(
            hashlib.sha256(profile["bio"].encode("utf-8")).hexdigest(),
            profile["content_sha256"],
        )
        self.assertNotIn("$", profile["bio"])
        self.assertIn("attention only", profile["boundary"])
        self.assertFalse(threads["follow_up_check"]["new_reply_observed"])
        self.assertEqual(threads["follow_up_check"]["visible_owned_posts_checked"], 4)
        self.assertEqual(threads["follow_up_check"]["public_thread_views"], 287)
        self.assertEqual(threads["follow_up_check"]["visible_reply_count"], 2)
        self.assertEqual(threads["follow_up_check"]["known_owned_reply_count"], 1)
        self.assertEqual(threads["follow_up_check"]["unanswered_reply_count"], 0)
        self.assertEqual(threads["follow_up_check"]["response_action"], "none")

    def test_interaction_does_not_inflate_the_revenue_funnel(self):
        funnel = self.campaign["funnel"]

        self.assertEqual(funnel["state"], "helpful_interaction")
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["verified_received_gross_usd"], 0)


if __name__ == "__main__":
    unittest.main()
