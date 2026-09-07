import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WeTheFlywheelCampaignTests(unittest.TestCase):
    def test_failed_form_and_single_email_remain_distinct(self):
        campaign = json.loads(
            (
                ROOT
                / "campaigns"
                / "wetheflywheel-agentic-engineer.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(campaign["fit"]["projects"], ["LazyPromotion", "LazyEdge"])
        application = campaign["application"]
        self.assertEqual(
            application["state"], "email_fallback_sent_awaiting_human_reply"
        )
        self.assertEqual(application["official_form"]["submit_attempts"], 1)
        self.assertFalse(application["official_form"]["accepted"])
        self.assertFalse(application["official_form"]["retried"])
        self.assertFalse(application["resume_attached"])
        self.assertFalse(application["whatsapp_supplied"])
        self.assertFalse(application["fallback"]["automatic_follow_up"])

    def test_outbound_application_is_not_revenue(self):
        campaign = json.loads(
            (
                ROOT
                / "campaigns"
                / "wetheflywheel-agentic-engineer.json"
            ).read_text(encoding="utf-8")
        )
        funnel = campaign["funnel"]
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertTrue(funnel["sender_side_sent_evidence_observed"])
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["contract_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
