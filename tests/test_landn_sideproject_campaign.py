import hashlib
import json
from pathlib import Path
import unittest

import owned_monitor


ROOT = Path(__file__).resolve().parents[1]


class LandnSideprojectCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads(
            (ROOT / "campaigns/l-and-n-sideproject-introduction.json").read_text()
        )
        self.post = self.campaign["channels"]["reddit"]

    def test_one_verified_creator_introduction(self):
        self.assertEqual(set(self.campaign["channels"]), {"reddit"})
        self.assertEqual(self.post["state"], "published")
        self.assertEqual(self.post["community"], "r/SideProject")
        self.assertTrue(self.post["title"].startswith("L & N - "))
        self.assertEqual(hashlib.sha256(self.post["content"].encode()).hexdigest(), self.post["content_sha256"])
        verification = self.post["publication_verification"]
        self.assertEqual(verification["verified_state"], "PUBLISHED")
        self.assertTrue(verification["live_page_reviewed"])
        self.assertTrue(verification["logged_out_visibility_verified"])
        self.assertTrue(verification["original_links_preserved"])
        self.assertEqual(verification["expected_links_verified"], 4)

    def test_store_first_copy_uses_correct_english_demo(self):
        evidence = self.campaign["source_evidence"]
        for name in ("apple", "google", "repository", "english_walkthrough"):
            self.assertIn(evidence[name], self.post["content"])
        self.assertEqual(evidence["english_walkthrough"], "https://www.youtube.com/shorts/Nlsx_5U6g6U")
        self.assertIn("US$0.99", self.post["content"])
        self.assertIn("free download, with in-app purchases", self.post["content"])
        for unsupported in ("testflight", "internaltest", ".apk", "jirylmFo5U8", "l-and-n.lazying.art"):
            self.assertNotIn(unsupported.lower(), self.post["content"].lower())

    def test_monitor_route_and_no_invented_revenue(self):
        route = owned_monitor.route_for_post("reddit", self.post["content"], owned_monitor.route_index())
        self.assertEqual(route["campaign_id"], self.campaign["id"])
        self.assertEqual(route["known_owned_replies"], 0)
        for key in ("qualified_leads", "payments_confirmed", "verified_received_gross_usd"):
            self.assertEqual(self.campaign["funnel"][key], 0)
        for key in ("automatic_replies", "automatic_reposts", "unsolicited_private_messages"):
            self.assertFalse(self.campaign["follow_up"][key])

    def test_public_media_library_retains_review_boundaries(self):
        library = (ROOT / "docs/product-video-library.md").read_text()
        for video in ("Nlsx_5U6g6U", "pSWnOwzyc-4", "5sfJwp-sgrQ"):
            self.assertIn(video, library)
        self.assertIn("TestFlight-installed", library)
        self.assertIn("not** yet been reviewed", library)
        self.assertIn("No LazyEdit or AutoPublish social post was published", library)
        for private in ("/home/", ".local/", "127.0.0.1", "integrationId"):
            self.assertNotIn(private, library + json.dumps(self.campaign))


if __name__ == "__main__":
    unittest.main()
