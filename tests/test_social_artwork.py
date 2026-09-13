"""Protect offer wording and frozen evidence when preparing social artwork."""

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SocialArtworkTests(unittest.TestCase):
    def test_story_card_is_self_contained_and_matches_the_scoped_offer(self):
        campaign = json.loads((ROOT / "campaigns/content-repurposing-pilot.json").read_text())
        channel = campaign["owned_offer"]["postiz_instagram"]
        source = (ROOT / channel["media_source"]).read_text()
        data = (ROOT / channel["media_asset"]).read_bytes()
        self.assertEqual(data[:3], b"\xff\xd8\xff")
        self.assertEqual(len(data), 140262)
        self.assertEqual(hashlib.sha256(data).hexdigest(), channel["media_sha256"])
        for text in (
            "width: 1080px; height: 1350px", "Find the story.",
            "Then cut the clip.", "$250", "One rights-cleared recording",
            "Up to 30 minutes", "Editable SRT", "Source notes", "lazying.art/story-clip",
        ):
            self.assertIn(text, source)
        for text in ("<script", "<img", "https://", "@import", "url("):
            self.assertNotIn(text, source)
        self.assertNotIn("post_id", channel)
        self.assertNotEqual(channel["media_asset"], campaign["owned_offer"]["contra_marketplace"]["cover_asset"])
        self.assertTrue(channel["visual_review"]["previous_media_preserved"])
        self.assertTrue(channel["visual_review"]["copy_date_account_and_settings_unchanged"])

    def test_openhi_preview_review_preserves_exact_scientific_artifact(self):
        campaign = json.loads((ROOT / "campaigns/openhi-reproducibility-sprint.json").read_text())
        review = campaign["channels"]["instagram"]["visual_review"]
        data = (ROOT / review["source_asset"]).read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(int.from_bytes(data[16:20], "big"), 1280)
        self.assertEqual(int.from_bytes(data[20:24], "big"), 701)
        self.assertEqual(hashlib.sha256(data).hexdigest(), review["source_sha256"])
        self.assertTrue(review["media_retained"])
        self.assertTrue(review["uploaded_source_hash_matches"])
        self.assertIn("preview", review["observed_issue"])
        self.assertIn("remain unverified until publication", review["boundary"])
        self.assertFalse(review["new_item_created"])


if __name__ == "__main__":
    unittest.main()
