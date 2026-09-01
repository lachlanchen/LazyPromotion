import json
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
