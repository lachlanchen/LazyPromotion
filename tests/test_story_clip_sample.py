import hashlib
import json
import subprocess
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "story-clip-pilot"


class StoryClipSampleTests(unittest.TestCase):
    def test_two_candidates_preserve_selection_and_source_boundaries(self):
        payload = json.loads((SAMPLE / "candidates.json").read_text())
        candidates = payload["candidates"]

        self.assertEqual(payload["schema"], "story-clip-candidates/v1")
        self.assertEqual(len(candidates), 2)
        self.assertEqual([item["id"] for item in candidates], ["candidate-a", "candidate-b"])
        self.assertEqual([item["id"] for item in candidates if item["selected"]], ["candidate-b"])
        self.assertTrue(all(item["hook"] and item["cut_rationale"] for item in candidates))
        self.assertTrue(all("Project-owned" in item["rights_note"] for item in candidates))

    def test_manifest_and_rights_keep_process_evidence_bounded(self):
        manifest = json.loads((SAMPLE / "delivery" / "manifest.json").read_text())
        rights = json.loads((SAMPLE / "delivery" / "rights-manifest.json").read_text())

        self.assertEqual(manifest["schema"], "story-clip-pilot-sample/v1")
        self.assertEqual(manifest["status"], "project_owned_synthetic_process_evidence")
        self.assertEqual(manifest["selection"]["candidate_count"], 2)
        self.assertEqual(manifest["selection"]["selected_id"], "candidate-b")
        self.assertTrue(rights["source_owned_or_licensed"])
        self.assertFalse(rights["customer_content"])
        self.assertIn("customer result", manifest["exclusions"])
        self.assertIn("30-minute source turnaround proof", manifest["exclusions"])
        self.assertIn("natural-interview editing proof", rights["excluded_claims"])

    def test_source_reference_is_pinned_to_existing_project_owned_media(self):
        source = json.loads((SAMPLE / "source-reference.json").read_text())
        source_path = ROOT / source["repository_path"]

        self.assertTrue(source_path.is_file())
        self.assertEqual(
            hashlib.sha256(source_path.read_bytes()).hexdigest(),
            source["sha256"],
        )
        self.assertEqual(source["rights_holder"], "LazyingArt LLC")
        self.assertFalse(source["third_party_content"])

    def test_selected_video_is_vertical_bounded_and_has_audio(self):
        video = SAMPLE / "delivery" / "selected-provenance-clip.mp4"
        probe = json.loads(
            subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-show_entries",
                    "stream=codec_type,width,height",
                    "-of",
                    "json",
                    str(video),
                ],
                text=True,
            )
        )
        streams = probe["streams"]
        video_stream = next(item for item in streams if item["codec_type"] == "video")

        self.assertEqual((video_stream["width"], video_stream["height"]), (1080, 1920))
        self.assertIn("audio", [item["codec_type"] for item in streams])
        self.assertAlmostEqual(float(probe["format"]["duration"]), 12.82, delta=0.15)

    def test_caption_and_ledger_keep_exact_source_corrections(self):
        captions = (SAMPLE / "delivery" / "selected-caption.en.srt").read_text()
        ledger = (SAMPLE / "delivery" / "caption-source-ledger.md").read_text()

        self.assertEqual(captions.count("\n\n"), 1)
        self.assertIn("Provenance does not make every claim true", captions)
        self.assertIn("but it makes each claim inspectable", captions)
        self.assertIn("Provens", ledger)
        self.assertIn("impeccable", ledger)
        self.assertIn("−27.600 seconds", ledger)

    def test_checksums_and_delivery_zip_are_complete(self):
        for line in (SAMPLE / "delivery" / "SHA256SUMS").read_text().splitlines():
            digest, relative_path = line.split("  ", 1)
            payload = (SAMPLE / relative_path).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), digest, relative_path)

        archive = SAMPLE / "artifacts" / "story-clip-pilot-sample.zip"
        expected_digest = (
            SAMPLE / "artifacts" / "story-clip-pilot-sample.zip.sha256"
        ).read_text().split()[0]
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), expected_digest)
        with zipfile.ZipFile(archive) as packet:
            self.assertIsNone(packet.testzip())
            names = set(packet.namelist())
        self.assertTrue(
            {
                "candidates.json",
                "source-reference.json",
                "delivery/selected-provenance-clip.mp4",
                "delivery/selected-caption.en.srt",
                "delivery/caption-source-ledger.md",
                "delivery/rights-manifest.json",
                "delivery/manifest.json",
                "delivery/SHA256SUMS",
            }.issubset(names)
        )

    def test_public_copy_does_not_inflate_the_sample(self):
        readme = (SAMPLE / "README.md").read_text()
        self.assertIn("project-owned process evidence", readme)
        self.assertIn("not customer work", readme)
        self.assertIn("not promise views, retention, conversion, or publishing", readme)


if __name__ == "__main__":
    unittest.main()
