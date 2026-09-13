import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LandnInstagramPublicationTests(unittest.TestCase):
    """Keep the reviewed public release record distinct from queue and revenue."""

    def test_release_preserves_reviewed_copy_media_and_schedule(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "l-and-n-pronunciation-launch.json").read_text(
                encoding="utf-8"
            )
        )
        channel = campaign["channels"]["instagram"]
        publication = channel["publication"]
        self.assertEqual(channel["state"], "published")
        self.assertEqual(publication["provider_state"], "PUBLISHED")
        self.assertEqual(
            publication["url"], "https://www.instagram.com/reel/DdOg9nfDGhu/"
        )
        self.assertEqual(publication["public_account"], "lazying.art")
        self.assertEqual(channel["publish_at"], "2026-09-13T12:00:00Z")
        self.assertEqual(channel["content"], channel["postiz_content"])
        self.assertEqual(
            hashlib.sha256(channel["content"].encode()).hexdigest(),
            channel["content_sha256"],
        )
        self.assertIn(channel["destination"], channel["content"])
        self.assertEqual(
            channel["media_sha256"],
            campaign["source_evidence"]["media_quality_review"]["replacement"][
                "sha256"
            ],
        )
        self.assertNotEqual(
            channel["media_sha256"],
            campaign["source_evidence"]["media"]["sha256"],
        )
        self.assertEqual(channel["verification"]["verified_state"], "QUEUE")
        self.assertFalse(publication["organic_engagement_claimed"])
        self.assertEqual(publication["operator_review_sessions"], 1)
        self.assertNotIn("releaseId", publication)
        self.assertNotIn("integrationId", publication)


if __name__ == "__main__":
    unittest.main()
