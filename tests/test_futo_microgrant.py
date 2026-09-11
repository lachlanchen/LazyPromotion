import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FutoMicrograntTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "campaigns" / "futo-lkt-microgrant.json"
        cls.campaign = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_program_evidence_is_bounded_to_published_facts(self):
        program = self.campaign["program"]
        self.assertEqual(self.campaign["version"], 3)
        self.assertEqual(program["award_range_usd"], {"minimum": 1000, "maximum": 5000})
        self.assertEqual(
            program["state"],
            "applications_open_and_microgrant_range_officially_verified",
        )
        self.assertTrue(program["microgrant_application_route_published"])
        self.assertFalse(program["application_fee_observed"])
        self.assertFalse(program["deadline_published"])
        self.assertFalse(program["geographic_eligibility_published"])
        self.assertFalse(program["agreement_or_ip_terms_published"])
        self.assertIn("publishes the USD 1,000–5,000", program["policy"])

    def test_mit_license_is_verified_without_claiming_corpus_rights(self):
        audit = self.campaign["fit"]["license_audit"]
        self.assertEqual(audit["state"], "mit_license_published_and_github_detected")
        self.assertEqual(audit["github_detected_license"], "MIT")
        self.assertTrue(audit["root_license_file_present"])
        self.assertIn("does not grant rights", audit["boundary"])

    def test_private_package_is_sent_once_and_ignored(self):
        proposal = self.campaign["proposal"]
        draft = ROOT / proposal["private_draft"]
        brief_source = ROOT / proposal["private_brief_source"]
        brief_pdf = ROOT / proposal["private_brief_pdf"]
        self.assertEqual(proposal["state"], "email_sent_with_one_page_brief")
        self.assertTrue(proposal["application_sent"])
        self.assertTrue(draft.is_file())
        self.assertTrue(brief_source.is_file())
        self.assertTrue(brief_pdf.is_file())
        for path in (draft, brief_source, brief_pdf):
            self.assertTrue(
                str(path.resolve()).startswith(str((ROOT / ".local").resolve()))
            )

    def test_sent_application_is_not_a_reply_award_or_revenue(self):
        application = self.campaign["application"]
        self.assertEqual(application["state"], "email_sent_awaiting_human_reply")
        self.assertFalse(application["automatic_follow_up"])
        self.assertFalse(application["identity_document_submitted"])
        self.assertFalse(application["agreement_accepted"])
        inbound = application["inbound_monitor"]
        self.assertEqual(inbound["state"], "baseline_initialized")
        self.assertEqual(inbound["matching_thread_count"], 0)
        self.assertFalse(inbound["mail_opened"])
        self.assertFalse(inbound["message_preview_read"])
        funnel = self.campaign["funnel"]
        self.assertTrue(funnel["application_sent"])
        self.assertFalse(funnel["reply_received"])
        self.assertFalse(funnel["award_offered"])
        self.assertEqual(funnel["funds_received_usd"], 0)

    def test_budget_is_complete_and_grant_does_not_inflate_revenue(self):
        proposal = self.campaign["proposal"]
        self.assertEqual(sum(item["budget_usd"] for item in proposal["milestones"]), proposal["requested_usd"])
        funnel = self.campaign["funnel"]
        self.assertEqual(funnel["funds_received_usd"], 0)
        self.assertEqual(funnel["verified_received_gross_revenue_usd"], 0)
        self.assertIn("not customer revenue", funnel["policy"])


if __name__ == "__main__":
    unittest.main()
