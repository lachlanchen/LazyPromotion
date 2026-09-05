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
        self.assertEqual(program["award_range_usd"], {"minimum": 1000, "maximum": 5000})
        self.assertEqual(program["state"], "applications_open_official_page_verified")
        self.assertFalse(program["application_fee_observed"])
        self.assertFalse(program["deadline_published"])
        self.assertFalse(program["geographic_eligibility_published"])
        self.assertFalse(program["agreement_or_ip_terms_published"])

    def test_missing_license_is_a_pre_award_gate(self):
        audit = self.campaign["fit"]["license_audit"]
        self.assertEqual(audit["state"], "explicit_license_missing")
        self.assertIsNone(audit["github_detected_license"])
        self.assertFalse(audit["root_license_file_present"])
        self.assertIn("owner-approved license", audit["gate"])

    def test_private_package_is_unsent_and_ignored(self):
        proposal = self.campaign["proposal"]
        draft = ROOT / proposal["private_draft"]
        brief_source = ROOT / proposal["private_brief_source"]
        brief_pdf = ROOT / proposal["private_brief_pdf"]
        self.assertEqual(proposal["state"], "private_package_ready_not_sent")
        self.assertFalse(proposal["application_sent"])
        self.assertTrue(draft.is_file())
        self.assertTrue(brief_source.is_file())
        self.assertTrue(brief_pdf.is_file())
        for path in (draft, brief_source, brief_pdf):
            self.assertTrue(
                str(path.resolve()).startswith(str((ROOT / ".local").resolve()))
            )

    def test_budget_is_complete_and_grant_does_not_inflate_revenue(self):
        proposal = self.campaign["proposal"]
        self.assertEqual(sum(item["budget_usd"] for item in proposal["milestones"]), proposal["requested_usd"])
        funnel = self.campaign["funnel"]
        self.assertEqual(funnel["funds_received_usd"], 0)
        self.assertEqual(funnel["verified_received_gross_revenue_usd"], 0)
        self.assertIn("not customer revenue", funnel["policy"])


if __name__ == "__main__":
    unittest.main()
