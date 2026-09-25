import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BunkoJapaneseCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads((ROOT / "campaigns/bunko-japanese-reader-introduction.json").read_text())
        self.post = self.campaign["channels"]["reddit"]

    def test_hash_destination_and_linkless_copy(self):
        self.assertEqual(hashlib.sha256(self.post["content"].encode()).hexdigest(), self.post["content_sha256"])
        self.assertEqual(self.post["community"], "r/Japaneselanguage")
        self.assertIn("/1sky7tt/", self.post["source_url"])
        self.assertTrue(self.post["release_url"].endswith("/comment/pc03ka1/"))
        for link in ("http://", "https://", "www."):
            self.assertNotIn(link, self.post["content"])
        self.assertIn("Bunko: Classics with Ruby", self.post["content"])
        self.assertIn("LazyingArt LLC", self.post["content"])
        self.assertIn("US$0.99", self.post["content"])
        self.assertIn("AI-generated", self.post["content"])

    def test_signed_in_evidence_does_not_become_public_or_customer_evidence(self):
        verification = self.post["publication_verification"]
        self.assertTrue(verification["single_submit_click"])
        self.assertTrue(verification["exact_text_verified_after_reload"])
        self.assertFalse(verification["logged_out_visibility_verified"])
        self.assertEqual(self.campaign["funnel"]["qualified_leads"], 0)
        self.assertEqual(self.campaign["funnel"]["verified_received_gross_usd"], 0)
        for key in ("postiz_managed", "automatic_replies", "automatic_reposts", "unsolicited_private_messages"):
            self.assertFalse(self.campaign["follow_up"][key])
        for private in ("/home/", ".local/", "127.0.0.1", "approval_token", "integrationId"):
            self.assertNotIn(private, json.dumps(self.campaign))


if __name__ == "__main__":
    unittest.main()
