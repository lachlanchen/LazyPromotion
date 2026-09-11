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
