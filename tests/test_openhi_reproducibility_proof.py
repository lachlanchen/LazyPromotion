import hashlib
import json
import struct
import unittest
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "openhi-reproducibility"
ARTIFACTS = SAMPLE / "artifacts"
PACKET = ARTIFACTS / "openhi-reproducibility-sample.zip"
CHECKSUM = ARTIFACTS / "openhi-reproducibility-sample.zip.sha256"
PACKET_ROOT = "openhi-reproducibility-sample"
PACKET_MEMBERS = [
    f"{PACKET_ROOT}/README.md",
    f"{PACKET_ROOT}/build.py",
    f"{PACKET_ROOT}/artifacts/environment.json",
    f"{PACKET_ROOT}/artifacts/manifest.json",
    f"{PACKET_ROOT}/artifacts/report.md",
    f"{PACKET_ROOT}/artifacts/run.log",
    f"{PACKET_ROOT}/artifacts/summary.json",
    f"{PACKET_ROOT}/artifacts/synthetic-events.npz",
    f"{PACKET_ROOT}/artifacts/weighted-cumulative.png",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(name: str):
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


class OpenHIReproducibilityProofTests(unittest.TestCase):
    def test_summary_pins_stage_and_reports_the_narrow_result(self):
        summary = load_json("summary.json")
        self.assertEqual(
            summary["openhi_commit"],
            "080ad074a4581f34e3b87e6f23be64321eda5222",
        )
        self.assertEqual(summary["script"], "visualize_cumulative_weighted.py")
        self.assertEqual(summary["checks"]["stage_exit_code"], 0)
        self.assertEqual(summary["checks"]["time_bins"], 120)
        self.assertEqual(summary["checks"]["selected_negative_scale"], 1.51)
        self.assertTrue(summary["checks"]["output_png_valid"])
        self.assertTrue(summary["synthetic_fixture"])
        self.assertFalse(summary["client_data_used"])
        self.assertFalse(summary["network_used_by_stage"])

    def test_fixture_schema_counts_and_archive_metadata_are_frozen(self):
        fixture = ARTIFACTS / "synthetic-events.npz"
        with np.load(fixture) as data:
            self.assertEqual(sorted(data.files), ["p", "t", "x", "y"])
            self.assertTrue(all(data[name].shape == (4096,) for name in data.files))
            self.assertEqual(int(np.count_nonzero(data["p"] > 0)), 2460)
            self.assertEqual(int(np.count_nonzero(data["p"] < 0)), 1636)
            self.assertEqual(float(data["t"].min()), 0.0)
            self.assertEqual(float(data["t"].max()), 240000.0)
        with zipfile.ZipFile(fixture) as archive:
            self.assertEqual(
                [item.filename for item in archive.infolist()],
                ["p.npy", "t.npy", "x.npy", "y.npy"],
            )
            self.assertTrue(
                all(item.date_time == (1980, 1, 1, 0, 0, 0) for item in archive.infolist())
            )

    def test_plot_and_log_are_present_and_do_not_expose_local_paths(self):
        image = (ARTIFACTS / "weighted-cumulative.png").read_bytes()
        self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", image[16:24]), (1280, 701))
        log = (ARTIFACTS / "run.log").read_text(encoding="utf-8")
        self.assertIn("exit_code=0", log)
        self.assertIn("neg_scale=1.510", log)
        self.assertIn("<OPENHI_ROOT>", log)
        self.assertIn("<WORK_DIR>", log)
        self.assertNotIn("/home/", log)
        self.assertNotIn("/tmp/", log)

    def test_manifest_hashes_sources_and_artifacts(self):
        manifest = load_json("manifest.json")
        self.assertFalse(manifest["manifest_self_hashed"])
        self.assertNotIn("manifest.json", manifest["artifact_sha256"])
        for name, expected in manifest["source_sha256"].items():
            self.assertEqual(digest(SAMPLE / name), expected)
        for name, expected in manifest["artifact_sha256"].items():
            self.assertEqual(digest(ARTIFACTS / name), expected)

    def test_report_states_go_no_go_and_scientific_boundaries(self):
        report = (ARTIFACTS / "report.md").read_text(encoding="utf-8").casefold()
        for phrase in (
            "go for the selected visualization-only stage",
            "no-go as evidence for the full openhi",
            "no client data",
            "no customer result",
            "scientifically correct reconstruction",
        ):
            self.assertIn(phrase, report)

    def test_download_packet_is_exact_safe_and_byte_identical(self):
        expected_paths = {
            f"{PACKET_ROOT}/README.md": SAMPLE / "README.md",
            f"{PACKET_ROOT}/build.py": SAMPLE / "build.py",
            **{
                f"{PACKET_ROOT}/artifacts/{name}": ARTIFACTS / name
                for name in (
                    "environment.json",
                    "manifest.json",
                    "report.md",
                    "run.log",
                    "summary.json",
                    "synthetic-events.npz",
                    "weighted-cumulative.png",
                )
            },
        }
        with zipfile.ZipFile(PACKET) as archive:
            self.assertIsNone(archive.testzip())
            infos = archive.infolist()
            self.assertEqual([info.filename for info in infos], PACKET_MEMBERS)
            for info in infos:
                path = PurePosixPath(info.filename)
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
                self.assertEqual(info.date_time, (2026, 9, 9, 0, 0, 0))
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(info.create_system, 3)
                self.assertEqual((info.external_attr >> 16) & 0o777, 0o644)
                data = archive.read(info.filename)
                self.assertEqual(data, expected_paths[info.filename].read_bytes())
                lowered = data.lower()
                for forbidden in (b"/home/", b"/tmp/", b"api_key", b"secret_key"):
                    self.assertNotIn(forbidden, lowered, info.filename)

    def test_download_packet_checksum_matches_archive(self):
        line = CHECKSUM.read_text(encoding="utf-8")
        expected = f"{digest(PACKET)}  {PACKET.name}\n"
        self.assertEqual(line, expected)


if __name__ == "__main__":
    unittest.main()
