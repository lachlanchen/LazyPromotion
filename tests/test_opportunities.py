import json
import tempfile
import unittest
from pathlib import Path

import opportunities


class OpportunityTests(unittest.TestCase):
    def test_registry_uses_only_original_public_projects(self):
        payload = opportunities.load_registry()
        self.assertGreaterEqual(len(payload["opportunities"]), 10)
        self.assertEqual(
            [item["id"] for item in payload["opportunities"] if item["state"] == "active"],
            [
                "private-collection-intelligence",
                "lecture-to-study-library",
                "source-aware-book-specimen",
                "story-first-content-repurposing",
                "ai-clip-assembly",
                "scientific-manuscript-workbench",
                "private-multidevice-remote-access",
                "openhi-reproducibility-session",
            ],
        )
        self.assertEqual(
            [
                item["id"]
                for item in payload["opportunities"]
                if item["state"] == "evidence-building"
            ],
            ["short-video-pipeline-engineering"],
        )

    def test_renderer_keeps_scores_directional_and_gates_visible(self):
        body = opportunities.render(opportunities.load_registry())
        self.assertIn("not market validation", body)
        self.assertIn("## Opportunity contracts", body)
        self.assertIn("### Private collection intelligence", body)
        self.assertIn("### Source-preserving lexical ingestion", body)
        self.assertIn("https://lazying.art/lkt/lexical-ingest/", body)
        self.assertIn("closed USD 1,200 listing is historical buyer-intent evidence", body)
        self.assertIn("### Source-aware book specimen", body)
        self.assertIn("https://lazying.art/book-specimen/", body)
        self.assertIn("### AI clip assembly pilot", body)
        self.assertIn("https://lazying.art/video/brand-film/#sample", body)
        self.assertIn("### Manuscript build and redline sprint", body)
        self.assertIn("https://lazying.art/lkt/passage-graph/", body)
        self.assertIn(
            "https://www.reddit.com/r/KnowledgeGraph/comments/1sogxlr/comment/oguk95a/",
            body,
        )
        self.assertIn("hand-reviewed and project-owned", body)
        self.assertIn("https://lazying.art/manuscript-sprint/", body)
        self.assertIn("https://lazying.art/lecture-pack/", body)
        self.assertIn("https://lazying.art/lecture-pack/#example", body)
        self.assertIn("https://lazying.art/story-clip/", body)
        self.assertIn("### Story-first interview clip pilot", body)
        self.assertIn("three current one-time applications", body)
        self.assertIn("https://lazying.art/story-clip/fit-check/", body)
        self.assertIn("https://youdontevenhear.me/apply", body)
        self.assertIn("a51ac6f33ce28d9a42143cfc4651e859ec35b6bb/examples/story-clip-pilot", body)
        self.assertIn("urn:li:activity:7501848655239233536", body)
        self.assertIn("not customer work, travel-client experience", body)
        self.assertIn("41.191-second synthetic project-owned source", body)
        self.assertIn(
            "https://github.com/lachlanchen/LazyPromotion/tree/8db8e1722c85c626296f1306e7dca662439a6a6e/examples/cantonese-caption-delivery",
            body,
        )
        self.assertIn("not spoken-word, sermon, customer", body)
        self.assertIn(
            "https://l-and-n.lazying.art/downloads/L-and-N-1.0-build3-test.apk",
            body,
        )
        self.assertIn("### Durable AI conversation and voice memory", body)
        self.assertIn(
            "https://www.reddit.com/r/ChatGPT/comments/1vygqua/has_anyone_figured_out_a_sane_way_to_archive/",
            body,
        )
        self.assertIn("Keep AiMemo as a gated private alpha", body)
        self.assertIn("synthetic-audio transcription and organization", body)
        self.assertIn("physical-microphone round trip", body)
        self.assertIn("Do not link AiMemo in public replies", body)
        self.assertIn("free private-alpha state", body)
        self.assertNotIn("Restore the AI provider", body)
        self.assertNotIn("its two public sites disagree", body)
        self.assertIn("### Short-video caption pipeline feasibility", body)
        self.assertIn("Hebrew and bidirectional-text risk test", body)
        self.assertIn("rtl-caption-feasibility", body)
        self.assertIn("low historical spend", body)
        self.assertIn("https://github.com/lachlanchen/LazyTunnel", body)
        self.assertIn("https://github.com/lachlanchen/kvm-qemu-workstation", body)
        self.assertIn("https://github.com/lachlanchen/uu-remote-ubuntu-bridge", body)
        self.assertIn("operator-reviewed deployment evidence", body)
        self.assertIn("Google Play production listing is independently public", body)
        self.assertIn("Treat TestFlight as a beta route", body)
        self.assertIn("are eight priced service routes", body)
        self.assertIn("listing closed before submission", body)
        self.assertIn("Gates:", body)
        self.assertNotIn("EchoMind", body)

    def test_main_writes_a_deterministic_markdown_map(self):
        payload = opportunities.load_registry()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "opportunities.md"
            output.write_text(opportunities.render(payload), encoding="utf-8")
            first = output.read_text(encoding="utf-8")
            output.write_text(opportunities.render(payload), encoding="utf-8")
            self.assertEqual(output.read_text(encoding="utf-8"), first)


if __name__ == "__main__":
    unittest.main()
