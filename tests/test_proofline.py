import json
import tempfile
import unittest
from pathlib import Path

import proofline


class ProoflineTest(unittest.TestCase):
    def write_fixture(self, root: Path) -> Path:
        source = root / "source.txt"
        artifact = root / "artifact.txt"
        source.write_text("source passage\n", encoding="utf-8")
        artifact.write_text("derived card\n", encoding="utf-8")
        manifest = {
            "schema_version": "proofline/v1",
            "project": {"name": "test", "license": "MIT"},
            "files": [
                {
                    "id": "source",
                    "path": "source.txt",
                    "sha256": proofline.sha256_file(source),
                },
                {
                    "id": "artifact",
                    "path": "artifact.txt",
                    "sha256": proofline.sha256_file(artifact),
                },
            ],
            "transformations": [
                {
                    "id": "build",
                    "inputs": ["source"],
                    "outputs": ["artifact"],
                    "method": "manual reviewed derivation",
                }
            ],
            "claims": [
                {
                    "id": "claim",
                    "statement": "The artifact is tied to the source.",
                    "status": "verified",
                    "evidence": [{"file_id": "source", "locator": "line 1"}],
                }
            ],
        }
        path = root / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_valid_manifest_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            report = proofline.verify_manifest(self.write_fixture(Path(directory)))
        self.assertTrue(report["valid"])
        self.assertEqual(report["files_checked"], 2)
        self.assertEqual(report["verified_claims"], 1)

    def test_hash_mismatch_fails_without_exposing_file_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_fixture(root)
            (root / "artifact.txt").write_text("changed private value\n", encoding="utf-8")
            report = proofline.verify_manifest(manifest)
        self.assertFalse(report["valid"])
        self.assertIn("hash mismatch", " ".join(report["errors"]))
        self.assertNotIn("private value", json.dumps(report))

    def test_verified_claim_requires_known_file_and_locator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_fixture(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["claims"][0]["evidence"] = [{"file_id": "missing"}]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            report = proofline.verify_manifest(manifest)
        self.assertFalse(report["valid"])
        self.assertIn("unknown file", " ".join(report["errors"]))
        self.assertIn("locator is required", " ".join(report["errors"]))

    def test_duplicate_ids_and_escaping_paths_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_fixture(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["files"][1]["id"] = "source"
            payload["files"][0]["path"] = "../outside.txt"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            report = proofline.verify_manifest(manifest)
        self.assertFalse(report["valid"])
        errors = " ".join(report["errors"])
        self.assertIn("duplicates", errors)
        self.assertIn("escapes", errors)

    def test_unverified_claim_does_not_pretend_to_have_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_fixture(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["claims"][0] = {
                "id": "future",
                "statement": "A future result is not established yet.",
                "status": "unverified",
                "evidence": [],
            }
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            report = proofline.verify_manifest(manifest)
        self.assertTrue(report["valid"])
        self.assertEqual(report["verified_claims"], 0)

    def test_optional_evidence_on_unverified_claim_must_still_resolve(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_fixture(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["claims"][0]["status"] = "unverified"
            payload["claims"][0]["evidence"] = [
                {"file_id": "missing", "locator": "page 1"}
            ]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            report = proofline.verify_manifest(manifest)
        self.assertFalse(report["valid"])
        self.assertIn("unknown file", " ".join(report["errors"]))


if __name__ == "__main__":
    unittest.main()
