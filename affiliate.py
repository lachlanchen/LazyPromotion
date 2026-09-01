#!/usr/bin/env python3
"""Inspect the public affiliate portfolio without exposing private links."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "affiliate-programs.json"
PRIVATE_ROOT = ROOT / ".local" / "private" / "affiliate-programs"
BLOCKED_STATES = {
    "hold",
    "delay",
    "conditional",
    "rebuild_first",
    "clarification_first",
    "terms_conflict_review",
    "migration_first",
}
REQUIRED_PRIVATE_FIELDS = {
    "accepted": bool,
    "terms_reviewed_at": str,
    "issued_url": str,
    "destination_tested": bool,
    "payout_ready": bool,
    "placement_reviewed": bool,
}


class RegistryError(ValueError):
    pass


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_registry(data)
    return data


def _valid_https(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def _host_allowed(url: str, allowed_hosts: list[str]) -> bool:
    host = (urlparse(url).hostname or "").casefold()
    return any(host == allowed.casefold() or host.endswith(f".{allowed.casefold()}") for allowed in allowed_hosts)


def validate_registry(data: dict) -> None:
    if data.get("version") != 1:
        raise RegistryError("unsupported affiliate registry version")
    try:
        date.fromisoformat(data["reviewed_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RegistryError("reviewed_at must be an ISO date") from exc
    if data.get("revenue_event") != "affiliate_commission_received":
        raise RegistryError("received commission must be the only revenue event")

    programs = data.get("programs")
    if not isinstance(programs, list) or not programs:
        raise RegistryError("programs must be a non-empty list")
    ids: set[str] = set()
    priorities: set[int] = set()
    for program in programs:
        program_id = program.get("id")
        if not isinstance(program_id, str) or not program_id or program_id in ids:
            raise RegistryError("program IDs must be unique non-empty strings")
        ids.add(program_id)
        priority = program.get("priority")
        if not isinstance(priority, int) or priority < 1 or priority in priorities:
            raise RegistryError(f"{program_id}: priority must be a unique positive integer")
        priorities.add(priority)
        urls = program.get("official_urls", {})
        for key in ("program", "terms", "application"):
            if not _valid_https(urls.get(key, "")):
                raise RegistryError(f"{program_id}: invalid official {key} URL")
        for key, value in urls.items():
            if not _valid_https(value):
                raise RegistryError(f"{program_id}: invalid official {key} URL")
        if not _valid_https(program.get("direct_url", "")):
            raise RegistryError(f"{program_id}: invalid direct URL")
        if not program.get("permitted_link_hosts"):
            raise RegistryError(f"{program_id}: missing permitted link hosts")
        if not program.get("matches") or not program.get("activation_gates"):
            raise RegistryError(f"{program_id}: matches and activation gates are required")
        if not program.get("disclosure") or not program.get("forbidden_actions"):
            raise RegistryError(f"{program_id}: disclosure and forbidden actions are required")
        if program.get("state") == "terms_conflict_review":
            if not isinstance(program.get("clarification_request"), str) or not program["clarification_request"].strip():
                raise RegistryError(f"{program_id}: terms conflict requires a written clarification request")
            if "neutral_review_permission_confirmed_in_writing" not in program["activation_gates"]:
                raise RegistryError(f"{program_id}: terms conflict requires a written-permission activation gate")
        approval_media = program.get("approval_media")
        if approval_media is not None:
            if not isinstance(approval_media, dict) or not _valid_https(approval_media.get("url", "")):
                raise RegistryError(f"{program_id}: approval media must include an official HTTPS URL")
            for key in ("asset", "version"):
                if not isinstance(approval_media.get(key), str) or not approval_media[key].strip():
                    raise RegistryError(f"{program_id}: approval media requires {key}")
            channels = approval_media.get("channels")
            if not isinstance(channels, list) or not channels or not all(
                isinstance(channel, str) and channel.strip() for channel in channels
            ):
                raise RegistryError(f"{program_id}: approval media requires named channels")
        serialized = json.dumps(program, sort_keys=True).casefold()
        for forbidden_key in ("issued_url", "referral_code", "affiliate_id", "tracking_id"):
            if f'"{forbidden_key}"' in serialized:
                raise RegistryError(f"{program_id}: private identifier field appears in public registry")
    expected = list(range(1, len(programs) + 1))
    if sorted(priorities) != expected:
        raise RegistryError("priorities must form a contiguous execution order")


def by_id(registry: dict, program_id: str) -> dict:
    for program in registry["programs"]:
        if program["id"] == program_id:
            return program
    raise RegistryError(f"unknown affiliate program: {program_id}")


def readiness(program: dict, private: dict) -> list[str]:
    failures: list[str] = []
    if program["state"] in BLOCKED_STATES:
        failures.append(f"public state is {program['state']}")
    for field, field_type in REQUIRED_PRIVATE_FIELDS.items():
        value = private.get(field)
        if not isinstance(value, field_type):
            failures.append(f"{field} is missing or has the wrong type")
        elif field_type is bool and not value:
            failures.append(f"{field} is not confirmed")
        elif field_type is str and not value.strip():
            failures.append(f"{field} is empty")
    reviewed_at = private.get("terms_reviewed_at")
    if isinstance(reviewed_at, str) and reviewed_at:
        try:
            reviewed = date.fromisoformat(reviewed_at)
            if reviewed > date.today():
                failures.append("terms_reviewed_at is in the future")
        except ValueError:
            failures.append("terms_reviewed_at is not an ISO date")
    issued_url = private.get("issued_url")
    if isinstance(issued_url, str) and issued_url:
        if not _valid_https(issued_url):
            failures.append("issued_url is not a credential-free HTTPS URL")
        elif not _host_allowed(issued_url, program["permitted_link_hosts"]):
            failures.append("issued_url host is not in the reviewed allowlist")
        elif issued_url.rstrip("/") == program["direct_url"].rstrip("/"):
            failures.append("issued_url is only the plain official URL")
    confirmed_gates = private.get("confirmed_gates")
    if not isinstance(confirmed_gates, list):
        failures.append("confirmed_gates is missing or has the wrong type")
    else:
        missing = sorted(set(program["activation_gates"]) - set(confirmed_gates))
        failures.extend(f"activation gate is unconfirmed: {gate}" for gate in missing)
    return failures


def list_programs(registry: dict) -> None:
    print("PRIORITY  STATE                PROGRAM")
    for program in sorted(registry["programs"], key=lambda item: item["priority"]):
        print(f"{program['priority']:>8}  {program['state']:<19}  {program['id']}: {program['name']}")


def print_packet(program: dict) -> None:
    print(f"# {program['name']} application packet")
    print(f"State: {program['state']} (priority {program['priority']})")
    print(f"Application: {program['official_urls']['application']}")
    print(f"Program evidence: {program['official_urls']['program']}")
    print(f"Terms to review: {program['official_urls']['terms']}")
    if program["official_urls"].get("contact"):
        print(f"Official contact: {program['official_urls']['contact']}")
    print(f"Public economics: {program['public_economics']}")
    print(f"Conversion: {program['conversion_event']}")
    print("\nApplication answer:")
    print(program["application_pitch"])
    form_packet = program.get("application_form_packet")
    if form_packet:
        print("\nPrepared non-sensitive application fields:")
        labels = {
            "website_or_social_channel": "Website / social channel",
            "promotion_plan": "Promotion plan",
            "additional_comments": "Additional comments",
        }
        for key, label in labels.items():
            value = form_packet.get(key)
            if value:
                print(f"- {label}: {value}")
        print("\nOperator-only application steps:")
        for field in form_packet.get("operator_only_fields", []):
            print(f"- {field}")
        print(f"Submission state: {form_packet.get('submit_state', 'unknown')}")
    if program.get("clarification_request"):
        print("\nWritten clarification request:")
        print(program["clarification_request"])
    if program.get("approval_media"):
        media = program["approval_media"]
        print("\nExact media submitted for approval:")
        print(f"- {media['asset']} ({media['version']}): {media['url']}")
        print(f"- Channels: {', '.join(media['channels'])}")
    print("\nExact matches:")
    for match in program["matches"]:
        print(f"- {match['asset']} — {match['placement']}: {match['reason']}")
    print("\nDisclosure:")
    print(program["disclosure"])
    print(f"Plain non-affiliate destination: {program['direct_url']}")
    if program["unknowns"]:
        print("\nMust resolve:")
        for unknown in program["unknowns"]:
            print(f"- {unknown}")


def print_private_template(program: dict) -> None:
    template = {
        "accepted": False,
        "terms_reviewed_at": "YYYY-MM-DD",
        "issued_url": "https://REPLACE-WITH-ISSUED-LINK.example/",
        "destination_tested": False,
        "payout_ready": False,
        "placement_reviewed": False,
        "confirmed_gates": [],
    }
    print(json.dumps(template, indent=2))
    print(f"# Save privately as .local/private/affiliate-programs/{program['id']}.json")


def check_ready(program: dict, confirm: bool, private_root: Path = PRIVATE_ROOT) -> int:
    if not confirm:
        raise RegistryError("refusing private read without --confirm-private-affiliate-read")
    private_path = private_root / f"{program['id']}.json"
    if not private_path.is_file():
        print(f"NOT READY: private record is absent for {program['id']}")
        return 1
    private = json.loads(private_path.read_text(encoding="utf-8"))
    failures = readiness(program, private)
    if failures:
        print(f"NOT READY: {program['id']} has {len(failures)} unresolved gate(s)")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"READY: {program['id']} passed the private activation checks; no private link was displayed")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="show the public execution order")
    packet = subparsers.add_parser("packet", help="show a public application packet")
    packet.add_argument("program_id")
    template = subparsers.add_parser("template", help="print an ignored private-record template")
    template.add_argument("program_id")
    ready = subparsers.add_parser("ready", help="validate an ignored private activation record")
    ready.add_argument("program_id")
    ready.add_argument("--confirm-private-affiliate-read", action="store_true")
    subparsers.add_parser("check", help="validate the public registry")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        registry = load_registry()
        if args.command == "list":
            list_programs(registry)
        elif args.command == "packet":
            print_packet(by_id(registry, args.program_id))
        elif args.command == "template":
            print_private_template(by_id(registry, args.program_id))
        elif args.command == "ready":
            return check_ready(
                by_id(registry, args.program_id),
                args.confirm_private_affiliate_read,
            )
        elif args.command == "check":
            print(f"OK: {len(registry['programs'])} public affiliate candidates validated")
        return 0
    except (OSError, json.JSONDecodeError, RegistryError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
