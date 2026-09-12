import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "mcp-boundary-review.json"
PACKET = (
    ROOT
    / "examples"
    / "mcp-boundary-review"
    / "artifacts"
    / "lkt-mcp-boundary-review-sample.zip"
)


class McpBoundaryReviewCampaignTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_two_bounded_reviews_reach_target_without_inventing_revenue(self):
        self.assertEqual(self.payload["version"], 1)
        self.assertIn("2 paid reviews x USD 500", self.payload["strategy"]["target_math"])
        offer = self.payload["offer"]
        self.assertEqual(offer["price"], "USD 500")
        self.assertEqual(offer["repository_revision_limit"], 1)
        self.assertEqual(offer["mcp_server_limit"], 1)
        self.assertEqual(offer["tool_and_resource_limit"], 8)
        self.assertEqual(offer["protocol_check_limit"], 10)
        self.assertEqual(sum(offer["deliverable_allocation_usd"].values()), 500)
        self.assertEqual(self.payload["funnel"]["received_revenue_usd"], 0)

    def test_offer_preserves_security_and_data_boundaries(self):
        offer = self.payload["offer"]
        excluded = " ".join(offer["excluded"]).casefold()
        self.assertIn("penetration testing", excluded)
        self.assertIn("security certification", excluded)
        self.assertIn("production secrets", excluded)
        self.assertIn("not a public self-serve checkout", offer["payment_policy"].casefold())
        self.assertIn("metadata only", offer["data_policy"].casefold())

    def test_executed_public_packet_is_pinned_and_integral(self):
        proof = self.payload["public_proof"]
        self.assertEqual(proof["revision"], "e750e5ae24b780e45de896f7dc3a769d2410dabd")
        self.assertEqual(proof["observed"]["focused_tests_passed"], 14)
        self.assertEqual(proof["observed"]["tools"], 2)
        self.assertEqual(proof["observed"]["resources"], 1)
        self.assertEqual(proof["observed"]["prompts"], 0)
        self.assertIn("NO-GO for direct remote exposure", proof["decision"])
        self.assertEqual(
            proof["packet"]["sha256"],
            hashlib.sha256(PACKET.read_bytes()).hexdigest(),
        )
        self.assertTrue(proof["packet"]["live_byte_identical"])

    def test_demand_is_separate_from_selection_or_sales(self):
        self.assertEqual(len(self.payload["demand_evidence"]), 2)
        self.assertTrue(
            all(item["source"].startswith("https://") for item in self.payload["demand_evidence"])
        )
        self.assertFalse(self.payload["intake"]["lead_or_sale_observed"])
        self.assertFalse(self.payload["funnel"]["qualified_lead_observed"])
        self.assertFalse(self.payload["funnel"]["payment_confirmed"])

    def test_payment_path_is_guarded_and_non_mutating(self):
        payment = self.payload["payment_readiness"]
        self.assertEqual(payment["state"], "ready_for_reviewed_live_request")
        self.assertEqual(payment["price"], "USD 500")
        self.assertEqual(payment["quantity"], 1)
        self.assertEqual(payment["fulfillment_review_notes"], 9)
        self.assertFalse(payment["public_payment_link"])
        self.assertIn("No Product", payment["read_only_account_check"])


if __name__ == "__main__":
    unittest.main()
