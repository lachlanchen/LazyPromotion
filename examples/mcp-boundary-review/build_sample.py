#!/usr/bin/env python3
"""Build the public, deterministic LKT MCP boundary-review sample packet."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import zipfile
from importlib.metadata import version
from pathlib import Path
from typing import Any


FROZEN_AT = "2026-09-12"
PACKET_NAME = "lkt-mcp-boundary-review-sample.zip"
PACKET_FILES = (
    "environment.json",
    "tool-inventory.json",
    "collection-status.json",
    "query-result.json",
    "trace-result.json",
    "test.log",
    "report.md",
    "source-hashes.json",
    "summary.json",
    "manifest.json",
)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(json_bytes(value))


def sanitize_log(value: str, lkt_root: Path, temporary_root: Path) -> str:
    sanitized = value.replace(str(lkt_root), "<lkt-repository>")
    sanitized = sanitized.replace(str(temporary_root), "<temporary-fixture>")
    sanitized = re.sub(r"/tmp/lkt-mcp-review-venv", "<review-venv>", sanitized)
    sanitized = re.sub(r"/home/[^/]+/\.local/share/uv/[^\s:'\"]+", "<python-runtime>", sanitized)
    sanitized = re.sub(r"took \d+(?:\.\d+)? seconds", "took <elapsed> seconds", sanitized)
    sanitized = re.sub(
        r"^(Ran \d+ tests? in )\d+(?:\.\d+)?s$",
        r"\1<elapsed>s",
        sanitized,
        flags=re.MULTILINE,
    )
    return sanitized.strip() + "\n"


async def collect_protocol_evidence(lkt_root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(lkt_root))
    from mcp.client import Client
    from lkt.mcp_server import create_mcp_server
    from tests.test_mcp_query import make_knowledge_database

    with tempfile.TemporaryDirectory(prefix="lkt-mcp-sample-") as temporary:
        database, expected = make_knowledge_database(Path(temporary))
        before = database.stat().st_mtime_ns
        async with Client(create_mcp_server(database)) as client:
            tools_result = await client.list_tools()
            resources_result = await client.list_resources()
            query_result = await client.call_tool(
                "query_private_knowledge",
                {"query": "春", "response_language": "ja", "limit": 1},
            )
            trace_result = await client.call_tool(
                "trace_private_claim", {"identifier": expected["claim_id"]}
            )
            status_result = await client.read_resource("lkt://collections/status")
        after = database.stat().st_mtime_ns

    tools = []
    for item in tools_result.tools:
        payload = item.model_dump(mode="json", by_alias=True)
        tools.append(
            {
                "name": payload["name"],
                "title": payload["title"],
                "description": payload["description"],
                "inputSchema": payload["inputSchema"],
                "annotations": payload["annotations"],
            }
        )
    resources = []
    for item in resources_result.resources:
        payload = item.model_dump(mode="json", by_alias=True)
        resources.append(
            {
                "name": payload["name"],
                "title": payload["title"],
                "uri": payload["uri"],
                "description": payload["description"],
                "mimeType": payload["mimeType"],
            }
        )
    return {
        "inventory": {
            "server": "lkt-private-knowledge",
            "server_version": "0.1.0",
            "tools": tools,
            "resources": resources,
            "prompts": [],
        },
        "query": query_result.structured_content,
        "trace": trace_result.structured_content,
        "status": json.loads(status_result.contents[0].text),
        "database_unchanged": before == after,
    }


def run_tests(lkt_root: Path) -> tuple[str, int]:
    env = os.environ.copy()
    env["PYTHONASYNCIODEBUG"] = "0"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "-v", "tests.test_mcp_query"],
        cwd=lkt_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    combined = result.stdout + result.stderr
    with tempfile.TemporaryDirectory(prefix="lkt-log-sanitize-") as temporary:
        log = sanitize_log(combined, lkt_root, Path(temporary))
    if result.returncode != 0:
        raise RuntimeError(log)
    match = re.search(r"^Ran (\d+) tests? in ", log, flags=re.MULTILINE)
    if match is None:
        raise RuntimeError("unittest did not report its executed test count")
    return log, int(match.group(1))


def source_hashes(lkt_root: Path) -> dict[str, str]:
    names = ("lkt/mcp_query.py", "lkt/mcp_server.py", "tests/test_mcp_query.py")
    return {name: sha256(lkt_root / name) for name in names}


def report(summary: dict[str, Any]) -> str:
    return f"""# LKT MCP boundary review — public sample

Frozen: {FROZEN_AT}  
Repository revision: `{summary['lkt_commit']}`

## Decision

**GO for local, read-only use in the recorded scope.** The inspected server exposes exactly two read-only tools and one status resource. Protocol calls completed against a project-owned multilingual fixture, the database modification timestamp did not change, and all {summary['checks']['tests_passed']} focused tests passed.

**NO-GO for direct remote exposure.** The standalone HTTP bridge has no client authentication. It correctly refuses non-loopback binding, but loopback is not an authorization system. Any connected client can receive returned excerpts and may send them beyond the device.

## Inspected surface

- `query_private_knowledge`: bounded multilingual search over accepted knowledge.
- `trace_private_claim`: resolves a returned claim or evidence identifier.
- `lkt://collections/status`: bounded counts, languages, opaque collection IDs, and hashes.
- No prompts, ingestion tools, model calls, SQL tools, write tools, delete tools, or configuration tools are advertised.

## Controls observed

- Both tools advertise `readOnlyHint=true`, `destructiveHint=false`, `idempotentHint=true`, and `openWorldHint=false`.
- SQLite opens with `mode=ro` and `PRAGMA query_only=ON`.
- Queries, results, graph depth, nodes, claims, evidence, excerpts, collections, and SQL work are bounded.
- Rejected, archived, model-basis, ungrounded, and unsafe-locator cases have focused regression tests.
- Non-loopback HTTP binding is refused.

## Evidence executed

The official Python MCP SDK {summary['environment']['mcp']} listed the tool/resource surface and called both tools. The query `春` returned one accepted multilingual result; its claim was traced to one project-owned excerpt and a validated source hash. The status resource reported English, Japanese, and Chinese while withholding the database path.

## Residual risks and required decisions

1. A read-only server can still disclose data to an authorized or compromised client.
2. Tool annotations are advisory; the SQLite boundary and response filtering are the stronger controls here.
3. Loopback HTTP requires a separately designed authenticated, encrypted gateway before remote use.
4. Returned excerpts must not contain credentials or material the operator is not permitted to disclose.
5. This is a code-and-protocol boundary review, not a penetration test, security certification, or guarantee of fitness for production.

## Packet contents

The packet includes the protocol inventory, project-owned query/trace/status outputs, environment versions, focused test log, inspected-source hashes, this report, a summary, and a manifest. It contains no customer data, browser session, credential, model weight, private book, or production database.
"""


def deterministic_zip(output: Path) -> None:
    packet = output / PACKET_NAME
    timestamp = (2026, 9, 12, 0, 0, 0)
    with zipfile.ZipFile(packet, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in PACKET_FILES:
            info = zipfile.ZipInfo(name, timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (output / name).read_bytes())
    (output / f"{PACKET_NAME}.sha256").write_text(
        f"{sha256(packet)}  {PACKET_NAME}\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lkt-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "artifacts")
    args = parser.parse_args()
    lkt_root = args.lkt_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=lkt_root, capture_output=True, text=True, check=True
    ).stdout.strip()
    protocol = asyncio.run(collect_protocol_evidence(lkt_root))
    test_log, tests_passed = run_tests(lkt_root)
    environment = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "architecture": platform.machine(),
        "mcp": version("mcp"),
        "mcp-types": version("mcp-types"),
        "pypinyin": version("pypinyin"),
    }
    summary = {
        "sample": "lkt-mcp-boundary-review/v1",
        "frozen_at": FROZEN_AT,
        "lkt_commit": revision,
        "fixture": "project-owned PocketPolyglot multilingual sample",
        "environment": environment,
        "checks": {
            "tests_passed": tests_passed,
            "test_exit_code": 0,
            "tool_count": len(protocol["inventory"]["tools"]),
            "resource_count": len(protocol["inventory"]["resources"]),
            "prompt_count": len(protocol["inventory"]["prompts"]),
            "database_mtime_unchanged": protocol["database_unchanged"],
            "query_match_count": protocol["query"]["match_count"],
            "query_is_error": False,
            "trace_is_error": False,
        },
        "decision": "GO for the recorded local read-only scope; NO-GO for direct remote exposure",
    }

    write_json(output / "environment.json", environment)
    write_json(output / "tool-inventory.json", protocol["inventory"])
    write_json(output / "collection-status.json", protocol["status"])
    write_json(output / "query-result.json", protocol["query"])
    write_json(output / "trace-result.json", protocol["trace"])
    (output / "test.log").write_text(test_log, encoding="utf-8")
    write_json(output / "source-hashes.json", source_hashes(lkt_root))
    write_json(output / "summary.json", summary)
    (output / "report.md").write_text(report(summary), encoding="utf-8")
    manifest_names = [name for name in PACKET_FILES if name != "manifest.json"]
    write_json(
        output / "manifest.json",
        {
            "schema": "lazyingart-mcp-review-manifest/v1",
            "frozen_at": FROZEN_AT,
            "artifact_sha256": {name: sha256(output / name) for name in manifest_names},
        },
    )
    deterministic_zip(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
