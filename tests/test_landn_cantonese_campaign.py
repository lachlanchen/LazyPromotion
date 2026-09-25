import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LandnCantoneseCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads(
            (ROOT / "campaigns/l-and-n-cantonese-introduction.json").read_text()
        )
        self.post = self.campaign["channels"]["reddit"]

    def test_one_verified_introduction_in_invited_thread(self):
        self.assertEqual(self.post["state"], "published")
        self.assertEqual(self.post["community"], "r/Cantonese")
        self.assertEqual(self.post["format"], "top_level_comment_in_creator_ads_thread")
        self.assertIn("/1wo97ez/", self.post["source_url"])
        self.assertTrue(self.post["release_url"].endswith("/comment/pbytqan/"))
        self.assertEqual(
            hashlib.sha256(self.post["content"].encode()).hexdigest(),
            self.post["content_sha256"],
        )
        verification = self.post["publication_verification"]
        for key in (
            "visible_copy_and_destination_reviewed", "single_submit_click",
            "exact_text_verified_after_reload", "logged_out_visibility_verified",
            "original_links_preserved",
        ):
            self.assertTrue(verification[key])

    def test_concrete_exercise_and_honest_store_destinations(self):
        text = self.post["content"]
        evidence = self.campaign["source_evidence"]
        self.assertIn(evidence["curriculum_pair"], text)
        self.assertIn("If you want to practise", text)
        self.assertIn(evidence["apple"], text)
        self.assertIn(evidence["google"], text)
        self.assertIn("US$0.99", text)
        self.assertIn("free download, with in-app purchases", text)
        self.assertEqual(text.count("https://"), 2)
        for unsupported in (
            "testflight", "internaltest", ".apk", "l-and-n.lazying.art",
            "lazy sounds", "perfect score", "all offline",
        ):
            self.assertNotIn(unsupported, text.lower())

    def test_no_automation_or_invented_outcome(self):
        follow_up = self.campaign["follow_up"]
        self.assertEqual(follow_up["mode"], "manual_review")
        for key in (
            "postiz_managed", "direct_comment_monitor_configured",
            "automatic_replies", "automatic_reposts", "unsolicited_private_messages",
        ):
            self.assertFalse(follow_up[key])
        for key in ("qualified_leads", "payments_confirmed", "verified_received_gross_usd"):
            self.assertEqual(self.campaign["funnel"][key], 0)
        for private in ("/home/", ".local/", "127.0.0.1", "integrationId", "approval_token"):
            self.assertNotIn(private, json.dumps(self.campaign))


if __name__ == "__main__":
    unittest.main()
