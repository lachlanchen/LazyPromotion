import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

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

    def chat_observation(self, count, navigation=True):
        observed = self.observation(reddit=7)
        observed["platforms"]["reddit"].update(
            chat_navigation_available=navigation,
            chat_unread_badge_total=count,
        )
        return observed

    def test_chat_counter_is_independent_of_unchanged_notifications(self):
        _, previous = monitor.summarize_observation(self.chat_observation(0), None)
        status, state = monitor.summarize_observation(self.chat_observation(1), previous)
        self.assertTrue(status["review_required"])
        self.assertEqual(status["alerts"], [{
            "kind": "reddit_chat_unread_detected",
            "platform": "reddit",
            "unread_badge_total": 1,
        }])
        self.assertEqual(state["platforms"]["reddit"]["chat_unread_badge_total"], 1)
        self.assertFalse(status["policy"]["conversation_opened"])

    def test_first_chat_counter_requests_review_if_already_nonzero(self):
        status, _ = monitor.summarize_observation(self.chat_observation(2), None)
        self.assertTrue(status["review_required"])
        self.assertEqual(status["alerts"][0]["kind"], "reddit_chat_unread_detected")

    def test_unchanged_or_decreased_chat_counter_is_quiet(self):
        _, previous = monitor.summarize_observation(self.chat_observation(2), None)
        for count in (2, 1, 0):
            with self.subTest(count=count):
                status, _ = monitor.summarize_observation(self.chat_observation(count), previous)
                self.assertFalse(status["review_required"])

    def test_missing_chat_counter_preserves_last_count_and_requests_review(self):
        _, previous = monitor.summarize_observation(self.chat_observation(2), None)
        status, state = monitor.summarize_observation(self.chat_observation(None), previous)
        self.assertTrue(status["review_required"])
        self.assertTrue(status["platforms"]["reddit"]["layout_unknown"])
        self.assertIsNone(status["platforms"]["reddit"]["chat_unread_badge_total"])
        self.assertEqual(state["platforms"]["reddit"]["chat_unread_badge_total"], 2)

    def test_missing_chat_navigation_requests_review(self):
        status, _ = monitor.summarize_observation(self.chat_observation(0, False), None)
        self.assertTrue(status["review_required"])

    def test_invalid_chat_counter_is_rejected(self):
        for count in (True, -1, "2"):
            with self.subTest(count=count), self.assertRaises(ValueError):
                monitor.summarize_observation(self.chat_observation(count), None)

    def test_chat_badge_reads_only_its_counter_surface(self):
        page = Mock()
        badge = page.locator.return_value
        badge.count.return_value = 1
        badge.get_attribute.return_value = "0"
        with patch.object(monitor, "badge_numbers", side_effect=[[], [3]]):
            self.assertEqual(monitor.reddit_chat_badge_count(page), 3)
        page.locator.assert_called_once_with("#header-action-item-chat-button-badge")
        badge.locator.assert_called_once_with("span, [aria-label]")
        badge.get_attribute.assert_called_once_with("initial-count")

    def test_chat_badge_zero_is_distinct_from_unknown(self):
        page = Mock()
        badge = page.locator.return_value
        badge.count.return_value = 1
        with patch.object(monitor, "badge_numbers", return_value=[]):
            badge.get_attribute.return_value = "0"
            self.assertEqual(monitor.reddit_chat_badge_count(page), 0)
            badge.get_attribute.return_value = "unavailable"
            self.assertIsNone(monitor.reddit_chat_badge_count(page))
            badge.count.return_value = 0
            self.assertIsNone(monitor.reddit_chat_badge_count(page))

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
