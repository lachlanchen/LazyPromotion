import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "auditable-policy-coding"
ARTIFACTS = SAMPLE / "artifacts"


def load_builder():
    spec = importlib.util.spec_from_file_location("auditable_policy_coding_build", SAMPLE / "build.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AuditablePolicyCodingTests(unittest.TestCase):
    def test_frozen_codebook_and_exact_evidence_contract(self):
        builder = load_builder()
        codebook = load_json(SAMPLE / "inputs" / "codebook.json")
        passages = load_json(SAMPLE / "inputs" / "passages.json")
        classifications = load_json(SAMPLE / "inputs" / "classifications.json")
        result = builder.validate(codebook, passages, classifications)
        self.assertTrue(codebook["frozen"])
        self.assertEqual(result["passage_count"], 3)
        self.assertEqual(result["annotation_count"], 3)
        self.assertEqual(result["exact_excerpt_matches"], 6)
        self.assertEqual(result["ambiguity_flags"], 1)

    def test_report_exposes_codes_locators_rationales_and_ambiguity(self):
        report = (ARTIFACTS / "report.md").read_text(encoding="utf-8")
        for expected in (
            "PUBLIC_ACCESS",
            "PHASED_IMPLEMENTATION",
            "INDEPENDENT_REVIEW",
            "`P-001:S-01`",
            "`P-002:S-02`",
            "`P-003:S-02`",
            "- Rationale:",
            "- Ambiguity: Yes",
            "no network or model calls",
        ):
            self.assertIn(expected, report)

    def test_manifest_hashes_sources_and_report_without_self_hash_cycle(self):
        manifest = load_json(ARTIFACTS / "manifest.json")
        self.assertFalse(manifest["manifest_self_hashed"])
        self.assertNotIn("manifest.json", manifest["artifact_sha256"])
        for relative, expected in manifest["source_sha256"].items():
            self.assertEqual(digest(SAMPLE / relative), expected)
        for name, expected in manifest["artifact_sha256"].items():
            self.assertEqual(digest(ARTIFACTS / name), expected)
        self.assertEqual(
            manifest["inputs"],
            {
                "client_data_used": False,
                "copyrighted_source_text_used": False,
                "model_calls_used": False,
                "network_used": False,
                "synthetic_passages": True,
            },
        )

    def test_build_is_deterministic_and_committed_artifacts_are_current(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            builder.build(Path(first))
            builder.build(Path(second))
            first_hashes = {path.name: digest(path) for path in Path(first).iterdir()}
            second_hashes = {path.name: digest(path) for path in Path(second).iterdir()}
        self.assertEqual(first_hashes, second_hashes)
        completed = subprocess.run(
            [sys.executable, str(SAMPLE / "build.py"), "--check"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
