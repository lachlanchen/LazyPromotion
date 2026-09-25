import hashlib
import json
from pathlib import Path
import struct
import unittest

import owned_monitor


ROOT = Path(__file__).resolve().parents[1]


class BunkoInstagramCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads(
            (ROOT / "campaigns/bunko-instagram-reading-demo.json").read_text()
        )
        self.channel = self.campaign["channels"]["instagram"]

    def test_reviewed_copy_and_exact_destination(self):
        content = self.channel["content"]
        self.assertEqual(hashlib.sha256(content.encode()).hexdigest(), self.channel["content_sha256"])
        self.assertLessEqual(len(content), 2200)
        self.assertTrue(content.startswith("Try one paragraph"))
        self.assertIn("I built Bunko", content)
        self.assertIn("browser reader", content)
        self.assertIn("Bunko: Classics with Ruby", content)
        self.assertIn("US$0.99 once, no subscription", content)
        self.assertTrue(self.channel["destination"].endswith("id6815137919"))
        self.assertNotIn("link in bio", content.lower())

    def test_actual_reader_asset_has_reviewed_hash_and_portrait_ratio(self):
        source = self.campaign["source_evidence"]
        image = (ROOT / source["image"]).read_bytes()
        self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", image[16:24]), (720, 900))
        self.assertEqual(hashlib.sha256(image).hexdigest(), source["image_sha256"])
        self.assertTrue(source["image_reviewed"])
        self.assertIn("Not an iOS binary capture", source["image_kind"])

    def test_queue_does_not_claim_publication_or_attribution(self):
        self.assertEqual(set(self.campaign["channels"]), {"instagram"})
        self.assertEqual(self.channel["state"], "queued_verified")
        self.assertEqual(self.channel["publish_at"], "2026-09-26T12:00:00Z")
        self.assertEqual(self.channel["settings"], {"post_type": "post"})
        verification = self.channel["publication_verification"]
        self.assertEqual(verification["verified_state"], "QUEUE")
        self.assertEqual(verification["schedule_actions"], 1)
        self.assertTrue(verification["single_matching_item"])
        self.assertFalse(verification["release_present"])
        self.assertNotIn("release_url", self.channel)
        self.assertIsNone(self.campaign["funnel"]["verified_new_users"])
        self.assertIsNone(self.campaign["funnel"]["verified_received_gross_usd"])

    def test_monitor_recognizes_the_reviewed_caption(self):
        route = owned_monitor.route_for_post(
            "instagram-standalone", self.channel["content"], owned_monitor.route_index(),
        )
        self.assertEqual(route["campaign_id"], self.campaign["id"])
        self.assertEqual(route["route"], "product")

    def test_no_pending_feature_or_unapproved_store_claims(self):
        content = self.channel["content"]
        self.assertIn("AI-generated and can make mistakes", content)
        self.assertIn("not beginner lessons", content)
        for unsupported in ("Google Play", "Android", "macOS", "1.0.1", "AI tutor", "183"):
            self.assertNotIn(unsupported, content)
        for key in ("automatic_replies", "automatic_reposts", "unsolicited_private_messages"):
            self.assertFalse(self.campaign["follow_up"][key])

    def test_public_record_excludes_private_runtime_and_provider_identifiers(self):
        raw = json.dumps(self.campaign)
        for marker in ("/home/", ".local/", "127.0.0.1", "integrationId", "postId", "releaseId"):
            self.assertNotIn(marker, raw)


if __name__ == "__main__":
    unittest.main()
