import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "campaigns" / "lexical-database-ingestion.json"


class LexicalDatabaseIngestionCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))

    def test_offer_matches_public_budget_and_has_bounded_milestones(self):
        offer = self.campaign["offer"]
        self.assertEqual(offer["quotation_usd"], 1200)
        self.assertEqual(offer["hour_cap"], 60)
        self.assertEqual(offer["rate_basis_usd_per_hour"], 20)
        self.assertEqual(sum(offer["milestones_usd"]), offer["quotation_usd"])
        self.assertEqual(len(offer["milestones"]), len(offer["milestones_usd"]))
        self.assertTrue(any("target schema" in item for item in offer["assumptions_to_confirm"]))

    def test_proof_preserves_exact_claim_boundaries(self):
        proof = self.campaign["owned_proof"]
        limits = " ".join(proof["limits"]).casefold()
        self.assertIn("no outofpapua data", limits)
        self.assertIn("not proof of compatibility", limits)
        self.assertIn("supplied ipa is preserved", limits)
        self.assertIn("not prior customer work", limits)
        self.assertEqual(proof["landing_page"], "https://lazying.art/lkt/lexical-ingest/")
        self.assertRegex(proof["website_commit"], r"^[0-9a-f]{40}$")
        self.assertIn("actions/runs/34048755968", proof["deployment_run"])
        self.assertIn("HTTP 200", proof["deployment_verification"])
        self.assertIn("lexical-ingest-proof", proof["lexical_ingest_sample"])
        evidence = self.campaign["source_evidence"]
        self.assertIn("/blob/f73ace6", evidence["atomic_source_hashed_ingestion"])
        self.assertIn("test_knowledge.py#L1073-L1096", evidence["transaction_rollback_test"])
        self.assertEqual(evidence["owned_landing_page"], proof["landing_page"])
        self.assertEqual(evidence["synthetic_ingestion_proof"], proof["lexical_ingest_sample"])

    def test_marketplace_and_revenue_states_do_not_overclaim(self):
        upwork = self.campaign["channels"]["upwork"]
        funnel = self.campaign["funnel"]
        self.assertEqual(upwork["state"], "application_prepared_login_required")
        self.assertFalse(upwork["application_submitted"])
        self.assertEqual(upwork["connects_spent"], 0)
        self.assertFalse(funnel["interview_observed"])
        self.assertFalse(funnel["contract_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_postiz_items_are_reviewed_queue_items_with_first_party_proof_only(self):
        channels = self.campaign["channels"]
        funnel = self.campaign["funnel"]
        serialized = json.dumps(channels, ensure_ascii=False).casefold()
        self.assertNotIn("post_id", serialized)
        for platform in ("x", "linkedin"):
            item = channels[platform]
            with self.subTest(platform=platform):
                self.assertEqual(item["state"], "postiz_queue")
                self.assertFalse(item["shortener_used"])
                self.assertIn("QUEUE", item["verification"])
                self.assertNotIn("outofpapua", item["content"].casefold())
                self.assertRegex(item["content_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("lazying.art/lkt/lexical-ingest/", channels["x"]["content"])
        self.assertIn("https://lazying.art/lkt/lexical-ingest/", channels["linkedin"]["content"])
        self.assertEqual(funnel["social_drafts_created"], 2)
        self.assertEqual(funnel["social_posts_queued"], 2)
        self.assertEqual(funnel["social_posts_published"], 0)


if __name__ == "__main__":
    unittest.main()
