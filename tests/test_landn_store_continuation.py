import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LandnStoreContinuationTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads(
            (ROOT / "campaigns/l-and-n-pronunciation-launch.json").read_text(
                encoding="utf-8"
            )
        )
        self.continuation = self.campaign["source_evidence"][
            "owned_store_continuation"
        ]

    def test_existing_store_path_does_not_reprice_or_change_native_releases(self):
        path = self.continuation
        self.assertEqual(path["state"], "live")
        self.assertTrue(path["web_only"])
        self.assertTrue(path["browser_practice_remains_free"])
        self.assertEqual(path["locales"], ["en", "zh-Hans", "zh-Hant", "yue"])
        self.assertEqual(
            path["destinations"],
            [
                "https://apps.apple.com/us/app/l-n-speech-practice/id6808872450",
                "https://play.google.com/store/apps/details?id=art.lazying.landn",
            ],
        )
        self.assertFalse(path["verification"]["native_releases_changed"])
        self.assertFalse(path["verification"]["prices_changed"])
        self.assertIn("not evidence", path["policy"])
        self.assertIn("revenue", path["policy"])

    def test_release_has_revision_pinned_evidence_without_private_runtime_data(self):
        path = self.continuation
        for field in ("source_commit", "evidence_commit"):
            self.assertRegex(path[field], r"^[0-9a-f]{40}$")
        self.assertRegex(path["entry_asset_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            path["evidence_path"], "store/artifacts/pwa-store-links-release.json"
        )
        serialized = json.dumps(path)
        for private_marker in ("/home/", ".runtime/", "127.0.0.1", "integrationId"):
            self.assertNotIn(private_marker, serialized)

    def test_store_continuation_preserves_reviewed_linkedin_copy_and_media(self):
        channel = self.campaign["channels"]["linkedin"]
        self.assertEqual(channel["destination"], self.continuation["url"])
        self.assertEqual(
            hashlib.sha256(channel["content"].encode()).hexdigest(),
            channel["content_sha256"],
        )
        self.assertEqual(
            channel["media_sha256"],
            self.campaign["source_evidence"]["media_quality_review"]["replacement"][
                "sha256"
            ],
        )
        self.assertIn("free and open source", channel["content"])
        self.assertNotIn("App Store", channel["content"])
        self.assertFalse(channel["provider_recheck"]["new_post_created"])

    def test_published_linkedin_demo_reaches_current_app_without_counting_review_as_demand(self):
        channel = self.campaign["channels"]["linkedin"]
        publication = channel["publication"]
        self.assertEqual(channel["state"], "published")
        self.assertEqual(publication["provider_state"], "PUBLISHED")
        self.assertEqual(
            publication["url"],
            "https://www.linkedin.com/feed/update/urn:li:ugcPost:7507260594853482496",
        )
        self.assertTrue(publication["visible_copy_matches_except_platform_shortening"])
        self.assertTrue(publication["external_link_confirmation_observed"])
        self.assertEqual(
            publication["destination_after_visible_confirmation"],
            self.continuation["url"],
        )
        self.assertTrue(publication["destination_app_root_verified"])
        self.assertEqual(
            publication["destination_entry_asset"], self.continuation["entry_asset"]
        )
        self.assertTrue(publication["playable_video_observed"])
        self.assertEqual(len(publication["visually_reviewed_frame_times_seconds"]), 5)
        self.assertEqual(publication["operator_playback_sessions"], 1)
        self.assertFalse(publication["organic_engagement_claimed"])
        self.assertFalse(channel["schedule_verification"]["release_present"])
        self.assertEqual(channel["schedule_verification"]["verified_state"], "QUEUE")
        self.assertEqual(self.campaign["funnel"]["qualified_leads"], 0)
        self.assertEqual(self.campaign["funnel"]["verified_received_gross_usd"], 0)
        self.assertNotIn("integrationId", publication)
        self.assertNotIn("releaseId", publication)


if __name__ == "__main__":
    unittest.main()
