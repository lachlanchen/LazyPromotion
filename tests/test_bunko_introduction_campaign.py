import hashlib
import json
from pathlib import Path
import unittest

import owned_monitor


ROOT = Path(__file__).resolve().parents[1]


class BunkoIntroductionCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads(
            (ROOT / "campaigns/bunko-classics-introduction.json").read_text()
        )

    def test_two_verified_publications_preserve_exact_copy(self):
        channels = self.campaign["channels"]
        self.assertEqual(set(channels), {"reddit", "x"})
        for channel in channels.values():
            self.assertEqual(channel["state"], "published")
            self.assertEqual(
                hashlib.sha256(channel["content"].encode()).hexdigest(),
                channel["content_sha256"],
            )
            verification = channel["publication_verification"]
            self.assertEqual(verification["verified_state"], "PUBLISHED")
            self.assertTrue(verification["live_page_reviewed"])
            self.assertTrue(verification["stored_copy_matches_reviewed_text"])
            self.assertTrue(channel["content"].startswith("I built Bunko"))
            self.assertIn("$0.99", channel["content"])
        self.assertIn("/r/SideProject/", channels["reddit"]["release_url"])
        self.assertIn("/lazyingart/status/", channels["x"]["release_url"])

    def test_real_reader_image_and_price_are_pinned(self):
        evidence = self.campaign["source_evidence"]
        self.assertIn(evidence["source_commit"], evidence["image"])
        self.assertEqual(len(evidence["image_sha256"]), 64)
        self.assertIn("not a customer result", evidence["image_kind"])
        self.assertEqual(evidence["apple_version_verified"], "1.0.0")
        self.assertEqual(evidence["apple_price_usd_verified"], 0.99)
        x = self.campaign["channels"]["x"]
        self.assertLessEqual(len(x["content"]), 280)
        self.assertTrue(x["publication_verification"]["live_image_loaded"])
        self.assertIn(x["destination"].removeprefix("https://"), x["content"])
        self.assertFalse(x["settings"]["paid_partnership"])
        self.assertTrue(x["settings"]["made_with_ai"])

    def test_owned_monitor_matches_both_posts(self):
        routes = owned_monitor.route_index()
        for provider, channel in self.campaign["channels"].items():
            route = owned_monitor.route_for_post(provider, channel["content"], routes)
            self.assertEqual(route["campaign_id"], self.campaign["id"])
            self.assertEqual(route["route"], "product")
            self.assertEqual(route["known_owned_replies"], 0)

    def test_no_unapproved_release_claim_or_automatic_followup(self):
        for channel in self.campaign["channels"].values():
            self.assertNotIn("play.google.com", channel["content"])
            self.assertNotIn("1.0.1", channel["content"])
            self.assertIn("can make mistakes", channel["content"])
        follow_up = self.campaign["follow_up"]
        for key in ("automatic_replies", "automatic_reposts", "unsolicited_private_messages"):
            self.assertFalse(follow_up[key])
        for key in ("qualified_leads", "payments_confirmed", "verified_received_gross_usd"):
            self.assertEqual(self.campaign["funnel"][key], 0)

    def test_public_record_has_no_private_runtime_or_provider_identifiers(self):
        raw = json.dumps(self.campaign)
        for marker in ("/home/", ".local/", "127.0.0.1", "integrationId", "releaseId"):
            self.assertNotIn(marker, raw)


if __name__ == "__main__":
    unittest.main()
