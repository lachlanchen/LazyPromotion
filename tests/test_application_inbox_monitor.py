import contextlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import application_inbox_monitor


class FakeMailConnection:
    def __init__(
        self,
        *,
        folder_found=True,
        folder_selected=False,
        tree_found=True,
        campaigns=None,
    ):
        self.calls = []
        self.payload = {
            "folderFound": folder_found,
            "folderSelected": folder_selected,
            "treeFound": tree_found,
            "campaigns": campaigns or [],
        }

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
            return {"executionContextId": 23}
        return {"result": {"value": self.payload}}


class ApplicationInboxMonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "application-inbox.sqlite3"
        self.status = self.root / "status.json"
        self.config = {
            "folder_name": "Primary",
            "campaigns": [
                {
                    "campaign_id": "alpha-application",
                    "participant_terms": ["Hiring Team", "jobs@example.invalid"],
                    "subject_terms": ["Alpha role"],
                },
                {
                    "campaign_id": "beta-application",
                    "participant_terms": ["Beta Studio"],
                    "subject_terms": ["Video editor"],
                },
            ],
        }

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def mail_target(websocket_url):
        return {
            "type": "page",
            "url": "https://www.icloud.com/mail/",
            "webSocketDebuggerUrl": websocket_url,
        }

    @staticmethod
    def summary(campaign_id, matching, unread):
        return {
            "campaignId": campaign_id,
            "matchingThreadCount": matching,
            "unreadMatchingThreadCount": unread,
            "hasMatchingThread": matching > 0,
            "hasUnreadMatchingThread": unread > 0,
        }

    def persisted_summary(self, campaign_id, matching, unread):
        return {
            "campaign_id": campaign_id,
            "matching_thread_count": matching,
            "unread_matching_thread_count": unread,
            "has_matching_thread": matching > 0,
            "has_unread_matching_thread": unread > 0,
        }

    def read_with(self, targets, connections):
        def open_target(websocket_url):
            return contextlib.nullcontext(connections[websocket_url])

        with (
            mock.patch.object(
                application_inbox_monitor.inbound_monitor,
                "load_cdp_targets",
                return_value=targets,
            ),
            mock.patch.object(
                application_inbox_monitor.inbound_monitor,
                "open_cdp_target",
                side_effect=open_target,
            ),
            mock.patch.object(
                application_inbox_monitor.browser,
                "browser_operation_lock",
                return_value=contextlib.nullcontext(),
            ),
        ):
            return application_inbox_monitor.read_application_counts(
                cdp="http://127.0.0.1:9436",
                config=self.config,
            )

    def test_config_validation_is_pure_and_canonical(self):
        original = json.loads(json.dumps(self.config))
        validated = application_inbox_monitor.validate_config(self.config)
        self.assertEqual(validated, self.config)
        self.assertEqual(self.config, original)
        self.assertIsNot(validated, self.config)
        self.assertIsNot(validated["campaigns"], self.config["campaigns"])

    def test_config_rejects_ambiguous_or_unsafe_rules(self):
        invalid = [
            {},
            {"folder_name": "Primary", "campaigns": []},
            {
                "folder_name": "Primary",
                "campaigns": [
                    {
                        "campaign_id": "Unsafe ID",
                        "participant_terms": ["one"],
                        "subject_terms": ["two"],
                    }
                ],
            },
            {
                "folder_name": "Primary",
                "campaigns": [
                    {
                        "campaign_id": "same",
                        "participant_terms": ["one"],
                        "subject_terms": ["two"],
                    },
                    {
                        "campaign_id": "same",
                        "participant_terms": ["three"],
                        "subject_terms": ["four"],
                    },
                ],
            },
            {
                "folder_name": "Primary",
                "campaigns": [
                    {
                        "campaign_id": "missing-subject-rule",
                        "participant_terms": ["one"],
                    }
                ],
            },
        ]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                application_inbox_monitor.validate_config(payload)

    def test_private_config_load_errors_do_not_repeat_private_values(self):
        path = self.root / "private.json"
        private_value = "secret-person@example.invalid"
        path.write_text(
            json.dumps(
                {
                    "folder_name": "Primary",
                    "campaigns": [
                        {
                            "campaign_id": "bad id",
                            "participant_terms": [private_value],
                            "subject_terms": ["secret subject"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaises(RuntimeError) as raised:
            application_inbox_monitor.load_config(path)
        self.assertNotIn(private_value, str(raised.exception))
        self.assertNotIn("secret subject", str(raised.exception))

    def test_pure_matching_requires_participant_and_subject(self):
        rows = [
            {
                "participants": "Hiring Team, Me",
                "subject": "RE: ALPHA   ROLE",
                "timestamp": "10:42 AM",
                "unread": True,
            },
            {
                "participants": "Beta Studio",
                "subject": "A different project",
                "timestamp": "Yesterday",
                "unread": True,
            },
            {
                "participants": "Unrelated Person",
                "subject": "Video editor",
                "timestamp": "Monday",
                "unread": True,
            },
            {
                "participants": "jobs@example.invalid",
                "subject": "Alpha role — follow-up",
                "timestamp": "Sunday",
                "unread": False,
            },
        ]
        summaries = application_inbox_monitor.match_rows(self.config, rows)
        self.assertEqual(
            summaries,
            [
                self.persisted_summary("alpha-application", 2, 1),
                self.persisted_summary("beta-application", 0, 0),
            ],
        )
        serialized = json.dumps(summaries).casefold()
        for private_value in (
            "hiring team",
            "jobs@example.invalid",
            "alpha role",
            "beta studio",
            "video editor",
            "unrelated person",
            "yesterday",
        ):
            self.assertNotIn(private_value, serialized)

    def test_dom_expression_uses_only_approved_row_fields(self):
        expression = application_inbox_monitor.application_rows_expression(
            self.config
        )
        lowered = expression.casefold().replace(" ", "")
        self.assertIn(
            '[role="tree"][aria-label="messages"][role="treeitem"]',
            lowered,
        )
        for required in (
            ".thread-participants",
            ".thread-subject",
            ".thread-timestamp",
            ".adornment-unread",
        ):
            self.assertIn(required, expression)
        for forbidden in (
            ".thread-preview",
            "row.textcontent",
            "row.innertext",
            "row.getattribute('aria-label')",
            "row.getattribute(\"aria-label\")",
            ".click(",
            "page.navigate",
            "dispatchmouseevent",
        ):
            self.assertNotIn(forbidden, expression.casefold())

    def test_selects_exactly_one_configured_folder_without_ui_actions(self):
        first = FakeMailConnection(folder_selected=False)
        second = FakeMailConnection(
            folder_selected=True,
            campaigns=[
                self.summary("alpha-application", 1, 1),
                self.summary("beta-application", 0, 0),
            ],
        )
        result = self.read_with(
            [self.mail_target("ws://one"), self.mail_target("ws://two")],
            {"ws://one": first, "ws://two": second},
        )
        self.assertEqual(
            result,
            [
                self.persisted_summary("alpha-application", 1, 1),
                self.persisted_summary("beta-application", 0, 0),
            ],
        )
        for connection in (first, second):
            methods = [method for method, _ in connection.calls]
            self.assertEqual(
                methods,
                ["Page.getFrameTree", "Page.createIsolatedWorld", "Runtime.evaluate"],
            )
            self.assertFalse(
                {
                    "Page.bringToFront",
                    "Page.navigate",
                    "Input.dispatchMouseEvent",
                }
                & set(methods)
            )

    def test_zero_multiple_or_missing_tree_states_fail_closed(self):
        scenarios = {
            "zero": [FakeMailConnection(), FakeMailConnection()],
            "multiple": [
                FakeMailConnection(folder_selected=True),
                FakeMailConnection(folder_selected=True),
            ],
            "missing-tree": [
                FakeMailConnection(folder_selected=True, tree_found=False)
            ],
            "wrong-folder": [
                FakeMailConnection(folder_found=False, folder_selected=False)
            ],
        }
        for name, connections_list in scenarios.items():
            with self.subTest(name=name):
                targets = []
                connections = {}
                for index, connection in enumerate(connections_list):
                    websocket_url = f"ws://{index}"
                    targets.append(self.mail_target(websocket_url))
                    connections[websocket_url] = connection
                with self.assertRaises(RuntimeError):
                    self.read_with(targets, connections)

    def test_browser_summary_shape_and_consistency_fail_closed(self):
        bad_summaries = [
            [self.summary("wrong-id", 1, 1), self.summary("beta-application", 0, 0)],
            [self.summary("alpha-application", 1, 2), self.summary("beta-application", 0, 0)],
            [self.summary("alpha-application", 0, 0)],
        ]
        for summaries in bad_summaries:
            with self.subTest(summaries=summaries):
                connection = FakeMailConnection(
                    folder_selected=True,
                    campaigns=summaries,
                )
                with self.assertRaises(RuntimeError):
                    self.read_with(
                        [self.mail_target("ws://mail")],
                        {"ws://mail": connection},
                    )

    def test_first_observation_is_baseline_and_second_increase_alerts(self):
        initial = [
            self.persisted_summary("alpha-application", 1, 0),
            self.persisted_summary("beta-application", 0, 0),
        ]
        first = application_inbox_monitor.record_observation(
            initial,
            db_path=self.db,
            status_path=self.status,
            observed_at="2026-09-09T08:00:00Z",
        )
        self.assertEqual(first["alerts"], [])
        changed = [
            self.persisted_summary("alpha-application", 1, 1),
            self.persisted_summary("beta-application", 1, 0),
        ]
        second = application_inbox_monitor.record_observation(
            changed,
            db_path=self.db,
            status_path=self.status,
            observed_at="2026-09-09T08:15:00Z",
        )
        self.assertEqual(
            second["alerts"],
            [
                {
                    "campaign_id": "alpha-application",
                    "matching_thread_count_increased": False,
                    "unread_matching_thread_count_increased": True,
                },
                {
                    "campaign_id": "beta-application",
                    "matching_thread_count_increased": True,
                    "unread_matching_thread_count_increased": False,
                },
            ],
        )
        self.assertEqual(second["summary"]["campaigns_with_matching_threads"], 2)
        self.assertEqual(
            second["summary"]["campaigns_with_unread_matching_threads"], 1
        )
        self.assertFalse(second["policy"]["mail_opened"])
        self.assertFalse(second["policy"]["sender_or_subject_persisted"])
        self.assertTrue(second["policy"]["automatic_reply_is_not_human_reply"])
        self.assertTrue(second["policy"]["match_is_not_human_reply"])

    def test_storage_contains_no_folder_or_mail_metadata(self):
        summaries = [
            self.persisted_summary("alpha-application", 1, 1),
            self.persisted_summary("beta-application", 0, 0),
        ]
        application_inbox_monitor.record_observation(
            summaries,
            db_path=self.db,
            status_path=self.status,
            observed_at="2026-09-09T08:00:00Z",
        )
        db = sqlite3.connect(self.db)
        try:
            stored = json.dumps(
                {
                    "schema": db.execute(
                        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
                    ).fetchall(),
                    "rows": db.execute(
                        "SELECT observed_at, campaign_id, matching_thread_count, "
                        "unread_matching_thread_count, has_matching_thread, "
                        "has_unread_matching_thread "
                        "FROM application_inbox_observations"
                    ).fetchall(),
                }
            ).casefold()
        finally:
            db.close()
        persisted = stored + self.status.read_text(encoding="utf-8").casefold()
        for private_value in (
            "hiring team",
            "jobs@example.invalid",
            "alpha role",
            "beta studio",
            "video editor",
            "thread-preview",
        ):
            self.assertNotIn(private_value, persisted)
        for forbidden_field in ('"participants":', '"subject":', '"timestamp":'):
            self.assertNotIn(forbidden_field, persisted)
        self.assertNotIn('"folder": "primary"', persisted)
        self.assertNotIn('"folder_name": "primary"', persisted)

    def test_invalid_persisted_aggregates_fail_closed(self):
        bad = self.persisted_summary("alpha-application", 1, 1)
        bad["unread_matching_thread_count"] = 2
        with self.assertRaises(ValueError):
            application_inbox_monitor.record_observation(
                [bad], db_path=self.db, status_path=self.status
            )
        self.assertFalse(self.db.exists())
        self.assertFalse(self.status.exists())

    def test_loop_interval_has_five_minute_floor_before_runtime_access(self):
        with (
            mock.patch.object(
                application_inbox_monitor.Path,
                "mkdir",
                side_effect=AssertionError("runtime touched"),
            ),
            self.assertRaisesRegex(ValueError, "at least five"),
        ):
            application_inbox_monitor.loop(4)

    def test_parser_supports_once_and_loop(self):
        parser = application_inbox_monitor.build_parser()
        self.assertEqual(parser.parse_args(["once"]).command, "once")
        loop_args = parser.parse_args(["loop", "--interval-minutes", "5"])
        self.assertEqual(loop_args.command, "loop")
        self.assertEqual(loop_args.interval_minutes, 5)


if __name__ == "__main__":
    unittest.main()
