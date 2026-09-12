import hashlib
import json
import unittest
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "mcp-boundary-review"
ARTIFACTS = SAMPLE / "artifacts"
PACKET = ARTIFACTS / "lkt-mcp-boundary-review-sample.zip"
CHECKSUM = ARTIFACTS / "lkt-mcp-boundary-review-sample.zip.sha256"
REPORT_PDF = ARTIFACTS / "report.pdf"
MEMBERS = [
    "environment.json",
    "tool-inventory.json",
    "collection-status.json",
    "query-result.json",
    "trace-result.json",
    "test.log",
    "report.md",
    "source-hashes.json",
    "summary.json",
    "manifest.json",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(name: str):
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


class McpBoundaryReviewProofTests(unittest.TestCase):
    def test_summary_pins_source_and_reports_the_narrow_decision(self):
        summary = load_json("summary.json")
        self.assertEqual(
            summary["lkt_commit"],
            "e750e5ae24b780e45de896f7dc3a769d2410dabd",
        )
        self.assertEqual(summary["checks"]["tests_passed"], 14)
        self.assertEqual(summary["checks"]["test_exit_code"], 0)
        self.assertEqual(summary["checks"]["tool_count"], 2)
        self.assertEqual(summary["checks"]["resource_count"], 1)
        self.assertEqual(summary["checks"]["prompt_count"], 0)
        self.assertTrue(summary["checks"]["database_mtime_unchanged"])
        self.assertIn("NO-GO for direct remote exposure", summary["decision"])

    def test_protocol_inventory_is_read_only_and_exact(self):
        inventory = load_json("tool-inventory.json")
        self.assertEqual(
            [tool["name"] for tool in inventory["tools"]],
            ["query_private_knowledge", "trace_private_claim"],
        )
        self.assertEqual(
            [resource["uri"] for resource in inventory["resources"]],
            ["lkt://collections/status"],
        )
        self.assertEqual(inventory["prompts"], [])
        for tool in inventory["tools"]:
            annotations = tool["annotations"]
            self.assertTrue(annotations["readOnlyHint"])
            self.assertFalse(annotations["destructiveHint"])
            self.assertTrue(annotations["idempotentHint"])
            self.assertFalse(annotations["openWorldHint"])

    def test_public_fixture_returns_traceable_multilingual_evidence(self):
        query = load_json("query-result.json")
        trace = load_json("trace-result.json")
        status = load_json("collection-status.json")
        self.assertEqual(query["query"], "春")
        self.assertEqual(query["response_language"], "ja")
        self.assertEqual(query["match_count"], 1)
        self.assertEqual(trace["kind"], "claim")
        self.assertEqual(len(trace["evidence"]), 1)
        self.assertEqual(status["languages"], ["en", "ja", "zh"])
        self.assertTrue(status["read_only"])
        self.assertFalse(status["model_invocation"])
        self.assertNotIn("/home/", json.dumps((query, trace, status)))

    def test_manifest_hashes_every_public_artifact(self):
        manifest = load_json("manifest.json")
        self.assertNotIn("manifest.json", manifest["artifact_sha256"])
        self.assertEqual(set(manifest["artifact_sha256"]), set(MEMBERS) - {"manifest.json"})
        for name, expected in manifest["artifact_sha256"].items():
            self.assertEqual(digest(ARTIFACTS / name), expected)

    def test_report_and_log_state_the_security_boundary(self):
        report = (ARTIFACTS / "report.md").read_text(encoding="utf-8").casefold()
        log = (ARTIFACTS / "test.log").read_text(encoding="utf-8")
        for phrase in (
            "go for local, read-only use",
            "no-go for direct remote exposure",
            "not a penetration test",
            "any connected client",
        ):
            self.assertIn(phrase, report)
        self.assertIn("Ran 14 tests", log)
        self.assertIn("OK", log)
        for value in (report, log):
            self.assertNotIn("/home/", value)
            self.assertNotIn("/tmp/", value)

    def test_printable_report_is_present_but_outside_deterministic_packet(self):
        self.assertGreater(REPORT_PDF.stat().st_size, 10_000)
        self.assertTrue(REPORT_PDF.read_bytes().startswith(b"%PDF-1."))
        self.assertNotIn("report.pdf", MEMBERS)

    def test_download_packet_is_exact_safe_and_has_matching_checksum(self):
        with zipfile.ZipFile(PACKET) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual([item.filename for item in archive.infolist()], MEMBERS)
            for item in archive.infolist():
                path = PurePosixPath(item.filename)
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
                self.assertEqual(item.date_time, (2026, 9, 12, 0, 0, 0))
                self.assertEqual((item.external_attr >> 16) & 0o777, 0o644)
                self.assertEqual(archive.read(item.filename), (ARTIFACTS / item.filename).read_bytes())
        self.assertEqual(
            CHECKSUM.read_text(encoding="utf-8"),
            f"{digest(PACKET)}  {PACKET.name}\n",
        )


if __name__ == "__main__":
    unittest.main()
