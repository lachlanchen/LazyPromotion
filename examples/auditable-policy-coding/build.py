#!/usr/bin/env python3
"""Build and verify a deterministic, wholly synthetic policy-coding sample."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs"
DEFAULT_OUTPUT = ROOT / "artifacts"
BOUNDARY = (
    "Project-owned synthetic workflow proof; not a customer result, benchmark, "
    "offer, revenue claim, or analysis of client or copyrighted text."
)
SOURCE_FILES = (
    "build.py",
    "inputs/codebook.json",
    "inputs/passages.json",
    "inputs/classifications.json",
)
ARTIFACT_FILES = ("report.md",)


class BuildError(RuntimeError):
    """Raised when an input or committed artifact violates the sample contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read valid JSON from {path}") from exc
    if not isinstance(value, dict):
        raise BuildError(f"expected an object in {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def require_nonempty_line(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise BuildError(f"{field} must be one non-empty line")
    return value


def validate(
    codebook: dict[str, Any],
    passages: dict[str, Any],
    classifications: dict[str, Any],
) -> dict[str, Any]:
    if codebook.get("frozen") is not True or codebook.get("version") != "1.0.0":
        raise BuildError("the sample requires frozen codebook version 1.0.0")
    if passages.get("synthetic") is not True:
        raise BuildError("all sample passages must be declared synthetic")
    if "no client or copyrighted source text" not in passages.get("boundary", "").casefold():
        raise BuildError("the passage boundary must exclude client and copyrighted source text")
    if classifications.get("codebook_version") != codebook["version"]:
        raise BuildError("classification and codebook versions differ")

    codes = codebook.get("codes")
    if not isinstance(codes, list) or not codes:
        raise BuildError("the codebook must contain codes")
    code_ids: list[str] = []
    for index, code in enumerate(codes):
        if not isinstance(code, dict):
            raise BuildError(f"code {index} must be an object")
        code_id = require_nonempty_line(code.get("id"), f"code {index} id")
        for field in ("label", "definition", "inclusion_rule", "exclusion_rule"):
            require_nonempty_line(code.get(field), f"code {code_id} {field}")
        code_ids.append(code_id)
    if len(code_ids) != len(set(code_ids)):
        raise BuildError("code ids must be unique")

    source_passages = passages.get("passages")
    if not isinstance(source_passages, list) or len(source_passages) != 3:
        raise BuildError("the sample must contain exactly three passages")
    passage_by_id: dict[str, dict[str, Any]] = {}
    locator_text: dict[str, str] = {}
    for passage in source_passages:
        if not isinstance(passage, dict):
            raise BuildError("each passage must be an object")
        passage_id = require_nonempty_line(passage.get("id"), "passage id")
        require_nonempty_line(passage.get("title"), f"passage {passage_id} title")
        if passage_id in passage_by_id:
            raise BuildError(f"duplicate passage id: {passage_id}")
        segments = passage.get("segments")
        if not isinstance(segments, list) or not segments:
            raise BuildError(f"passage {passage_id} has no segments")
        passage_by_id[passage_id] = passage
        for segment in segments:
            if not isinstance(segment, dict):
                raise BuildError(f"passage {passage_id} contains an invalid segment")
            locator = require_nonempty_line(segment.get("locator"), "segment locator")
            text = require_nonempty_line(segment.get("text"), f"segment {locator} text")
            if not locator.startswith(f"{passage_id}:"):
                raise BuildError(f"locator {locator} does not belong to {passage_id}")
            if locator in locator_text:
                raise BuildError(f"duplicate locator: {locator}")
            locator_text[locator] = text

    annotations = classifications.get("annotations")
    if not isinstance(annotations, list):
        raise BuildError("annotations must be a list")
    annotation_ids: list[str] = []
    evidence_count = 0
    ambiguous_count = 0
    for annotation in annotations:
        if not isinstance(annotation, dict):
            raise BuildError("each annotation must be an object")
        passage_id = require_nonempty_line(annotation.get("passage_id"), "annotation passage_id")
        if passage_id not in passage_by_id:
            raise BuildError(f"annotation references unknown passage: {passage_id}")
        annotation_ids.append(passage_id)
        applied = annotation.get("applied_codes")
        if not isinstance(applied, list) or not applied or len(applied) != len(set(applied)):
            raise BuildError(f"annotation {passage_id} needs unique applied codes")
        if any(code_id not in code_ids for code_id in applied):
            raise BuildError(f"annotation {passage_id} uses an unknown code")
        if annotation.get("primary_code") not in applied:
            raise BuildError(f"annotation {passage_id} primary code is not applied")
        require_nonempty_line(annotation.get("rationale"), f"annotation {passage_id} rationale")

        ambiguity = annotation.get("ambiguity")
        if not isinstance(ambiguity, dict) or not isinstance(ambiguity.get("flag"), bool):
            raise BuildError(f"annotation {passage_id} needs a boolean ambiguity flag")
        require_nonempty_line(ambiguity.get("note"), f"annotation {passage_id} ambiguity note")
        ambiguous_count += int(ambiguity["flag"])

        evidence = annotation.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise BuildError(f"annotation {passage_id} needs deciding evidence")
        for item in evidence:
            if not isinstance(item, dict):
                raise BuildError(f"annotation {passage_id} has invalid evidence")
            locator = require_nonempty_line(item.get("locator"), "evidence locator")
            excerpt = require_nonempty_line(item.get("excerpt"), f"evidence {locator} excerpt")
            if not locator.startswith(f"{passage_id}:") or locator not in locator_text:
                raise BuildError(f"evidence locator {locator} does not resolve in {passage_id}")
            if excerpt != locator_text[locator]:
                raise BuildError(f"evidence excerpt does not exactly match {locator}")
            evidence_count += 1

    if annotation_ids != list(passage_by_id):
        raise BuildError("annotations must cover each passage once and in source order")

    return {
        "annotation_count": len(annotations),
        "ambiguity_flags": ambiguous_count,
        "code_count": len(code_ids),
        "evidence_excerpt_count": evidence_count,
        "exact_excerpt_matches": evidence_count,
        "passage_count": len(source_passages),
    }


def render_report(
    codebook: dict[str, Any],
    passages: dict[str, Any],
    classifications: dict[str, Any],
) -> str:
    code_by_id = {code["id"]: code for code in codebook["codes"]}
    passage_by_id = {passage["id"]: passage for passage in passages["passages"]}
    lines = [
        "# Auditable policy content-coding sample",
        "",
        f"> {BOUNDARY}",
        "",
        "## Frozen codebook",
        "",
        f"Version `{codebook['version']}` was frozen on {codebook['frozen_on']}. The unit of analysis is {codebook['unit_of_analysis']}.",
        "",
    ]
    for code in codebook["codes"]:
        lines.extend(
            [
                f"### {code['id']} — {code['label']}",
                "",
                code["definition"],
                "",
                f"- Include: {code['inclusion_rule']}",
                f"- Exclude: {code['exclusion_rule']}",
                "",
            ]
        )

    lines.extend(["## Coding decisions", ""])
    for annotation in classifications["annotations"]:
        passage = passage_by_id[annotation["passage_id"]]
        labels = [f"`{code_id}` ({code_by_id[code_id]['label']})" for code_id in annotation["applied_codes"]]
        ambiguity = annotation["ambiguity"]
        lines.extend(
            [
                f"### {passage['id']} — {passage['title']}",
                "",
                " ".join(segment["text"] for segment in passage["segments"]),
                "",
                f"- Classification: {', '.join(labels)}",
                f"- Primary code: `{annotation['primary_code']}`",
                f"- Rationale: {annotation['rationale']}",
                f"- Ambiguity: {'Yes' if ambiguity['flag'] else 'No'} — {ambiguity['note']}",
                "- Deciding evidence:",
            ]
        )
        for item in annotation["evidence"]:
            lines.append(f"  - `{item['locator']}` — “{item['excerpt']}”")
        lines.append("")

    lines.extend(
        [
            "## Verification boundary",
            "",
            "The builder resolves every locator, requires every deciding excerpt to match its source segment byte for byte, validates complete passage coverage, and rejects unknown codes. It makes no network or model calls.",
            "",
        ]
    )
    return "\n".join(lines)


def build(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    codebook = load_json(INPUTS / "codebook.json")
    passages = load_json(INPUTS / "passages.json")
    classifications = load_json(INPUTS / "classifications.json")
    verification = validate(codebook, passages, classifications)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.md"
    report_path.write_text(
        render_report(codebook, passages, classifications),
        encoding="utf-8",
    )
    manifest = {
        "artifact_sha256": {name: sha256(output_dir / name) for name in ARTIFACT_FILES},
        "boundary": BOUNDARY,
        "builder": "auditable-policy-coding-v1",
        "inputs": {
            "client_data_used": False,
            "copyrighted_source_text_used": False,
            "model_calls_used": False,
            "network_used": False,
            "synthetic_passages": True,
        },
        "manifest_self_hashed": False,
        "schema_version": 1,
        "source_sha256": {name: sha256(ROOT / name) for name in SOURCE_FILES},
        "verification": verification,
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def check_committed() -> None:
    with tempfile.TemporaryDirectory(prefix="auditable-policy-coding-") as temporary:
        rebuilt = Path(temporary)
        build(rebuilt)
        for name in (*ARTIFACT_FILES, "manifest.json"):
            committed = DEFAULT_OUTPUT / name
            candidate = rebuilt / name
            if not committed.is_file():
                raise BuildError(f"missing committed artifact: {committed}")
            if committed.read_bytes() != candidate.read_bytes():
                raise BuildError(f"committed artifact is stale or changed: {committed}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="rebuild in a temporary directory and compare with committed artifacts",
    )
    arguments = parser.parse_args()
    if arguments.check:
        check_committed()
        print("auditable policy-coding artifacts verified")
    else:
        manifest = build()
        print(
            "built auditable policy-coding sample: "
            f"{manifest['verification']['passage_count']} passages, "
            f"{manifest['verification']['exact_excerpt_matches']} exact excerpts"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as exc:
        raise SystemExit(f"error: {exc}") from exc
