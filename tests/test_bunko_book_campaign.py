import hashlib
import json
from pathlib import Path
import unittest

import owned_monitor

ROOT = Path(__file__).resolve().parents[1]


class BunkoBookCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads(
            (ROOT / "campaigns/bunko-book-reading-introduction.json").read_text()
        )
        self.post = self.campaign["channels"]["reddit"]

    def test_exact_copy_and_public_destinations(self):
        copy = self.post["content"]
        self.assertEqual(hashlib.sha256(copy.encode()).hexdigest(), self.post["content_sha256"])
        self.assertIn("Sanshirō", copy)
        self.assertIn("I built Bunko", copy)
        self.assertIn("https://lachlan.lazying.art/Bunko/", copy)
        self.assertIn("https://apps.apple.com/us/app/bunko-classics-with-ruby/id6815137919", copy)
        self.assertIn("US$0.99 once, no subscription", copy)
        self.assertEqual(copy.count("https://"), 2)

    def test_reader_venue_has_explicit_policy_and_live_settings_evidence(self):
        self.assertEqual(self.post["community"], "r/Recommend_A_Book")
        self.assertIn("regarding_self_promotion", self.campaign["source_evidence"]["pinned_promotion_policy"])
        self.assertEqual(self.post["settings"]["type"], "self")
        self.assertFalse(self.post["settings"]["flair_required"])
        verification = self.post["publication_verification"]
        for key in ("saved_preview_reviewed", "account_title_destination_time_reviewed",
                    "original_links_preserved", "provider_settings_checked", "no_flair_required_verified"):
            self.assertTrue(verification[key])

    def test_one_spaced_queue_is_not_publication_or_revenue(self):
        self.assertEqual(self.post["state"], "queued_verified")
        self.assertEqual(self.post["publish_at"], "2026-09-28T12:00:00Z")
        verification = self.post["publication_verification"]
        self.assertEqual(verification["verified_state"], "QUEUE")
        self.assertEqual(verification["schedule_actions"], 1)
        self.assertTrue(verification["single_matching_item"])
        self.assertFalse(verification["release_present"])
        self.assertNotIn("release_url", self.post)
        for key in ("verified_new_users", "verified_received_gross_usd"):
            self.assertIsNone(self.campaign["funnel"][key])

    def test_pending_releases_and_learning_claims_are_not_advertised(self):
        copy = self.post["content"]
        self.assertIn("not simplified readers", copy)
        self.assertIn("AI-generated study aids and can make mistakes", copy)
        for unsupported in ("Google Play", "Android", "macOS", "TestFlight", "183", "1.0.1"):
            self.assertNotIn(unsupported, copy)
        for key in ("automatic_replies", "automatic_reposts", "unsolicited_private_messages"):
            self.assertFalse(self.campaign["follow_up"][key])

    def test_monitor_matches_without_private_provider_ids(self):
        route = owned_monitor.route_for_post("reddit", self.post["content"], owned_monitor.route_index())
        self.assertEqual(route["campaign_id"], self.campaign["id"])
        self.assertEqual(route["known_owned_replies"], 0)
        raw = json.dumps(self.campaign)
        for marker in ("/home/", ".local/", "127.0.0.1", "integrationId", "postId", "cmuhex"):
            self.assertNotIn(marker, raw)


if __name__ == "__main__":
    unittest.main()
