import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BountyAgentMarketplaceCampaignTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "campaigns" / "bounty-agent-marketplace.json"
        self.serialized = self.path.read_text(encoding="utf-8")
        self.campaign = json.loads(self.serialized)

    def test_account_and_read_only_route_are_recorded_without_private_values(self):
        self.assertEqual(self.campaign["account"]["state"], "registered_email_verified")
        api = self.campaign["api"]
        self.assertEqual(api["state"], "authenticated_read_only")
        self.assertEqual(api["last_http_status"], 200)
        self.assertEqual(api["available_bounty_count"], 0)
        self.assertIn("revoked", api["initial_dashboard_key"])
        self.assertEqual(api["replacement_key"], "stored_private_never_committed")
        self.assertFalse(api["automatic_comments"])
        self.assertFalse(api["automatic_messages"])
        self.assertFalse(api["automatic_claims"])
        self.assertFalse(api["automatic_submissions"])
        self.assertIsNone(
            re.search(
                r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
                self.serialized,
                re.IGNORECASE,
            )
        )
        self.assertIsNone(re.search(r"\bak_[A-Za-z0-9_-]{12,}\b", self.serialized))
        self.assertNotRegex(self.serialized, r"\b\d{7,15}\b")

    def test_payout_and_support_boundaries_are_explicit(self):
        readiness = self.campaign["commercial_readiness"]
        self.assertEqual(readiness["payout_state"], "action_required")
        self.assertTrue(readiness["stripe_email_verification_completed"])
        self.assertFalse(
            readiness["stripe_onboarding_fields_available_after_verification"]
        )
        self.assertFalse(readiness["bank_details_submitted"])
        self.assertFalse(readiness["tax_details_submitted"])
        self.assertFalse(readiness["identity_document_submitted"])
        self.assertFalse(readiness["business_or_residence_declaration_submitted"])
        self.assertEqual(self.campaign["support_request"]["review_after"], "2026-09-18")
        self.assertFalse(self.campaign["support_request"]["automatic_follow_up"])
        monitoring = self.campaign["support_request"]["inbox_monitoring"]
        self.assertEqual(monitoring["state"], "private_aggregate_baselined")
        self.assertEqual(monitoring["matching_thread_count"], 0)
        self.assertEqual(monitoring["unread_matching_thread_count"], 0)
        self.assertFalse(monitoring["message_opened"])
        self.assertFalse(monitoring["message_preview_read"])
        self.assertFalse(monitoring["automatic_reply"])
        self.assertIn("explicit project-browser mailbox pass", monitoring["boundary"])

    def test_no_marketplace_or_revenue_event_is_inferred(self):
        funnel = self.campaign["funnel"]
        self.assertFalse(funnel["available_work_observed"])
        self.assertFalse(funnel["work_reviewed"])
        self.assertFalse(funnel["work_claimed"])
        self.assertFalse(funnel["requester_contacted"])
        self.assertFalse(funnel["submission_delivered"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)
        self.assertIn(
            "not a lead, contract, payment, or revenue", self.campaign["policy"]
        )


if __name__ == "__main__":
    unittest.main()
