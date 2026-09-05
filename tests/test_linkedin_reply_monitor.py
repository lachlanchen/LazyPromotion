import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import linkedin_reply_monitor


class LinkedInReplyMonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "linkedin.sqlite3"
        self.status = self.root / "status.json"

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, count, at):
        return linkedin_reply_monitor.record_observation(
            count,
            public_label="Reviewed company outreach",
            db_path=self.db,
            status_path=self.status,
            observed_at=at,
        )

    def test_private_config_exposes_only_safe_public_label(self):
        config = self.root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "thread_url": "https://www.linkedin.com/messaging/thread/private-id/",
                    "public_label": "Reviewed company outreach",
                    "minimum_event_count": 1,
                }
            ),
            encoding="utf-8",
        )
        loaded = linkedin_reply_monitor.load_config(config)
        self.assertEqual(loaded["public_label"], "Reviewed company outreach")
        self.assertEqual(loaded["minimum_event_count"], 1)

    def test_target_match_is_exact_to_private_thread_path(self):
        targets = [
            {
                "type": "page",
                "url": "https://www.linkedin.com/messaging/thread/other/",
                "webSocketDebuggerUrl": "ws://other",
            },
            {
                "type": "page",
                "url": "https://www.linkedin.com/messaging/thread/private-id/",
                "webSocketDebuggerUrl": "ws://expected",
            },
        ]
        selected = linkedin_reply_monitor.linkedin_thread_target(
            targets,
            "https://www.linkedin.com/messaging/thread/private-id/",
        )
        self.assertEqual(selected["webSocketDebuggerUrl"], "ws://expected")

    def test_count_expression_does_not_read_message_or_sender_text(self):
        expression = linkedin_reply_monitor.event_count_expression()
        self.assertIn("msg-s-message-list__event", expression)
        self.assertNotIn("innerText", expression)
        self.assertNotIn("textContent", expression)
        self.assertNotIn("msg-s-message-group__name", expression)

    def test_reads_count_without_focus_navigation_or_input(self):
        class FakeConnection:
            def __init__(self):
                self.calls = []

            def command(self, method, params=None):
                self.calls.append((method, params or {}))
                if method == "Page.getFrameTree":
                    return {
                        "frameTree": {
                            "frame": {
                                "id": "main",
                                "url": "https://www.linkedin.com/messaging/thread/private-id/",
                            }
                        }
                    }
                if method == "Page.createIsolatedWorld":
                    return {"executionContextId": 23}
                return {
                    "result": {
                        "value": {"conversationFound": True, "eventCount": 1}
                    }
                }

        fake = FakeConnection()
        target = {
            "type": "page",
            "url": "https://www.linkedin.com/messaging/thread/private-id/",
            "webSocketDebuggerUrl": "ws://expected",
        }
        manager = mock.MagicMock()
        manager.__enter__.return_value = fake
        with (
            mock.patch.object(
                linkedin_reply_monitor.inbound_monitor,
                "load_cdp_targets",
                return_value=[target],
            ),
            mock.patch.object(
                linkedin_reply_monitor.inbound_monitor,
                "open_cdp_target",
                return_value=manager,
            ),
            mock.patch.object(
                linkedin_reply_monitor.browser,
                "browser_operation_lock",
                return_value=mock.MagicMock(),
            ),
        ):
            count = linkedin_reply_monitor.read_event_count(
                cdp="http://127.0.0.1:9436",
                thread_url="https://www.linkedin.com/messaging/thread/private-id/",
                minimum_event_count=1,
            )
        self.assertEqual(count, 1)
        methods = {method for method, _ in fake.calls}
        self.assertFalse(
            {"Page.bringToFront", "Page.navigate", "Input.dispatchMouseEvent"} & methods
        )

    def test_first_observation_is_a_private_baseline(self):
        report = self.record(1, "2026-09-05T15:30:00Z")
        self.assertEqual(report["alerts"], [])
        self.assertFalse(report["policy"]["message_content_read"])
        serialized = json.dumps(report).casefold()
        self.assertNotIn("thread", serialized)
        self.assertNotIn("sender", serialized.replace("sender_metadata_persisted", ""))

    def test_increase_creates_review_alert_without_inflating_funnel(self):
        self.record(1, "2026-09-05T15:30:00Z")
        report = self.record(2, "2026-09-05T15:45:00Z")
        self.assertEqual(
            report["alerts"][0]["kind"],
            "linkedin_conversation_event_count_increased",
        )
        self.assertEqual(report["alerts"][0]["event_delta"], 1)
        self.assertTrue(report["policy"]["event_increase_is_not_a_reply_or_lead"])
        self.assertNotIn("revenue", json.dumps(report).casefold())

    def test_decrease_fails_closed_and_preserves_previous_baseline(self):
        self.record(2, "2026-09-05T15:30:00Z")
        with self.assertRaisesRegex(RuntimeError, "decreased"):
            self.record(1, "2026-09-05T15:45:00Z")
        report = self.record(2, "2026-09-05T16:00:00Z")
        self.assertEqual(report["alerts"], [])

    def test_missing_or_unloaded_conversation_fails_closed(self):
        with self.assertRaises(RuntimeError):
            linkedin_reply_monitor.parse_event_count(
                {"conversationFound": False, "eventCount": 0},
                minimum_event_count=1,
            )
        with self.assertRaises(RuntimeError):
            linkedin_reply_monitor.parse_event_count(
                {"conversationFound": True, "eventCount": 0},
                minimum_event_count=1,
            )


if __name__ == "__main__":
    unittest.main()
