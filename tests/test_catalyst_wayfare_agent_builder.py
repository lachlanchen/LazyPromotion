import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "catalyst-wayfare-agent-builder.json"


class CatalystWayfareAgentBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_application_is_sent_once_and_scheduled(self):
        application = self.campaign["application"]
        self.assertEqual(application["state"], "email_sent_awaiting_human_reply")
        self.assertEqual(application["subject"], "AI Engineer - Agent Builder")
        self.assertEqual(application["review_after"], "2026-09-18")
        self.assertFalse(application["automatic_follow_up"])

    def test_eligibility_and_commercial_terms_remain_gated(self):
        source = self.campaign["source_need"]
        self.assertIn("international candidates", source["eligibility"])
        self.assertIn("United States", source["eligibility"])
        self.assertIn("numerical compensation", source["published_terms"])
        gate = self.campaign["application"]["acceptance_gate"]
        for term in ("international eligibility", "numerical rate", "IP", "payment"):
            self.assertIn(term, gate)

    def test_application_does_not_inflate_the_funnel(self):
        funnel = self.campaign["funnel"]
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertTrue(funnel["sender_side_sent_evidence_observed"])
        for key in (
            "human_reply_observed",
            "qualified_lead_observed",
            "paid_assessment_offered",
            "contract_observed",
            "payment_confirmed",
            "delivered",
        ):
            self.assertFalse(funnel[key])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
