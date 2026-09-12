import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "kicad-plugin-evaluation"


class KiCadPluginEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (EXAMPLE / "artifacts" / "fixture-manifest.json").read_text(
                encoding="utf-8"
            )
        )

    def test_fixture_covers_geometry_without_claiming_a_plugin_result(self):
        manifest = self.manifest

        self.assertEqual(manifest["version"], 1)
        self.assertEqual(manifest["kicad_version"], "10.0.3")
        self.assertEqual(len(manifest["cases"]), 7)
        self.assertEqual(manifest["geometry"]["segment_count"], 34)
        self.assertEqual(manifest["geometry"]["via_count"], 1)
        self.assertEqual(
            manifest["geometry"]["width_segment_counts_mm"],
            {"0.25": 20, "0.5": 10, "1": 4},
        )
        self.assertGreater(manifest["geometry"]["angle_counts_degrees"]["45"], 0)
        self.assertGreater(manifest["geometry"]["angle_counts_degrees"]["90"], 0)
        self.assertIn("no third-party plugin result", manifest["scope"].casefold())

    def test_committed_baseline_is_drc_clean_and_hash_bound(self):
        self.assertEqual(self.manifest["drc"], {"unconnected_items": 0, "violations": 0})

        for name, expected in self.manifest["artifacts"].items():
            path = EXAMPLE / name if name.endswith(".kicad_pcb") else EXAMPLE / "artifacts" / name
            self.assertTrue(path.is_file(), name)
            self.assertEqual(path.stat().st_size, expected["bytes"], name)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected["sha256"], name)

        for name in ("track-rounding-fixture-top.png", "track-rounding-fixture-3d.png"):
            image = (EXAMPLE / "artifacts" / name).read_bytes()
            self.assertTrue(image.startswith(b"\x89PNG\r\n\x1a\n"), name)

    def test_readme_defines_before_after_and_customer_boundaries(self):
        body = (EXAMPLE / "README.md").read_text(encoding="utf-8")

        self.assertIn("Start from a fresh copy of the baseline board", body)
        self.assertIn("Capture the same viewport after execution", body)
        self.assertIn("Run KiCad DRC", body)
        self.assertIn("No proprietary plugin, buyer board, or customer data is included", body)
        self.assertIn("HybridImager V2 board", body)
        self.assertIn("digiOBSCURA image-sensor board", body)


if __name__ == "__main__":
    unittest.main()
