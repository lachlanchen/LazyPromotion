import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GodengineAgentOrchestrationTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / "campaigns" / "godengine-agent-orchestration-engineering.json"
        self.campaign = json.loads(path.read_text(encoding="utf-8"))

    def test_application_uses_current_first_party_route_and_real_public_work(self):
        source = self.campaign["source_need"]
        self.assertEqual(source["official_url"], "https://godengine.ai/careers")
        self.assertEqual(
            source["state"], "first_party_open_general_engineering_route"
        )
        self.assertEqual(len(self.campaign["fit"]["public_proof"]), 3)
        self.assertIn(
            "AgInTi-LabCanvas", self.campaign["fit"]["public_proof"][0]
        )

    def test_sent_application_does_not_inflate_the_funnel(self):
        application = self.campaign["application"]
        funnel = self.campaign["funnel"]
        self.assertEqual(application["state"], "email_sent_awaiting_human_reply")
        self.assertEqual(application["attachments_sent"], 0)
        self.assertFalse(application["automatic_follow_up"])
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertTrue(funnel["sender_side_sent_evidence_observed"])
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["paid_assessment_offered"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
