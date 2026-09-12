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
        self.assertEqual(self.payload["version"], 5)
        self.assertIn("2 paid reviews x USD 500", self.payload["strategy"]["target_math"])
        offer = self.payload["offer"]
        self.assertEqual(offer["price"], "USD 500")
        self.assertEqual(offer["base_repository_revision_limit"], 1)
        self.assertEqual(offer["follow_up_successor_revision_limit"], 1)
        self.assertEqual(offer["follow_up_failed_check_limit"], 3)
        self.assertEqual(offer["mcp_server_limit"], 1)
        self.assertEqual(offer["tool_and_resource_limit"], 8)
        self.assertEqual(offer["protocol_check_limit"], 10)
        self.assertEqual(len(offer["default_check_set"]), 10)
        self.assertIn("up to three checks", offer["follow_up_recheck"])
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
        self.assertEqual(len(self.payload["demand_evidence"]), 3)
        self.assertTrue(
            all(item["source"].startswith("https://") for item in self.payload["demand_evidence"])
        )
        self.assertFalse(self.payload["intake"]["lead_or_sale_observed"])
        self.assertFalse(self.payload["funnel"]["qualified_lead_observed"])
        self.assertFalse(self.payload["funnel"]["payment_confirmed"])

    def test_price_is_validated_without_becoming_a_security_claim(self):
        validation = self.payload["market_validation"]
        self.assertIn("Keep USD 500", validation["decision"])
        self.assertEqual(len(validation["benchmarks"]), 3)
        self.assertTrue(all(item["source"].startswith("https://") for item in validation["benchmarks"]))
        self.assertIn("pre-deployment evidence", validation["decision"])

    def test_payment_path_is_guarded_and_non_mutating(self):
        payment = self.payload["payment_readiness"]
        self.assertEqual(payment["state"], "ready_for_reviewed_live_request")
        self.assertEqual(payment["price"], "USD 500")
        self.assertEqual(payment["quantity"], 1)
        self.assertEqual(payment["fulfillment_review_notes"], 9)
        self.assertFalse(payment["public_payment_link"])
        self.assertIn("No Product", payment["read_only_account_check"])

    def test_live_intake_round_trip_is_verified_without_claiming_a_lead(self):
        intake = self.payload["intake"]
        self.assertEqual(intake["state"], "live_verified")
        self.assertTrue(intake["review_before_send"])
        self.assertTrue(intake["receiver_authenticated_decrypted_and_saved"])
        self.assertTrue(intake["remote_spool_empty"])
        self.assertEqual(len(intake["required_buyer_inputs"]), 5)
        self.assertIn("second receiver pass returned no_pending", intake["live_round_trip"])
        self.assertFalse(intake["lead_or_sale_observed"])

    def test_linkedin_queue_replaces_overlapping_volume(self):
        postiz = self.payload["channels"]["postiz"]
        self.assertEqual(postiz["state"], "linkedin_queue_verified")
        self.assertEqual(postiz["publish_at"], "2026-09-21T02:00:00.000Z")
        self.assertIn("14 focused tests", postiz["content"])
        self.assertIn("fixed USD 500 pre-deployment review", postiz["content"])
        self.assertIn("utm_source=linkedin", postiz["destination"])
        self.assertIn("queue volume did not increase", postiz["superseded_post_removed"])
        self.assertFalse(postiz["lead_or_sale_observed"])

    def test_contra_listing_preserves_scope_and_revenue_boundaries(self):
        contra = self.payload["contra_marketplace"]
        self.assertEqual(contra["state"], "published_live_verified_identity_and_payout_pending")
        self.assertEqual(contra["price"], "USD 500 one-time")
        self.assertEqual(contra["duration"], "2 weeks")
        self.assertEqual(contra["faq_count"], 3)
        self.assertEqual(len(contra["tags"]), 6)
        self.assertEqual(contra["title"], "MCP Server Pre-Deployment Review")
        self.assertIn("up-to-three-failed-check", contra["payment_policy"])
        self.assertIn("stay on Contra", contra["payment_policy"])
        self.assertFalse(contra["identity_verified"])
        self.assertFalse(contra["payout_configured"])
        self.assertFalse(contra["buyer_inquiry_observed"])
        self.assertFalse(contra["payment_observed"])
        self.assertEqual(contra["received_gross_usd"], 0)


if __name__ == "__main__":
    unittest.main()
