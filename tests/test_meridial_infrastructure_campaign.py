import json
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "meridial-infrastructure-specialist.json"


class MeridialInfrastructureCampaignTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_current_rate_is_not_a_contract_or_revenue_claim(self):
        source = self.payload["source_need"]
        self.assertEqual(
            source["advertised_rate"],
            "USD 80–150 per hour, adjusted for experience and geography",
        )
        self.assertIn("not an interview", source["boundary"])
        self.assertIn("not", source["boundary"])

    def test_fit_keeps_unsupported_requirements_visible(self):
        fit = self.payload["fit"]
        gaps = " ".join(fit["not_proven"])

        self.assertIn("LazyEdge", fit["projects"])
        self.assertIn("LazyTunnel", fit["projects"])
        self.assertIn("TypeScript fluency", gaps)
        self.assertIn("Terraform", gaps)
        self.assertIn("Hyperscale", gaps)

    def test_personal_and_legal_gates_are_not_crossed(self):
        application = self.payload["application"]

        self.assertEqual(application["state"], "private_packet_prepared_not_submitted")
        self.assertTrue(application["verified_public_linkedin"].startswith("https://www.linkedin.com/in/"))
        self.assertFalse(application["privacy_acknowledgement_selected"])
        self.assertFalse(application["form_filled"])
        self.assertFalse(application["resume_uploaded"])
        self.assertFalse(application["application_submitted"])
        self.assertFalse(application["assessment_started"])
        self.assertFalse(application["identity_verification_started"])

    def test_prepared_packet_does_not_enter_application_watch_or_funnel(self):
        watched = application_watch.application_record(
            self.payload,
            source_file=CAMPAIGN,
            on=application_watch.parse_day("2026-09-12"),
        )
        funnel = self.payload["funnel"]

        self.assertIsNone(watched)
        self.assertEqual(funnel["outbound_application_count"], 0)
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_public_record_contains_no_private_application_values(self):
        serialized = CAMPAIGN.read_text(encoding="utf-8").casefold()
        for forbidden in ("cookie", "browser profile", "date of birth", "passport"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
