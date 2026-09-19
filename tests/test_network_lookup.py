import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import network
import promotion


class ScreeningLookupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "screen.sqlite3"
        self.db = promotion.open_db(self.path)
        network.upsert_entity(
            self.db, "screen:example", kind="paid_need_screen", label="Private label",
            url="https://example.test/jobs/123/", visibility="private",
            metadata={"decision": "defer_unbounded_ongoing_work", "checked_on": "2026-09-20",
                      "next_trigger": "Changed scope or a relevant invitation",
                      "customer_email": "private@example.test", "body": "private correspondence"},
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_returns_prior_decision_without_private_message_fields(self):
        result = network.lookup_sources(self.db, ["https://example.test/jobs/123/"])
        match = result["sources"][0]["matches"][0]
        self.assertEqual(match["screening"]["decision"], "defer_unbounded_ongoing_work")
        self.assertEqual(match["visibility"], "private")
        self.assertTrue(result["private_context"])
        self.assertNotIn("private@example.test", json.dumps(result))
        self.assertNotIn("private correspondence", json.dumps(result))
        self.assertNotIn("Private label", json.dumps(result))

    def test_lookup_does_not_change_entities_or_timestamps(self):
        before = list(self.db.iterdump())
        changes = self.db.total_changes
        network.lookup_sources(self.db, ["https://example.test/jobs/123/"])
        self.assertEqual(changes, self.db.total_changes)
        self.assertEqual(before, list(self.db.iterdump()))

    def test_tracking_only_variant_matches(self):
        result = network.lookup_sources(self.db, ["https://EXAMPLE.test/jobs/123/?utm_source=search&utm_campaign=test"])
        self.assertEqual(result["sources"][0]["state"], "recorded")

    def test_meaningful_queries_fragments_paths_and_schemes_remain_distinct(self):
        for url in (
            "https://example.test/jobs/123/?id=4", "https://example.test/jobs/123/#reply-1",
            "https://example.test/jobs/123", "http://example.test/jobs/123/",
            "https://example.test/Jobs/123/",
        ):
            with self.subTest(url=url):
                result = network.lookup_sources(self.db, [url])
                self.assertEqual(result["sources"][0]["state"], "not_recorded")

    def test_unknown_is_not_an_eligibility_decision(self):
        result = network.lookup_sources(self.db, ["https://example.test/new"])
        self.assertEqual(result["sources"][0]["matches"], [])
        self.assertNotIn("eligible", result["sources"][0])
        self.assertIn("not eligibility", result["notice"])

    def test_preserves_all_matches_without_resolving_conflicting_decisions(self):
        network.upsert_entity(
            self.db, "screen:second", kind="paid_need_screen", label="Second",
            url="https://example.test/jobs/123/", visibility="private",
            metadata={"decision": "application_already_sent"},
        )
        result = network.lookup_sources(self.db, ["https://example.test/jobs/123/"])
        matches = result["sources"][0]["matches"]
        self.assertEqual(len(matches), 2)
        self.assertEqual({item["screening"]["decision"] for item in matches},
                         {"defer_unbounded_ongoing_work", "application_already_sent"})

    def test_query_identity_is_not_discarded(self):
        one = network.screening_url_key("https://example.test/view?id=1&part=2")
        two = network.screening_url_key("https://example.test/view?id=2&part=2")
        self.assertNotEqual(one, two)
        self.assertNotEqual(one, network.screening_url_key("https://example.test/view?id=1&id=2&part=2"))

    def test_rejects_invalid_or_credential_urls_and_batch_sizes(self):
        for url in ("file:///tmp/private", "https://user:pass@example.test/", "/relative",
                    "https://example.test:bad/", "https://example.test/a b"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                network.lookup_sources(self.db, [url])
        for urls in ([], ["https://example.test/"] * 21):
            with self.assertRaises(ValueError):
                network.lookup_sources(self.db, urls)

    def test_bad_stored_url_or_metadata_does_not_become_no_match(self):
        self.db.execute("UPDATE entities SET metadata_json='not-json' WHERE id='screen:example'")
        network.upsert_entity(self.db, "screen:bad", kind="test", label="Bad URL", url="not-a-url")
        result = network.lookup_sources(self.db, ["https://example.test/jobs/123/"])
        match = result["sources"][0]["matches"][0]
        self.assertEqual(match["metadata_state"], "unreadable")
        self.assertEqual(match["screening"], {})

    def test_cli_is_read_only_and_missing_database_is_not_created(self):
        before = self.path.read_bytes()
        command = [sys.executable, str(network.ROOT / "network.py"), "lookup",
                   "https://example.test/jobs/123/", "--db", str(self.path)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["sources"][0]["state"], "recorded")
        self.assertEqual(before, self.path.read_bytes())
        missing = Path(self.tmp.name) / "missing.sqlite3"
        result = subprocess.run(command[:-1] + [str(missing)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
