import json
import unittest
from datetime import date
from pathlib import Path

import application_watch

CAMPAIGN = Path(__file__).resolve().parents[1] / "campaigns/wordpress-teaching-site-updates.json"


class WordPressTeachingUpdatesTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(CAMPAIGN.read_text())

    def test_solicited_email_is_not_a_contract_or_sale(self):
        self.assertIn("Apply via Email", self.payload["source_need"]["application_invitation"])
        self.assertEqual(self.payload["application"]["submission_count"], 1)
        self.assertTrue(self.payload["application"]["sent_folder_verified"])
        self.assertFalse(self.payload["application"]["automatic_follow_up"])
        self.assertEqual(self.payload["application"]["attachment_count"], 0)
        self.assertEqual(self.payload["application"]["submission_fee_usd"], 0)
        funnel = self.payload["funnel"]
        for key in ("buyer_reply_observed", "qualified_lead_observed", "scope_accepted", "payment_confirmed", "delivered"):
            self.assertFalse(funnel[key])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_first_pass_preserves_scope_and_recurring_support_boundary(self):
        gates = " ".join(self.payload["scope_gate"])
        for text in ("before quoting", "fixed first-pass", "staging", "recoverable backup", "release approval", "No recurring support", "malware recovery"):
            self.assertIn(text, gates)
        self.assertIn("AI-assisted", self.payload["application"]["development_method_disclosed"])
        self.assertIn("Not stated", self.payload["source_need"]["budget"])

    def test_public_record_has_no_private_message_or_contact(self):
        serialized = CAMPAIGN.read_text().casefold()
        for forbidden in ("@samplecraze.com", "@lazying.art", "@icloud.com", "hi eddie", "cookie", "body_sha256"):
            self.assertNotIn(forbidden, serialized)

    def test_watch_uses_the_recorded_review_date(self):
        record = application_watch.application_record(self.payload, source_file=CAMPAIGN, on=date(2026, 9, 20))
        self.assertEqual(record["review_after"], "2026-09-27")
        self.assertFalse(record["due_for_human_review"])


if __name__ == "__main__":
    unittest.main()
