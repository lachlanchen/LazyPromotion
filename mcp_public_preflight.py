#!/usr/bin/env python3
"""Create a private, review-ready preflight for one public GitHub MCP server.

The preflight is intentionally static. It reads public repository metadata and
selected text blobs through explicit GitHub API GET requests, pins one commit,
and never clones the repository or executes its code.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import re
import stat
import subprocess
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote, urlsplit


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = ROOT / ".local" / "mcp-preflight"
API_VERSION = "2022-11-28"
MAX_TREE_ENTRIES = 100_000
MAX_BLOB_BYTES = 262_144
DEFAULT_MAX_FILES = 28
MAX_FILES_LIMIT = 60

REPOSITORY_PART_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z")
SHA_RE = re.compile(r"\A[a-f0-9]{40}\Z")
SAFE_PATH_RE = re.compile(r"\A[^\x00\r\n]+\Z")
BASE64_RE = re.compile(r"\A(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?\Z")
TEXT_EXTENSIONS = {
    ".cjs",
    ".go",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".rs",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
MANIFEST_NAMES = {
    ".mcp.json",
    "cargo.toml",
    "deno.json",
    "go.mod",
    "manifest.json",
    "mcp.json",
    "package.json",
    "pyproject.toml",
    "server.json",
}
TRANSPORT_PATTERNS = {
    "stdio": re.compile(r"\bstdio\b", re.IGNORECASE),
    "Streamable HTTP": re.compile(r"\bstreamable[ _-]*http\b", re.IGNORECASE),
    "SSE": re.compile(r"\b(?:server[ _-]*sent events?|sse)\b", re.IGNORECASE),
    "WebSocket": re.compile(r"\bwebsockets?\b", re.IGNORECASE),
}
ENV_PATTERNS = (
    re.compile(r"\bprocess\.env\.([A-Z][A-Z0-9_]{2,})\b"),
    re.compile(r"\bos\.environ(?:\.get)?\(?(?:\[)?[\"']([A-Z][A-Z0-9_]{2,})[\"']"),
    re.compile(r"\bgetenv\(\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']"),
    re.compile(r"\$\{([A-Z][A-Z0-9_]{2,})\}"),
    re.compile(
        r"\b([A-Z][A-Z0-9_]{1,}(?:_API_KEY|_TOKEN|_SECRET|_PASSWORD|_DATABASE|_DB|_URL))\b"
    ),
)
URL_RE = re.compile(r"https?://([A-Za-z0-9.-]+)(?::\d+)?(?:[/\s\"'`<>)]|\Z)")
IGNORED_EXTERNAL_HOSTS = {
    "badge.fury.io",
    "github.com",
    "img.shields.io",
    "modelcontextprotocol.io",
    "npmjs.com",
    "pypi.org",
    "spec.modelcontextprotocol.io",
    "www.github.com",
}
MUTATING_WORDS = {
    "add",
    "create",
    "delete",
    "execute",
    "import",
    "install",
    "post",
    "publish",
    "remove",
    "run",
    "send",
    "set",
    "update",
    "upload",
    "write",
}

TEN_CHECKS = (
    "Protocol version negotiation.",
    "Advertised versus live tool and resource discovery.",
    "One agreed valid tool call, including output bounds and result handoff.",
    "One agreed valid resource read, including locator resolution by the intended client.",
    "Unknown tool or resource rejection.",
    "Malformed or missing input rejection.",
    "Actual reads, writes, external calls, and approval gates.",
    "Credential, path, and private-context disclosure in agreed outputs and logs.",
    "One safe failure or timeout case.",
    "Client and transport authentication and isolation boundary.",
)

Runner = Callable[..., subprocess.CompletedProcess[str]]


class PreflightError(RuntimeError):
    """A safe public-repository preflight failure."""


class Fetcher(Protocol):
    def get(self, endpoint: str) -> Any: ...


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def default_runner(
    command: list[str], **kwargs: Any
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, **kwargs)


class GhFetcher:
    """Authenticated GitHub API reader restricted to explicit GET requests."""

    def __init__(self, runner: Runner = default_runner) -> None:
        self.runner = runner

    def get(self, endpoint: str) -> Any:
        command = [
            "gh",
            "api",
            "--method",
            "GET",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            f"X-GitHub-Api-Version: {API_VERSION}",
            endpoint,
        ]
        try:
            completed = self.runner(
                command,
                text=True,
                capture_output=True,
                check=False,
                timeout=60,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PreflightError("GitHub public metadata is unavailable") from exc
        if completed.returncode != 0:
            # GitHub CLI diagnostics can contain account details. Do not relay them.
            raise PreflightError(f"GitHub GET failed for {endpoint}")
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise PreflightError(f"GitHub returned invalid JSON for {endpoint}") from exc


def parse_repository_url(value: str) -> tuple[str, str, str]:
    """Return owner, repository, and canonical URL for a clean public repo URL."""

    if not isinstance(value, str) or value.strip() != value or "%" in value:
        raise PreflightError("repository URL must be a clean GitHub URL")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise PreflightError("repository URL must be a clean GitHub URL") from exc
    if (
        parsed.scheme != "https"
        or hostname != "github.com"
        or parsed.username
        or parsed.password
        or port is not None
        or parsed.query
        or parsed.fragment
    ):
        raise PreflightError("repository URL must be https://github.com/owner/repo")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise PreflightError("repository URL must not include a file, issue, or branch path")
    owner, repository = parts
    if repository.endswith(".git"):
        repository = repository[:-4]
    if not REPOSITORY_PART_RE.fullmatch(owner) or not REPOSITORY_PART_RE.fullmatch(repository):
        raise PreflightError("repository owner or name is invalid")
    return owner, repository, f"https://github.com/{owner}/{repository}"


def _safe_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise PreflightError(f"GitHub {label} is invalid")
    return value


def _safe_tree_path(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not SAFE_PATH_RE.fullmatch(value)
        or value.startswith("/")
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise PreflightError("GitHub tree contains an unsafe path")
    return value


def candidate_score(path: str) -> tuple[int, int, str]:
    lower = path.casefold()
    name = Path(lower).name
    depth = lower.count("/")
    if name in {".mcp.json", "mcp.json", "server.json"}:
        bucket = 0
    elif name in MANIFEST_NAMES:
        bucket = 1
    elif "mcp" in lower and Path(lower).suffix in TEXT_EXTENSIONS:
        bucket = 2
    elif "server" in lower and Path(lower).suffix in TEXT_EXTENSIONS:
        bucket = 3
    elif name.startswith("readme"):
        bucket = 4
    else:
        bucket = 5
    return bucket, depth, lower


def select_text_blobs(tree: list[dict[str, Any]], *, maximum: int) -> list[dict[str, Any]]:
    if not 1 <= maximum <= MAX_FILES_LIMIT:
        raise PreflightError(f"maximum files must be between 1 and {MAX_FILES_LIMIT}")
    candidates: list[dict[str, Any]] = []
    for entry in tree:
        if not isinstance(entry, dict) or entry.get("type") != "blob":
            continue
        path = _safe_tree_path(entry.get("path"))
        size = entry.get("size")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise PreflightError("GitHub tree contains an invalid blob size")
        if size > MAX_BLOB_BYTES:
            continue
        lower = path.casefold()
        name = Path(lower).name
        relevant = (
            name in MANIFEST_NAMES
            or name.startswith("readme")
            or "mcp" in lower
            or "server" in lower
        )
        if not relevant or Path(lower).suffix not in TEXT_EXTENSIONS:
            continue
        candidates.append(
            {
                "path": path,
                "sha": _safe_sha(entry.get("sha"), "blob SHA"),
                "size": size,
            }
        )
    candidates.sort(key=lambda entry: candidate_score(entry["path"]))
    return candidates[:maximum]


def decode_blob(payload: Any) -> str:
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        raise PreflightError("GitHub blob encoding is unsupported")
    content = payload.get("content")
    size = payload.get("size")
    if (
        not isinstance(content, str)
        or isinstance(size, bool)
        or not isinstance(size, int)
        or not 0 <= size <= MAX_BLOB_BYTES
    ):
        raise PreflightError("GitHub blob payload is invalid")
    compact_content = "".join(content.split())
    if not BASE64_RE.fullmatch(compact_content):
        raise PreflightError("GitHub blob encoding is invalid")
    try:
        raw = base64.b64decode(compact_content, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise PreflightError("GitHub blob encoding is invalid") from exc
    if len(raw) != size or len(raw) > MAX_BLOB_BYTES or b"\x00" in raw:
        raise PreflightError("GitHub blob is not a bounded text file")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreflightError("GitHub blob is not UTF-8 text") from exc


def _append_detection(
    detections: dict[str, list[dict[str, str]]],
    kind: str,
    name: str,
    path: str,
) -> None:
    if not name or len(name) > 160:
        return
    item = {"name": name, "path": path}
    if item not in detections[kind]:
        detections[kind].append(item)


def detect_surface(files: list[dict[str, Any]]) -> dict[str, Any]:
    detections: dict[str, list[dict[str, str]]] = defaultdict(list)
    transport_paths: dict[str, set[str]] = defaultdict(set)
    env_paths: dict[str, set[str]] = defaultdict(set)
    host_paths: dict[str, set[str]] = defaultdict(set)

    decorator_patterns = {
        "tool": re.compile(
            r"@[A-Za-z_][\w.]*\.tool\(\s*\)\s*(?:async\s+)?def\s+([A-Za-z_][\w]*)",
            re.MULTILINE,
        ),
        "resource": re.compile(
            r"@[A-Za-z_][\w.]*\.resource\(\s*[\"']([^\"']+)[\"']",
            re.MULTILINE,
        ),
        "prompt": re.compile(
            r"@[A-Za-z_][\w.]*\.prompt\(\s*\)\s*(?:async\s+)?def\s+([A-Za-z_][\w]*)",
            re.MULTILINE,
        ),
    }
    named_decorator_patterns = {
        kind: re.compile(
            rf"@[A-Za-z_][\w.]*\.{kind}\(\s*name\s*=\s*[\"']([^\"']+)[\"']",
            re.MULTILINE,
        )
        for kind in ("tool", "resource", "prompt")
    }
    call_patterns = {
        "tool": re.compile(
            r"\b(?:registerTool|\.tool)\(\s*[\"']([^\"']+)[\"']",
            re.MULTILINE,
        ),
        "resource": re.compile(
            r"\b(?:registerResource|\.resource)\(\s*[\"']([^\"']+)[\"']",
            re.MULTILINE,
        ),
        "prompt": re.compile(
            r"\b(?:registerPrompt|\.prompt)\(\s*[\"']([^\"']+)[\"']",
            re.MULTILINE,
        ),
    }

    for item in files:
        path = item["path"]
        text = item["text"]
        for label, pattern in TRANSPORT_PATTERNS.items():
            if pattern.search(text):
                transport_paths[label].add(path)
        for kind, pattern in decorator_patterns.items():
            for match in pattern.finditer(text):
                _append_detection(detections, kind, match.group(1), path)
        for kind, pattern in named_decorator_patterns.items():
            for match in pattern.finditer(text):
                _append_detection(detections, kind, match.group(1), path)
        for kind, pattern in call_patterns.items():
            for match in pattern.finditer(text):
                _append_detection(detections, kind, match.group(1), path)
        for pattern in ENV_PATTERNS:
            for match in pattern.finditer(text):
                env_paths[match.group(1)].add(path)
        if Path(path).suffix.casefold() != ".md":
            for match in URL_RE.finditer(text):
                host = match.group(1).casefold().strip(".")
                if host and host not in IGNORED_EXTERNAL_HOSTS:
                    host_paths[host].add(path)

    for kind in detections:
        detections[kind].sort(key=lambda item: (item["name"].casefold(), item["path"]))
    capability_names = [
        item["name"]
        for kind in ("tool", "resource", "prompt")
        for item in detections[kind]
    ]
    mutating = sorted(
        {
            name
            for name in capability_names
            if MUTATING_WORDS
            & set(filter(None, re.split(r"[^a-z0-9]+", name.casefold())))
        },
        key=str.casefold,
    )
    return {
        "capabilities": {kind: detections[kind] for kind in ("tool", "resource", "prompt")},
        "transports": [
            {"name": name, "paths": sorted(paths)}
            for name, paths in sorted(transport_paths.items())
        ],
        "environment_variables": [
            {"name": name, "paths": sorted(paths)}
            for name, paths in sorted(env_paths.items())[:40]
        ],
        "external_host_candidates": [
            {"name": name, "paths": sorted(paths)}
            for name, paths in sorted(host_paths.items())[:40]
        ],
        "mutating_name_candidates": mutating,
    }


def build_preflight(
    repository_url: str,
    *,
    fetcher: Fetcher | None = None,
    generated_at: str | None = None,
    maximum_files: int = DEFAULT_MAX_FILES,
) -> dict[str, Any]:
    owner, repository, canonical_url = parse_repository_url(repository_url)
    fetcher = fetcher or GhFetcher()
    base = f"repos/{quote(owner, safe='')}/{quote(repository, safe='')}"
    metadata = fetcher.get(base)
    if not isinstance(metadata, dict) or metadata.get("private") is not False:
        raise PreflightError("repository must be public")
    full_name = metadata.get("full_name")
    if not isinstance(full_name, str) or full_name.casefold() != f"{owner}/{repository}".casefold():
        raise PreflightError("GitHub repository identity does not match the request")
    default_branch = metadata.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch or len(default_branch) > 255:
        raise PreflightError("GitHub default branch is invalid")

    commit = fetcher.get(f"{base}/commits/{quote(default_branch, safe='')}")
    if not isinstance(commit, dict):
        raise PreflightError("GitHub commit metadata is invalid")
    revision = _safe_sha(commit.get("sha"), "commit SHA")
    commit_record = commit.get("commit")
    if not isinstance(commit_record, dict) or not isinstance(commit_record.get("tree"), dict):
        raise PreflightError("GitHub commit tree is missing")
    tree_sha = _safe_sha(commit_record["tree"].get("sha"), "tree SHA")

    tree_payload = fetcher.get(f"{base}/git/trees/{tree_sha}?recursive=1")
    if not isinstance(tree_payload, dict) or not isinstance(tree_payload.get("tree"), list):
        raise PreflightError("GitHub repository tree is invalid")
    tree = tree_payload["tree"]
    if len(tree) > MAX_TREE_ENTRIES:
        raise PreflightError("GitHub repository tree is too large for metadata preflight")
    selected = select_text_blobs(tree, maximum=maximum_files)

    files: list[dict[str, Any]] = []
    unreadable: list[str] = []
    for entry in selected:
        try:
            text = decode_blob(fetcher.get(f"{base}/git/blobs/{entry['sha']}"))
        except PreflightError:
            unreadable.append(entry["path"])
            continue
        files.append({**entry, "text": text})

    surface = detect_surface(files)
    return {
        "version": 1,
        "generated_at": generated_at or utc_now(),
        "repository": {
            "url": canonical_url,
            "full_name": full_name,
            "default_branch": default_branch,
            "revision": revision,
            "tree_sha": tree_sha,
            "archived": metadata.get("archived") is True,
            "fork": metadata.get("fork") is True,
        },
        "method": {
            "static_only": True,
            "repository_code_executed": False,
            "public_metadata_only": True,
            "tree_complete": tree_payload.get("truncated") is False,
            "selected_file_limit": maximum_files,
            "selected_files": len(selected),
            "readable_files": len(files),
            "unreadable_files": unreadable,
        },
        "files": [
            {"path": item["path"], "sha": item["sha"], "size": item["size"]}
            for item in files
        ],
        "surface": surface,
        "proposed_checks": list(TEN_CHECKS),
        "commercial_boundary": {
            "preflight_fee_usd": 0,
            "review_fee_usd": 500,
            "maximum_tools_and_resources": 8,
            "review_is_certification": False,
            "review_includes_fix_implementation": False,
        },
    }


def _markdown_cell(value: str) -> str:
    return " ".join(value.split()).replace("|", "\\|")


def render_markdown(report: dict[str, Any]) -> str:
    repository = report["repository"]
    method = report["method"]
    surface = report["surface"]
    lines = [
        "# MCP public-repository preflight",
        "",
        (
            f"Static preflight for [{repository['full_name']}]({repository['url']}) at "
            f"commit `{repository['revision']}`. No repository code was cloned or executed. "
            "This is a scoping aid, not a security audit, certification, vulnerability finding, "
            "or production-readiness decision."
        ),
        "",
        "## Pinned boundary",
        "",
        f"- Default branch: `{repository['default_branch']}`",
        f"- Commit: `{repository['revision']}`",
        f"- Tree: `{repository['tree_sha']}`",
        f"- Recursive tree complete: `{'yes' if method['tree_complete'] else 'no'}`",
        f"- Static text files inspected: `{method['readable_files']}` of `{method['selected_files']}` selected",
        f"- Archived repository: `{'yes' if repository['archived'] else 'no'}`",
        f"- Fork: `{'yes' if repository['fork'] else 'no'}`",
        "",
        "## Static surface candidates",
        "",
    ]

    capabilities = surface["capabilities"]
    rows = [
        (kind, item["name"], item["path"])
        for kind in ("tool", "resource", "prompt")
        for item in capabilities[kind]
    ]
    if rows:
        lines.extend(["| Kind | Candidate name or URI | Evidence file |", "|---|---|---|"])
        for kind, name, path in rows[:80]:
            lines.append(
                f"| {_markdown_cell(kind)} | `{_markdown_cell(name)}` | `{_markdown_cell(path)}` |"
            )
    else:
        lines.append(
            "No tool, resource, or prompt registration name was recovered from the bounded "
            "static file set. Runtime discovery is still required."
        )

    lines.extend(["", "### Transport and authority clues", ""])
    if surface["transports"]:
        for item in surface["transports"]:
            lines.append(
                f"- `{item['name']}` appears in: "
                + ", ".join(f"`{path}`" for path in item["paths"][:8])
            )
    else:
        lines.append("- No supported transport term was recovered from the inspected files.")
    if surface["environment_variables"]:
        lines.append(
            "- Configuration names (values were not requested): "
            + ", ".join(f"`{item['name']}`" for item in surface["environment_variables"])
        )
    else:
        lines.append("- No environment-variable name was recovered from the inspected files.")
    if surface["external_host_candidates"]:
        lines.append(
            "- Candidate external hosts found in non-Markdown source: "
            + ", ".join(f"`{item['name']}`" for item in surface["external_host_candidates"])
        )
    else:
        lines.append("- No external host candidate was recovered from inspected non-Markdown source.")
    if surface["mutating_name_candidates"]:
        lines.append(
            "- Names that require write/side-effect confirmation: "
            + ", ".join(f"`{name}`" for name in surface["mutating_name_candidates"])
        )
    else:
        lines.append("- No capability name matched the bounded write/side-effect verb list.")

    lines.extend(["", "## Files inspected", ""])
    if report["files"]:
        lines.extend(["| Path | Bytes | Blob |", "|---|---:|---|"])
        for item in report["files"]:
            lines.append(
                f"| `{_markdown_cell(item['path'])}` | {item['size']} | `{item['sha']}` |"
            )
    else:
        lines.append("No bounded candidate text file could be decoded.")
    if method["unreadable_files"]:
        lines.append("")
        lines.append(
            "Unreadable or unsupported selected files: "
            + ", ".join(f"`{path}`" for path in method["unreadable_files"])
        )

    lines.extend(["", "## Proposed ten-check review", ""])
    for number, check in enumerate(report["proposed_checks"], start=1):
        lines.append(f"{number}. {check}")

    lines.extend(
        [
            "",
            "## Missing decisions before scope",
            "",
            "- Which MCP client and exact version will consume this server?",
            "- Which transport and network boundary should be tested?",
            "- Which detected tools/resources are in scope, up to eight total?",
            "- Which disposable fixtures and network calls are authorized?",
            "- What decision must the report support, and what would make it a no-go?",
            "",
            "## Review-ready reply draft",
            "",
            (
                f"I pinned `{repository['full_name']}` at `{repository['revision'][:12]}` and "
                f"performed a static public-repository preflight without running its code. "
                f"It recovered {len(rows)} tool/resource/prompt candidate(s) and "
                f"{len(surface['transports'])} transport clue(s). Before fixing scope, I still "
                "need the intended MCP client/version, transport boundary, and the decision the "
                "review must support. The full review is a fixed USD 500 for one revision, one "
                "server, up to eight tools/resources, and ten agreed checks; it is not a "
                "penetration test, certification, fix implementation, or production guarantee."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def validate_private_output_dir(
    output_dir: Path,
    *,
    root: Path = ROOT,
    runner: Runner = default_runner,
) -> Path:
    root = root.resolve()
    candidate = output_dir if output_dir.is_absolute() else root / output_dir
    if candidate.is_symlink():
        raise PreflightError("output directory must not be a symbolic link")
    candidate = candidate.resolve(strict=False)
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise PreflightError("output directory must stay inside the repository") from exc
    completed = runner(
        ["git", "-C", str(root), "check-ignore", "--quiet", "--no-index", "--", relative.as_posix()],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        raise PreflightError("output directory must be ignored by Git")
    return candidate


def private_atomic_write(path: Path, data: bytes) -> None:
    if path.is_symlink():
        raise PreflightError("output file must not be a symbolic link")
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.parent.chmod(0o700)
    metadata = path.parent.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise PreflightError("private output directory is invalid")
    temporary = path.parent / f".{path.name}.{os.urandom(8).hex()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, flags, 0o600)
        os.fchmod(descriptor, 0o600)
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise PreflightError("private preflight write was incomplete")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.replace(temporary, path)
        path.chmod(0o600)
    except OSError as exc:
        raise PreflightError("private preflight write failed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def write_preflight(
    report: dict[str, Any],
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    root: Path = ROOT,
    runner: Runner = default_runner,
) -> Path:
    destination_dir = validate_private_output_dir(output_dir, root=root, runner=runner)
    repository = report["repository"]
    slug = re.sub(
        r"[^a-z0-9.-]+",
        "-",
        f"{repository['full_name']}--{repository['revision'][:12]}".casefold(),
    ).strip("-")
    destination = destination_dir / f"{slug}.md"
    private_atomic_write(destination, render_markdown(report).encode("utf-8"))
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository_url")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = build_preflight(args.repository_url, maximum_files=args.max_files)
        destination = write_preflight(report, output_dir=args.output_dir)
    except (OSError, PreflightError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=os.sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(destination),
                "repository": report["repository"]["url"],
                "revision": report["repository"]["revision"],
                "static_only": True,
                "repository_code_executed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
