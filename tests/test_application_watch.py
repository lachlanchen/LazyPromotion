import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import application_watch


class ApplicationWatchTests(unittest.TestCase):
    def write_campaign(self, root: Path, name: str, payload: dict) -> None:
        (root / name).write_text(json.dumps(payload), encoding="utf-8")

    def test_normalizes_explicit_and_default_review_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_campaign(
                root,
                "explicit.json",
                {
                    "id": "explicit",
                    "source_need": {"url": "https://example.com/role"},
                    "application": {
                        "state": "sent_awaiting_human_reply",
                        "sent_at": "2026-09-01T12:00:00Z",
                        "review_after": "2026-09-10",
                        "automatic_follow_up": False,
                    },
                },
            )
            self.write_campaign(
                root,
                "default.json",
                {
                    "id": "default",
                    "application": {
                        "state": "sent_awaiting_reply",
                        "sent_at": "2026-09-04T12:00:00Z",
                        "automatic_follow_up": False,
                    },
                },
            )
            self.write_campaign(
                root,
                "draft.json",
                {"id": "draft", "application": {"state": "prepared_not_sent"}},
            )

            report = application_watch.build_report(
                campaigns_dir=root,
                on=date(2026, 9, 10),
            )

        self.assertEqual(
            [item["campaign_id"] for item in report["applications"]],
            ["explicit", "default"],
        )
        explicit, default = report["applications"]
        self.assertEqual(explicit["review_after"], "2026-09-10")
        self.assertEqual(explicit["schedule_source"], "campaign")
        self.assertTrue(explicit["due_for_human_review"])
        self.assertEqual(default["review_after"], "2026-09-11")
        self.assertEqual(default["schedule_source"], "default_7_days_after_sent")
        self.assertFalse(default["due_for_human_review"])
        self.assertFalse(report["policy"]["automatic_follow_up"])
        self.assertTrue(report["policy"]["application_is_not_a_lead"])

    def test_reports_missing_schedule_without_inventing_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_campaign(
                root,
                "missing.json",
                {
                    "id": "missing",
                    "application": {
                        "state": "email_fallback_sent_awaiting_human_reply"
                    },
                },
            )
            report = application_watch.build_report(
                campaigns_dir=root,
                on=date(2026, 9, 10),
            )

        self.assertIsNone(report["applications"][0]["review_after"])
        self.assertEqual(report["summary"]["missing_review_schedule"], 1)
        self.assertFalse(report["applications"][0]["due_for_human_review"])

    def test_current_campaigns_have_no_automatic_follow_up(self):
        report = application_watch.build_report(on=date(2026, 9, 9))
        self.assertGreaterEqual(report["summary"]["awaiting_human_reply"], 8)
        self.assertEqual(report["summary"]["missing_review_schedule"], 0)
        self.assertIn(
            "manicule-technical-writer-opportunity",
            [item["campaign_id"] for item in report["applications"]],
        )
        for item in report["applications"]:
            self.assertFalse(item["due_for_human_review"])


if __name__ == "__main__":
    unittest.main()
