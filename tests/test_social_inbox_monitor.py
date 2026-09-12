import json
import tempfile
import unittest
from pathlib import Path

import social_inbox_monitor as monitor


class SocialInboxMonitorTests(unittest.TestCase):
    def config(self):
        return {
            "version": 1,
            "campaigns": [
                {
                    "campaign_id": "instagram-campaign",
                    "platform": "instagram",
                    "participant": "known.handle",
                },
                {
                    "campaign_id": "reddit-campaign",
                    "platform": "reddit",
                    "source_url": "https://www.reddit.com/r/forhire/comments/abc123/example/",
                },
            ],
        }

    def observation(self, instagram=1, reddit=0, instagram_match=False, reddit_match=False):
        return {
            "checked_at": "2026-09-13T00:00:00Z",
            "platforms": {
                "instagram": {
                    "authenticated": True,
                    "navigation_available": True,
                    "unread_badge_total": instagram,
                },
                "reddit": {
                    "authenticated": True,
                    "navigation_available": True,
                    "unread_badge_total": reddit,
                },
            },
            "campaigns": [
                {
                    "campaign_id": "instagram-campaign",
                    "platform": "instagram",
                    "known_participant_present": instagram_match,
                },
                {
                    "campaign_id": "reddit-campaign",
                    "platform": "reddit",
                    "known_participant_present": reddit_match,
                },
            ],
        }

    def test_private_config_is_strict_and_normalized(self):
        config = monitor.validate_config(self.config())
        self.assertEqual(len(config["campaigns"]), 2)
        self.assertEqual(config["campaigns"][0]["participant"], "known.handle")

    def test_config_rejects_non_reddit_source_and_duplicate_id(self):
        invalid = self.config()
        invalid["campaigns"][1]["source_url"] = "https://example.com/post"
        with self.assertRaises(ValueError):
            monitor.validate_config(invalid)
        duplicate = self.config()
        duplicate["campaigns"][1]["campaign_id"] = "instagram-campaign"
        with self.assertRaises(ValueError):
            monitor.validate_config(duplicate)

    def test_first_observation_is_a_quiet_baseline(self):
        status, state = monitor.summarize_observation(self.observation(), None)
        self.assertTrue(status["baseline_created"])
        self.assertFalse(status["review_required"])
        self.assertEqual(status["alerts"], [])
        self.assertEqual(state["platforms"]["instagram"]["unread_badge_total"], 1)

    def test_unread_increase_requires_review_without_opening_content(self):
        _, previous = monitor.summarize_observation(self.observation(), None)
        status, _ = monitor.summarize_observation(
            self.observation(instagram=2), previous
        )
        self.assertTrue(status["review_required"])
        self.assertEqual(status["alerts"][0]["unread_delta"], 1)
        self.assertFalse(status["policy"]["conversation_opened"])
        self.assertFalse(status["policy"]["message_body_or_preview_collected"])
        self.assertTrue(status["policy"]["activity_is_not_a_lead_or_revenue"])

    def test_known_participant_appearance_requires_exact_review(self):
        _, previous = monitor.summarize_observation(self.observation(), None)
        status, _ = monitor.summarize_observation(
            self.observation(instagram_match=True), previous
        )
        self.assertTrue(status["review_required"])
        self.assertEqual(
            status["alerts"][0]["kind"], "known_campaign_participant_appeared"
        )

    def test_status_and_state_do_not_persist_participant_terms(self):
        status, state = monitor.summarize_observation(self.observation(), None)
        serialized = json.dumps({"status": status, "state": state})
        self.assertNotIn("known.handle", serialized)
        self.assertNotIn("forhire", serialized)
        self.assertNotIn("message", serialized.replace("message_body_or_preview_collected", ""))

    def test_layout_uncertainty_fails_toward_review(self):
        observed = self.observation()
        observed["platforms"]["reddit"]["navigation_available"] = False
        status, _ = monitor.summarize_observation(observed, None)
        self.assertTrue(status["platforms"]["reddit"]["layout_unknown"])
        self.assertTrue(status["review_required"])

    def test_status_summary_exposes_only_privacy_limited_fields(self):
        status, _ = monitor.summarize_observation(self.observation(), None)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "status.json"
            path.write_text(json.dumps(status), encoding="utf-8")
            summary = monitor.status_summary(path)
        self.assertTrue(summary["available"])
        self.assertEqual(summary["alert_count"], 0)
        self.assertNotIn("known.handle", json.dumps(summary))
        self.assertFalse(summary["policy"]["participant_persisted"])


if __name__ == "__main__":
    unittest.main()
