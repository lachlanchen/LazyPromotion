import hashlib
import json
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "bilingual-lecture-pack"


class BilingualLectureSampleTests(unittest.TestCase):
    def test_manifest_records_bounded_project_owned_sample(self):
        manifest = json.loads((SAMPLE / "delivery" / "manifest.json").read_text())

        self.assertEqual(manifest["schema"], "bilingual-lecture-pack-sample/v1")
        self.assertEqual(manifest["status"], "project_owned_synthetic_process_evidence")
        self.assertEqual(manifest["source"]["language"], "en")
        self.assertEqual(manifest["target"]["language"], "zh-TW")
        self.assertFalse(manifest["source"]["third_party_content"])
        self.assertGreaterEqual(manifest["preview"]["duration_seconds"], 30)
        self.assertLessEqual(manifest["preview"]["duration_seconds"], 45)
        self.assertIn("customer result", manifest["exclusions"])
        self.assertIn("certified translation", manifest["exclusions"])

    def test_editable_alignment_is_complete_and_ordered(self):
        alignment = json.loads((SAMPLE / "delivery" / "aligned-source.json").read_text())
        segments = alignment["segments"]

        self.assertEqual(alignment["source_language"], "en")
        self.assertEqual(alignment["target_language"], "zh-TW")
        self.assertEqual(len(segments), 8)
        self.assertEqual([item["id"] for item in segments], [f"seg-{n:03d}" for n in range(1, 9)])
        self.assertTrue(all(item["start_ms"] < item["end_ms"] for item in segments))
        self.assertTrue(all(left["end_ms"] <= right["start_ms"] for left, right in zip(segments, segments[1:])))
        self.assertTrue(all(item["source"] and item["target"] for item in segments))

    def test_delivery_hashes_match_every_listed_file(self):
        checksum_lines = (SAMPLE / "delivery" / "SHA256SUMS").read_text().splitlines()
        self.assertGreaterEqual(len(checksum_lines), 15)

        for line in checksum_lines:
            digest, relative_path = line.split("  ", 1)
            payload = (SAMPLE / relative_path).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), digest, relative_path)

    def test_zip_is_verified_and_contains_the_promised_packet(self):
        archive = SAMPLE / "artifacts" / "bilingual-lecture-pack-sample.zip"
        expected_digest = (SAMPLE / "artifacts" / "bilingual-lecture-pack-sample.zip.sha256").read_text().split()[0]
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), expected_digest)

        with zipfile.ZipFile(archive) as packet:
            self.assertIsNone(packet.testzip())
            names = set(packet.namelist())

        expected = {
            "source/lecture-source.wav",
            "working/asr-draft.srt",
            "delivery/transcript/english-transcript.md",
            "delivery/subtitles/en.srt",
            "delivery/subtitles/zh-TW.srt",
            "delivery/aligned-source.json",
            "delivery/study-companion/study-companion.tex",
            "delivery/study-companion/study-companion.pdf",
            "delivery/preview/bilingual-caption-preview.mp4",
            "delivery/manifest.json",
            "delivery/issue-ledger.md",
            "delivery/SHA256SUMS",
        }
        self.assertTrue(expected.issubset(names))

    def test_binary_outputs_have_expected_container_signatures(self):
        pdf = (SAMPLE / "delivery" / "study-companion" / "study-companion.pdf").read_bytes()
        mp4 = (SAMPLE / "delivery" / "preview" / "bilingual-caption-preview.mp4").read_bytes()
        wav = (SAMPLE / "source" / "lecture-source.wav").read_bytes()
        poster = (SAMPLE / "delivery" / "preview" / "poster.png").read_bytes()

        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertEqual(mp4[4:8], b"ftyp")
        self.assertEqual(wav[:4], b"RIFF")
        self.assertEqual(wav[8:12], b"WAVE")
        self.assertEqual(poster[:8], b"\x89PNG\r\n\x1a\n")

    def test_public_copy_keeps_sample_boundaries_visible(self):
        readme = (SAMPLE / "README.md").read_text()
        source_note = (SAMPLE / "source" / "source-note.md").read_text()
        issue_ledger = (SAMPLE / "delivery" / "issue-ledger.md").read_text()

        combined = "\n".join((readme, source_note, issue_ledger))
        self.assertIn("project-owned", combined)
        self.assertIn("not a customer", combined)
        self.assertIn("not a certified translation", combined)
        self.assertIn("independent native-language review", combined)


if __name__ == "__main__":
    unittest.main()
