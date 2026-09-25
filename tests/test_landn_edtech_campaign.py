import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LandnEdtechCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads((ROOT / "campaigns/l-and-n-edtech-introduction.json").read_text())
        self.post = self.campaign["channels"]["reddit"]

    def test_one_introduction_in_the_invited_monthly_thread(self):
        self.assertEqual(self.post["state"], "published")
        self.assertEqual(self.post["community"], "r/edtech")
        self.assertEqual(self.post["format"], "top_level_comment_in_monthly_developer_thread")
        self.assertIn("/1w42eqz/", self.post["source_url"])
        self.assertTrue(self.post["release_url"].endswith("/comment/pc0du25/"))
        self.assertEqual(hashlib.sha256(self.post["content"].encode()).hexdigest(), self.post["content_sha256"])

    def test_useful_exercise_and_original_store_links(self):
        text = self.post["content"]
        self.assertIn("light/night", text)
        self.assertIn("For tutors", text)
        self.assertIn("coaching feedback, not a classroom assessment", text)
        self.assertIn("US$0.99", text)
        self.assertIn("free download, with in-app purchases", text)
        for store in ("apple", "google"):
            self.assertIn(self.campaign["source_evidence"][store], text)
        self.assertEqual(text.count("https://"), 2)
        for forbidden in ("testflight", "internaltest", ".apk", "l-and-n.lazying.art", "guaranteed", "Bunko"):
            self.assertNotIn(forbidden, text)

    def test_visibility_uncertainty_and_no_automatic_contact(self):
        verification = self.post["publication_verification"]
        for key in ("visible_copy_and_destination_reviewed", "single_submit_click",
                    "exact_text_verified_after_reload", "author_verified", "original_links_preserved"):
            self.assertTrue(verification[key])
        self.assertFalse(verification["logged_out_visibility_verified"])
        self.assertIn("unresolved", verification["logged_out_check_state"])
        for key in ("postiz_managed", "direct_comment_monitor_configured", "automatic_replies",
                    "automatic_reposts", "unsolicited_private_messages"):
            self.assertFalse(self.campaign["follow_up"][key])
        for key in ("qualified_leads", "payments_confirmed", "verified_received_gross_usd"):
            self.assertEqual(self.campaign["funnel"][key], 0)
        for secret in ("/home/", ".local/", "127.0.0.1", "approval_token", "integrationId"):
            self.assertNotIn(secret, json.dumps(self.campaign))


if __name__ == "__main__":
    unittest.main()
