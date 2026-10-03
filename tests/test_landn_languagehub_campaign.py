import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LandnLanguageHubCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads(
            (ROOT / "campaigns/l-and-n-languagehub-introduction.json").read_text()
        )
        self.post = self.campaign["channels"]["reddit"]

    def test_exact_approved_comment_and_destination(self):
        normalized = " ".join(self.post["content"].split())
        self.assertEqual(
            hashlib.sha256(normalized.encode()).hexdigest(),
            self.post["content_sha256"],
        )
        self.assertEqual(self.post["state"], "published")
        self.assertEqual(self.post["community"], "r/languagehub")
        self.assertIn("/1sic66r/", self.post["source_url"])
        self.assertTrue(self.post["release_url"].endswith("/comment/pdkuafk/"))

    def test_useful_practice_and_exact_store_destinations(self):
        text = self.post["content"]
        for phrase in (
            "Try separating listening from speaking",
            "I built L & N",
            "US$0.99",
            "free download, with in-app purchases",
        ):
            self.assertIn(phrase, text)
        for key in ("apple", "google"):
            self.assertIn(self.campaign["source_evidence"][key], text)
        self.assertEqual(text.count("https://"), 2)
        self.assertIn("\n\n", text)
        for forbidden in ("TestFlight", "Bunko", "guaranteed", "fully offline"):
            self.assertNotIn(forbidden, text)

    def test_publication_is_not_a_conversion_or_automated_followup(self):
        evidence = self.post["publication_verification"]
        for key in (
            "owner_approved_exact_comment",
            "single_submit_click",
            "guarded_approval_consumed",
            "exact_text_verified_after_reload",
            "logged_out_visibility_verified",
            "original_links_preserved",
        ):
            self.assertTrue(evidence[key])
        for key in (
            "postiz_managed",
            "automatic_replies",
            "automatic_reposts",
            "unsolicited_private_messages",
        ):
            self.assertFalse(self.campaign["follow_up"][key])
        for key in (
            "qualified_leads",
            "payments_confirmed",
            "verified_received_gross_usd",
        ):
            self.assertEqual(self.campaign["funnel"][key], 0)
        for private in ("/home/", ".local/", "approval_token", "127.0.0.1"):
            self.assertNotIn(private, json.dumps(self.campaign))


if __name__ == "__main__":
    unittest.main()
