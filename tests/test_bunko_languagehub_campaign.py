import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BunkoLanguageHubCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads((ROOT / "campaigns/bunko-languagehub-introduction.json").read_text())
        self.post = self.campaign["channels"]["reddit"]

    def test_exact_copy_in_invited_thread(self):
        self.assertEqual(hashlib.sha256(self.post["content"].encode()).hexdigest(), self.post["content_sha256"])
        self.assertEqual(self.post["community"], "r/languagehub")
        self.assertEqual(self.post["format"], "top_level_comment_in_pinned_tools_thread")
        self.assertIn("/1sic66r/", self.post["source_url"])
        self.assertTrue(self.post["release_url"].endswith("/comment/pc0legb/"))
        self.assertEqual(self.post["state"], "published")

    def test_reader_fit_price_and_only_verified_destinations(self):
        text = self.post["content"]
        for phrase in ("I built Bunko", "Sanshirō", "unadapted classics", "AI-generated study aids", "US$0.99 once"):
            self.assertIn(phrase, text)
        for key in ("reader", "apple"):
            self.assertIn(self.campaign["source_evidence"][key], text)
        self.assertEqual(text.count("https://"), 2)
        for forbidden in ("play.google.com", "TestFlight", "1.0.1", "L & N", "guaranteed"):
            self.assertNotIn(forbidden, text)

    def test_no_inferred_visibility_conversion_or_automatic_contact(self):
        evidence = self.post["publication_verification"]
        self.assertTrue(evidence["exact_text_verified_after_reload"])
        self.assertTrue(evidence["single_submit_click"])
        self.assertFalse(evidence["logged_out_visibility_verified"])
        for key in ("postiz_managed", "direct_comment_monitor_configured", "automatic_replies", "automatic_reposts", "unsolicited_private_messages"):
            self.assertFalse(self.campaign["follow_up"][key])
        for key in ("qualified_leads", "payments_confirmed", "verified_received_gross_usd"):
            self.assertEqual(self.campaign["funnel"][key], 0)
        for private in ("/home/", ".local/", "approval_token", "127.0.0.1", "integrationId"):
            self.assertNotIn(private, json.dumps(self.campaign))


if __name__ == "__main__":
    unittest.main()
