import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError

import reddit_reply_monitor as monitor


TARGET_URL = "https://www.reddit.com/r/mcp/comments/1we4buv/comment/p9cgosi/"


def comment(thing_id: str, parent_id: str, body: str = "private sentinel") -> str:
    return (
        f'<shreddit-comment thingid="{thing_id}" parentid="{parent_id}">'
        f'<a href="/user/private-author">private-author</a>'
        f'<div slot="comment">{body}</div>'
        "</shreddit-comment>"
    )


def page(*rows: str) -> bytes:
    return ("<!doctype html><html><body>" + "".join(rows) + "</body></html>").encode()


class Headers(dict):
    def get_content_type(self):
        return str(self.get("Content-Type", "")).split(";", 1)[0]


class FakeResponse:
    def __init__(
        self,
        body: bytes,
        *,
        status: int = 200,
        content_type: str = "text/html; charset=utf-8",
        final_url: str = TARGET_URL,
    ):
        self.stream = io.BytesIO(body)
        self.status = status
        self.headers = Headers({"Content-Type": content_type})
        self.final_url = final_url

    def read(self, size=-1):
        return self.stream.read(size)

    def geturl(self):
        return self.final_url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


class RedditReplyMonitorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / ".local").mkdir(mode=0o700)
        self.state = self.root / ".local" / "state.json"
        self.status = self.root / ".local" / "status.json"
        self.log = self.root / ".local" / "status.jsonl"
        self.campaign = self.root / "campaign.json"
        self.campaign.write_text(
            json.dumps(
                {
                    "channels": {
                        "community_replies": {
                            "reddit_kin_graph_design": {
                                "public_reply": TARGET_URL
                            }
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def html(*extra: str) -> bytes:
        return page(comment("t1_p9cgosi", "t3_1we4buv", "target body"), *extra)

    def run_once(self, body: bytes, *, at="2026-09-12T14:00:00Z"):
        opener = FakeOpener(FakeResponse(body))
        report = monitor.monitor_once(
            campaign_path=self.campaign,
            state_path=self.state,
            status_path=self.status,
            log_path=self.log,
            root=self.root,
            opener=opener,
            checked_at=at,
        )
        return report, opener

    def test_real_campaign_exposes_the_single_expected_target(self):
        target = monitor.load_allowlisted_target()
        self.assertEqual(target["url"], TARGET_URL)
        self.assertEqual(target["post_id"], "1we4buv")
        self.assertEqual(target["comment_id"], "p9cgosi")

    def test_target_validation_rejects_non_exact_or_unsafe_urls(self):
        bad = [
            TARGET_URL.replace("https://", "http://"),
            TARGET_URL.replace("www.reddit.com", "www.reddit.com.evil.test"),
            "https://www.reddit.com/r/mcp/comments/1we4buv/comment/",
            "https://www.reddit.com/r/mcp/s/shortshare/",
            TARGET_URL + "extra/",
            TARGET_URL + "?context=1",
            TARGET_URL + "#reply",
            TARGET_URL.replace("www.reddit.com", "user@www.reddit.com"),
            TARGET_URL.replace("www.reddit.com", "www.reddit.com:443"),
            TARGET_URL.replace("www.reddit.com", "www.reddit.com:bad"),
        ]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                monitor.parse_target_url(value)

    def test_campaign_file_cannot_switch_the_allowlisted_comment(self):
        payload = json.loads(self.campaign.read_text(encoding="utf-8"))
        payload["channels"]["community_replies"]["reddit_kin_graph_design"][
            "public_reply"
        ] = TARGET_URL.replace("p9cgosi", "different")
        self.campaign.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not allowlisted"):
            monitor.load_allowlisted_target(self.campaign)

    def test_default_transport_refuses_redirect_requests(self):
        handler = monitor.NoRedirectHandler()
        self.assertIsNone(
            handler.redirect_request(
                None,
                None,
                302,
                "Found",
                {},
                "https://www.reddit.com/login/",
            )
        )

    def test_fetch_is_one_credential_free_get_and_returns_only_metadata(self):
        target = monitor.parse_target_url(TARGET_URL)
        opener = FakeOpener(
            FakeResponse(
                self.html(comment("t1_reply1", "t1_p9cgosi", "secret reply"))
            )
        )
        observed = monitor.fetch_public_comment(target, opener=opener)
        self.assertEqual(observed["direct_reply_count"], 1)
        self.assertNotIn("secret reply", json.dumps(observed))
        self.assertNotIn("private-author", json.dumps(observed))
        self.assertEqual(len(opener.calls), 1)
        request, timeout = opener.calls[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(timeout, 30)
        headers = {key.casefold(): value for key, value in request.header_items()}
        self.assertIn("user-agent", headers)
        self.assertEqual(headers["accept"], "text/html")
        self.assertNotIn("authorization", headers)
        self.assertNotIn("cookie", headers)

    def test_only_direct_replies_count(self):
        target = monitor.parse_target_url(TARGET_URL)
        parser = monitor.RedditCommentMetadataParser()
        parser.feed(
            self.html(
                comment("t1_direct", "t1_p9cgosi"),
                comment("t1_grandchild", "t1_direct"),
                comment("t1_other", "t3_1we4buv"),
            ).decode()
        )
        observed = monitor.parse_comment_metadata(parser, target=target)
        self.assertEqual(observed["direct_reply_count"], 1)
        self.assertEqual(len(observed["direct_reply_fingerprints"]), 1)

    def test_missing_duplicate_and_malformed_markup_fail_closed(self):
        target = monitor.parse_target_url(TARGET_URL)
        cases = [
            page(comment("t1_other", "t3_1we4buv")),
            self.html(comment("t1_p9cgosi", "t3_1we4buv")),
            self.html('<shreddit-comment thingid="bad" parentid="t1_p9cgosi">x</shreddit-comment>'),
            self.html('<shreddit-comment thingid="t1_reply">x</shreddit-comment>'),
        ]
        for html in cases:
            parser = monitor.RedditCommentMetadataParser()
            parser.feed(html.decode())
            with self.subTest(html=html[:80]), self.assertRaisesRegex(
                monitor.RedditMonitorError, "Reddit"
            ):
                monitor.parse_comment_metadata(parser, target=target)

    def test_baseline_change_reordering_deletion_and_reappearance(self):
        first, _ = self.run_once(
            self.html(comment("t1_old", "t1_p9cgosi", "old body"))
        )
        self.assertTrue(first["baseline_created"])
        self.assertEqual(first["new_direct_reply_count"], 0)
        self.assertFalse(first["review_required"])

        second, _ = self.run_once(
            self.html(
                comment("t1_new", "t1_p9cgosi", "new body"),
                comment("t1_old", "t1_p9cgosi", "old body"),
            ),
            at="2026-09-12T15:00:00Z",
        )
        self.assertEqual(second["new_direct_reply_count"], 1)
        self.assertTrue(second["review_required"])
        self.assertNotIn("new body", json.dumps(second))

        deleted, _ = self.run_once(
            self.html(comment("t1_old", "t1_p9cgosi")),
            at="2026-09-12T16:00:00Z",
        )
        self.assertEqual(deleted["new_direct_reply_count"], 0)

        reappeared, _ = self.run_once(
            self.html(
                comment("t1_old", "t1_p9cgosi"),
                comment("t1_new", "t1_p9cgosi"),
            ),
            at="2026-09-12T17:00:00Z",
        )
        self.assertEqual(reappeared["new_direct_reply_count"], 0)

    def test_bodies_authors_and_raw_reply_ids_are_never_persisted(self):
        self.run_once(
            self.html(comment("t1_rawreply", "t1_p9cgosi", "DO-NOT-PERSIST"))
        )
        persisted = self.state.read_text() + self.status.read_text() + self.log.read_text()
        self.assertNotIn("DO-NOT-PERSIST", persisted)
        self.assertNotIn("private-author", persisted)
        self.assertNotIn("rawreply", persisted)
        self.assertIn("comment_bodies_persisted", persisted)
        self.assertFalse(json.loads(self.status.read_text())["policy"]["automatic_reply"])

    def test_http_layout_redirect_content_type_and_size_failures_preserve_state(self):
        self.run_once(self.html(comment("t1_old", "t1_p9cgosi")))
        before = self.state.read_bytes()
        failures = [
            FakeOpener(
                error=HTTPError(TARGET_URL, 429, "Too Many Requests", {}, None)
            ),
            FakeOpener(
                FakeResponse(
                    self.html(), final_url="https://www.reddit.com/login/"
                )
            ),
            FakeOpener(FakeResponse(b"{}", content_type="application/json")),
            FakeOpener(FakeResponse(b"x" * (monitor.MAX_RESPONSE_BYTES + 1))),
            FakeOpener(FakeResponse(page(comment("t1_other", "t3_1we4buv")))),
        ]
        for index, opener in enumerate(failures):
            report = monitor.monitor_once(
                campaign_path=self.campaign,
                state_path=self.state,
                status_path=self.status,
                log_path=self.log,
                root=self.root,
                opener=opener,
                checked_at=f"2026-09-12T{18 + index:02d}:00:00Z",
            )
            self.assertFalse(report["available"])
            self.assertTrue(report["prior_state_preserved"])
            self.assertEqual(self.state.read_bytes(), before)
            self.assertNotIn("Too Many Requests", json.dumps(report))

    def test_private_atomic_files_path_confinement_and_symlink_refusal(self):
        self.run_once(self.html())
        for path in (self.state, self.status, self.log):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        with self.assertRaises(ValueError):
            monitor.validate_runtime_path(
                self.root / "outside.json", root=self.root, suffix=".json"
            )
        link = self.root / ".local" / "link"
        link.symlink_to(self.root)
        with self.assertRaises(ValueError):
            monitor.validate_runtime_path(
                link / "state.json", root=self.root, suffix=".json"
            )

    def test_state_target_mismatch_and_unsafe_permissions_are_rejected(self):
        self.run_once(self.html())
        payload = json.loads(self.state.read_text())
        payload["comment_id"] = "wrong"
        self.state.write_text(json.dumps(payload), encoding="utf-8")
        os.chmod(self.state, 0o600)
        with self.assertRaises(ValueError):
            monitor.monitor_once(
                campaign_path=self.campaign,
                state_path=self.state,
                status_path=self.status,
                log_path=self.log,
                root=self.root,
                opener=FakeOpener(FakeResponse(self.html())),
            )
        os.chmod(self.state, 0o644)
        with self.assertRaisesRegex(ValueError, "private"):
            monitor.read_private_json(self.state)

    def test_status_summary_is_aggregate_only(self):
        self.run_once(self.html(comment("t1_rawreply", "t1_p9cgosi")))
        summary = monitor.status_summary(self.status)
        serialized = json.dumps(summary)
        self.assertTrue(summary["available"])
        self.assertFalse(summary["automatic_reply"])
        self.assertNotIn("fingerprint", serialized)
        self.assertNotIn("rawreply", serialized)
        self.assertNotIn(TARGET_URL, serialized)

    def test_loop_has_hourly_floor_single_lock_and_one_sleep_per_pass(self):
        with self.assertRaisesRegex(ValueError, "at least 60"):
            monitor.monitor_loop(59)
        lock = self.root / ".local" / "monitor.lock"
        with monitor.monitor_lock(lock):
            with self.assertRaisesRegex(RuntimeError, "already running"):
                with monitor.monitor_lock(lock):
                    pass
        with patch.object(monitor, "monitor_once", return_value={"available": True}) as once, patch.object(
            monitor.time, "sleep", side_effect=RuntimeError("stop")
        ) as sleep:
            with self.assertRaisesRegex(RuntimeError, "stop"):
                monitor.monitor_loop(60, lock_path=lock)
        once.assert_called_once_with()
        sleep.assert_called_once_with(3600)

    def test_wrapper_is_private_single_session_and_hourly(self):
        wrapper = monitor.ROOT / "scripts" / "reddit-reply-monitor.sh"
        text = wrapper.read_text(encoding="utf-8")
        self.assertIn("lazypromotion-reddit-reply-monitor", text)
        self.assertIn("REDDIT_REPLY_MONITOR_INTERVAL_MINUTES:-60", text)
        self.assertIn("INTERVAL_MINUTES < 60", text)
        self.assertIn('chmod 600 "$LOG"', text)


if __name__ == "__main__":
    unittest.main()
