"""Build and verify the project-owned edge-IQA evidence packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from iqa import Thresholds, assess


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
FIXTURES = ARTIFACTS / "fixtures"
RESULTS = ARTIFACTS / "results"
SOURCE_NAMES = ("iqa.py", "api.py", "build.py", "Dockerfile", "requirements.txt")
FIXTURE_NAMES = ("reference.png", "blurred.png", "underexposed.png", "overexposed.png", "glare.png")
EXPECTED = {
    "reference.png": ("PASS", []),
    "blurred.png": ("FAIL", ["blur_or_low_detail"]),
    "underexposed.png": ("FAIL", ["blur_or_low_detail", "underexposed"]),
    "overexposed.png": ("FAIL", ["overexposed"]),
    "glare.png": ("FAIL", ["possible_glare"]),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_reference() -> np.ndarray:
    height, width = 400, 640
    image = np.full((height, width, 3), (118, 124, 132), dtype=np.uint8)
    for y in range(20, 380, 40):
        for x in range(20, 380, 40):
            shade = 60 if ((x + y) // 40) % 2 else 190
            cv2.rectangle(image, (x, y), (x + 39, y + 39), (shade,) * 3, -1)
    cv2.rectangle(image, (420, 35), (610, 135), (45, 105, 175), -1)
    cv2.circle(image, (515, 220), 65, (175, 95, 55), -1)
    cv2.line(image, (405, 325), (620, 325), (25, 25, 25), 4)
    cv2.putText(image, "EDGE IQA", (405, 375), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (35, 35, 35), 2)
    return image


def build_fixtures() -> dict[str, np.ndarray]:
    reference = make_reference()
    glare = reference.copy()
    cv2.ellipse(glare, (500, 205), (120, 70), -15, 0, 360, (255, 255, 255), -1)
    return {
        "reference.png": reference,
        "blurred.png": cv2.GaussianBlur(reference, (25, 25), 0),
        "underexposed.png": cv2.convertScaleAbs(reference, alpha=0.22, beta=0),
        "overexposed.png": cv2.convertScaleAbs(reference, alpha=0.35, beta=175),
        "glare.png": glare,
    }


def write_fixture_grid(fixtures: dict[str, np.ndarray]) -> None:
    tile_width, image_height, label_height = 320, 200, 32
    canvas = np.full((2 * (image_height + label_height), 3 * tile_width, 3), 245, dtype=np.uint8)
    for index, name in enumerate(FIXTURE_NAMES):
        row, column = divmod(index, 3)
        x0 = column * tile_width
        y0 = row * (image_height + label_height)
        thumbnail = cv2.resize(fixtures[name], (tile_width, image_height), interpolation=cv2.INTER_AREA)
        canvas[y0 : y0 + image_height, x0 : x0 + tile_width] = thumbnail
        cv2.putText(
            canvas,
            Path(name).stem.replace("_", " "),
            (x0 + 10, y0 + image_height + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (35, 35, 35),
            1,
            cv2.LINE_AA,
        )
    path = ARTIFACTS / "fixture-grid.png"
    if not cv2.imwrite(str(path), canvas, [cv2.IMWRITE_PNG_COMPRESSION, 9]):
        raise RuntimeError(f"could not write {path}")


def measure_latency(image: np.ndarray, iterations: int = 250) -> dict[str, float | int]:
    for _ in range(10):
        assess(image)
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        assess(image)
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    ordered = sorted(samples)
    return {
        "iterations": iterations,
        "median_ms": round(statistics.median(ordered), 4),
        "p95_ms": round(ordered[int(0.95 * (iterations - 1))], 4),
        "minimum_ms": round(ordered[0], 4),
    }


def build() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    fixtures = build_fixtures()
    results = {}
    for name, image in fixtures.items():
        path = FIXTURES / name
        if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 9]):
            raise RuntimeError(f"could not write {path}")
        result = assess(image, Thresholds())
        results[name] = result
        write_json(RESULTS / f"{Path(name).stem}.json", result)
    write_fixture_grid(fixtures)

    benchmark = measure_latency(fixtures["reference.png"])
    environment = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "numpy": np.__version__,
        "opencv": cv2.__version__,
        "benchmark": benchmark,
    }
    write_json(ARTIFACTS / "environment.json", environment)

    summary = {
        "fixture_count": len(fixtures),
        "synthetic_project_owned_fixtures": True,
        "client_data_used": False,
        "diagnostic_or_clinical_validation": False,
        "incorrect_view_detection_implemented": False,
        "reason": "incorrect-view rules require representative labelled domain images",
        "results": {
            name: {"status": result["status"], "reasons": result["reasons"]}
            for name, result in results.items()
        },
        "benchmark": benchmark,
    }
    write_json(ARTIFACTS / "summary.json", summary)

    report = f"""# Edge image-quality baseline report

## Result

The small CPU baseline classified the five project-owned fixtures as expected: one reference passed, while blur, underexposure, overexposure, and a large low-saturation highlight each produced an explicit reason code. On this workstation the 640×400 reference took a median of **{benchmark['median_ms']:.4f} ms** across {benchmark['iterations']} measured iterations; this is a local benchmark, not a deployment promise.

## What is inspectable

- deterministic synthetic fixtures and their individual JSON results;
- Laplacian detail, mean luminance, dark/bright clipping, and possible-glare measurements;
- explicit thresholds, reason codes, input validation, and a raw-image FastAPI boundary;
- a CPU-only Docker recipe and hashes for every source and output in this packet.

## Boundary

This is engineering-process evidence, not a customer result, medical-device validation, diagnostic software, or proof of accuracy on clinical images. The fixed thresholds are illustrative. A real milestone must calibrate them on rights-cleared, representative labelled data and keep a held-out evaluation set. Incorrect-view detection is intentionally absent until the buyer defines views and supplies representative examples; pretending that one generic heuristic solves it would be misleading.
"""
    (ARTIFACTS / "report.md").write_text(report, encoding="utf-8")

    artifact_paths = sorted(
        path for path in ARTIFACTS.rglob("*") if path.is_file() and path.name != "manifest.json"
    )
    manifest = {
        "manifest_self_hashed": False,
        "source_sha256": {name: digest(ROOT / name) for name in SOURCE_NAMES},
        "artifact_sha256": {
            str(path.relative_to(ARTIFACTS)): digest(path) for path in artifact_paths
        },
    }
    write_json(ARTIFACTS / "manifest.json", manifest)


def check() -> None:
    summary = json.loads((ARTIFACTS / "summary.json").read_text(encoding="utf-8"))
    if summary["results"] != {
        name: {"status": status, "reasons": reasons}
        for name, (status, reasons) in EXPECTED.items()
    }:
        raise SystemExit("stored fixture results do not match the expected boundary")
    for name, image in build_fixtures().items():
        stored = cv2.imread(str(FIXTURES / name), cv2.IMREAD_COLOR)
        if stored is None or not np.array_equal(stored, image):
            raise SystemExit(f"stored fixture is not deterministic: {name}")
        expected = json.loads((RESULTS / f"{Path(name).stem}.json").read_text(encoding="utf-8"))
        if assess(stored) != expected:
            raise SystemExit(f"stored assessment is stale: {name}")
    grid = cv2.imread(str(ARTIFACTS / "fixture-grid.png"), cv2.IMREAD_COLOR)
    if grid is None or tuple(grid.shape) != (464, 960, 3):
        raise SystemExit("fixture grid is missing or has the wrong dimensions")

    manifest = json.loads((ARTIFACTS / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise SystemExit(f"source hash mismatch: {name}")
    for name, expected in manifest["artifact_sha256"].items():
        if digest(ARTIFACTS / name) != expected:
            raise SystemExit(f"artifact hash mismatch: {name}")
    benchmark = summary["benchmark"]
    if benchmark["iterations"] < 100 or benchmark["median_ms"] <= 0:
        raise SystemExit("benchmark evidence is incomplete")
    print("edge image-quality evidence packet verified")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
    else:
        build()
        check()
    return 0


if __name__ == "__main__":
    sys.exit(main())
