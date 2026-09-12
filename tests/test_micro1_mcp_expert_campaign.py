import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "micro1-mcp-expert.json"


class Micro1McpExpertCampaignTests(unittest.TestCase):
    def setUp(self):
        self.serialized = CAMPAIGN.read_text(encoding="utf-8")
        self.payload = json.loads(self.serialized)

    def test_official_role_and_output_based_pay_are_bounded(self):
        source = self.payload["source_need"]

        self.assertEqual(self.payload["version"], 1)
        self.assertTrue(source["official_url"].startswith("https://jobs.micro1.ai/post/"))
        self.assertEqual(source["published_rate_usd_per_hour"], {"minimum": 60, "maximum": 120})
        self.assertIn("output-based", source["compensation_boundary"])
        self.assertIn("not a guaranteed", source["compensation_boundary"])

    def test_fit_uses_mcp_evidence_without_claiming_selection(self):
        fit = self.payload["fit"]
        supported = " ".join(fit["supported_now"])
        gaps = " ".join(fit["not_claimed"])

        self.assertIn("LocalKnowledgeTerminal", fit["projects"])
        self.assertIn("LazyPromotion", fit["projects"])
        self.assertIn("MCP tools", supported)
        self.assertIn("Selection", gaps)

    def test_agent_stops_before_personal_interview_or_assessment(self):
        boundary = self.payload["platform_boundary"]
        restrictions = " ".join(boundary["agent_restrictions"])
        application = self.payload["application"]

        self.assertIn("automated scripts", restrictions)
        self.assertIn("original interview answers", restrictions)
        self.assertIn("Do not automate registration", boundary["decision"])
        self.assertEqual(application["state"], "not_applied_user_personal_action_required")
        self.assertEqual(application["submission_count"], 0)

    def test_no_application_or_revenue_is_invented(self):
        funnel = self.payload["funnel"]

        self.assertEqual(funnel["outbound_application_count"], 0)
        self.assertFalse(funnel["interview_observed"])
        self.assertFalse(funnel["contract_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_public_record_contains_no_private_identity_or_session_data(self):
        serialized = self.serialized.casefold()
        for forbidden in ("@gmail", "passport", "cookie", ".local/private", "phone number"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
