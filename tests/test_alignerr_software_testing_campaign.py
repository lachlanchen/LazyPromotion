import json
import unittest
from pathlib import Path

import application_watch


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "alignerr-software-testing-analyst.json"


class AlignerrSoftwareTestingCampaignTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_current_listing_rate_stays_distinct_from_a_contract(self):
        source = self.payload["source_need"]
        self.assertEqual(source["published_rate"], "USD 40–120 per hour")
        self.assertIn("not an accepted rate", source["boundary"])
        self.assertIn("Hong Kong", source["boundary"])

    def test_personal_legal_gate_was_not_crossed(self):
        application = self.payload["application"]
        gate = application["terms_gate"]
        self.assertEqual(
            application["state"], "prepared_not_submitted_terms_review_required"
        )
        self.assertEqual(gate["state"], "not_accepted")
        self.assertIn("irrevocable", " ".join(gate["material_terms"]))
        self.assertIn("explicit decision", gate["policy"])
        self.assertEqual(application["submission_attempts"], 0)
        self.assertFalse(application["account_created"])
        self.assertFalse(application["resume_uploaded"])
        self.assertFalse(application["identity_submitted"])
        self.assertFalse(application["interview_started"])

    def test_prepared_route_is_not_watched_as_a_sent_application_or_revenue(self):
        application = application_watch.application_record(
            self.payload,
            source_file=CAMPAIGN,
            on=application_watch.parse_day("2026-09-09"),
        )
        funnel = self.payload["funnel"]
        self.assertIsNone(application)
        self.assertEqual(funnel["outbound_application_count"], 0)
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_public_record_has_no_private_contact_or_browser_data(self):
        serialized = CAMPAIGN.read_text(encoding="utf-8").casefold()
        for forbidden in ("lach@", "cookie", "browser profile", "persona session"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
