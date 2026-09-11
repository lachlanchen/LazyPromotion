import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "agentspace-devops-freelance.json"


class AgentspaceDevOpsFreelanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_paid_need_and_application_state_are_exact(self):
        source = self.campaign["source_need"]
        self.assertEqual(source["state"], "public_explicit_paid_request")
        self.assertIn("INR 1,000 per hour", source["published_compensation"])
        application = self.campaign["application"]
        self.assertEqual(application["state"], "email_sent_awaiting_human_reply")
        self.assertFalse(application["automatic_follow_up"])
        self.assertEqual(application["review_after"], "2026-09-18")

    def test_public_proof_and_stack_gap_are_both_recorded(self):
        fit = self.campaign["fit"]
        self.assertEqual(len(fit["public_proof"]), 3)
        self.assertTrue(all(url.startswith("https://github.com/") for url in fit["public_proof"]))
        self.assertTrue(any("Jenkins" in gap for gap in fit["not_proven"]))
        self.assertTrue(any("Grafana" in gap for gap in fit["not_proven"]))
        self.assertIn("explicitly distinguishes", fit["claim_boundary"])

    def test_no_funnel_or_revenue_inflation(self):
        funnel = self.campaign["funnel"]
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertTrue(funnel["sender_side_sent_evidence_observed"])
        for key in (
            "human_reply_observed",
            "qualified_lead_observed",
            "paid_trial_offered",
            "contract_observed",
            "payment_confirmed",
            "delivered",
        ):
            self.assertFalse(funnel[key])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
