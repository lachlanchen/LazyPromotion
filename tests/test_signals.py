import json
import tempfile
import unittest
from pathlib import Path

import network
import promotion
import signals


class DemandSignalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = promotion.open_db(Path(self.tmp.name) / "signals.sqlite3")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def payload(self):
        return {
            "version": 1,
            "source": "google_search_console",
            "period": "last_28_days_ending_2026-08-31",
            "observed_at": "2026-08-31T14:30:00Z",
            "evidence_path": ".local/evidence/search-console.png",
            "signals": [
                {
                    "signal_kind": "content",
                    "subject": "Classical Mechanics Reader",
                    "url": "https://learn.lazying.art/leonardsusskind-reader.html",
                    "project_id": "leonardsusskind",
                    "metric": "clicks",
                    "value": 22,
                    "delta_value": 47,
                    "delta_unit": "percent",
                }
            ],
        }

    def test_import_is_idempotent_and_report_does_not_call_clicks_sales(self):
        first = signals.import_payload(self.db, self.payload())
        second = signals.import_payload(self.db, self.payload())
        self.assertEqual(first["ids"], second["ids"])
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM demand_signals").fetchone()[0], 1
        )
        report = signals.signal_report(self.db)
        self.assertEqual(report["signals"], 1)
        self.assertIn("not a lead", report["interpretation_guard"])

    def test_private_signal_links_to_project_but_never_enters_public_export(self):
        signals.import_payload(self.db, self.payload())
        network.sync_graph(self.db)
        link = self.db.execute(
            """
            SELECT 1 FROM relationships
            WHERE source_id LIKE 'signal:%'
              AND relation='indicates_interest_in'
              AND target_id='project:leonardsusskind'
            """
        ).fetchone()
        self.assertIsNotNone(link)
        snapshot = json.dumps(network.public_snapshot(self.db), ensure_ascii=False)
        self.assertNotIn("Classical Mechanics Reader", snapshot)
        self.assertNotIn("google_search_console", snapshot)

    def test_rejects_unsafe_evidence_path_and_unknown_project(self):
        payload = self.payload()
        payload["evidence_path"] = "../private.png"
        with self.assertRaisesRegex(ValueError, "evidence_path"):
            signals.import_payload(self.db, payload)

        payload = self.payload()
        payload["signals"][0]["project_id"] = "not-a-project"
        with self.assertRaisesRegex(ValueError, "unknown project"):
            signals.import_payload(self.db, payload)


if __name__ == "__main__":
    unittest.main()
