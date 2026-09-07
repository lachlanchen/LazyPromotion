import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "soft-event-frame-code-release.json"


class SoftEventFrameReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_release_evidence_is_exact_and_public(self):
        evidence = self.campaign["source_evidence"]
        self.assertIn("b82aec90bcb4694d1de2e8495fb0b3b3c563a5e5", evidence["release_commit"])
        self.assertEqual(
            evidence["delivery"]["state"],
            "public_release_delivered_and_ci_verified",
        )
        self.assertIn("not an alignment benchmark", evidence["delivery"]["boundary"])

    def test_private_research_artifacts_remain_excluded(self):
        excluded = " ".join(self.campaign["source_evidence"]["delivery"]["excluded"])
        for term in ("recordings", "identifiable", "arrays", "checkpoints"):
            self.assertIn(term, excluded)

    def test_value_is_not_counted_as_revenue(self):
        funnel = self.campaign["funnel"]
        self.assertTrue(funnel["public_value_delivered"])
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["verified_received_gross_usd"], 0)

    def test_fulfilled_issue_is_closed_without_a_follow_up_pitch(self):
        github = self.campaign["channels"]["github"]
        self.assertEqual(github["state"], "request_fulfilled_issue_closed_completed")
        self.assertTrue(github["issue_closed"])
        self.assertEqual(github["close_reason"], "completed")
        self.assertIn("do not add a sales pitch", github["policy"])


if __name__ == "__main__":
    unittest.main()
