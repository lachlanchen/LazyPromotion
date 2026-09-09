import importlib.util
import json
import sys
import unittest
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "edge-image-quality"
ARTIFACTS = SAMPLE / "artifacts"
SPEC = importlib.util.spec_from_file_location("edge_iqa", SAMPLE / "iqa.py")
IQA = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = IQA
SPEC.loader.exec_module(IQA)


class EdgeImageQualityProofTests(unittest.TestCase):
    def test_frozen_fixture_results_are_narrow_and_interpretable(self):
        summary = json.loads((ARTIFACTS / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["fixture_count"], 5)
        self.assertEqual(summary["results"]["reference.png"], {"status": "PASS", "reasons": []})
        self.assertEqual(summary["results"]["blurred.png"]["reasons"], ["blur_or_low_detail"])
        self.assertEqual(
            summary["results"]["underexposed.png"]["reasons"],
            ["blur_or_low_detail", "underexposed"],
        )
        self.assertEqual(summary["results"]["overexposed.png"]["reasons"], ["overexposed"])
        self.assertEqual(summary["results"]["glare.png"]["reasons"], ["possible_glare"])
        self.assertFalse(summary["diagnostic_or_clinical_validation"])
        self.assertFalse(summary["incorrect_view_detection_implemented"])

    def test_decoder_and_validation_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            IQA.assess_encoded(b"")
        with self.assertRaisesRegex(ValueError, "decodable"):
            IQA.assess_encoded(b"not an image")
        with self.assertRaisesRegex(ValueError, "32 by 32"):
            IQA.assess(np.zeros((12, 12), dtype=np.uint8))
        with self.assertRaisesRegex(ValueError, "uint8"):
            IQA.assess(np.zeros((64, 64), dtype=np.float32))

    def test_stored_results_recompute_exactly(self):
        for path in sorted((ARTIFACTS / "fixtures").glob("*.png")):
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            expected = json.loads(
                (ARTIFACTS / "results" / f"{path.stem}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(IQA.assess(image), expected)

    def test_visual_summary_is_a_fixed_png(self):
        grid = cv2.imread(str(ARTIFACTS / "fixture-grid.png"), cv2.IMREAD_COLOR)
        self.assertIsNotNone(grid)
        self.assertEqual(grid.shape, (464, 960, 3))

    def test_report_keeps_medical_and_customer_claims_out(self):
        report = (ARTIFACTS / "report.md").read_text(encoding="utf-8").casefold()
        for phrase in (
            "not a customer result",
            "medical-device validation",
            "not a deployment promise",
            "held-out evaluation set",
            "incorrect-view detection is intentionally absent",
        ):
            self.assertIn(phrase, report)


if __name__ == "__main__":
    unittest.main()
