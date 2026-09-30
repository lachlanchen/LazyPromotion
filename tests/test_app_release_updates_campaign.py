import hashlib
import json
from pathlib import Path
import unittest

import owned_monitor

ROOT = Path(__file__).resolve().parents[1]


class AppReleaseUpdateCampaignTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "campaigns" / f"{name}.json").read_text())

    def test_exact_copy_and_native_publication_boundary(self):
        for name in ("l-and-n-pair-playback-update", "bunko-mac-release"):
            with self.subTest(name=name):
                campaign = self.load(name)
                channel = campaign["channels"]["x"]
                content = channel["content"]
                self.assertEqual(hashlib.sha256(content.encode()).hexdigest(), channel["content_sha256"])
                self.assertEqual(channel["account"], "https://x.com/lazyingart")
                self.assertIn("I built", content)
                self.assertFalse(campaign["follow_up"]["postiz_managed"])
                for key in ("automatic_replies", "automatic_reposts", "unsolicited_private_messages"):
                    self.assertFalse(campaign["follow_up"][key])
                self.assertIsNone(campaign["funnel"]["verified_received_gross_usd"])
                self.assertIsNone(campaign["funnel"]["verified_new_users"])
                for unsupported in ("TestFlight", "airdrop", "earn LAC", "shared login", "guaranteed"):
                    self.assertNotIn(unsupported, content)
                route = owned_monitor.route_for_post("x", content, owned_monitor.route_index())
                self.assertEqual(route["campaign_id"], campaign["id"])
                for private in ("/home/", ".local/", "127.0.0.1", "integrationId", "postId"):
                    self.assertNotIn(private, json.dumps(campaign))

    def test_landn_published_with_both_store_links(self):
        campaign = self.load("l-and-n-pair-playback-update")
        channel = campaign["channels"]["x"]
        self.assertEqual(channel["state"], "published")
        self.assertEqual(channel["release_url"], "https://x.com/lazyingart/status/2104002096811147621")
        for platform in ("apple", "google"):
            self.assertIn(campaign["source_evidence"][platform], channel["content"])
        self.assertIn("free download + IAP", channel["content"])
        self.assertIn("US$0.99", channel["content"])
        self.assertTrue(channel["publication_verification"]["both_store_redirects_verified_http_200"])

    def test_bunko_native_publication_is_not_pending_app_release(self):
        campaign = self.load("bunko-mac-release")
        channel = campaign["channels"]["x"]
        self.assertEqual(channel["state"], "published_verified")
        self.assertEqual(channel["publish_at"], "2026-09-28T02:00:00Z")
        self.assertEqual(channel["release_url"], "https://x.com/lazyingart/status/2104390638531957108")
        self.assertTrue(channel["publication_verification"]["release_present"])
        self.assertTrue(channel["publication_verification"]["native_scheduled_list_verified_after_reload"])
        self.assertIn("AI study translations can make mistakes", channel["content"])
        self.assertNotIn("1.0.6", channel["content"])
        self.assertNotIn("Android", channel["content"])
        self.assertTrue(campaign["source_evidence"]["image_reviewed"])
        self.assertIn("Sanshirō", channel["media_alt"])


if __name__ == "__main__":
    unittest.main()
