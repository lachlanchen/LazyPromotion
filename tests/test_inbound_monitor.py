import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import inbound_monitor


class InboundMonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "inbound.sqlite3"
        self.status = self.root / "status.json"

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, messages, unread, at):
        return inbound_monitor.record_observation(
            messages,
            unread,
            db_path=self.db,
            status_path=self.status,
            observed_at=at,
        )

    def test_parses_singular_and_plural_aggregate_status(self):
        self.assertEqual(
            inbound_monitor.parse_folder_status("1 Message, 1 unread"),
            (1, 1),
        )
        self.assertEqual(
            inbound_monitor.parse_folder_status("12 Messages, 0 unread"),
            (12, 0),
        )
        self.assertEqual(
            inbound_monitor.parse_folder_status("1 Message"),
            (1, 0),
        )

    def test_first_observation_is_baseline_not_a_lead(self):
        report = self.record(1, 1, "2026-09-01T01:00:00Z")
        self.assertEqual(report["alerts"], [])
        self.assertTrue(report["policy"]["count_increase_is_not_a_qualified_lead"])
        self.assertFalse(report["policy"]["message_content_opened"])

    def test_message_count_increase_creates_review_alert_only(self):
        self.record(1, 1, "2026-09-01T01:00:00Z")
        report = self.record(2, 1, "2026-09-01T01:15:00Z")
        self.assertEqual(report["alerts"][0]["kind"], "inbound_count_increased")
        self.assertEqual(report["alerts"][0]["message_delta"], 1)
        self.assertIn("review fit", report["alerts"][0]["action"])
        serialized = json.dumps(report).casefold()
        self.assertNotIn("qualified_lead\": false", serialized)
        self.assertNotIn("sender", serialized)
        self.assertNotIn("subject", serialized)

    def test_invalid_counts_fail_closed(self):
        with self.assertRaises(ValueError):
            self.record(1, 2, "2026-09-01T01:00:00Z")

    def test_selects_only_the_icloud_mail_page_target(self):
        targets = [
            {
                "type": "iframe",
                "url": "https://www-mail.icloud-sandbox.com/applications/mail2-message/current/",
                "webSocketDebuggerUrl": "ws://message",
            },
            {
                "type": "page",
                "url": "https://www.icloud.com/mail/",
                "webSocketDebuggerUrl": "ws://mail",
            },
        ]
        self.assertEqual(
            inbound_monitor.icloud_mail_target(targets)["webSocketDebuggerUrl"],
            "ws://mail",
        )

    def test_finds_mail_app_frame_but_not_message_body_frame(self):
        tree = {
            "frame": {"id": "root", "url": "https://www.icloud.com/mail/"},
            "childFrames": [
                {
                    "frame": {
                        "id": "message",
                        "url": "https://www-mail.icloud-sandbox.com/applications/mail2-message/current/",
                    }
                },
                {
                    "frame": {
                        "id": "mail-app",
                        "url": "https://www.icloud.com/applications/mail2/current/",
                    }
                },
            ],
        }
        self.assertEqual(inbound_monitor.find_mail_app_frame(tree)["id"], "mail-app")

    def test_reads_aggregate_counts_without_focus_click_or_navigation(self):
        class FakeConnection:
            def __init__(self):
                self.calls = []

            def command(self, method, params=None):
                self.calls.append((method, params or {}))
                if method == "Page.getFrameTree":
                    return {
                        "frameTree": {
                            "frame": {"id": "root", "url": "https://www.icloud.com/mail/"},
                            "childFrames": [
                                {
                                    "frame": {
                                        "id": "mail-app",
                                        "url": "https://www.icloud.com/applications/mail2/current/",
                                    }
                                }
                            ],
                        }
                    }
                if method == "Page.createIsolatedWorld":
                    return {"executionContextId": 17}
                return {
                    "result": {
                        "value": {
                            "folderFound": True,
                            "folderSelected": True,
                            "status": "3 Messages, 1 unread",
                        }
                    }
                }

        fake = FakeConnection()
        target = {
            "type": "page",
            "url": "https://www.icloud.com/mail/",
            "webSocketDebuggerUrl": "ws://mail",
        }
        manager = mock.MagicMock()
        manager.__enter__.return_value = fake
        with (
            mock.patch.object(inbound_monitor, "load_cdp_targets", return_value=[target]),
            mock.patch.object(inbound_monitor, "open_cdp_target", return_value=manager),
            mock.patch.object(inbound_monitor.browser, "browser_operation_lock", return_value=mock.MagicMock()),
        ):
            self.assertEqual(inbound_monitor.read_folder_counts(), (3, 1))

        self.assertEqual(
            [method for method, _ in fake.calls],
            ["Page.getFrameTree", "Page.createIsolatedWorld", "Runtime.evaluate"],
        )
        self.assertFalse(
            {"Page.bringToFront", "Page.navigate", "Input.dispatchMouseEvent"}
            & {method for method, _ in fake.calls}
        )

    def test_unselected_folder_fails_closed(self):
        class FakeConnection:
            def command(self, method, params=None):
                if method == "Page.getFrameTree":
                    return {
                        "frameTree": {
                            "frame": {"id": "root", "url": "https://www.icloud.com/mail/"},
                            "childFrames": [
                                {
                                    "frame": {
                                        "id": "mail-app",
                                        "url": "https://www.icloud.com/applications/mail2/current/",
                                    }
                                }
                            ],
                        }
                    }
                if method == "Page.createIsolatedWorld":
                    return {"executionContextId": 17}
                return {
                    "result": {
                        "value": {
                            "folderFound": True,
                            "folderSelected": False,
                            "status": None,
                        }
                    }
                }

        manager = mock.MagicMock()
        manager.__enter__.return_value = FakeConnection()
        target = {
            "type": "page",
            "url": "https://www.icloud.com/mail/",
            "webSocketDebuggerUrl": "ws://mail",
        }
        with (
            mock.patch.object(inbound_monitor, "load_cdp_targets", return_value=[target]),
            mock.patch.object(inbound_monitor, "open_cdp_target", return_value=manager),
            mock.patch.object(inbound_monitor.browser, "browser_operation_lock", return_value=mock.MagicMock()),
            self.assertRaisesRegex(RuntimeError, "not selected"),
        ):
            inbound_monitor.read_folder_counts()


if __name__ == "__main__":
    unittest.main()
