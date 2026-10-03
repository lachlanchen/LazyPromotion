import hashlib
import json
from pathlib import Path
import unittest

import owned_monitor


ROOT = Path(__file__).resolve().parents[1]


class BunkoAndroidShowcaseTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads(
            (ROOT / "campaigns/bunko-android-showcase.json").read_text()
        )
        self.post = self.campaign["channels"]["reddit"]

    def test_exact_published_copy_and_owned_route(self):
        self.assertEqual(
            hashlib.sha256(self.post["content"].encode()).hexdigest(),
            self.post["content_sha256"],
        )
        self.assertEqual(self.post["state"], "published")
        self.assertEqual(self.post["community"], "r/droidappshowcase")
        self.assertLessEqual(len(self.post["title"]), 50)
        self.assertEqual(self.post["flair"], "Showcase")
        self.assertIn("/1wwzfbj/", self.post["release_url"])
        route = owned_monitor.route_for_post(
            "reddit", self.post["content"], owned_monitor.route_index()
        )
        self.assertEqual(route["campaign_id"], self.campaign["id"])
        self.assertEqual(route["known_owned_replies"], 0)

    def test_android_only_price_affiliation_and_actual_limits(self):
        text = self.post["content"]
        for phrase in (
            "I built Bunko", "Daodejing", "modern Mandarin pinyin",
            "unadapted classics", "AI-assisted", "US$0.99 once for the app",
        ):
            self.assertIn(phrase, text)
        self.assertIn(self.campaign["source_evidence"]["google"], text)
        self.assertEqual(text.count("https://"), 1)
        for forbidden in (
            "apps.apple.com", "TestFlight", "Apple Watch", "PWA",
            "guaranteed", "unlimited", "ancient pronunciation",
        ):
            self.assertNotIn(forbidden, text)

    def test_publication_bots_are_not_revenue_or_permission_to_spam(self):
        evidence = self.post["publication_verification"]
        for key in (
            "single_submit_click", "exact_title_author_text_verified_after_reload",
            "original_link_preserved", "logged_out_visibility_verified",
        ):
            self.assertTrue(evidence[key])
        self.assertFalse(evidence["automated_comments_are_reader_engagement"])
        self.assertEqual(evidence["human_reader_replies_at_verification"], 0)
        for key in (
            "postiz_managed", "direct_comment_monitor_configured",
            "automatic_replies", "automatic_reposts", "unsolicited_private_messages",
        ):
            self.assertFalse(self.campaign["follow_up"][key])
        for key in (
            "qualified_leads", "payments_confirmed", "verified_received_gross_usd",
        ):
            self.assertEqual(self.campaign["funnel"][key], 0)
        for private in (
            "/home/", ".local/", "127.0.0.1", "client_secret", "integrationId",
        ):
            self.assertNotIn(private, json.dumps(self.campaign))


if __name__ == "__main__":
    unittest.main()
