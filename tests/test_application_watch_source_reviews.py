import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest.mock import patch

import application_watch
import network
import promotion


class ApplicationSourceReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "graph.sqlite3"
        self.db = promotion.open_db(self.path)
        self.url = "https://example.test/paid-request/"
        network.upsert_entity(
            self.db, "review:one", kind="source_screen", label="PRIVATE LABEL",
            url=self.url, visibility="private",
            metadata={
                "state": "reviewed_no_new_signal", "checked_at": "2026-09-20T01:00:00Z",
                "next_routine_review_not_before": "2026-09-27T00:00:00Z",
                "decision": "No repeat without a relevant response",
                "evidence_file": ".local/private/synthetic-review.md",
                "email": "secret@example.test", "body": "PRIVATE CORRESPONDENCE",
            },
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def report(self, urls=None):
        urls = [self.url] if urls is None else urls
        return {
            "applications": [
                {"campaign_id": f"sample:{index}", "source_url": url,
                 "review_after": "2026-09-18", "due_for_human_review": True}
                for index, url in enumerate(urls)
            ],
            "summary": {"awaiting_human_reply": len(urls), "due_for_human_review": len(urls)},
            "policy": {"automatic_follow_up": False},
        }

    def test_adds_later_context_without_mutating_report_dates_or_database(self):
        report = self.report()
        before = deepcopy(report)
        db_bytes = self.path.read_bytes()
        result = application_watch.attach_source_reviews(report, db_path=self.path)
        self.assertEqual(report, before)
        self.assertEqual(result["summary"], report["summary"])
        item = result["applications"][0]
        self.assertTrue(item["due_for_human_review"])
        self.assertEqual(item["review_after"], "2026-09-18")
        context = item["stored_source_review"]
        self.assertEqual(context["state"], "recorded")
        self.assertEqual(context["matches"][0]["screening"]["next_routine_review_not_before"],
                         "2026-09-27T00:00:00Z")
        self.assertEqual(db_bytes, self.path.read_bytes())
        self.assertTrue(result["private_context"])
        self.assertFalse(result["source_review_policy"]["provider_checked"])
        self.assertFalse(result["source_review_policy"]["automatic_follow_up"])

    def test_omits_correspondence_and_labels_using_existing_projection(self):
        result = application_watch.attach_source_reviews(self.report(), db_path=self.path)
        serialized = json.dumps(result)
        for secret in ("PRIVATE LABEL", "PRIVATE CORRESPONDENCE", "secret@example.test"):
            self.assertNotIn(secret, serialized)
        self.assertIn(".local/private/synthetic-review.md", serialized)
        self.assertIn("must not be committed", serialized)

    def test_unknown_missing_invalid_and_tracking_variant_are_explicit(self):
        report = self.report([
            "https://EXAMPLE.test/paid-request/?utm_source=campaign",
            "https://example.test/unknown", "", "/relative",
        ])
        result = application_watch.attach_source_reviews(report, db_path=self.path)
        self.assertEqual(
            [item["stored_source_review"]["state"] for item in result["applications"]],
            ["recorded", "not_recorded", "source_url_missing", "source_url_invalid"],
        )
        for item in result["applications"]:
            self.assertNotIn("eligible", item["stored_source_review"])

    def test_conflicts_and_unreadable_metadata_are_not_silently_resolved(self):
        network.upsert_entity(self.db, "review:other", kind="source_screen", label="Other",
                              url=self.url, metadata={"decision": "Different decision"})
        self.db.execute("UPDATE entities SET metadata_json='not-json' WHERE id='review:one'")
        self.db.commit()
        result = application_watch.attach_source_reviews(self.report(), db_path=self.path)
        matches = result["applications"][0]["stored_source_review"]["matches"]
        self.assertEqual(len(matches), 2)
        self.assertEqual({item["metadata_state"] for item in matches}, {"available", "unreadable"})

    def test_batches_more_than_twenty_and_keeps_duplicate_applications_distinct(self):
        urls = [f"https://example.test/jobs/{index}" for index in range(24)]
        urls.extend([self.url, self.url])
        report = self.report(urls)
        report["applications"][-1]["parent_campaign_id"] = "parent"
        with patch.object(network, "lookup_sources", wraps=network.lookup_sources) as lookup:
            result = application_watch.attach_source_reviews(report, db_path=self.path)
        self.assertEqual([len(call.args[1]) for call in lookup.call_args_list], [20, 5])
        self.assertEqual(len(result["applications"]), 26)
        self.assertEqual(result["applications"][-1]["parent_campaign_id"], "parent")
        self.assertNotEqual(result["applications"][-1]["campaign_id"],
                            result["applications"][-2]["campaign_id"])
        self.assertEqual(result["applications"][-1]["stored_source_review"],
                         result["applications"][-2]["stored_source_review"])

    def test_missing_or_wrong_schema_fails_without_creating_database(self):
        missing = Path(self.tmp.name) / "missing.sqlite3"
        with self.assertRaises(sqlite3.Error):
            application_watch.attach_source_reviews(self.report(), db_path=missing)
        self.assertFalse(missing.exists())
        empty = Path(self.tmp.name) / "empty.sqlite3"
        connection = sqlite3.connect(empty)
        connection.close()
        before = empty.read_bytes()
        with self.assertRaises(sqlite3.Error):
            application_watch.attach_source_reviews(self.report(), db_path=empty)
        self.assertEqual(empty.read_bytes(), before)

    def test_default_report_does_not_access_private_graph(self):
        with patch.object(sqlite3, "connect", side_effect=AssertionError("No graph read")):
            result = application_watch.build_report(on=date(2026, 9, 20))
        self.assertNotIn("private_context", result)
        self.assertTrue(all("stored_source_review" not in item for item in result["applications"]))

    def test_cli_is_opt_in_and_fails_closed_for_missing_database(self):
        command = [sys.executable, str(application_watch.ROOT / "application_watch.py"),
                   "--on", "2026-09-20"]
        default = subprocess.run(command, capture_output=True, text=True, check=True)
        enriched = subprocess.run(command + ["--with-source-reviews", "--db", str(self.path)],
                                  capture_output=True, text=True, check=True)
        self.assertNotIn("private_context", json.loads(default.stdout))
        self.assertEqual(json.loads(default.stdout)["summary"], json.loads(enriched.stdout)["summary"])
        self.assertTrue(json.loads(enriched.stdout)["private_context"])
        missing = Path(self.tmp.name) / "not-created.sqlite3"
        failed = subprocess.run(command + ["--with-source-reviews", "--db", str(missing)],
                                capture_output=True, text=True)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(failed.stdout, "")
        self.assertFalse(missing.exists())
        ignored_db = subprocess.run(command + ["--db", str(self.path)], capture_output=True, text=True)
        self.assertNotEqual(ignored_db.returncode, 0)
        self.assertIn("requires --with-source-reviews", ignored_db.stderr)


if __name__ == "__main__":
    unittest.main()
