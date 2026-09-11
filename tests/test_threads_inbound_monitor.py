import json
import tempfile
import unittest
from pathlib import Path

import threads_inbound_monitor


class ThreadsInboundMonitorTests(unittest.TestCase):
    def test_fingerprints_keep_reply_rows_private_and_distinct(self):
        paths = [
            "https://www.threads.com/@person/post/ABC123?x=1",
            "https://www.threads.com/@person/post/ABC123",
            "https://www.threads.com/@lazying.art",
            "https://example.com/@person/post/ABC123",
        ]
        fingerprints = threads_inbound_monitor.reply_fingerprints(paths)
        self.assertEqual(len(fingerprints), 2)
        self.assertEqual(len(set(fingerprints)), 2)
        self.assertNotIn("person", json.dumps(fingerprints))

    def test_first_observation_creates_quiet_baseline(self):
        status, state = threads_inbound_monitor.summarize_observation(
            current_fingerprints=["one"],
            previous_fingerprints=None,
            empty_message_visible=False,
            authenticated=True,
            checked_at="2026-09-12T00:00:00Z",
        )
        self.assertTrue(status["baseline_created"])
        self.assertFalse(status["review_required"])
        self.assertEqual(state["fingerprints"], ["one"])
        self.assertEqual(state["profile_fingerprints"], [])
        self.assertFalse(status["content_opened"])
        self.assertFalse(status["automatic_reply"])

    def test_new_reply_requires_review_without_automatic_reply(self):
        status, _ = threads_inbound_monitor.summarize_observation(
            current_fingerprints=["old", "new"],
            previous_fingerprints=["old"],
            empty_message_visible=False,
            authenticated=True,
            checked_at="2026-09-12T00:15:00Z",
        )
        self.assertTrue(status["review_required"])
        self.assertEqual(status["new_reply_item_count"], 1)
        self.assertFalse(status["content_opened"])
        self.assertFalse(status["automatic_reply"])

    def test_unknown_layout_fails_toward_visible_review(self):
        status, _ = threads_inbound_monitor.summarize_observation(
            current_fingerprints=[],
            previous_fingerprints=[],
            empty_message_visible=False,
            authenticated=True,
            checked_at="2026-09-12T00:15:00Z",
        )
        self.assertTrue(status["layout_unknown"])
        self.assertTrue(status["review_required"])

    def test_profile_reply_count_is_a_quiet_fallback_baseline(self):
        status, state = threads_inbound_monitor.summarize_observation(
            current_fingerprints=[],
            previous_fingerprints=[],
            current_profile_fingerprints=["owned-one", "owned-two"],
            previous_profile_fingerprints=None,
            profile_available=True,
            empty_message_visible=True,
            authenticated=True,
            checked_at="2026-09-12T00:15:00Z",
        )
        self.assertFalse(status["review_required"])
        self.assertTrue(status["profile_baseline_created"])
        self.assertEqual(status["profile_reply_item_count"], 2)
        self.assertEqual(state["profile_fingerprints"], ["owned-one", "owned-two"])

    def test_new_profile_reply_requires_review_when_activity_filter_is_empty(self):
        status, _ = threads_inbound_monitor.summarize_observation(
            current_fingerprints=[],
            previous_fingerprints=[],
            current_profile_fingerprints=["owned-one", "owned-two", "owned-three"],
            previous_profile_fingerprints=["owned-one", "owned-two"],
            profile_available=True,
            empty_message_visible=True,
            authenticated=True,
            checked_at="2026-09-12T00:30:00Z",
        )
        self.assertTrue(status["review_required"])
        self.assertEqual(status["new_reply_item_count"], 1)
        self.assertFalse(status["automatic_reply"])

    def test_status_summary_never_returns_private_fingerprints(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "status.json"
            path.write_text(
                json.dumps(
                    {
                        "checked_at": "2026-09-12T00:15:00Z",
                        "available": True,
                        "reply_item_count": 2,
                        "review_required": True,
                        "fingerprints": ["private"],
                    }
                ),
                encoding="utf-8",
            )
            summary = threads_inbound_monitor.status_summary(path)
            self.assertTrue(summary["review_required"])
            self.assertNotIn("fingerprints", summary)
            self.assertNotIn("private", json.dumps(summary))


if __name__ == "__main__":
    unittest.main()
