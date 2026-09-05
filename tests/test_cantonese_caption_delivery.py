import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "cantonese-caption-delivery"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cues(path: Path) -> list[tuple[str, str, str]]:
    blocks = re.split(r"\n{2,}", path.read_text(encoding="utf-8").strip())
    parsed = []
    for block in blocks:
        number, timing, *text = block.splitlines()
        parsed.append((number, timing, "\n".join(text)))
    return parsed


class CantoneseCaptionDeliveryTests(unittest.TestCase):
    def test_traditional_and_simplified_tracks_share_four_cue_boundaries(self):
        traditional = cues(SAMPLE / "captions-yue-Hant.srt")
        simplified = cues(SAMPLE / "captions-zh-Hans.srt")

        self.assertEqual(len(traditional), 4)
        self.assertEqual(
            [(number, timing) for number, timing, _ in traditional],
            [(number, timing) for number, timing, _ in simplified],
        )
        self.assertEqual(traditional[0][2], "微光森林晨風醒來")
        self.assertEqual(simplified[0][2], "微光森林晨风醒来")
        self.assertEqual(traditional[-1][1], "00:00:18,020 --> 00:00:23,520")

    def test_manifest_pins_source_outputs_and_truthful_boundary(self):
        source = json.loads((SAMPLE / "source-manifest.json").read_text())
        manifest = json.loads((SAMPLE / "artifacts" / "manifest.json").read_text())

        self.assertEqual(source["source_audio_sha256"], manifest["source"]["sha256"])
        self.assertEqual(manifest["delivery"]["cue_count"], 4)
        self.assertEqual(manifest["delivery"]["tracks"], ["yue-Hant", "zh-Hans"])
        self.assertEqual(manifest["delivery"]["burned_track"], "zh-Hans")
        self.assertEqual(
            manifest["delivery"]["traditional_srt_sha256"],
            sha256(SAMPLE / "captions-yue-Hant.srt"),
        )
        self.assertEqual(
            manifest["delivery"]["simplified_srt_sha256"],
            sha256(SAMPLE / "captions-zh-Hans.srt"),
        )
        self.assertEqual(
            manifest["delivery"]["video_sha256"],
            sha256(SAMPLE / "artifacts" / "cantonese-caption-sample.mp4"),
        )
        verification = manifest["verification"]
        self.assertEqual(verification["dimensions"], "1280x720")
        self.assertEqual(verification["video_codec"], "h264")
        self.assertEqual(verification["audio_codec"], "aac")
        self.assertGreaterEqual(verification["output_duration_seconds"], 23.52)
        self.assertLessEqual(verification["output_duration_seconds"], 23.57)
        self.assertFalse(manifest["verification"]["native_spoken_word_review"])
        self.assertFalse(
            manifest["verification"]["unseen_alignment_tolerance_claimed"]
        )
        boundary = manifest["evidence_boundary"].casefold()
        for phrase in ("not a sermon", "customer work", "asr", "translation benchmark"):
            self.assertIn(phrase, boundary)


if __name__ == "__main__":
    unittest.main()
