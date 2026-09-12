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
        self.assertEqual(self.payload["version"], 2)
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

    def test_single_application_is_submitted_without_assessment_or_identity_claim(self):
        application = self.payload["application"]

        self.assertEqual(application["state"], "submitted_awaiting_reply")
        self.assertEqual(
            application["verified_public_linkedin"],
            "https://www.linkedin.com/in/lazyingart",
        )
        self.assertTrue(application["privacy_acknowledgement_selected"])
        self.assertTrue(application["form_filled"])
        self.assertTrue(application["resume_uploaded"])
        self.assertTrue(application["application_submitted"])
        self.assertEqual(application["submission_count"], 1)
        self.assertEqual(application["submission_fee_usd"], 0)
        self.assertTrue(application["confirmation"]["visible_reviewed"])
        self.assertFalse(application["confirmation"]["verification_challenge_present"])
        self.assertFalse(application["assessment_started"])
        self.assertFalse(application["identity_verification_started"])

    def test_submitted_application_enters_watch_without_becoming_a_lead(self):
        watched = application_watch.application_record(
            self.payload,
            source_file=CAMPAIGN,
            on=application_watch.parse_day("2026-09-12"),
        )
        funnel = self.payload["funnel"]

        self.assertIsNotNone(watched)
        self.assertEqual(watched["review_after"], "2026-09-19")
        self.assertFalse(watched["due_for_human_review"])
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_public_record_contains_no_private_application_values(self):
        serialized = CAMPAIGN.read_text(encoding="utf-8").casefold()
        for forbidden in ("cookie", "browser profile", "date of birth", "passport"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
