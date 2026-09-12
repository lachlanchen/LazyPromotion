from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPECIMEN = ROOT / "examples" / "source-bounded-educational-prompt" / "README.md"


class EducationalPromptSpecimenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SPECIMEN.read_text(encoding="utf-8")

    def test_contract_has_required_sections(self):
        for heading in (
            "### Inputs",
            "### Work",
            "### Output",
            "### Constraints",
            "### Evaluation",
            "## Section annotation",
        ):
            self.assertIn(heading, self.text)

    def test_prompt_names_source_and_missing_input_boundaries(self):
        self.assertIn("the only factual reference", self.text)
        self.assertIn("Do not guess it", self.text)
        self.assertIn("cannot be traced", self.text)
        self.assertIn("missing information is named rather than invented", self.text)

    def test_specimen_does_not_claim_customer_work_or_guaranteed_model_output(self):
        compact = " ".join(self.text.split())
        self.assertIn("not a customer delivery", compact)
        self.assertIn("or a guarantee about a particular model", compact)


if __name__ == "__main__":
    unittest.main()
