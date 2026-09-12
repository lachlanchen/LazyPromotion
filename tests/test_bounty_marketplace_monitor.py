import io
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import bounty_marketplace_monitor as monitor


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


class BountyMarketplaceMonitorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / ".local" / "private").mkdir(parents=True)
        self.credentials = self.root / ".local" / "private" / "CREDENTIALS.md"
        self.api_key = "ak_abcdefghijklmnopqrstuvwxyz012345"
        self.credentials.write_text(
            "# Private credentials\n\n"
            "## Unrelated\n- Password: `leave-unread`\n\n"
            "## Bounty agent API\n"
            f"- API key: `{self.api_key}`\n\n"
            "## Later section\n- Token: `also-unrelated`\n",
            encoding="utf-8",
        )
        os.chmod(self.credentials, 0o600)
        self.state = self.root / ".local" / "bounty-status.json"

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def opener(pages, requests):
        pages = list(pages)

        def open_request(request, timeout=0):
            requests.append(
                {
                    "url": request.full_url,
                    "method": request.get_method(),
                    "authorization": request.headers.get("Authorization"),
                    "timeout": timeout,
                }
            )
            return FakeResponse(json.dumps(pages.pop(0)).encode("utf-8"))

        return open_request

    @staticmethod
    def page(rows=None, *, done=True, cursor=None):
        return {
            "bounties": rows or [],
            "is_done": done,
            "next_cursor": cursor,
        }

    @staticmethod
    def taskbounty_feed(rows=None):
        return {
            "version": "https://jsonfeed.org/version/1.1",
            "title": "TaskBounty · Open Bounties",
            "items": rows or [],
        }

    def test_credentials_must_be_private_regular_singly_linked_and_valid(self):
        self.assertEqual(monitor.load_api_key(self.credentials), self.api_key)

        os.chmod(self.credentials, 0o644)
        with self.assertRaisesRegex(ValueError, "private"):
            monitor.load_api_key(self.credentials)
        os.chmod(self.credentials, 0o600)

        linked = self.root / "linked-credentials.md"
        linked.symlink_to(self.credentials)
        with self.assertRaisesRegex(ValueError, "regular file"):
            monitor.load_api_key(linked)

        missing = self.root / "missing.md"
        with self.assertRaisesRegex(ValueError, "regular file"):
            monitor.load_api_key(missing)

        self.credentials.write_text(
            "## Bounty agent API\n- API key: `not-a-key`\n", encoding="utf-8"
        )
        os.chmod(self.credentials, 0o600)
        with self.assertRaisesRegex(ValueError, "missing or invalid"):
            monitor.load_api_key(self.credentials)

    def test_fetch_is_get_only_and_paginates_without_returning_credentials(self):
        requests = []
        pages = [
            self.page([{"_id": "one", "version": 1}], done=False, cursor="c2"),
            self.page([{"id": "two", "version": 3}]),
        ]
        report = monitor.fetch_available_bounties(
            self.api_key, opener=self.opener(pages, requests)
        )

        self.assertEqual(report["pages_read"], 2)
        self.assertEqual(
            report["bounties"],
            [
                {"bounty_id": "one", "version": 1},
                {"bounty_id": "two", "version": 3},
            ],
        )
        self.assertEqual([row["method"] for row in requests], ["GET", "GET"])
        self.assertTrue(all(row["timeout"] == 30 for row in requests))
        self.assertTrue(
            all(row["authorization"] == f"Bearer {self.api_key}" for row in requests)
        )
        self.assertEqual(
            parse_qs(urlparse(requests[1]["url"]).query), {"cursor": ["c2"]}
        )
        self.assertNotIn(self.api_key, json.dumps(report))

    def test_invalid_pages_duplicate_summaries_and_stalled_cursor_fail_closed(self):
        cases = [
            {"bounties": "wrong", "is_done": True, "next_cursor": None},
            self.page([{"id": "missing-version"}]),
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(RuntimeError):
                    monitor.fetch_available_bounties(
                        self.api_key, opener=self.opener([payload], [])
                    )

        duplicate = self.page(
            [{"id": "same", "version": 1}, {"id": "same", "version": 2}]
        )
        with self.assertRaisesRegex(RuntimeError, "duplicate"):
            monitor.fetch_available_bounties(
                self.api_key, opener=self.opener([duplicate], [])
            )

        stalled = self.page([], done=False, cursor=None)
        with self.assertRaisesRegex(RuntimeError, "cannot advance"):
            monitor.fetch_available_bounties(
                self.api_key, opener=self.opener([stalled], [])
            )

    def test_taskbounty_public_feed_is_get_only_keyless_and_minimal(self):
        requests = []
        report = monitor.fetch_taskbounty_open_tasks(
            opener=self.opener(
                [
                    self.taskbounty_feed(
                        [
                            {
                                "id": "tb-two",
                                "title": "Fix the second regression",
                                "date_modified": "2026-09-12T12:00:00Z",
                                "content_text": "Untrusted task details stay out of state.",
                            },
                            {"id": "tb-one", "title": "Fix the first regression"},
                        ]
                    )
                ],
                requests,
            )
        )
        self.assertEqual([row["task_id"] for row in report["tasks"]], ["tb-one", "tb-two"])
        self.assertEqual(requests[0]["method"], "GET")
        self.assertIsNone(requests[0]["authorization"])
        self.assertEqual(requests[0]["timeout"], 30)
        serialized = json.dumps(report)
        self.assertNotIn("Untrusted task details", serialized)
        self.assertRegex(report["tasks"][0]["fingerprint"], r"^[0-9a-f]{64}$")

        invalid = self.taskbounty_feed([{"title": "missing id"}])
        with self.assertRaisesRegex(RuntimeError, "no ID"):
            monitor.fetch_taskbounty_open_tasks(
                opener=self.opener([invalid], [])
            )

    def test_baseline_then_new_and_updated_versions_raise_private_review_alerts(self):
        requests = []
        first = monitor.monitor_once(
            credentials_path=self.credentials,
            state_path=self.state,
            root=self.root,
            opener=self.opener(
                [
                    self.page([{"id": "alpha", "version": 1}]),
                    self.taskbounty_feed(),
                ],
                requests,
            ),
            checked_at="2026-09-11T12:00:00Z",
        )
        self.assertTrue(first["baseline_created"])
        self.assertEqual(first["alerts"], [])

        second = monitor.monitor_once(
            credentials_path=self.credentials,
            state_path=self.state,
            root=self.root,
            opener=self.opener(
                [
                    self.page(
                        [
                            {"id": "alpha", "version": 2},
                            {"id": "beta", "version": 1},
                        ]
                    ),
                    self.taskbounty_feed(),
                ],
                requests,
            ),
            checked_at="2026-09-11T12:05:00Z",
        )
        self.assertFalse(second["baseline_created"])
        self.assertEqual(
            [(row["kind"], row["bounty_id"]) for row in second["alerts"]],
            [
                ("available_bounty_changed", "alpha"),
                ("new_available_bounty", "beta"),
            ],
        )
        self.assertEqual(second["seen_bounty_versions"], {"alpha": 2, "beta": 1})
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o600)
        serialized = self.state.read_text(encoding="utf-8")
        self.assertNotIn(self.api_key, serialized)
        self.assertEqual(second["policy"]["http_method"], "GET")
        self.assertFalse(second["policy"]["comments_or_messages_written"])
        self.assertFalse(second["policy"]["claims_created"])
        self.assertFalse(second["policy"]["submissions_created"])
        self.assertFalse(second["policy"]["accounts_registered"])
        self.assertFalse(second["policy"]["payout_methods_configured"])
        self.assertTrue(second["policy"]["available_work_is_not_a_lead"])
        self.assertTrue(second["policy"]["available_work_is_not_revenue"])

    def test_taskbounty_baseline_then_change_raises_review_only_alerts(self):
        first_task = {
            "id": "tb-one",
            "title": "Fix one Python regression",
            "date_published": "2026-09-12T12:00:00Z",
        }
        first = monitor.build_state(
            {"bounties": [], "pages_read": 1},
            None,
            taskbounty_observation={
                "tasks": monitor.fetch_taskbounty_open_tasks(
                    opener=self.opener([self.taskbounty_feed([first_task])], [])
                )["tasks"],
                "pages_read": 1,
            },
            checked_at="2026-09-12T12:01:00Z",
        )
        self.assertTrue(first["taskbounty_baseline_created"])
        self.assertEqual(first["alerts"], [])

        changed_task = {**first_task, "title": "Fix one Python parser regression"}
        new_task = {"id": "tb-two", "title": "Repair a TypeScript test"}
        second = monitor.build_state(
            {"bounties": [], "pages_read": 1},
            first,
            taskbounty_observation={
                "tasks": monitor.fetch_taskbounty_open_tasks(
                    opener=self.opener(
                        [self.taskbounty_feed([changed_task, new_task])], []
                    )
                )["tasks"],
                "pages_read": 1,
            },
            checked_at="2026-09-12T12:06:00Z",
        )
        self.assertFalse(second["taskbounty_baseline_created"])
        self.assertEqual(
            [(row["kind"], row["task_id"]) for row in second["alerts"]],
            [
                ("taskbounty_task_changed", "tb-one"),
                ("new_taskbounty_task", "tb-two"),
            ],
        )
        self.assertTrue(all(row["provider"] == "taskbounty" for row in second["alerts"]))
        self.assertTrue(
            all("do not register" in row["action"] for row in second["alerts"])
        )

    def test_seen_versions_survive_work_leaving_the_available_feed(self):
        previous = {
            "version": 1,
            "seen_bounty_versions": {"alpha": 4},
        }
        report = monitor.build_state(
            {"bounties": [], "pages_read": 1},
            previous,
            checked_at="2026-09-11T12:10:00Z",
        )
        self.assertEqual(report["available_bounties"], [])
        self.assertEqual(report["seen_bounty_versions"], {"alpha": 4})
        self.assertEqual(report["alerts"], [])

    def test_loop_rejects_an_interval_below_the_five_minute_floor(self):
        with self.assertRaisesRegex(ValueError, "at least 5"):
            monitor.monitor_loop(4)

    def test_wrapper_is_syntax_valid_private_and_single_session(self):
        root = Path(__file__).resolve().parents[1]
        wrapper = root / "scripts" / "bounty-marketplace-monitor.sh"
        subprocess.run(["bash", "-n", wrapper], check=True)
        text = wrapper.read_text(encoding="utf-8")
        self.assertIn("lazypromotion-bounty-marketplace-monitor", text)
        self.assertIn("bounty_marketplace_monitor.py loop", text)
        self.assertIn("INTERVAL_MINUTES < 5", text)
        self.assertIn('chmod 600 "$LOG"', text)
        self.assertEqual(stat.S_IMODE(wrapper.stat().st_mode), 0o755)


if __name__ == "__main__":
    unittest.main()
