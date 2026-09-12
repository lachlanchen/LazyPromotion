import json
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "steinke-python-maintainer.json"


class SteinkePythonMaintainerCampaignTests(unittest.TestCase):
    def setUp(self):
        self.serialized = CAMPAIGN.read_text(encoding="utf-8")
        self.payload = json.loads(self.serialized)

    def test_source_correction_records_matching_official_geography(self):
        source = self.payload["source_need"]
        match = source["likely_underlying_listing"]

        self.assertEqual(self.payload["version"], 2)
        self.assertEqual(source["compensation"], "Not published")
        self.assertIn("Vietnam", source["geography"])
        self.assertEqual(
            match["official_url"],
            "https://attacan.com/en/careers/freelance-python-developer-connector-libraries/",
        )
        self.assertIn("unconfirmed", match["relationship_state"])
        self.assertIn("Vietnam", match["published_location"])
        self.assertIn("not confirmation", source["boundary"])
        self.assertIn("company website", source["verification"])

    def test_fit_keeps_material_gaps_visible(self):
        fit = self.payload["fit"]
        gaps = " ".join(fit["not_claimed"])

        self.assertIn("LocalLLM", fit["projects"])
        self.assertIn("LazyPromotion", fit["projects"])
        self.assertIn("Five or more years", gaps)
        self.assertIn("MQTT", gaps)
        self.assertIn("Confirmed availability", gaps)

    def test_one_email_and_resume_are_verified_without_a_lead_claim(self):
        application = self.payload["application"]
        funnel = self.payload["funnel"]

        self.assertEqual(
            application["state"],
            "email_sent_closed_unless_employer_confirms_hong_kong_eligibility",
        )
        self.assertTrue(application["resume_attached"])
        self.assertTrue(application["sent_folder_verified"])
        self.assertEqual(application["submission_count"], 1)
        self.assertEqual(application["submission_fee_usd"], 0)
        self.assertFalse(application["automatic_follow_up"])
        self.assertEqual(funnel["outbound_application_count"], 1)
        self.assertFalse(funnel["human_reply_observed"])
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_application_watch_excludes_closed_geography_risk(self):
        watched = application_watch.application_record(
            self.payload,
            source_file=CAMPAIGN,
            on=application_watch.parse_day("2026-09-12"),
        )

        self.assertIsNone(watched)
        self.assertNotIn("follow_up_not_before", self.payload["application"])
        self.assertIn("No proactive follow-up", self.payload["application"]["review_policy"])

    def test_public_record_contains_no_private_application_values(self):
        serialized = self.serialized.casefold()
        for forbidden in (
            "@gmail",
            "phone number",
            "passport",
            "cookie",
            ".local/private",
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
