#!/usr/bin/env python3
"""Build the deterministic public OpenHI sample packet."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from zipfile import ZIP_STORED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
OUTPUT = ARTIFACTS / "openhi-reproducibility-sample.zip"
CHECKSUM = ARTIFACTS / "openhi-reproducibility-sample.zip.sha256"
ARCHIVE_ROOT = "openhi-reproducibility-sample"
ZIP_TIMESTAMP = (2026, 9, 9, 0, 0, 0)

SOURCE_FILES = ("README.md", "build.py")
ARTIFACT_FILES = (
    "environment.json",
    "manifest.json",
    "report.md",
    "run.log",
    "summary.json",
    "synthetic-events.npz",
    "weighted-cumulative.png",
)
HASHED_ARTIFACT_FILES = tuple(
    name for name in ARTIFACT_FILES if name != "manifest.json"
)
ARCHIVE_MEMBERS = tuple(
    [f"{ARCHIVE_ROOT}/{name}" for name in SOURCE_FILES]
    + [f"{ARCHIVE_ROOT}/artifacts/{name}" for name in ARTIFACT_FILES]
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_payload() -> dict[str, bytes]:
    """Return exact public inputs after verifying the frozen build manifest."""
    manifest_path = ARTIFACTS / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit("the frozen build manifest is unavailable") from exc

    source_hashes = manifest.get("source_sha256")
    artifact_hashes = manifest.get("artifact_sha256")
    if not isinstance(source_hashes, dict) or set(source_hashes) != set(SOURCE_FILES):
        raise SystemExit("the frozen source manifest is incomplete")
    if not isinstance(artifact_hashes, dict) or set(artifact_hashes) != set(
        HASHED_ARTIFACT_FILES
    ):
        raise SystemExit("the frozen artifact manifest is incomplete")

    payload: dict[str, bytes] = {}
    for name in SOURCE_FILES:
        data = (ROOT / name).read_bytes()
        if digest(data) != source_hashes[name]:
            raise SystemExit(f"{name} no longer matches the frozen manifest")
        payload[f"{ARCHIVE_ROOT}/{name}"] = data
    for name in ARTIFACT_FILES:
        data = (ARTIFACTS / name).read_bytes()
        if name != "manifest.json" and digest(data) != artifact_hashes[name]:
            raise SystemExit(f"artifacts/{name} no longer matches the frozen manifest")
        payload[f"{ARCHIVE_ROOT}/artifacts/{name}"] = data

    if tuple(payload) != ARCHIVE_MEMBERS:
        raise SystemExit("the sample packet member order changed")
    for name in payload:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit("the sample packet contains an unsafe member path")
    return payload


def zip_info(name: str) -> ZipInfo:
    info = ZipInfo(name, ZIP_TIMESTAMP)
    info.compress_type = ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def main() -> None:
    payload = checked_payload()
    temporary = OUTPUT.with_suffix(".zip.tmp")
    try:
        with ZipFile(temporary, "w", compression=ZIP_STORED) as archive:
            for name, data in payload.items():
                archive.writestr(zip_info(name), data)
        os.replace(temporary, OUTPUT)
    finally:
        temporary.unlink(missing_ok=True)

    archive_digest = digest(OUTPUT.read_bytes())
    CHECKSUM.write_text(
        f"{archive_digest}  {OUTPUT.name}\n",
        encoding="utf-8",
    )
    print(f"{OUTPUT.name} {archive_digest}")


if __name__ == "__main__":
    main()
