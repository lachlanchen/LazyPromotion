#!/usr/bin/env python3
"""Build a deterministic, project-owned proof for one public OpenHI stage."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "artifacts"
EXPECTED_OPENHI_COMMIT = "080ad074a4581f34e3b87e6f23be64321eda5222"
SCRIPT_NAME = "visualize_cumulative_weighted.py"
PROOF_DATE = "2026-09-09"
SENSOR_WIDTH = 64
SENSOR_HEIGHT = 32
EVENT_COUNT = 4096
STEP_US = 2000.0
ARTIFACT_FILES = (
    "environment.json",
    "manifest.json",
    "report.md",
    "run.log",
    "summary.json",
    "synthetic-events.npz",
    "weighted-cumulative.png",
)
SOURCE_FILES = ("README.md", "build.py")
BOUNDARY = (
    "Project-owned synthetic workflow evidence only: no client data, camera, "
    "optics, specimen, acquisition, calibration, compensation, reconstruction "
    "accuracy, hardware qualification, or paper-result reproduction, and no customer result."
)


class BuildError(RuntimeError):
    """Raised when the proof contract is not satisfied."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(json_bytes(value))


def git_head(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise BuildError("OpenHI root is not a readable Git checkout")
    return result.stdout.strip()


def npy_bytes(array: np.ndarray) -> bytes:
    handle = io.BytesIO()
    np.save(handle, array, allow_pickle=False)
    return handle.getvalue()


def write_deterministic_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    """Write an NPZ with fixed entry ordering, timestamps, and permissions."""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(arrays):
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, npy_bytes(arrays[name]))


def fixture_arrays() -> dict[str, np.ndarray]:
    index = np.arange(EVENT_COUNT, dtype=np.int32)
    return {
        "p": np.where(index < 2460, 1, -1).astype(np.int8),
        "t": np.linspace(0.0, 240_000.0, EVENT_COUNT, dtype=np.float32),
        "x": (index % SENSOR_WIDTH).astype(np.int16),
        "y": ((index // SENSOR_WIDTH) % SENSOR_HEIGHT).astype(np.int16),
    }


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise BuildError("stage output is not a valid PNG")
    return struct.unpack(">II", data[16:24])


def run_stage(openhi_root: Path, work: Path) -> tuple[Path, str, str]:
    fixture = work / "synthetic-events.npz"
    write_deterministic_npz(fixture, fixture_arrays())
    script = openhi_root / SCRIPT_NAME
    if not script.is_file():
        raise BuildError(f"OpenHI script is missing: {SCRIPT_NAME}")

    command = [
        sys.executable,
        str(script),
        str(fixture),
        "--sensor_width",
        str(SENSOR_WIDTH),
        "--sensor_height",
        str(SENSOR_HEIGHT),
        "--step_us",
        str(int(STEP_US)),
        "--auto_scale",
        "--no_comp",
        "--ymin",
        "-0.05",
        "--ymax",
        "1.3",
    ]
    environment = os.environ.copy()
    environment.update({"MPLBACKEND": "Agg", "PYTHONHASHSEED": "0"})
    completed = subprocess.run(
        command,
        cwd=openhi_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    sanitized_stdout = completed.stdout.replace(str(openhi_root), "<OPENHI_ROOT>").replace(
        str(work), "<WORK_DIR>"
    )
    sanitized_stderr = completed.stderr.replace(str(openhi_root), "<OPENHI_ROOT>").replace(
        str(work), "<WORK_DIR>"
    )
    sanitized_stdout = re.sub(
        r"FIXED_visualization_\d{8}_\d{6}", "<OUTPUT_DIR>", sanitized_stdout
    )
    sanitized_stderr = re.sub(
        r"FIXED_visualization_\d{8}_\d{6}", "<OUTPUT_DIR>", sanitized_stderr
    )
    log = (
        f"exit_code={completed.returncode}\n"
        f"stdout:\n{sanitized_stdout.rstrip()}\n"
        f"stderr:\n{sanitized_stderr.rstrip()}\n"
    )
    if completed.returncode != 0:
        raise BuildError(f"OpenHI stage failed\n{log}")
    plots = list(work.glob("FIXED_visualization_*/cumulative_weighted/*.png"))
    if len(plots) != 1:
        raise BuildError(f"expected one PNG output, found {len(plots)}")
    return plots[0], log, sanitized_stdout


def report_text(summary: dict[str, Any], environment: dict[str, Any]) -> str:
    checks = summary["checks"]
    return f"""# OpenHI software-stage sample report

## Decision

**GO for the selected visualization-only stage on the recorded environment.**
The public `visualize_cumulative_weighted.py` entry point accepted the frozen
synthetic NPZ interface, completed with exit code 0, and produced one readable
PNG. **NO-GO as evidence for the full OpenHI acquisition or reconstruction
pipeline.** Those paths require separate data, dependencies, parameters, and
scientific checks that this sample deliberately does not supply.

## What was tested

- Repository: `lachlanchen/OpenHI` at `{summary['openhi_commit']}`.
- Script SHA-256: `{summary['script_sha256']}`.
- Input: `{checks['events']}` synthetic events on a
  `{checks['sensor_width']} × {checks['sensor_height']}` grid over
  `{checks['duration_us']:.0f}` microseconds.
- Command: `{summary['command']}`.
- Environment: Python {environment['python']}, NumPy {environment['numpy']},
  Matplotlib {environment['matplotlib']}, backend `Agg`, {environment['machine']}.
- Result: `{checks['time_bins']}` time bins, auto-selected negative polarity
  scale `{checks['selected_negative_scale']:.3f}`, one
  `{checks['output_width']} × {checks['output_height']}` PNG.

The fixture, environment record, sanitized log, summary, output image, and
hash manifest are included beside this report.

## Failure ledger and boundary

1. The repository does not currently provide a locked root environment, so the
   exact interpreter and library versions had to be recorded.
2. The public checkout does not include the RAW acquisition named by the full
   wrapper, and some acquisition paths require external vendor SDKs. The
   end-to-end wrapper was not claimed or attempted.
3. `--no_comp` was used, so learned compensation parameters and compensated
   timing were not tested.
4. The script creates a timestamped output directory and calls `plt.show()`.
   `MPLBACKEND=Agg` made the run headless; the generated plot was then copied to
   the stable delivery name `weighted-cumulative.png`.
5. The checks establish file/interface execution, not whether a plot is a
   scientifically correct reconstruction of real measurements.

## Scope statement

{summary['boundary']}
"""


def build(output: Path, openhi_root: Path) -> None:
    openhi_root = openhi_root.resolve()
    commit = git_head(openhi_root)
    if commit != EXPECTED_OPENHI_COMMIT:
        raise BuildError(
            f"OpenHI revision mismatch: expected {EXPECTED_OPENHI_COMMIT}, got {commit}"
        )
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="openhi-proof-") as temporary:
        work = Path(temporary)
        plot, log, stdout = run_stage(openhi_root, work)
        fixture = work / "synthetic-events.npz"
        selected = re.search(r"neg_scale=([0-9.]+)", stdout)
        if not selected:
            raise BuildError("stage log did not report the selected negative scale")
        selected_negative_scale = float(selected.group(1))
        if abs(selected_negative_scale - 1.51) > 0.001:
            raise BuildError("unexpected negative polarity scale for the frozen fixture")
        width, height = png_dimensions(plot)
        arrays = fixture_arrays()
        expected_bins = int((float(arrays["t"].max()) - float(arrays["t"].min())) // STEP_US)

        shutil.copyfile(fixture, output / "synthetic-events.npz")
        shutil.copyfile(plot, output / "weighted-cumulative.png")
        (output / "run.log").write_text(log, encoding="utf-8")

    script = openhi_root / SCRIPT_NAME
    environment = {
        "backend": "Agg",
        "machine": platform.machine(),
        "matplotlib": matplotlib.__version__,
        "numpy": np.__version__,
        "operating_system": platform.system(),
        "python": platform.python_version(),
    }
    summary = {
        "boundary": BOUNDARY,
        "checks": {
            "duration_us": float(arrays["t"].max() - arrays["t"].min()),
            "events": EVENT_COUNT,
            "negative_events": int(np.count_nonzero(arrays["p"] < 0)),
            "output_height": height,
            "output_png_valid": True,
            "output_width": width,
            "positive_events": int(np.count_nonzero(arrays["p"] > 0)),
            "required_npz_arrays": sorted(arrays),
            "selected_negative_scale": selected_negative_scale,
            "sensor_height": SENSOR_HEIGHT,
            "sensor_width": SENSOR_WIDTH,
            "stage_exit_code": 0,
            "time_bins": expected_bins,
        },
        "client_data_used": False,
        "command": (
            "MPLBACKEND=Agg python <OPENHI_ROOT>/visualize_cumulative_weighted.py "
            "<WORK_DIR>/synthetic-events.npz --sensor_width 64 --sensor_height 32 "
            "--step_us 2000 --auto_scale --no_comp --ymin -0.05 --ymax 1.3"
        ),
        "network_used_by_stage": False,
        "openhi_commit": commit,
        "proof_date": PROOF_DATE,
        "script": SCRIPT_NAME,
        "script_sha256": sha256(script),
        "synthetic_fixture": True,
    }
    write_json(output / "environment.json", environment)
    write_json(output / "summary.json", summary)
    (output / "report.md").write_text(report_text(summary, environment), encoding="utf-8")

    manifest = {
        "artifact_sha256": {
            name: sha256(output / name)
            for name in ARTIFACT_FILES
            if name != "manifest.json"
        },
        "boundary": BOUNDARY,
        "manifest_self_hashed": False,
        "source_sha256": {name: sha256(ROOT / name) for name in SOURCE_FILES},
    }
    write_json(output / "manifest.json", manifest)


def check(openhi_root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="openhi-proof-check-") as temporary:
        candidate = Path(temporary)
        build(candidate, openhi_root)
        problems = []
        for name in ARTIFACT_FILES:
            committed = DEFAULT_OUTPUT / name
            generated = candidate / name
            if not committed.is_file() or committed.read_bytes() != generated.read_bytes():
                problems.append(name)
        if problems:
            raise BuildError("committed proof artifacts differ: " + ", ".join(problems))
    print("OpenHI reproducibility proof artifacts are current")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--openhi-root",
        type=Path,
        default=Path(os.environ.get("OPENHI_ROOT", ROOT.parents[2] / "OpenHI")),
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check(args.openhi_root)
    else:
        build(args.output, args.openhi_root)


if __name__ == "__main__":
    main()
