import contextlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import outreach_monitor


class FakeMailConnection:
    def __init__(self, *, folder_found=True, folder_selected=False, status=None):
        self.calls = []
        self.folder_found = folder_found
        self.folder_selected = folder_selected
        self.status = status

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
                    "folderFound": self.folder_found,
                    "folderSelected": self.folder_selected,
                    "status": self.status,
                }
            }
        }


class OutreachMonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "outreach.sqlite3"
        self.status = self.root / "status.json"

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, messages, unread, at):
        return outreach_monitor.record_observation(
            messages,
            unread,
            public_label="Business outreach",
            db_path=self.db,
            status_path=self.status,
            observed_at=at,
        )

    @staticmethod
    def mail_target(websocket_url):
        return {
            "type": "page",
            "url": "https://www.icloud.com/mail/",
            "webSocketDebuggerUrl": websocket_url,
        }

    def read_with(self, targets, connections):
        def open_target(websocket_url):
            return contextlib.nullcontext(connections[websocket_url])

        with (
            mock.patch.object(
                outreach_monitor.inbound_monitor,
                "load_cdp_targets",
                return_value=targets,
            ),
            mock.patch.object(
                outreach_monitor.inbound_monitor,
                "open_cdp_target",
                side_effect=open_target,
            ),
            mock.patch.object(
                outreach_monitor.browser,
                "browser_operation_lock",
                return_value=contextlib.nullcontext(),
            ),
        ):
            return outreach_monitor.read_folder_counts(
                cdp="http://127.0.0.1:9436",
                folder_name="private-route@example.invalid",
            )

    def test_first_observation_is_sanitized_baseline(self):
        report = self.record(4, 0, "2026-09-05T15:00:00Z")
        self.assertEqual(report["alerts"], [])
        self.assertEqual(report["folder"], "Business outreach")
        self.assertEqual(report["message_count"], 4)
        self.assertEqual(report["unread_count"], 0)
        self.assertFalse(report["policy"]["message_content_opened"])
        self.assertFalse(report["policy"]["message_metadata_persisted"])
        serialized = json.dumps(report).casefold()
        self.assertNotIn("sender", serialized)
        self.assertNotIn("subject", serialized)
        self.assertNotIn("private-route", serialized)

    def test_message_count_increase_alerts_even_if_unread_stays_zero(self):
        self.record(4, 0, "2026-09-05T15:00:00Z")
        report = self.record(5, 0, "2026-09-05T15:15:00Z")
        self.assertEqual(report["alerts"][0]["kind"], "outreach_count_increased")
        self.assertEqual(report["alerts"][0]["message_delta"], 1)
        self.assertTrue(report["policy"]["count_increase_is_not_a_qualified_lead"])

    def test_unread_only_change_does_not_claim_a_reply_or_lead(self):
        self.record(4, 0, "2026-09-05T15:00:00Z")
        report = self.record(4, 1, "2026-09-05T15:15:00Z")
        self.assertEqual(report["alerts"], [])
        self.assertTrue(report["policy"]["count_increase_is_not_a_qualified_lead"])
        self.assertFalse(report["policy"]["automatic_reply"])

    def test_invalid_counts_fail_closed(self):
        for messages, unread in [(-1, 0), (1, -1), (1, 2)]:
            with self.subTest(messages=messages, unread=unread):
                with self.assertRaises(ValueError):
                    self.record(messages, unread, "2026-09-05T15:00:00Z")

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

    def test_selects_exactly_one_already_selected_folder_across_mail_tabs(self):
        first = FakeMailConnection(folder_selected=False, status=None)
        second = FakeMailConnection(
            folder_selected=True,
            status="5 Messages, 0 unread",
        )
        targets = [
            {
                "type": "page",
                "url": "https://example.invalid/",
                "webSocketDebuggerUrl": "ws://unrelated",
            },
            self.mail_target("ws://mail-one"),
            self.mail_target("ws://mail-two"),
        ]
        self.assertEqual(
            self.read_with(
                targets,
                {"ws://mail-one": first, "ws://mail-two": second},
            ),
            (5, 0),
        )

        for connection in (first, second):
            methods = [method for method, _ in connection.calls]
            self.assertEqual(
                methods,
                ["Page.getFrameTree", "Page.createIsolatedWorld", "Runtime.evaluate"],
            )
            self.assertFalse(
                {"Page.bringToFront", "Page.navigate", "Input.dispatchMouseEvent"}
                & set(methods)
            )

    def test_zero_or_multiple_selected_folder_tabs_fail_closed(self):
        scenarios = {
            "zero": [
                FakeMailConnection(folder_selected=False),
                FakeMailConnection(folder_found=False, folder_selected=False),
            ],
            "multiple": [
                FakeMailConnection(folder_selected=True, status="4 Messages"),
                FakeMailConnection(folder_selected=True, status="4 Messages"),
            ],
        }
        for name, connections_list in scenarios.items():
            with self.subTest(name=name):
                targets = [
                    self.mail_target("ws://mail-one"),
                    self.mail_target("ws://mail-two"),
                ]
                connections = {
                    "ws://mail-one": connections_list[0],
                    "ws://mail-two": connections_list[1],
                }
                with self.assertRaisesRegex(RuntimeError, "exactly one"):
                    self.read_with(targets, connections)

    def test_missing_mail_target_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "not open"):
            outreach_monitor.icloud_mail_targets(
                [
                    {
                        "type": "iframe",
                        "url": "https://www.icloud.com/mail/",
                        "webSocketDebuggerUrl": "ws://iframe",
                    }
                ]
            )

    def test_count_expression_does_not_read_message_content_or_metadata(self):
        expression = outreach_monitor.inbound_monitor.aggregate_status_expression(
            "private-route@example.invalid"
        ).casefold()
        for forbidden in (
            "subject",
            "sender",
            "message-list",
            "mail2-message",
            "document.body",
            "[role=\"row\"]",
        ):
            self.assertNotIn(forbidden, expression)

    def test_legacy_unread_table_and_rows_are_preserved(self):
        db = sqlite3.connect(self.db)
        db.execute(
            """
            CREATE TABLE outreach_unread_observations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              observed_at TEXT NOT NULL,
              public_label TEXT NOT NULL,
              unread_count INTEGER NOT NULL
            )
            """
        )
        db.execute(
            """
            INSERT INTO outreach_unread_observations
              (observed_at, public_label, unread_count)
            VALUES (?, ?, ?)
            """,
            ("2026-09-05T14:45:00Z", "Business outreach", 0),
        )
        db.commit()
        db.close()

        self.record(4, 0, "2026-09-05T15:00:00Z")

        db = sqlite3.connect(self.db)
        try:
            legacy = db.execute(
                "SELECT observed_at, public_label, unread_count "
                "FROM outreach_unread_observations"
            ).fetchall()
            current = db.execute(
                "SELECT observed_at, public_label, message_count, unread_count "
                "FROM outreach_count_observations"
            ).fetchall()
        finally:
            db.close()
        self.assertEqual(
            legacy,
            [("2026-09-05T14:45:00Z", "Business outreach", 0)],
        )
        self.assertEqual(
            current,
            [("2026-09-05T15:00:00Z", "Business outreach", 4, 0)],
        )

    def test_status_and_database_do_not_store_private_folder_or_mail_metadata(self):
        self.record(4, 0, "2026-09-05T15:00:00Z")
        status_text = self.status.read_text(encoding="utf-8").casefold()
        self.assertNotIn("private-route", status_text)
        self.assertNotIn("sender", status_text)
        self.assertNotIn("subject", status_text)

        db = sqlite3.connect(self.db)
        try:
            schema_and_values = json.dumps(
                {
                    "schema": db.execute(
                        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
                    ).fetchall(),
                    "values": db.execute(
                        "SELECT observed_at, public_label, message_count, unread_count "
                        "FROM outreach_count_observations"
                    ).fetchall(),
                }
            ).casefold()
        finally:
            db.close()
        self.assertNotIn("private-route", schema_and_values)
        self.assertNotIn("sender", schema_and_values)
        self.assertNotIn("subject", schema_and_values)


if __name__ == "__main__":
    unittest.main()
