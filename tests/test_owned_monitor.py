import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import owned_monitor


class FakePostiz:
    def __init__(
        self,
        *,
        posts,
        post_metrics=None,
        platform_metrics=None,
        integrations=None,
    ):
        self.posts = posts
        self.post_metrics = list(post_metrics or [])
        self.platform_metrics = platform_metrics or []
        self.integrations = integrations or [
            {"id": "private-integration", "identifier": "x"}
        ]
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
            return self.result(self.integrations)
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

    def test_metric_snapshot_normalizes_postiz_numeric_strings(self):
        snapshot = owned_monitor.metric_snapshot(
            [
                {"label": "Impressions", "data": [{"date": "2026-09-05", "total": "1,234"}]},
                {"label": "Watch percentage", "data": [{"date": "2026-09-05", "total": "108.26"}]},
                {"label": "Unavailable", "data": [{"date": "2026-09-05", "total": "N/A"}]},
                {"label": "Boolean", "data": [{"date": "2026-09-05", "total": True}]},
            ]
        )

        self.assertEqual(snapshot["Impressions"]["latest"], 1234)
        self.assertEqual(snapshot["Watch percentage"]["latest"], 108.26)
        self.assertIsNone(snapshot["Unavailable"]["latest"])
        self.assertIsNone(snapshot["Boolean"]["latest"])

    def test_string_reply_metric_still_creates_review_alert(self):
        published = post(state="PUBLISHED")
        published["releaseURL"] = "https://x.com/lazyingart/status/123"
        fake = FakePostiz(
            posts=[published],
            post_metrics=[
                [{"label": "Replies", "data": [{"date": "2026-09-05", "total": "1"}]}]
            ],
        )

        report = self.run_monitor(fake)

        self.assertEqual(report["posts"][0]["replies"], 1)
        self.assertEqual(report["alerts"][0]["kind"], "engagement_increased")
        self.assertIn("do not reply automatically", report["alerts"][0]["action"])

    def test_recorded_owned_reply_is_not_external_engagement(self):
        campaign = json.loads(
            (owned_monitor.CAMPAIGNS / "local-knowledge-terminal-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        sample = campaign["channels"]["x"]["sample_report_post"]
        published = post(state="PUBLISHED")
        published["content"] = sample["postiz_content"]
        published["releaseURL"] = sample["url"]
        first = FakePostiz(
            posts=[published],
            post_metrics=[
                [{"label": "Replies", "data": [{"date": "2026-09-05", "total": "1"}]}]
            ],
        )

        report = self.run_monitor(first)

        observed = report["posts"][0]
        self.assertEqual(observed["provider_replies"], 1)
        self.assertEqual(observed["known_owned_replies"], 1)
        self.assertEqual(observed["replies"], 0)
        self.assertEqual(report["alerts"], [])

        second = FakePostiz(
            posts=[published],
            post_metrics=[
                [{"label": "Replies", "data": [{"date": "2026-09-05", "total": "2"}]}]
            ],
        )
        report = self.run_monitor(second)
        alert = report["alerts"][0]
        self.assertEqual(alert["provider_replies"], 2)
        self.assertEqual(alert["known_owned_replies"], 1)
        self.assertEqual(alert["replies"], 1)
        self.assertEqual(alert["reply_delta"], 1)

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
        fake = FakePostiz(posts=[post(publish_at="2026-08-31T23:00:00Z")])
        report = self.run_monitor(fake)
        self.assertEqual(report["alerts"][0]["kind"], "publication_overdue")
        self.assertIn("do not resubmit", report["alerts"][0]["action"])

    def test_missing_release_requires_explicit_connection_review(self):
        missing = post(state="PUBLISHED")
        missing["releaseId"] = "missing"
        fake = FakePostiz(posts=[missing], post_metrics=[{"missing": True}])
        report = self.run_monitor(fake)
        self.assertEqual(report["alerts"][0]["kind"], "release_connection_required")
        self.assertTrue(report["posts"][0]["needs_release_connection"])

    def test_queue_to_published_requires_visible_release_verification(self):
        queued = FakePostiz(posts=[post()])
        self.run_monitor(queued)

        published = post(state="PUBLISHED")
        published["releaseURL"] = "https://x.com/lazyingart/status/456"
        current = FakePostiz(posts=[published], post_metrics=[[]])
        report = self.run_monitor(current)
        alert = next(
            item for item in report["alerts"] if item["kind"] == "publication_observed"
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

    def test_existing_latex_queue_keeps_its_original_campaign_route(self):
        campaign = json.loads(
            (owned_monitor.CAMPAIGNS / "latex-redline-build.json").read_text(
                encoding="utf-8"
            )
        )
        content = campaign["channels"]["x"]["postiz_content"]
        route = owned_monitor.route_for_post("x", content, owned_monitor.route_index())
        self.assertEqual(route["campaign_id"], "latex-redline-build")
        self.assertEqual(route["route"], "product")

    def test_route_index_accepts_original_postiz_copy_after_public_link_repair(self):
        campaign = json.loads(
            (owned_monitor.CAMPAIGNS / "local-knowledge-terminal-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        guide = campaign["channels"]["reddit"]["profile_guide"]
        self.assertNotEqual(guide["content"], guide["postiz_content"])
        route = owned_monitor.route_for_post(
            "reddit", guide["postiz_content"], owned_monitor.route_index()
        )
        self.assertEqual(route["campaign_id"], "local-knowledge-terminal-pilot")
        self.assertEqual(route["route"], "profile_guide")

    def test_lecture_archive_queue_matches_verified_owned_route(self):
        campaign = json.loads(
            (owned_monitor.CAMPAIGNS / "lecture-archive-provenance.json").read_text(
                encoding="utf-8"
            )
        )
        channel = campaign["channels"]["x"]
        self.assertEqual(channel["content"], channel["postiz_content"])
        self.assertIn("blog.lazying.art/?p=3167", channel["postiz_content"])
        self.assertIn("utm_campaign=lecture_archive", channel["destination"])
        self.assertIn("two superseded unpublished drafts", channel["repair"]["outcome"])
        route = owned_monitor.route_for_post(
            "x", channel["postiz_content"], owned_monitor.route_index()
        )
        self.assertEqual(route["campaign_id"], "lecture-archive-provenance")
        self.assertEqual(route["route"], "product")

    def test_bilingual_lecture_pack_queue_keeps_protocol_less_destination(self):
        campaign = json.loads(
            (owned_monitor.CAMPAIGNS / "bilingual-lecture-pack-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        sample = campaign["source_evidence"]["executed_media_sample"]
        self.assertIn("LalaMedias/videos/", sample["url"])
        self.assertIn("45 searchable strings", "\n".join(sample["verified_outputs"]))
        self.assertIn("not an automated LKT import", sample["claim_boundary"])
        channel = campaign["channels"]["x"]
        self.assertEqual(channel["state"], "postiz_published")
        self.assertEqual(
            channel["content_sha256"],
            "e42b66d1e4601b115a409fed4ac885359aab2005183c2c5ce7e34eb2bdc8d7bd",
        )
        self.assertIn("x.com/lazyingart/status/", channel["release_url"])
        self.assertTrue(channel["visible_review"]["stored_text_exact"])
        self.assertTrue(channel["visible_review"]["tracked_destination_preserved"])
        self.assertIn("lazying.art/lecture-pack/", channel["postiz_content"])
        self.assertNotIn("https://", channel["postiz_content"])
        route = owned_monitor.route_for_post(
            "x", channel["postiz_content"], owned_monitor.route_index()
        )
        self.assertEqual(route["campaign_id"], "bilingual-lecture-pack-pilot")
        self.assertEqual(route["route"], "product")

        instagram = campaign["channels"]["instagram"]
        self.assertEqual(instagram["state"], "postiz_queue")
        self.assertEqual(instagram["settings"]["post_type"], "post")
        self.assertEqual(64, len(instagram["media_sha256"]))
        self.assertEqual(
            owned_monitor.content_hash(instagram["postiz_content"]),
            "b92c0a7394e46c421d8cd5bb738da489d80824b6dba763d83fa653956f013924",
        )
        self.assertTrue(instagram["visible_review"]["stored_text_exact"])
        instagram_route = owned_monitor.route_for_post(
            "instagram-standalone",
            instagram["postiz_content"],
            owned_monitor.route_index(),
        )
        self.assertEqual(instagram_route["campaign_id"], "bilingual-lecture-pack-pilot")
        self.assertEqual(instagram_route["route"], "product")

        linkedin = campaign["channels"]["linkedin"]
        self.assertEqual(linkedin["state"], "postiz_queue")
        self.assertEqual(linkedin["publish_at"], "2026-09-15T02:00:00Z")
        self.assertFalse(linkedin["shortlink"])
        self.assertEqual(
            owned_monitor.content_hash(linkedin["postiz_content"]),
            "bed12b3e8c3e93752ba9fd1cb475bc181b34180276445798f2fb7e5147ca7c17",
        )
        linkedin_route = owned_monitor.route_for_post(
            "linkedin", linkedin["postiz_content"], owned_monitor.route_index()
        )
        self.assertEqual(linkedin_route["campaign_id"], "bilingual-lecture-pack-pilot")
        self.assertEqual(linkedin_route["route"], "product")

        practical_guide = linkedin["practical_guide"]
        guide_route = owned_monitor.route_for_post(
            "linkedin", practical_guide["postiz_content"], owned_monitor.route_index()
        )
        self.assertEqual(guide_route["campaign_id"], "bilingual-lecture-pack-pilot")
        self.assertEqual(guide_route["route"], "practical_guide")

        youtube = campaign["channels"]["youtube"]
        self.assertEqual(youtube["state"], "postiz_published")
        self.assertEqual(youtube["content"], youtube["postiz_content"])
        self.assertEqual(
            owned_monitor.content_hash(youtube["postiz_content"]),
            "ca984ae13b5b96f459f792dc39b0d726872abc3a09e0a55347d9cb708df25198",
        )
        self.assertEqual(
            youtube["content_sha256"],
            "ca984ae13b5b96f459f792dc39b0d726872abc3a09e0a55347d9cb708df25198",
        )
        self.assertIn("youtube.com/watch?v=", youtube["release_url"])
        self.assertEqual(youtube["review"]["stored_state"], "PUBLISHED")
        self.assertTrue(youtube["review"]["release_present"])
        self.assertEqual(youtube["analytics_observation"]["views"], 21)
        self.assertEqual(youtube["analytics_observation"]["comments"], 0)
        self.assertFalse(youtube["analytics_observation"]["lead_or_sale_observed"])
        youtube_route = owned_monitor.route_for_post(
            "youtube", youtube["postiz_content"], owned_monitor.route_index()
        )
        self.assertEqual(youtube_route["campaign_id"], "bilingual-lecture-pack-pilot")
        self.assertEqual(youtube_route["route"], "product")

    def test_live_sample_report_posts_match_the_lkt_campaign(self):
        campaign = json.loads(
            (owned_monitor.CAMPAIGNS / "local-knowledge-terminal-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        routes = owned_monitor.route_index()
        x_post = campaign["channels"]["x"]["sample_report_post"]
        x_route = owned_monitor.route_for_post("x", x_post["postiz_content"], routes)
        self.assertEqual(x_route["campaign_id"], "local-knowledge-terminal-pilot")
        self.assertEqual(x_route["route"], "sample_report_post")
        self.assertEqual(x_route["known_owned_replies"], 1)

        instagram_post = campaign["channels"]["instagram"]["sample_report_post"]
        instagram_route = owned_monitor.route_for_post(
            "instagram-standalone", instagram_post["content"], routes
        )
        self.assertEqual(
            instagram_route["campaign_id"], "local-knowledge-terminal-pilot"
        )
        self.assertEqual(instagram_route["route"], "sample_report_post")

    def test_linkedin_post_is_observed_and_matches_reviewed_campaign_route(self):
        campaign = json.loads(
            (owned_monitor.CAMPAIGNS / "local-knowledge-terminal-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        content = campaign["channels"]["linkedin"]["passage_provenance_post"]["content"]
        linkedin_post = post(
            post_id="private-linkedin-post",
            publish_at="2026-09-18T02:00:00Z",
        )
        linkedin_post["content"] = content
        linkedin_post["integration"] = {"providerIdentifier": "linkedin"}
        fake = FakePostiz(
            posts=[linkedin_post],
            integrations=[
                {"id": "private-linkedin-integration", "identifier": "linkedin"}
            ],
        )

        report = self.run_monitor(fake)

        self.assertEqual(report["summary"]["queued"], 1)
        self.assertEqual(report["posts"][0]["provider"], "linkedin")
        self.assertEqual(
            report["posts"][0]["campaign_id"], "local-knowledge-terminal-pilot"
        )
        self.assertEqual(report["posts"][0]["route"], "passage_provenance_post")
        serialized = json.dumps(report)
        self.assertNotIn("private-linkedin-post", serialized)
        self.assertNotIn("private-linkedin-integration", serialized)

    def test_linkedin_collection_fit_offer_is_an_owned_queue_not_a_sale(self):
        campaign = json.loads(
            (owned_monitor.CAMPAIGNS / "local-knowledge-terminal-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        offer = campaign["channels"]["linkedin"]["collection_fit_offer_post"]
        linkedin_post = post(
            post_id="private-linkedin-offer-post",
            publish_at=offer["publish_at"],
        )
        linkedin_post["content"] = offer["postiz_content"]
        linkedin_post["integration"] = {"providerIdentifier": "linkedin"}
        fake = FakePostiz(
            posts=[linkedin_post],
            integrations=[
                {"id": "private-linkedin-integration", "identifier": "linkedin"}
            ],
        )

        report = self.run_monitor(fake)

        self.assertEqual(report["summary"]["queued"], 1)
        self.assertEqual(report["posts"][0]["campaign_id"], "local-knowledge-terminal-pilot")
        self.assertEqual(report["posts"][0]["route"], "collection_fit_offer_post")
        self.assertNotIn("revenue", report["posts"][0])
        serialized = json.dumps(report)
        self.assertNotIn("private-linkedin-offer-post", serialized)
        self.assertNotIn("private-linkedin-integration", serialized)


if __name__ == "__main__":
    unittest.main()
