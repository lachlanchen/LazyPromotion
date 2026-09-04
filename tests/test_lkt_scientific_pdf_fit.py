import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "lkt-scientific-pdf-fit"
ARTIFACTS = SAMPLE / "artifacts"


def load_json(name):
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_builder():
    spec = importlib.util.spec_from_file_location("lkt_scientific_pdf_fit_build", SAMPLE / "build.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class ScientificPdfFitSampleTests(unittest.TestCase):
    def test_source_ledger_has_exact_duplicate_version_family_and_multilingual_source(self):
        ledger = load_json("source-ledger.json")
        self.assertEqual(ledger["exact_duplicate_groups"], [["prism-v1", "prism-v1-copy"]])
        by_id = {item["input_id"]: item for item in ledger["documents"]}
        self.assertEqual(by_id["prism-v1"]["source_sha256"], by_id["prism-v1-copy"]["source_sha256"])
        self.assertEqual(
            ledger["version_families"]["adaptive-prism-calibration"],
            ["v1", "v2"],
        )
        multilingual = by_id["spectral-multilingual-v1"]
        self.assertEqual(multilingual["languages"], ["en", "zh-Hans", "ja"])
        self.assertIn("synthetic", ledger["boundary"].casefold())
        self.assertIn("not a benchmark", ledger["boundary"].casefold())

    def test_fixed_questions_record_hits_miss_and_no_match_checks(self):
        ledger = load_json("retrieval-ledger.json")
        self.assertEqual(ledger["summary"], {
            "questions": 20,
            "expected_hits": 17,
            "hits": 16,
            "misses": 1,
            "expected_no_match": 3,
            "unexpected_matches": 0,
        })
        self.assertEqual(len({item["id"] for item in ledger["questions"]}), 20)
        miss = next(item for item in ledger["questions"] if item["status"] == "miss")
        self.assertEqual(miss["id"], "q17")
        self.assertTrue(miss["intended_lexical_miss"])

    def test_every_accepted_result_has_resolvable_provenance(self):
        retrieval = load_json("retrieval-ledger.json")
        check = load_json("citation-check.json")
        required = set(check["required_fields"])
        accepted = [item["accepted_result"] for item in retrieval["questions"] if item["accepted_result"]]
        self.assertEqual(len(accepted), 16)
        for result in accepted:
            self.assertTrue(required.issubset(result))
            self.assertTrue(all(result[field] not in (None, "") for field in required))
            self.assertEqual(len(result["source_sha256"]), 64)
        self.assertTrue(check["passed"])
        self.assertEqual(check["missing_provenance_fields"], 0)
        self.assertTrue(check["all_pages_within_source_bounds"])
        self.assertTrue(check["all_source_hashes_resolve"])

    def test_extraction_weaknesses_and_report_boundaries_are_explicit(self):
        extraction = load_json("extraction-ledger.json")
        weaknesses = " ".join(
            weakness for item in extraction["documents"] for weakness in item["declared_weaknesses"]
        ).casefold()
        for expected in ("mathematical", "table", "translation", "typography"):
            self.assertIn(expected, weaknesses)
        report = (ARTIFACTS / "fit-report.md").read_text(encoding="utf-8").casefold()
        self.assertIn("go for the bounded", report)
        self.assertIn("no-go for ocr", report)
        self.assertIn("not a benchmark", report)
        self.assertIn("customer result", report)
        self.assertIn("knowledge graph", report)

    def test_browser_card_is_static_and_contains_the_exact_citation_contract(self):
        page = (ARTIFACTS / "browser-card.html").read_text(encoding="utf-8")
        lowered = page.casefold()
        for label in ("document", "version", "pdf / printed page", "extraction", "source sha-256"):
            self.assertIn(label, lowered)
        self.assertIn("not a benchmark", lowered)
        self.assertIn("generated context</dt><dd>none", lowered)
        self.assertNotIn("<script", lowered)
        self.assertNotIn("http://", lowered)
        self.assertNotIn("https://", lowered)

    def test_manifest_hashes_sources_and_artifacts_without_self_hash_cycle(self):
        manifest = load_json("manifest.json")
        self.assertFalse(manifest["manifest_self_hashed"])
        self.assertNotIn("manifest.json", manifest["artifact_sha256"])
        for relative, expected in manifest["source_sha256"].items():
            self.assertEqual(digest(SAMPLE / relative), expected)
        for name, expected in manifest["artifact_sha256"].items():
            self.assertEqual(digest(ARTIFACTS / name), expected)
        self.assertEqual(manifest["verification"]["fixed_questions"], 20)
        self.assertFalse(manifest["verification"]["network_used"])
        self.assertFalse(manifest["verification"]["customer_data_used"])

    def test_campaign_records_the_sample_without_inflating_the_funnel(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "scientific-pdf-integrity.json").read_text(encoding="utf-8")
        )
        sample = campaign["source_evidence"]["executed_synthetic_sample"]
        self.assertEqual(campaign["version"], 4)
        self.assertEqual(
            campaign["source_evidence"]["executed_sample"],
            "https://github.com/lachlanchen/LazyPromotion/tree/main/examples/lkt-scientific-pdf-fit",
        )
        self.assertEqual(sample["state"], "built_and_reproducible")
        self.assertEqual(sample["fixed_questions"], 20)
        self.assertEqual(sample["accepted_hits"], 16)
        self.assertEqual(sample["citation_check"], "passed")
        self.assertFalse(sample["network_used"])
        self.assertFalse(sample["customer_data_used"])
        self.assertIn("not a benchmark", sample["boundary"].casefold())
        self.assertEqual(campaign["channels"]["lazyblog"]["proof_update_commit"], "839f614")
        self.assertEqual(campaign["channels"]["website"]["sample_report_commit"], "3422d01")
        self.assertEqual(campaign["funnel"]["state"], "attention")
        self.assertFalse(campaign["funnel"]["payment_confirmed"])
        self.assertEqual(campaign["funnel"]["received_revenue_usd"], 0)

    def test_two_local_builds_are_byte_identical(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            builder.build(Path(first))
            builder.build(Path(second))
            first_hashes = {path.name: digest(path) for path in Path(first).iterdir() if path.is_file()}
            second_hashes = {path.name: digest(path) for path in Path(second).iterdir() if path.is_file()}
        self.assertEqual(first_hashes, second_hashes)


if __name__ == "__main__":
    unittest.main()
