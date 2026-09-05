#!/usr/bin/env python3
"""Verify a small project's source-to-claim evidence chain offline.

Proofline deliberately does not fetch URLs or upload files. A manifest points to
files below its own directory, records their SHA-256 digests, connects derived
artifacts to inputs, and makes every verified claim cite at least one file and
locator. The command exits non-zero when any boundary is broken.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "proofline/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CLAIM_STATUSES = frozenset({"verified", "unverified", "rejected"})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _text(value: Any) -> str:
    return str(value or "").strip()


def _safe_local_file(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if not relative or candidate.is_absolute():
        raise ValueError("path must be a non-empty relative path")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError("path escapes the manifest directory") from error
    if not resolved.is_file():
        raise ValueError("path is not a local file")
    return resolved


def _unique_records(
    payload: Any, *, section: str, errors: list[str]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    if not isinstance(payload, list):
        errors.append(f"{section} must be an array")
        return [], {}
    records: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(payload, start=1):
        label = f"{section}[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        record_id = _text(record.get("id"))
        if not record_id:
            errors.append(f"{label}.id is required")
            continue
        if record_id in by_id:
            errors.append(f"{label}.id duplicates {record_id!r}")
            continue
        records.append(record)
        by_id[record_id] = record
    return records, by_id


def verify_manifest(path: Path) -> dict[str, Any]:
    manifest_path = path.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {
            "valid": False,
            "schema_version": "",
            "manifest": str(manifest_path),
            "files_checked": 0,
            "claims_checked": 0,
            "transformations_checked": 0,
            "errors": [f"manifest could not be read: {type(error).__name__}"],
            "warnings": [],
        }

    if not isinstance(payload, dict):
        errors.append("manifest root must be an object")
        payload = {}
    schema_version = _text(payload.get("schema_version"))
    if schema_version != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION!r}")

    project = payload.get("project")
    if not isinstance(project, dict):
        errors.append("project must be an object")
    else:
        if not _text(project.get("name")):
            errors.append("project.name is required")
        if not _text(project.get("license")):
            warnings.append("project.license is empty; public reuse terms are unclear")

    files, files_by_id = _unique_records(
        payload.get("files"), section="files", errors=errors
    )
    actual_hashes: dict[str, str] = {}
    for index, record in enumerate(files, start=1):
        record_id = _text(record.get("id"))
        label = f"files[{index}]({record_id})"
        relative = _text(record.get("path"))
        expected = _text(record.get("sha256"))
        if not SHA256_RE.fullmatch(expected):
            errors.append(f"{label}.sha256 must be 64 lowercase hexadecimal characters")
            continue
        try:
            local_path = _safe_local_file(manifest_path.parent, relative)
        except ValueError as error:
            errors.append(f"{label}.path {error}")
            continue
        actual = sha256_file(local_path)
        actual_hashes[record_id] = actual
        if actual != expected:
            errors.append(f"{label} hash mismatch")

    transformations, transformations_by_id = _unique_records(
        payload.get("transformations", []),
        section="transformations",
        errors=errors,
    )
    for index, record in enumerate(transformations, start=1):
        record_id = _text(record.get("id"))
        label = f"transformations[{index}]({record_id})"
        inputs = record.get("inputs")
        outputs = record.get("outputs")
        for key, references in (("inputs", inputs), ("outputs", outputs)):
            if not isinstance(references, list) or not references:
                errors.append(f"{label}.{key} must be a non-empty array")
                continue
            for reference in references:
                reference_id = _text(reference)
                if reference_id not in files_by_id:
                    errors.append(f"{label}.{key} references unknown file {reference_id!r}")
        if isinstance(inputs, list) and isinstance(outputs, list):
            overlap = {_text(item) for item in inputs} & {_text(item) for item in outputs}
            if overlap:
                errors.append(f"{label} cannot use the same file as input and output")
        if not _text(record.get("method")):
            errors.append(f"{label}.method is required")

    claims, claims_by_id = _unique_records(
        payload.get("claims"), section="claims", errors=errors
    )
    verified_claims = 0
    for index, record in enumerate(claims, start=1):
        record_id = _text(record.get("id"))
        label = f"claims[{index}]({record_id})"
        if not _text(record.get("statement")):
            errors.append(f"{label}.statement is required")
        status = _text(record.get("status"))
        if status not in CLAIM_STATUSES:
            errors.append(f"{label}.status must be verified, unverified, or rejected")
        evidence = record.get("evidence")
        if status == "verified":
            verified_claims += 1
        if not isinstance(evidence, list):
            errors.append(f"{label}.evidence must be an array")
            continue
        if status == "verified" and not evidence:
            errors.append(f"{label}.evidence is required for a verified claim")
            continue
        for evidence_index, item in enumerate(evidence, start=1):
            evidence_label = f"{label}.evidence[{evidence_index}]"
            if not isinstance(item, dict):
                errors.append(f"{evidence_label} must be an object")
                continue
            file_id = _text(item.get("file_id"))
            if file_id not in files_by_id:
                errors.append(f"{evidence_label} references unknown file {file_id!r}")
            if not _text(item.get("locator")):
                errors.append(f"{evidence_label}.locator is required")

    # Touch the indexes so static checks catch accidental removal of uniqueness.
    del transformations_by_id, claims_by_id
    return {
        "valid": not errors,
        "schema_version": schema_version,
        "manifest": str(manifest_path),
        "files_checked": len(actual_hashes),
        "claims_checked": len(claims),
        "verified_claims": verified_claims,
        "transformations_checked": len(transformations),
        "errors": errors,
        "warnings": warnings,
    }


def render_text(report: dict[str, Any]) -> str:
    state = "PASS" if report["valid"] else "FAIL"
    lines = [
        f"Proofline {state}",
        f"Manifest: {report['manifest']}",
        (
            "Checked: "
            f"{report['files_checked']} files, "
            f"{report['claims_checked']} claims, "
            f"{report['transformations_checked']} transformations"
        ),
    ]
    lines.extend(f"ERROR: {message}" for message in report["errors"])
    lines.extend(f"WARNING: {message}" for message in report["warnings"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify an offline source-to-claim provenance manifest."
    )
    parser.add_argument("manifest", type=Path, help="path to a proofline/v1 manifest")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="report format (default: text)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = verify_manifest(args.manifest)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
