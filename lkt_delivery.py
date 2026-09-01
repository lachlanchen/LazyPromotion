#!/usr/bin/env python3
"""Validate a sanitized LKT fit intake and render a truth-safe delivery packet.

This module accepts metadata only. It deliberately has no fields for names,
contact details, source paths, URLs, excerpts, document contents, or payment
state, and rejects unknown fields so those values cannot silently enter a
generated packet.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


MAX_INPUT_BYTES = 32_768
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")
LANGUAGE_TAG = re.compile(r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})?$")

ROOT_FIELDS = {
    "schema_version",
    "artifact_id",
    "prepared_on",
    "input_classification",
    "source_status",
    "collection",
    "rights",
    "privacy",
    "existing_machine",
    "requested_scope",
    "citation",
    "proof_plan",
}

NESTED_FIELDS = {
    "collection": {
        "format",
        "bounded",
        "approximate_items",
        "language_goal",
        "intended_readers",
    },
    "language_goal": {"goal", "source_language", "output_language"},
    "rights": {"status", "basis"},
    "privacy": {
        "processing_boundary",
        "sample_payload_included",
        "sensitive_identifiers_included",
    },
    "existing_machine": {"available", "memory_gib", "accelerator"},
    "requested_scope": {
        "browser_proof",
        "custom_ocr",
        "hardware_or_shipping",
        "production_deployment",
        "uptime_or_sla",
    },
    "citation": {
        "stable_source_id_available",
        "page_or_locator_available",
        "content_fingerprint_allowed",
    },
    "proof_plan": {"representative_items", "review_questions", "browser_cards"},
}

FORMATS = {"structured_jsonl", "searchable_pdf", "plain_text", "mixed_text", "image_only_pdf"}
GOALS = {"exact_search", "lexical_search", "multilingual_search", "multilingual_cards"}
READERS = {"individual_reader", "small_internal_team", "public_demo"}
RIGHTS_STATUSES = {"confirmed", "unconfirmed", "blocked"}
RIGHTS_BASES = {"owner_controlled", "licensed", "public_domain", "unknown"}
PRIVACY_BOUNDARIES = {"local_only", "approved_private_environment", "unresolved"}
ACCELERATORS = {"none", "integrated", "discrete"}
SOURCE_STATUSES = {"sanitized_hypothetical", "project_owned_public_example"}


class IntakeValidationError(ValueError):
    """Raised when an intake could contain data or is structurally ambiguous."""


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IntakeValidationError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IntakeValidationError(f"{path} must be an object")
    return value


def _require_exact_fields(value: dict[str, Any], expected: set[str], path: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        raise IntakeValidationError(f"{path} is missing fields: {', '.join(missing)}")
    if unknown:
        raise IntakeValidationError(
            f"{path} contains unsupported fields: {', '.join(unknown)}; "
            "source content and customer identifiers are never accepted"
        )


def _require_bool(value: Any, path: str) -> bool:
    if type(value) is not bool:
        raise IntakeValidationError(f"{path} must be true or false")
    return value


def _require_int(value: Any, path: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise IntakeValidationError(f"{path} must be an integer from {minimum} to {maximum}")
    return value


def _require_choice(value: Any, path: str, choices: set[str]) -> str:
    if not isinstance(value, str) or value not in choices:
        raise IntakeValidationError(f"{path} must be one of: {', '.join(sorted(choices))}")
    return value


def validate_intake(intake: Any) -> dict[str, Any]:
    """Validate and return a metadata-only LKT intake.

    Fit problems such as unconfirmed rights remain valid metadata and are
    represented as a no-go decision. Data-bearing or ambiguous inputs fail.
    """

    root = _require_object(intake, "intake")
    _require_exact_fields(root, ROOT_FIELDS, "intake")

    if root["schema_version"] != 1:
        raise IntakeValidationError("schema_version must be 1")
    if not isinstance(root["artifact_id"], str) or not SAFE_ID.fullmatch(root["artifact_id"]):
        raise IntakeValidationError("artifact_id must be a lowercase, non-identifying slug")
    if not isinstance(root["prepared_on"], str):
        raise IntakeValidationError("prepared_on must be an ISO date")
    try:
        date.fromisoformat(root["prepared_on"])
    except ValueError as exc:
        raise IntakeValidationError("prepared_on must be a real ISO date") from exc
    if root["input_classification"] != "sanitized_example_only":
        raise IntakeValidationError("input_classification must be sanitized_example_only")
    _require_choice(root["source_status"], "source_status", SOURCE_STATUSES)

    collection = _require_object(root["collection"], "collection")
    _require_exact_fields(collection, NESTED_FIELDS["collection"], "collection")
    _require_choice(collection["format"], "collection.format", FORMATS)
    _require_bool(collection["bounded"], "collection.bounded")
    approximate_items = _require_int(
        collection["approximate_items"], "collection.approximate_items", 1, 10_000_000
    )
    _require_choice(collection["intended_readers"], "collection.intended_readers", READERS)

    language_goal = _require_object(collection["language_goal"], "collection.language_goal")
    _require_exact_fields(language_goal, NESTED_FIELDS["language_goal"], "collection.language_goal")
    _require_choice(language_goal["goal"], "collection.language_goal.goal", GOALS)
    for field in ("source_language", "output_language"):
        value = language_goal[field]
        if not isinstance(value, str) or not LANGUAGE_TAG.fullmatch(value):
            raise IntakeValidationError(
                f"collection.language_goal.{field} must be a short BCP-47-style language tag"
            )

    rights = _require_object(root["rights"], "rights")
    _require_exact_fields(rights, NESTED_FIELDS["rights"], "rights")
    _require_choice(rights["status"], "rights.status", RIGHTS_STATUSES)
    _require_choice(rights["basis"], "rights.basis", RIGHTS_BASES)
    if rights["status"] == "confirmed" and rights["basis"] == "unknown":
        raise IntakeValidationError("confirmed rights require a known rights basis")

    privacy = _require_object(root["privacy"], "privacy")
    _require_exact_fields(privacy, NESTED_FIELDS["privacy"], "privacy")
    _require_choice(privacy["processing_boundary"], "privacy.processing_boundary", PRIVACY_BOUNDARIES)
    if _require_bool(privacy["sample_payload_included"], "privacy.sample_payload_included"):
        raise IntakeValidationError("sample_payload_included must be false; this tool never accepts source data")
    if _require_bool(
        privacy["sensitive_identifiers_included"], "privacy.sensitive_identifiers_included"
    ):
        raise IntakeValidationError(
            "sensitive_identifiers_included must be false; sanitize the intake before use"
        )

    machine = _require_object(root["existing_machine"], "existing_machine")
    _require_exact_fields(machine, NESTED_FIELDS["existing_machine"], "existing_machine")
    _require_bool(machine["available"], "existing_machine.available")
    _require_int(machine["memory_gib"], "existing_machine.memory_gib", 1, 1024)
    _require_choice(machine["accelerator"], "existing_machine.accelerator", ACCELERATORS)

    scope = _require_object(root["requested_scope"], "requested_scope")
    _require_exact_fields(scope, NESTED_FIELDS["requested_scope"], "requested_scope")
    for field in sorted(NESTED_FIELDS["requested_scope"]):
        _require_bool(scope[field], f"requested_scope.{field}")

    citation = _require_object(root["citation"], "citation")
    _require_exact_fields(citation, NESTED_FIELDS["citation"], "citation")
    for field in sorted(NESTED_FIELDS["citation"]):
        _require_bool(citation[field], f"citation.{field}")

    proof = _require_object(root["proof_plan"], "proof_plan")
    _require_exact_fields(proof, NESTED_FIELDS["proof_plan"], "proof_plan")
    representative_items = _require_int(
        proof["representative_items"], "proof_plan.representative_items", 1, 50
    )
    _require_int(proof["review_questions"], "proof_plan.review_questions", 5, 30)
    _require_int(proof["browser_cards"], "proof_plan.browser_cards", 1, 3)
    if representative_items > approximate_items:
        raise IntakeValidationError(
            "proof_plan.representative_items cannot exceed collection.approximate_items"
        )

    return root


def load_intake(path: Path) -> dict[str, Any]:
    """Load one small, sanitized JSON file without accepting duplicate fields."""

    if path.stat().st_size > MAX_INPUT_BYTES:
        raise IntakeValidationError(f"intake exceeds the {MAX_INPUT_BYTES}-byte metadata limit")
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_object_without_duplicate_keys
        )
    except json.JSONDecodeError as exc:
        raise IntakeValidationError(f"invalid JSON: {exc.msg}") from exc
    return validate_intake(payload)


def evaluate_fit(intake: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic intake-stage decision and its explicit reasons."""

    blocking: list[str] = []
    separate_scope: list[str] = []
    rights = intake["rights"]
    privacy = intake["privacy"]
    collection = intake["collection"]
    machine = intake["existing_machine"]
    scope = intake["requested_scope"]
    citation = intake["citation"]

    if rights["status"] != "confirmed":
        blocking.append("source rights are not confirmed")
    if not collection["bounded"]:
        blocking.append("the collection is not bounded")
    if privacy["processing_boundary"] == "unresolved":
        blocking.append("the approved privacy boundary is unresolved")
    if not citation["stable_source_id_available"]:
        blocking.append("stable source identifiers are unavailable")
    if not citation["page_or_locator_available"]:
        blocking.append("a checkable page or record locator is unavailable")

    if collection["format"] == "image_only_pdf" or scope["custom_ocr"]:
        separate_scope.append("image-only material or custom OCR is outside the sprint")
    if not machine["available"] or scope["hardware_or_shipping"]:
        separate_scope.append("hardware supply or shipping is outside the sprint")
    if scope["production_deployment"]:
        separate_scope.append("production deployment is outside the sprint")
    if scope["uptime_or_sla"]:
        separate_scope.append("uptime commitments and production SLAs are outside the sprint")
    if not scope["browser_proof"]:
        separate_scope.append("the fixed sprint deliverable is a small browser proof")

    if blocking:
        decision = "NO-GO"
    elif separate_scope:
        decision = "SEPARATE SCOPE"
    else:
        decision = "GO TO REPRESENTATIVE-PROOF PLAN"
    return {"decision": decision, "blocking": blocking, "separate_scope": separate_scope}


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _format_items(items: list[str], fallback: str) -> str:
    values = items or [fallback]
    return "\n".join(f"- {item}." for item in values)


def render_delivery_packet(intake: dict[str, Any]) -> str:
    """Render the validated intake as deterministic Markdown."""

    intake = validate_intake(intake)
    fit = evaluate_fit(intake)
    collection = intake["collection"]
    goal = collection["language_goal"]
    rights = intake["rights"]
    privacy = intake["privacy"]
    machine = intake["existing_machine"]
    citation = intake["citation"]
    proof = intake["proof_plan"]

    current_reasons = [*fit["blocking"], *fit["separate_scope"]]
    reason_text = _format_items(current_reasons, "the sanitized intake passes the bounded preflight gates")
    locator = "source ID + page/record locator"
    if citation["content_fingerprint_allowed"]:
        locator += " + content fingerprint"

    return f"""# LKT collection-fit delivery packet

> **TRUTH STATUS — SANITIZED PLANNING PACKET; NOT A CUSTOMER RESULT.**
>
> **DATA BOUNDARY —** The input passed the metadata-only structure and declaration checks. It declares that no source payload or sensitive identifier is included; the generator cannot independently prove de-identification.
>
> **EVIDENCE BOUNDARY —** Every representative-proof step below is planned, not executed or measured. This packet is not a testimonial or benchmark.
>
> **COMMERCIAL BOUNDARY —** Commercial outcomes are outside this packet and are not inferred from it.

| Packet metadata | Value |
| --- | --- |
| Prepared on | **{intake['prepared_on']}** |
| Artifact | `{intake['artifact_id']}` |
| Source status | `{intake['source_status']}` |
| Input classification | `{intake['input_classification']}` |

## Decision summary

**{fit['decision']}**

{reason_text}

This is an intake-stage boundary, not proof that ingestion, retrieval, rendering, or performance has succeeded.

## Rights, privacy, and bounded-scope validation

| Gate | Sanitized intake | Pass for fixed sprint |
| --- | --- | --- |
| Rights | `{rights['status']}` via `{rights['basis']}` | {_yes_no(rights['status'] == 'confirmed')} |
| Collection boundary | `{collection['approximate_items']:,}` approximate items; bounded `{_yes_no(collection['bounded'])}` | {_yes_no(collection['bounded'])} |
| One language goal | `{goal['goal']}` (`{goal['source_language']}` → `{goal['output_language']}`) | yes |
| Privacy boundary | `{privacy['processing_boundary']}` | {_yes_no(privacy['processing_boundary'] != 'unresolved')} |
| Source payload in intake | declared `no` | yes |
| Sensitive identifiers in intake | declared `no` | yes |
| Existing machine | available `{_yes_no(machine['available'])}`; {machine['memory_gib']} GiB; `{machine['accelerator']}` accelerator | {_yes_no(machine['available'])} |
| Checkable citation | source ID `{_yes_no(citation['stable_source_id_available'])}`; locator `{_yes_no(citation['page_or_locator_available'])}` | {_yes_no(citation['stable_source_id_available'] and citation['page_or_locator_available'])} |

## Data, privacy, and citation map

```text
authorized source (never supplied to this intake generator)
  -> owner-selected representative set inside the approved processing boundary
  -> local extraction or reviewed structured export
  -> local exact/lexical index
  -> retrieved record with {locator}
  -> normalized cited card
  -> small browser proof on the existing machine
```

- Format classification: `{collection['format']}`.
- Intended-reader class: `{collection['intended_readers']}`.
- Approved processing boundary: `{privacy['processing_boundary']}`.
- The proof operator must keep the source and generated index inside that boundary.
- Generated context must be labelled separately from retrieved source facts.
- Citation fields are deterministic payloads; a model must not invent or rewrite them.
- This repository receives only the sanitized intake and the resulting metadata-only packet.

## Representative-proof plan

1. Inside the approved environment, the collection owner selects **{proof['representative_items']}** representative items. Do not pass them through this generator or commit them to this repository.
2. Verify text extraction for `{collection['format']}` and retain stable source IDs before indexing. Image-only files stop at the custom-OCR exclusion.
3. Build a local exact/lexical index on the existing {machine['memory_gib']} GiB machine and preserve the approved locator fields.
4. Run **{proof['review_questions']}** owner-reviewed questions that cover exact terms, lexical variants, misses, and the single `{goal['goal']}` goal. Record evidence, not impressions.
5. Render **{proof['browser_cards']}** small browser card(s). Each accepted source fact must resolve to its stored citation; generated context must be visibly distinct.
6. Record failures and issue the post-proof go/no-go decision. Do not generalize the small proof into a production or whole-collection performance claim.

Planned evidence: extraction notes, index manifest, question/miss ledger, citation-resolution check, and browser capture. None is claimed to exist by this packet.

## Go/no-go boundary

Proceed from the representative proof only when:

- source rights remain confirmed for the tested material;
- the representative set stays inside the approved privacy boundary;
- text is extractable without custom OCR;
- every accepted source fact resolves to a stable source ID and page/record locator;
- the browser proof works on the existing machine; and
- any misses and generated context are labelled without overstating coverage.

Stop or create a separately reviewed scope when:

- rights become unclear or blocked;
- the collection or migration becomes unbounded;
- confidential material would enter an unapproved environment;
- custom OCR is required;
- citations cannot be checked;
- hardware, shipping, production deployment, uptime, or an SLA is required; or
- the representative proof does not support a truthful larger-scope recommendation.

## Fixed exclusions

- Hardware and shipping.
- Custom OCR.
- Production deployment, hosting, uptime commitments, and SLAs.
- Bulk or unbounded migration.
- Storage of source documents, excerpts, private indexes, contact details, or sensitive identifiers in this repository.
- Claims of whole-collection accuracy, model quality, customer outcomes, or commercial outcomes based on a planning packet.

## Human review checkpoint

A human must compare this metadata-only packet with the approved source environment before any representative proof begins. After the proof, replace planned statements only with retained, checkable evidence and keep the same rights, privacy, citation, and scope boundaries.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intake", type=Path, help="sanitized metadata-only intake JSON")
    parser.add_argument("--output", type=Path, help="write Markdown here instead of stdout")
    args = parser.parse_args(argv)

    try:
        packet = render_delivery_packet(load_intake(args.intake))
    except (OSError, IntakeValidationError) as exc:
        parser.error(str(exc))
    if args.output:
        args.output.write_text(packet, encoding="utf-8")
    else:
        print(packet, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
