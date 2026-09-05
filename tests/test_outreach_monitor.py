import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import outreach_monitor


class OutreachMonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "outreach.sqlite3"
        self.status = self.root / "status.json"

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, unread, at):
        return outreach_monitor.record_observation(
            unread,
            public_label="Business outreach",
            db_path=self.db,
            status_path=self.status,
            observed_at=at,
        )

    def test_parses_empty_exact_and_capped_badges(self):
        self.assertEqual(outreach_monitor.parse_badge_texts([]), 0)
        self.assertEqual(outreach_monitor.parse_badge_texts(["3"]), 3)
        self.assertEqual(outreach_monitor.parse_badge_texts(["99+"]), 99)
        self.assertEqual(outreach_monitor.parse_badge_texts(["2", "2"]), 2)

    def test_rejects_conflicting_or_non_numeric_badges(self):
        with self.assertRaises(ValueError):
            outreach_monitor.parse_badge_texts(["2", "3"])
        with self.assertRaises(ValueError):
            outreach_monitor.parse_badge_texts(["new"])

    def test_first_observation_is_private_baseline(self):
        report = self.record(0, "2026-09-05T15:00:00Z")
        self.assertEqual(report["alerts"], [])
        self.assertEqual(report["folder"], "Business outreach")
        self.assertFalse(report["policy"]["message_content_opened"])
        self.assertNotIn("sender", json.dumps(report).casefold())
        self.assertNotIn("subject", json.dumps(report).casefold())

    def test_unread_increase_creates_review_alert_not_lead(self):
        self.record(0, "2026-09-05T15:00:00Z")
        report = self.record(1, "2026-09-05T15:15:00Z")
        self.assertEqual(report["alerts"][0]["kind"], "outreach_unread_increased")
        self.assertEqual(report["alerts"][0]["unread_delta"], 1)
        self.assertTrue(report["policy"]["unread_increase_is_not_a_qualified_lead"])

    def test_config_keeps_private_folder_separate_from_public_label(self):
        config = self.root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "folder_name": "private-route@example.invalid",
                    "public_label": "Business outreach",
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            outreach_monitor.load_config(config),
            {
                "folder_name": "private-route@example.invalid",
                "public_label": "Business outreach",
            },
        )

    def test_reads_only_one_folder_badge_without_focus_or_navigation(self):
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
                    return {"executionContextId": 19}
                return {
                    "result": {
                        "value": {
                            "folderFound": True,
                            "folderSelected": False,
                            "badgeTexts": ["1"],
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
            mock.patch.object(outreach_monitor.inbound_monitor, "load_cdp_targets", return_value=[target]),
            mock.patch.object(outreach_monitor.inbound_monitor, "open_cdp_target", return_value=manager),
            mock.patch.object(outreach_monitor.browser, "browser_operation_lock", return_value=mock.MagicMock()),
        ):
            self.assertEqual(
                outreach_monitor.read_unread_badge(
                    cdp="http://127.0.0.1:9436",
                    folder_name="private-route@example.invalid",
                ),
                1,
            )
        methods = {method for method, _ in fake.calls}
        self.assertFalse(
            {"Page.bringToFront", "Page.navigate", "Input.dispatchMouseEvent"} & methods
        )


if __name__ == "__main__":
    unittest.main()
