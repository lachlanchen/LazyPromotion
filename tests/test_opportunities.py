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
            ["private-collection-intelligence"],
        )
        self.assertEqual(
            [
                item["id"]
                for item in payload["opportunities"]
                if item["state"] == "evidence-building"
            ],
            ["scientific-manuscript-workbench"],
        )

    def test_renderer_keeps_scores_directional_and_gates_visible(self):
        body = opportunities.render(opportunities.load_registry())
        self.assertIn("not market validation", body)
        self.assertIn("## Opportunity contracts", body)
        self.assertIn("### Private collection intelligence", body)
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
