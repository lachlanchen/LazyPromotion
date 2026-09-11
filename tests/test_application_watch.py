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

    def test_submitted_state_and_nested_outreach_are_not_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_campaign(
                root,
                "multi.json",
                {
                    "id": "multi",
                    "source_need": {"url": "https://example.com/main"},
                    "application": {
                        "state": "submitted_awaiting_editorial_reply",
                        "submitted_at": "2026-09-01T00:00:00Z",
                        "review_after": "2026-09-20",
                    },
                    "additional_outreach": [
                        {
                            "source_url": "https://example.com/one",
                            "application_state": "sent_awaiting_reply",
                            "sent_at": "2026-09-03T00:00:00Z",
                        },
                        {
                            "source_url": "https://example.com/two",
                            "application_state": "prepared_not_submitted",
                            "sent_at": "2026-09-03T00:00:00Z",
                        },
                    ],
                },
            )

            report = application_watch.build_report(
                campaigns_dir=root,
                on=date(2026, 9, 10),
            )

        self.assertEqual(report["summary"]["awaiting_human_reply"], 2)
        nested, root_application = report["applications"]
        self.assertEqual(nested["campaign_id"], "multi:additional_outreach:1")
        self.assertEqual(nested["parent_campaign_id"], "multi")
        self.assertEqual(nested["review_after"], "2026-09-10")
        self.assertTrue(nested["due_for_human_review"])
        self.assertEqual(root_application["campaign_id"], "multi")
        self.assertEqual(root_application["review_after"], "2026-09-20")

    def test_current_campaigns_have_no_automatic_follow_up(self):
        report = application_watch.build_report(on=date(2026, 9, 9))
        self.assertEqual(report["summary"]["awaiting_human_reply"], 24)
        self.assertEqual(report["summary"]["missing_review_schedule"], 0)
        self.assertIn(
            "manicule-technical-writer-opportunity",
            [item["campaign_id"] for item in report["applications"]],
        )
        self.assertIn(
            "draftdev-cybersecurity-writer-opportunity",
            [item["campaign_id"] for item in report["applications"]],
        )
        self.assertIn(
            "webspecification-technical-writer-intern",
            [item["campaign_id"] for item in report["applications"]],
        )
        self.assertIn(
            "signoz-technical-writer-program",
            [item["campaign_id"] for item in report["applications"]],
        )
        self.assertIn(
            "buddy-devops-writer-program",
            [item["campaign_id"] for item in report["applications"]],
        )
        self.assertIn(
            "creality-functional-fdm-writer-pitch",
            [item["campaign_id"] for item in report["applications"]],
        )
        self.assertIn(
            "plesk-reverse-ssh-contributor-pitch",
            [item["campaign_id"] for item in report["applications"]],
        )
        self.assertEqual(
            len(
                [
                    item
                    for item in report["applications"]
                    if item.get("parent_campaign_id") == "content-repurposing-pilot"
                ]
            ),
            4,
        )
        for item in report["applications"]:
            self.assertFalse(item["due_for_human_review"])


if __name__ == "__main__":
    unittest.main()
