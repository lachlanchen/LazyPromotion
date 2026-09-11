import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FeaturedMediaQualityTests(unittest.TestCase):
    def test_ai_clip_proof_requires_human_quality_review(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "ai-clip-assembly-pilot.json").read_text(
                encoding="utf-8"
            )
        )
        examples = campaign["proof"]["examples"]
        self.assertFalse(any("Desert Oasis" in example for example in examples))
        self.assertIn("human visual-quality review", campaign["proof"]["quality_gate"])

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


if __name__ == "__main__":
    unittest.main()
