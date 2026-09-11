import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FeaturedMediaQualityTests(unittest.TestCase):
    def test_landn_rejected_source_stays_out_while_reviewed_replacement_is_queued(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "l-and-n-pronunciation-launch.json").read_text(
                encoding="utf-8"
            )
        )
        quality = campaign["source_evidence"]["media_quality_review"]
        self.assertEqual(
            quality["decision"],
            "original_rejected_replacement_approved_and_queued",
        )
        self.assertIn("overlapping headings", quality["issue"])
        self.assertEqual(
            quality["replacement"]["state"],
            "queued_after_fresh_media_and_provider_recheck",
        )
        self.assertIn("hard cuts", quality["replacement"]["visual_review"])
        self.assertIn("queued", quality["replacement"]["postiz_boundary"])
        queue_review = quality["replacement_queue_review"]
        self.assertEqual(queue_review["decision"], "queue")
        self.assertEqual(queue_review["verified_state"], "QUEUE")
        self.assertFalse(queue_review["release_present"])
        for channel in ("instagram", "youtube", "linkedin"):
            self.assertEqual(
                campaign["channels"][channel]["state"],
                "postiz_queue",
            )
            self.assertEqual(
                campaign["channels"][channel]["media_sha256"],
                quality["replacement"]["sha256"],
            )
        self.assertEqual(campaign["channels"]["x"]["state"], "postiz_queue")

    def test_ai_clip_proof_requires_human_quality_review(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "ai-clip-assembly-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        examples = campaign["proof"]["examples"]
        self.assertFalse(any("Desert Oasis" in example for example in examples))
        self.assertFalse(any("Madeira" in example for example in examples))
        self.assertIn("human visual-quality review", campaign["proof"]["quality_gate"])
        self.assertEqual(campaign["offer"]["state"], "paused_quality_review")
        self.assertEqual(
            campaign["proof"]["assembly_sample"]["state"],
            "historical_not_featured",
        )
        linkedin = campaign["channels"]["linkedin"]
        self.assertEqual(linkedin["state"], "postiz_draft_quality_review")
        self.assertEqual(linkedin["verified_state"], "DRAFT")
        self.assertFalse(linkedin["release_present"])

    def test_rejected_science_reel_is_deleted_and_not_routed(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "bilingual-lecture-pack-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        correction = campaign["source_evidence"]["media_quality_correction"]
        instagram = campaign["channels"]["instagram"]
        self.assertEqual(
            correction["decision"],
            "delete_rejected_release_and_remove_from_current_selling_proof",
        )
        self.assertEqual(instagram["state"], "deleted_for_media_quality")
        self.assertTrue(
            instagram["visible_review"]["public_route_unavailable_after_reopen"]
        )
        self.assertIn("Do not recreate", instagram["policy"])

    def test_retired_sample_is_excluded_from_current_repurposing_proof(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "content-repurposing-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        current_urls = [item["url"] for item in campaign["fit"]["public_samples"]]
        self.assertNotIn(
            "https://www.youtube.com/watch?v=rVU37lPKPo8", current_urls
        )
        current_examples = campaign["fit"]["portfolio_reel"]["examples"]
        self.assertFalse(
            any("Desert Oasis" in example for example in current_examples)
        )
        self.assertEqual(
            campaign["quality_correction"]["retired_sample"], "Desert Oasis"
        )
        self.assertIn(
            "must not be reused", campaign["quality_correction"]["historical_boundary"]
        )

    def test_retired_sample_is_not_reusable_graph_evidence(self):
        retired_url = "https://www.youtube.com/watch?v=rVU37lPKPo8"
        opportunities = json.loads(
            (ROOT / "portfolio-opportunities.json").read_text(encoding="utf-8")
        )
        current_proof = {
            url
            for opportunity in opportunities["opportunities"]
            for url in opportunity["proof"]
        }
        self.assertNotIn(retired_url, current_proof)

        network = json.loads(
            (ROOT / "promotion-network.public.json").read_text(encoding="utf-8")
        )
        current_urls = {entity["url"] for entity in network["entities"]}
        current_evidence = {
            relationship["evidence_url"]
            for relationship in network["relationships"]
        }
        self.assertNotIn(retired_url, current_urls)
        self.assertNotIn(retired_url, current_evidence)


if __name__ == "__main__":
    unittest.main()
