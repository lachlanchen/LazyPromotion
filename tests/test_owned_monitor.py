import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import owned_monitor


class FakePostiz:
    def __init__(self, *, posts, post_metrics=None, platform_metrics=None):
        self.posts = posts
        self.post_metrics = list(post_metrics or [])
        self.platform_metrics = platform_metrics or []
        self.commands = []

    @staticmethod
    def result(payload="", returncode=0):
        if not isinstance(payload, str):
            payload = "result\n" + json.dumps(payload)
        return SimpleNamespace(returncode=returncode, stdout=payload, stderr="")

    def __call__(self, command):
        self.commands.append(command)
        action = command[1]
        if action == "auth:status":
            return self.result("Credentials are valid. 1 integration connected.")
        if action == "integrations:list":
            return self.result(
                [{"id": "private-integration", "identifier": "x"}]
            )
        if action == "posts:list":
            return self.result({"posts": self.posts})
        if action == "analytics:platform":
            return self.result(self.platform_metrics)
        if action == "analytics:post":
            return self.result(self.post_metrics.pop(0))
        raise AssertionError(command)


def post(*, state="QUEUE", post_id="private-post", publish_at="2026-09-08T01:00:00Z"):
    return {
        "id": post_id,
        "content": "<p>A useful owned post</p>",
        "publishDate": publish_at,
        "releaseURL": None,
        "releaseId": None,
        "state": state,
        "integration": {"providerIdentifier": "x"},
    }


class OwnedMonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "monitor.sqlite3"
        self.status_path = self.root / "status.json"
        self.now = datetime(2026, 9, 1, 1, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.tmp.cleanup()

    def run_monitor(self, fake):
        return owned_monitor.monitor_once(
            db_path=self.db_path,
            status_path=self.status_path,
            runner=fake,
            now=self.now,
        )

    def test_queued_post_stays_read_only_and_ids_are_not_persisted(self):
        fake = FakePostiz(posts=[post()])
        report = self.run_monitor(fake)
        self.assertEqual(report["summary"]["queued"], 1)
        self.assertEqual(report["alerts"], [])
        self.assertFalse(any(c[1] == "analytics:post" for c in fake.commands))
        serialized = json.dumps(report)
        self.assertNotIn("private-post", serialized)
        self.assertNotIn("private-integration", serialized)
        database = self.db_path.read_bytes()
        self.assertNotIn(b"private-post", database)
        self.assertNotIn(b"private-integration", database)

    def test_comment_increase_becomes_review_alert_not_lead(self):
        published = post(state="PUBLISHED")
        published["releaseURL"] = "https://x.com/lazyingart/status/123"
        first = FakePostiz(
            posts=[published],
            post_metrics=[
                [{"label": "Comments", "data": [{"date": "2026-09-01", "total": 1}]}]
            ],
        )
        report = self.run_monitor(first)
        self.assertEqual(report["alerts"][0]["kind"], "engagement_increased")
        self.assertNotIn("lead", report["alerts"][0]["kind"])

        second = FakePostiz(
            posts=[published],
            post_metrics=[
                [
                    {"label": "Comments", "data": [{"date": "2026-09-01", "total": 2}]},
                    {"label": "Replies", "data": [{"date": "2026-09-01", "total": 1}]},
                ]
            ],
        )
        report = self.run_monitor(second)
        alert = report["alerts"][0]
        self.assertEqual(alert["comment_delta"], 1)
        self.assertEqual(alert["reply_delta"], 1)
        self.assertIn("visible browser", alert["action"])
        self.assertTrue(report["policy"]["engagement_is_not_a_lead"])
        self.assertFalse(report["policy"]["automatic_public_reply"])

    def test_overdue_queue_requires_review_without_retry(self):
        fake = FakePostiz(
            posts=[post(publish_at="2026-08-31T23:00:00Z")]
        )
        report = self.run_monitor(fake)
        self.assertEqual(report["alerts"][0]["kind"], "publication_overdue")
        self.assertIn("do not resubmit", report["alerts"][0]["action"])

    def test_missing_release_requires_explicit_connection_review(self):
        missing = post(state="PUBLISHED")
        missing["releaseId"] = "missing"
        fake = FakePostiz(posts=[missing], post_metrics=[{"missing": True}])
        report = self.run_monitor(fake)
        self.assertEqual(
            report["alerts"][0]["kind"], "release_connection_required"
        )
        self.assertTrue(report["posts"][0]["needs_release_connection"])

    def test_queue_to_published_requires_visible_release_verification(self):
        queued = FakePostiz(posts=[post()])
        self.run_monitor(queued)

        published = post(state="PUBLISHED")
        published["releaseURL"] = "https://x.com/lazyingart/status/456"
        current = FakePostiz(posts=[published], post_metrics=[[]])
        report = self.run_monitor(current)
        alert = next(
            item for item in report["alerts"]
            if item["kind"] == "publication_observed"
        )
        self.assertEqual(alert["release_url"], published["releaseURL"])
        self.assertIn("visible browser", alert["action"])
        self.assertNotIn("private-post", json.dumps(report))

    def test_published_without_release_url_is_not_delivery_proof(self):
        published = post(state="PUBLISHED")
        published["releaseId"] = "provider-release"
        fake = FakePostiz(posts=[published], post_metrics=[[]])
        report = self.run_monitor(fake)
        alert = next(
            item for item in report["alerts"] if item["kind"] == "release_url_missing"
        )
        self.assertIn("do not reconnect or resubmit", alert["action"])

    def test_campaign_routes_match_postiz_html_without_private_ids(self):
        campaign = json.loads(
            (owned_monitor.CAMPAIGNS / "local-knowledge-terminal-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        content = campaign["channels"]["x"]["content"]
        route = owned_monitor.route_for_post(
            "x", f"<p>{content}</p>", owned_monitor.route_index()
        )
        self.assertEqual(route["campaign_id"], "local-knowledge-terminal-pilot")
        self.assertEqual(route["route"], "product")


if __name__ == "__main__":
    unittest.main()
