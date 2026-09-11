import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FeaturedMediaQualityTests(unittest.TestCase):
    def test_landn_media_posts_remain_drafts_after_timed_frame_review(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "l-and-n-pronunciation-launch.json").read_text(
                encoding="utf-8"
            )
        )
        quality = campaign["source_evidence"]["media_quality_review"]
        self.assertEqual(quality["decision"], "hold")
        self.assertIn("overlapping headings", quality["issue"])
        for channel in ("instagram", "youtube", "linkedin"):
            self.assertEqual(
                campaign["channels"][channel]["state"],
                "postiz_draft_quality_review",
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
        self.assertIn("human visual-quality review", campaign["proof"]["quality_gate"])
        linkedin = campaign["channels"]["linkedin"]
        self.assertEqual(linkedin["state"], "postiz_draft_quality_review")
        self.assertEqual(linkedin["verified_state"], "DRAFT")
        self.assertFalse(linkedin["release_present"])

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
