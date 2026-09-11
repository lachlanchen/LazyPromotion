import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GitHubSponsorsPathTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / "campaigns" / "github-sponsors-clear-support-tiers.json"
        self.campaign = json.loads(path.read_text(encoding="utf-8"))

    def test_public_tiers_are_small_clear_and_have_no_service_perks(self):
        path = self.campaign["public_path"]
        self.assertEqual(path["state"], "published_and_publicly_verified")
        self.assertEqual(
            [(tier["amount_usd"], tier["frequency"]) for tier in path["tiers"]],
            [(5, "monthly"), (25, "one_time"), (100, "one_time")],
        )
        self.assertFalse(path["welcome_message_enabled"])
        self.assertFalse(path["private_repository_access_enabled"])
        self.assertTrue(path["profile_updated"])
        self.assertEqual(len(path["featured_repositories"]), 6)
        self.assertIn("lachlanchen/OpenHI", path["featured_repositories"])
        self.assertIn(
            "lachlanchen/LocalKnowledgeTerminal", path["featured_repositories"]
        )
        self.assertIn("lachlanchen/L-and-N", path["featured_repositories"])
        serialized = json.dumps(path).casefold()
        self.assertIn("no guaranteed support", serialized)
        self.assertIn("no service", serialized)
        self.assertIn("no promised feature", serialized)

    def test_publication_does_not_inflate_revenue(self):
        funnel = self.campaign["funnel"]
        self.assertTrue(funnel["public_path_published"])
        self.assertFalse(funnel["sponsor_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertFalse(funnel["payout_observed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
