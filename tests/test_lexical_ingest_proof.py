import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "lexical-ingest-proof"
ARTIFACTS = SAMPLE / "artifacts"


def load_builder():
    spec = importlib.util.spec_from_file_location("lexical_ingest_proof_build", SAMPLE / "build.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def load_json(name):
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LexicalIngestProofTests(unittest.TestCase):
    def test_dry_run_and_deterministic_rejects(self):
        dry_run = load_json("dry-run.json")
        self.assertFalse(dry_run["database_written"])
        self.assertEqual(
            dry_run["planned"],
            {
                "accepted_records": 4,
                "field_values": 42,
                "gloss_normalizations_planned": 4,
                "records_by_format": {"csv": 3, "toolbox-style-text": 3},
                "reject_codes": {"missing_lemma": 2},
                "rejected_records": 2,
                "source_records": 6,
                "sources": 2,
            },
        )
        validation = load_json("validation.json")
        self.assertEqual(
            [(item["source_record_id"], item["code"]) for item in validation["rejects"]],
            [("TBX-003", "missing_lemma"), ("CSV-003", "missing_lemma")],
        )

    def test_database_schema_counts_provenance_and_raw_values(self):
        validation = load_json("validation.json")
        self.assertEqual(
            validation["counts"],
            {
                "gloss_normalizations": 4,
                "lexemes": 4,
                "source_fields": 42,
                "source_records": 6,
                "sources": 2,
                "transformation_log": 4,
            },
        )
        required_source_fields = {
            "source_id",
            "source_record_id",
            "locator",
            "raw_value",
            "source_sha256",
        }
        self.assertTrue(required_source_fields.issubset(validation["schema"]["source_fields"]))
        connection = sqlite3.connect(ARTIFACTS / "canonical-lexicon.sqlite")
        connection.row_factory = sqlite3.Row
        toolbox = connection.execute(
            """
            SELECT sf.raw_value, sf.locator, sf.source_sha256, l.english_gloss_source_raw,
                   g.normalized_english_gloss
            FROM source_fields sf
            JOIN lexemes l ON l.record_key = sf.record_key
            JOIN gloss_normalizations g ON g.lexeme_id = l.lexeme_id
            WHERE sf.source_id = 'synthetic-toolbox'
              AND sf.source_record_id = 'TBX-001'
              AND sf.canonical_name = 'gloss_en'
            """
        ).fetchone()
        self.assertEqual(toolbox["raw_value"], "River;  stream")
        self.assertEqual(toolbox["english_gloss_source_raw"], "River;  stream")
        self.assertEqual(toolbox["normalized_english_gloss"], "river; stream")
        self.assertRegex(toolbox["locator"], r"synthetic-toolbox\.txt:L\d+")
        self.assertEqual(len(toolbox["source_sha256"]), 64)
        ipa_pairs = connection.execute(
            """
            SELECT l.lexeme_id, l.ipa_supplied_raw, sf.raw_value
            FROM lexemes l JOIN source_fields sf ON sf.record_key = l.record_key
            WHERE sf.canonical_name = 'ipa' ORDER BY l.lexeme_id
            """
        ).fetchall()
        self.assertEqual(len(ipa_pairs), 4)
        self.assertTrue(all(row["ipa_supplied_raw"] == row["raw_value"] for row in ipa_pairs))
        rejected_lexemes = connection.execute(
            """
            SELECT COUNT(*) FROM lexemes l JOIN source_records r ON r.record_key = l.record_key
            WHERE r.status = 'rejected'
            """
        ).fetchone()[0]
        self.assertEqual(rejected_lexemes, 0)
        connection.close()

    def test_replay_is_noop_and_injected_failure_rolls_back(self):
        idempotency = load_json("idempotency.json")
        self.assertTrue(idempotency["database_bytes_unchanged"])
        self.assertTrue(idempotency["logical_state_unchanged"])
        self.assertEqual(idempotency["second_run"]["writes"], 0)
        rollback = load_json("rollback-safety.json")
        self.assertTrue(rollback["passed"])
        self.assertTrue(rollback["all_ingest_tables_empty_after_failure"])
        self.assertFalse(any(rollback["post_rollback_counts"].values()))

    def test_manifest_hashes_sources_and_artifacts_and_states_limits(self):
        manifest = load_json("manifest.json")
        self.assertFalse(manifest["manifest_self_hashed"])
        self.assertNotIn("manifest.json", manifest["artifact_sha256"])
        for relative, expected in manifest["source_sha256"].items():
            self.assertEqual(digest(SAMPLE / relative), expected)
        for relative, expected in manifest["artifact_sha256"].items():
            self.assertEqual(digest(ARTIFACTS / relative), expected)
        self.assertEqual(
            manifest["inputs"],
            {
                "client_data_used": False,
                "network_used": False,
                "ocr_used": False,
                "outofpapua_schema_used": False,
                "real_toolbox_corpus_used": False,
                "synthetic_project_owned_sources": 2,
            },
        )
        report = (ARTIFACTS / "report.md").read_text(encoding="utf-8").casefold()
        for phrase in (
            "no outofpapua schema",
            "no real toolbox corpus",
            "no client data",
            "no ocr",
            "no linguistic accuracy benchmark",
            "no customer result",
        ):
            self.assertIn(phrase, report)

    def test_two_clean_builds_are_byte_identical_and_committed_files_current(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            builder.build(Path(first))
            builder.build(Path(second))
            first_hashes = {path.name: digest(path) for path in Path(first).iterdir() if path.is_file()}
            second_hashes = {path.name: digest(path) for path in Path(second).iterdir() if path.is_file()}
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
