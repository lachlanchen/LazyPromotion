#!/usr/bin/env python3
"""Build the deterministic public delivery packet for the synthetic sample."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
OUTPUT = ARTIFACTS / "sample-delivery.zip"
PUBLIC_MANIFEST = ARTIFACTS / "delivery-manifest.json"
CHECKSUM = ARTIFACTS / "sample-delivery.zip.sha256"
ZIP_TIMESTAMP = (2026, 9, 5, 0, 0, 0)

PAYLOAD = {
    "DELIVERY.md": ROOT / "delivery-index.md",
    "ISSUE_LEDGER.md": ROOT / "issue-ledger.md",
    "sources/baseline/main.tex": ROOT / "baseline" / "main.tex",
    "sources/revision/main.tex": ROOT / "revision" / "main.tex",
    "redline/redline.tex": ARTIFACTS / "redline.tex",
    "pdf/baseline.pdf": ARTIFACTS / "baseline.pdf",
    "pdf/revision.pdf": ARTIFACTS / "revision.pdf",
    "pdf/redline.pdf": ARTIFACTS / "redline.pdf",
    "logs/baseline-final.log": ARTIFACTS / "baseline-final.log",
    "logs/revision-final.log": ARTIFACTS / "revision-final.log",
    "logs/redline-final.log": ARTIFACTS / "redline-final.log",
    "evidence/build-manifest.json": ARTIFACTS / "manifest.json",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def zip_info(name: str) -> ZipInfo:
    info = ZipInfo(name, ZIP_TIMESTAMP)
    info.compress_type = ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in PAYLOAD.values() if not path.is_file()]
    if missing:
        raise SystemExit("missing packet inputs: " + ", ".join(missing))

    build_manifest = json.loads((ARTIFACTS / "manifest.json").read_text(encoding="utf-8"))
    for label, path in {
        "baseline": ROOT / "baseline" / "main.tex",
        "revision": ROOT / "revision" / "main.tex",
    }.items():
        if sha256(path.read_bytes()) != build_manifest["source_sha256"][label]:
            raise SystemExit(f"{label} source no longer matches build-manifest.json")
    for label in ("baseline", "revision", "redline"):
        path = ARTIFACTS / f"{label}.pdf"
        if sha256(path.read_bytes()) != build_manifest["pdf_sha256"][label]:
            raise SystemExit(f"{label} PDF no longer matches build-manifest.json")

    file_hashes = {name: sha256(path.read_bytes()) for name, path in sorted(PAYLOAD.items())}
    delivery_manifest = {
        "sample": "project-owned synthetic manuscript delivery",
        "evidence_boundary": (
            "Not customer work, a scientific result, journal compliance, a paid delivery, "
            "or evidence of publication."
        ),
        "archive": OUTPUT.name,
        "deterministic_timestamp": "2026-09-05T00:00:00Z",
        "files": file_hashes,
    }
    manifest_bytes = (json.dumps(delivery_manifest, indent=2, sort_keys=True) + "\n").encode()
    PUBLIC_MANIFEST.write_bytes(manifest_bytes)

    temporary = OUTPUT.with_suffix(".zip.tmp")
    try:
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for name, path in sorted(PAYLOAD.items()):
                archive.writestr(zip_info(name), path.read_bytes())
            archive.writestr(zip_info("evidence/delivery-manifest.json"), manifest_bytes)
        os.replace(temporary, OUTPUT)
    finally:
        temporary.unlink(missing_ok=True)

    digest = sha256(OUTPUT.read_bytes())
    CHECKSUM.write_text(f"{digest}  {OUTPUT.name}\n", encoding="utf-8")
    print(f"{OUTPUT.name} {digest}")


if __name__ == "__main__":
    main()
