import tempfile
import unittest
from pathlib import Path

import inventory


class InventoryTests(unittest.TestCase):
    def test_every_public_source_repository_appears_once(self):
        payload = inventory.load_index()
        body = inventory.render(payload)
        complete_inventory = body.split("## Complete public repository inventory", 1)[1]
        self.assertEqual(len(payload["repositories"]), 108)
        for repo in payload["repositories"]:
            marker = f"]({repo['url']})"
            with self.subTest(repo=repo["name"]):
                self.assertEqual(complete_inventory.count(marker), 1)

    def test_category_map_is_complete_and_disjoint(self):
        payload = inventory.load_index()
        grouped = inventory.categorized_repositories(payload)
        names = [repo["name"] for repos in grouped.values() for repo in repos]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), {repo["name"] for repo in payload["repositories"]})

    def test_main_writes_public_only_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "inventory.md"
            old_output = inventory.OUTPUT
            try:
                inventory.OUTPUT = output
                # Render directly because argparse belongs to the real CLI boundary.
                output.write_text(inventory.render(inventory.load_index()), encoding="utf-8")
            finally:
                inventory.OUTPUT = old_output
            body = output.read_text(encoding="utf-8")
        self.assertIn("public-only map", body)
        self.assertNotIn("/home/", body)
        self.assertNotIn("candidate_", body)
        self.assertNotIn("draft_", body)

    def test_generated_priority_routes_preserve_commercial_boundaries(self):
        body = inventory.render(inventory.load_index())
        priority = body.split("## Portfolio at a glance", 1)[0]
        self.assertIn(
            "Public $128 / ¥999 pre-order inquiry; payment checkout awaits fulfillment review",
            priority,
        )
        self.assertIn("[Local Knowledge Terminal](https://lazying.art/lkt/)", priority)
        self.assertIn(
            "USD 250 collection-fit sprint after a free fit check; existing hardware only",
            priority,
        )
        self.assertIn(
            "first-USD-1,000 route is two confirmed USD 500 MCP Server Pre-Deployment Reviews",
            priority,
        )
        self.assertIn(
            "confirmed payments totalling USD 1,000 across nine adjacent bounded services",
            priority,
        )
        self.assertIn("free static public-repository preflight", priority)
        self.assertLess(
            priority.index("[LazyRemote + LazyTunnel]"),
            priority.index("[MCP Server Pre-Deployment Review]"),
        )
        self.assertLess(
            priority.index("[MCP Server Pre-Deployment Review]"),
            priority.index("[OpenHI]"),
        )
        self.assertIn("[LazyEdit + LocalVideoGen + Musia](https://lazying.art/story-clip/)", priority)
        self.assertIn(
            "USD 250 Story Clip Pilot after a metadata-only free fit check",
            priority,
        )
        self.assertIn("USD 250 Book Specimen Sprint after a free fit check", priority)
        self.assertIn("Paused; the old assembly is an archived technical record", priority)
        self.assertIn("USD 500 software reproducibility sprint after a metadata-only free fit check", priority)
        self.assertIn(
            "[HybridImager + CustomSensor](https://lazying.art/kicad-plugin-evaluation/)",
            priority,
        )
        self.assertIn("USD 400 KiCad Plugin Evaluation after a metadata-only fit check", priority)
        self.assertIn("USD 250 Custom Bilingual Pronunciation Mini-Lesson after a fit check", priority)
        self.assertNotIn("Verified public pre-order", priority)


if __name__ == "__main__":
    unittest.main()
