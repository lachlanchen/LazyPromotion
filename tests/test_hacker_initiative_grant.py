import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "hacker-initiative-proofline-grant.json"
class HackerInitiativeGrantTest(unittest.TestCase):
    def test_campaign_budget_and_state_are_truthful(self):
        campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
        application = campaign["application"]
        self.assertEqual(application["state"], "private_draft_not_submitted")
        self.assertEqual(len(application["categories"]), 2)
        self.assertEqual(
            sum(item["usd"] for item in application["budget"]),
            application["requested_usd"],
        )
        self.assertEqual(application["requested_usd"], 5000)
        self.assertFalse(campaign["funnel"]["application_submitted"])
        self.assertEqual(campaign["funnel"]["funding_received_usd"], 0)
        self.assertEqual(
            campaign["funnel"]["verified_received_gross_revenue_usd"], 0
        )

    def test_private_application_workspace_is_git_ignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".local/", ignore)
        campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
        required = " ".join(campaign["application"]["private_fields_required"])
        self.assertIn("tax identity", required)
        self.assertNotRegex(required, r"\b\d{2}-\d{7}\b")


if __name__ == "__main__":
    unittest.main()
