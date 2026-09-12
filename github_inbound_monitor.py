#!/usr/bin/env python3
"""Read-only monitor for public issues and pull requests in selected repositories.

The monitor performs one authenticated GraphQL query per pass.  Its query has
no mutation and does not request issue bodies.  It writes only an ignored,
owner-readable local state file and emits review alerts; an issue is never
classified as a lead, customer, sale, or revenue.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OWNER = "lachlanchen"
REPOSITORIES = (
    "uu-remote-ubuntu-bridge",
    "LazyTunnel",
    "LocalKnowledgeTerminal",
    "leonardsusskind",
    "OpenHI",
    "Kindle",
    "Video2Book",
    "LazyEdit",
    "L-and-N",
    "AgInTi-LabCanvas",
    "LocalVideoGen",
    "LazyPromotion",
    "Musia",
    "LinguaLeaf",
    "PocketPolyglot",
)
EXTERNAL_ISSUES = (
    ("arjun-techjays", "bos", 18),
    ("pilotariak", "azkena", 14),
    ("hivtools", "hivtools-mcp", 10),
)
ISSUES_PER_REPOSITORY = 100
PULL_REQUESTS_PER_REPOSITORY = 100
MINIMUM_INTERVAL_MINUTES = 15
DEFAULT_STATE_PATH = ROOT / ".local" / "github-inbound-monitor-status.json"
API_VERSION = "2022-11-28"
Runner = Callable[..., subprocess.CompletedProcess[str]]


def _graphql_document() -> str:
    repository_fields = []
    for index, name in enumerate(REPOSITORIES):
        repository_fields.append(
            f"""  repo{index}: repository(owner: $owner, name: {json.dumps(name)}) {{
    nameWithOwner
    visibility
    issues(
      first: {ISSUES_PER_REPOSITORY}
      states: [OPEN, CLOSED]
      orderBy: {{field: CREATED_AT, direction: DESC}}
    ) {{
      totalCount
      pageInfo {{ hasNextPage }}
      nodes {{
        number
        title
        url
        state
        createdAt
        updatedAt
        author {{ login }}
      }}
    }}
    pullRequests(
      first: {PULL_REQUESTS_PER_REPOSITORY}
      states: [OPEN, CLOSED, MERGED]
      orderBy: {{field: CREATED_AT, direction: DESC}}
    ) {{
      totalCount
      pageInfo {{ hasNextPage }}
      nodes {{
        number
        title
        url
        state
        isDraft
        createdAt
        updatedAt
        author {{ login }}
        comments {{ totalCount }}
        reviews {{ totalCount }}
      }}
    }}
  }}"""
        )
    external_fields = []
    for index, (owner, name, number) in enumerate(EXTERNAL_ISSUES):
        external_fields.append(
            f"""  external{index}: repository(
    owner: {json.dumps(owner)}
    name: {json.dumps(name)}
  ) {{
    nameWithOwner
    visibility
    issue(number: {number}) {{
      number
      title
      url
      state
      updatedAt
      comments {{ totalCount }}
    }}
  }}"""
        )
    return (
        "query GitHubInboundIssues($owner: String!) {\n"
        + "\n".join((*repository_fields, *external_fields))
        + "\n}"
    )


GRAPHQL_QUERY = _graphql_document()


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


def _run_read_only_query(
    *, runner: Runner = default_runner
) -> subprocess.CompletedProcess[str]:
    """Run the fixed GraphQL query; POST is transport, not a GitHub mutation."""
    command = [
        "gh",
        "api",
        "graphql",
        "--method",
        "POST",
        "--header",
        "Accept: application/vnd.github+json",
        "--header",
        f"X-GitHub-Api-Version: {API_VERSION}",
        "--raw-field",
        f"query={GRAPHQL_QUERY}",
        "--raw-field",
        f"owner={OWNER}",
    ]
    try:
        return runner(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("GitHub GraphQL query did not complete") from exc


def fetch_public_issues(*, runner: Runner = default_runner) -> dict[str, Any]:
    """Fetch and validate all allowlisted repositories in one GraphQL call."""
    completed = _run_read_only_query(runner=runner)
    if completed.returncode != 0:
        # gh stderr can contain account-specific diagnostics, so never relay it.
        raise RuntimeError("GitHub GraphQL query failed")
    try:
        payload = json.loads(str(completed.stdout or ""))
    except json.JSONDecodeError as exc:
        raise RuntimeError("GitHub GraphQL returned invalid JSON") from exc
    if not isinstance(payload, dict) or payload.get("errors"):
        raise RuntimeError("GitHub GraphQL query returned an error")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("GitHub GraphQL response did not contain data")

    # Validate the entire visibility boundary before accepting issue data from
    # any repository.  An authenticated token may otherwise expose private data.
    raw_repositories: list[dict[str, Any]] = []
    for index, name in enumerate(REPOSITORIES):
        raw = data.get(f"repo{index}")
        if not isinstance(raw, dict):
            raise ValueError(f"allowlisted repository is unavailable: {name}")
        expected = f"{OWNER}/{name}"
        actual = raw.get("nameWithOwner")
        if not isinstance(actual, str) or actual.casefold() != expected.casefold():
            raise ValueError(f"GitHub returned an unexpected repository: {name}")
        if raw.get("visibility") != "PUBLIC":
            raise ValueError(f"refusing non-public repository data: {name}")
        raw_repositories.append(raw)

    repositories = []
    for name, raw in zip(REPOSITORIES, raw_repositories):
        repositories.append(_parse_repository(name, raw))
    external_threads = []
    for index, (owner, name, number) in enumerate(EXTERNAL_ISSUES):
        raw = data.get(f"external{index}")
        external_threads.append(
            _parse_external_thread(owner, name, number, raw)
        )
    return {
        "owner": OWNER,
        "repositories": repositories,
        "external_threads": external_threads,
    }


def _nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be a timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return value


def _parse_repository(name: str, raw: dict[str, Any]) -> dict[str, Any]:
    connection = raw.get("issues")
    if not isinstance(connection, dict):
        raise ValueError(f"GitHub returned invalid issue data: {name}")
    total_count = _nonnegative_int(connection.get("totalCount"), f"{name} issue total")
    page_info = connection.get("pageInfo")
    if not isinstance(page_info, dict) or not isinstance(
        page_info.get("hasNextPage"), bool
    ):
        raise ValueError(f"GitHub returned invalid issue page data: {name}")
    nodes = connection.get("nodes")
    if not isinstance(nodes, list) or len(nodes) > ISSUES_PER_REPOSITORY:
        raise ValueError(f"GitHub returned an invalid issue window: {name}")
    if total_count < len(nodes):
        raise ValueError(f"GitHub returned an invalid issue total: {name}")

    issues = []
    numbers: set[int] = set()
    for raw_issue in nodes:
        if not isinstance(raw_issue, dict):
            raise ValueError(f"GitHub returned an invalid issue: {name}")
        number = _nonnegative_int(raw_issue.get("number"), f"{name} issue number")
        if number < 1 or number in numbers:
            raise ValueError(f"GitHub returned a duplicate or invalid issue: {name}")
        numbers.add(number)
        title = raw_issue.get("title")
        url = raw_issue.get("url")
        state = raw_issue.get("state")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"GitHub returned an invalid issue title: {name}#{number}")
        expected_url = f"https://github.com/{OWNER}/{name}/issues/{number}"
        if (
            not isinstance(url, str)
            or url.rstrip("/").casefold() != expected_url.casefold()
        ):
            raise ValueError(f"GitHub returned an invalid issue URL: {name}#{number}")
        if state not in {"OPEN", "CLOSED"}:
            raise ValueError(f"GitHub returned an invalid issue state: {name}#{number}")
        author = raw_issue.get("author")
        if author is not None and (
            not isinstance(author, dict) or not isinstance(author.get("login"), str)
        ):
            raise ValueError(
                f"GitHub returned an invalid issue author: {name}#{number}"
            )
        issues.append(
            {
                "key": issue_key(name, number),
                "repository": name,
                "number": number,
                "title": title,
                "url": url,
                "state": state,
                "created_at": _timestamp(
                    raw_issue.get("createdAt"), f"{name}#{number} createdAt"
                ),
                "updated_at": _timestamp(
                    raw_issue.get("updatedAt"), f"{name}#{number} updatedAt"
                ),
                "author_login": author.get("login") if author else None,
            }
        )
    issues.sort(key=lambda issue: issue["number"])
    pull_requests, pull_request_total, pull_request_truncated = (
        _parse_pull_requests(name, raw.get("pullRequests"))
    )
    return {
        "name": name,
        "name_with_owner": f"{OWNER}/{name}",
        "visibility": "PUBLIC",
        "total_issue_count": total_count,
        "window_issue_count": len(issues),
        "window_truncated": bool(page_info["hasNextPage"]),
        "issues": issues,
        "total_pull_request_count": pull_request_total,
        "window_pull_request_count": len(pull_requests),
        "pull_request_window_truncated": pull_request_truncated,
        "pull_requests": pull_requests,
    }


def _parse_pull_requests(
    name: str, connection: Any
) -> tuple[list[dict[str, Any]], int, bool]:
    if not isinstance(connection, dict):
        raise ValueError(f"GitHub returned invalid pull-request data: {name}")
    total_count = _nonnegative_int(
        connection.get("totalCount"), f"{name} pull-request total"
    )
    page_info = connection.get("pageInfo")
    if not isinstance(page_info, dict) or not isinstance(
        page_info.get("hasNextPage"), bool
    ):
        raise ValueError(f"GitHub returned invalid pull-request page data: {name}")
    nodes = connection.get("nodes")
    if not isinstance(nodes, list) or len(nodes) > PULL_REQUESTS_PER_REPOSITORY:
        raise ValueError(f"GitHub returned an invalid pull-request window: {name}")
    if total_count < len(nodes):
        raise ValueError(f"GitHub returned an invalid pull-request total: {name}")

    pull_requests = []
    numbers: set[int] = set()
    for raw_pull_request in nodes:
        if not isinstance(raw_pull_request, dict):
            raise ValueError(f"GitHub returned an invalid pull request: {name}")
        number = _nonnegative_int(
            raw_pull_request.get("number"), f"{name} pull-request number"
        )
        if number < 1 or number in numbers:
            raise ValueError(
                f"GitHub returned a duplicate or invalid pull request: {name}"
            )
        numbers.add(number)
        title = raw_pull_request.get("title")
        url = raw_pull_request.get("url")
        state = raw_pull_request.get("state")
        is_draft = raw_pull_request.get("isDraft")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(
                f"GitHub returned an invalid pull-request title: {name}#{number}"
            )
        expected_url = f"https://github.com/{OWNER}/{name}/pull/{number}"
        if (
            not isinstance(url, str)
            or url.rstrip("/").casefold() != expected_url.casefold()
        ):
            raise ValueError(
                f"GitHub returned an invalid pull-request URL: {name}#{number}"
            )
        if state not in {"OPEN", "CLOSED", "MERGED"}:
            raise ValueError(
                f"GitHub returned an invalid pull-request state: {name}#{number}"
            )
        if not isinstance(is_draft, bool):
            raise ValueError(
                f"GitHub returned an invalid pull-request draft state: {name}#{number}"
            )
        author = raw_pull_request.get("author")
        if author is not None and (
            not isinstance(author, dict) or not isinstance(author.get("login"), str)
        ):
            raise ValueError(
                f"GitHub returned an invalid pull-request author: {name}#{number}"
            )
        comments = raw_pull_request.get("comments")
        reviews = raw_pull_request.get("reviews")
        if not isinstance(comments, dict) or not isinstance(reviews, dict):
            raise ValueError(
                f"GitHub returned invalid pull-request activity: {name}#{number}"
            )
        pull_requests.append(
            {
                "key": pull_request_key(name, number),
                "repository": name,
                "number": number,
                "title": title,
                "url": url,
                "state": state,
                "is_draft": is_draft,
                "created_at": _timestamp(
                    raw_pull_request.get("createdAt"),
                    f"{name}#{number} createdAt",
                ),
                "updated_at": _timestamp(
                    raw_pull_request.get("updatedAt"),
                    f"{name}#{number} updatedAt",
                ),
                "author_login": author.get("login") if author else None,
                "comment_count": _nonnegative_int(
                    comments.get("totalCount"), f"{name}#{number} comment total"
                ),
                "review_count": _nonnegative_int(
                    reviews.get("totalCount"), f"{name}#{number} review total"
                ),
            }
        )
    pull_requests.sort(key=lambda pull_request: pull_request["number"])
    return pull_requests, total_count, bool(page_info["hasNextPage"])


def external_thread_key(owner: str, repository: str, number: int) -> str:
    return f"{owner}/{repository}#{number}"


def _parse_external_thread(
    owner: str,
    repository: str,
    number: int,
    raw_repository: Any,
) -> dict[str, Any]:
    """Validate one explicit public issue without requesting its body or comments."""
    expected_repository = f"{owner}/{repository}"
    if not isinstance(raw_repository, dict):
        raise ValueError(f"external repository is unavailable: {expected_repository}")
    actual_repository = raw_repository.get("nameWithOwner")
    if (
        not isinstance(actual_repository, str)
        or actual_repository.casefold() != expected_repository.casefold()
    ):
        raise ValueError(f"GitHub returned an unexpected external repository: {expected_repository}")
    if raw_repository.get("visibility") != "PUBLIC":
        raise ValueError(f"refusing non-public external repository data: {expected_repository}")
    issue = raw_repository.get("issue")
    if not isinstance(issue, dict):
        raise ValueError(f"external issue is unavailable: {expected_repository}#{number}")
    if _nonnegative_int(issue.get("number"), "external issue number") != number:
        raise ValueError("GitHub returned an unexpected external issue number")
    title = issue.get("title")
    url = issue.get("url")
    state = issue.get("state")
    expected_url = f"https://github.com/{owner}/{repository}/issues/{number}"
    if not isinstance(title, str) or not title.strip():
        raise ValueError("GitHub returned an invalid external issue title")
    if not isinstance(url, str) or url.rstrip("/").casefold() != expected_url.casefold():
        raise ValueError("GitHub returned an invalid external issue URL")
    if state not in {"OPEN", "CLOSED"}:
        raise ValueError("GitHub returned an invalid external issue state")
    comments = issue.get("comments")
    if not isinstance(comments, dict):
        raise ValueError("GitHub returned invalid external issue comment metadata")
    return {
        "key": external_thread_key(owner, repository, number),
        "repository": expected_repository,
        "number": number,
        "title": title,
        "url": url,
        "state": state,
        "updated_at": _timestamp(issue.get("updatedAt"), "external issue updatedAt"),
        "comment_count": _nonnegative_int(
            comments.get("totalCount"), "external issue comment total"
        ),
    }


def issue_key(repository: str, number: int) -> str:
    return f"{OWNER}/{repository}#{number}"


def pull_request_key(repository: str, number: int) -> str:
    return f"{OWNER}/{repository}#pr-{number}"


def _split_issue_key(key: str) -> tuple[int, int]:
    prefix, separator, number_text = key.rpartition("#")
    if not separator or not number_text.isdigit() or int(number_text) < 1:
        raise ValueError("state contains an invalid issue key")
    owner, slash, repository = prefix.partition("/")
    if owner != OWNER or not slash or repository not in REPOSITORIES:
        raise ValueError("state contains an issue outside the allowlist")
    return REPOSITORIES.index(repository), int(number_text)


def _split_pull_request_key(key: str) -> tuple[int, int]:
    prefix, separator, number_text = key.rpartition("#pr-")
    if not separator or not number_text.isdigit() or int(number_text) < 1:
        raise ValueError("state contains an invalid pull-request key")
    owner, slash, repository = prefix.partition("/")
    if owner != OWNER or not slash or repository not in REPOSITORIES:
        raise ValueError("state contains a pull request outside the allowlist")
    return REPOSITORIES.index(repository), int(number_text)


def _external_thread_sort_key(key: str) -> tuple[int, int]:
    allowed = [external_thread_key(*item) for item in EXTERNAL_ISSUES]
    if key not in allowed:
        raise ValueError("state contains an external issue outside the allowlist")
    return allowed.index(key), int(key.rpartition("#")[2])


def _run_git_check(
    command: list[str], *, runner: Runner
) -> subprocess.CompletedProcess[str]:
    try:
        return runner(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("state path safety check did not complete") from exc


def _reject_symlink_components(root: Path, relative: Path) -> None:
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError("state path must not contain symbolic links")
        if current != root / relative and not stat.S_ISDIR(metadata.st_mode):
            raise ValueError("state path parent must be a directory")
        if current == root / relative and not stat.S_ISREG(metadata.st_mode):
            raise ValueError("existing state path must be a regular file")
        if current == root / relative and metadata.st_nlink != 1:
            raise ValueError("existing state path must not be hard linked")


def validate_state_path(
    state_path: Path,
    *,
    root: Path = ROOT,
    runner: Runner = default_runner,
) -> Path:
    """Require an untracked, ignored JSON file below this repo's .local dir."""
    root = root.resolve()
    raw = state_path if state_path.is_absolute() else root / state_path
    candidate = Path(os.path.abspath(os.fspath(raw)))
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("state path must stay inside the repository") from exc
    if len(relative.parts) < 2 or relative.parts[0] != ".local":
        raise ValueError("state path must be below the repository .local directory")
    if candidate.suffix.casefold() != ".json":
        raise ValueError("state path must be a JSON file")
    _reject_symlink_components(root, relative)

    tracked = _run_git_check(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--error-unmatch",
            "--",
            relative.as_posix(),
        ],
        runner=runner,
    )
    if tracked.returncode == 0:
        raise ValueError("state path must not be tracked by Git")
    if tracked.returncode != 1:
        raise RuntimeError("could not verify whether the state path is tracked")
    ignored = _run_git_check(
        [
            "git",
            "-C",
            str(root),
            "check-ignore",
            "--quiet",
            "--no-index",
            "--",
            relative.as_posix(),
        ],
        runner=runner,
    )
    if ignored.returncode == 1:
        raise ValueError("state path must be ignored by Git")
    if ignored.returncode != 0:
        raise RuntimeError("could not verify that the state path is ignored")
    return candidate


def load_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("state path must be a private regular file")
        with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
            descriptor = -1
            payload = json.load(stream)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("existing monitor state is invalid")
    stored_allowlist = payload.get("repository_allowlist")
    allowlist_is_current_or_prefix = (
        isinstance(stored_allowlist, list)
        and bool(stored_allowlist)
        and all(isinstance(name, str) for name in stored_allowlist)
        and tuple(stored_allowlist) == REPOSITORIES[: len(stored_allowlist)]
    )
    if payload.get("owner") != OWNER or not allowlist_is_current_or_prefix:
        raise ValueError("existing monitor state does not match the fixed allowlist")
    if payload.get("initialized") is not True:
        raise ValueError("existing monitor state is not initialized")
    seen = payload.get("seen_issue_keys")
    if not isinstance(seen, list) or any(not isinstance(key, str) for key in seen):
        raise ValueError("existing monitor state has invalid seen issue keys")
    if len(seen) != len(set(seen)):
        raise ValueError("existing monitor state has duplicate seen issue keys")
    for key in seen:
        _split_issue_key(key)
    seen_pull_requests = payload.get("seen_pull_request_keys", [])
    if not isinstance(seen_pull_requests, list) or any(
        not isinstance(key, str) for key in seen_pull_requests
    ):
        raise ValueError("existing monitor state has invalid seen pull-request keys")
    if len(seen_pull_requests) != len(set(seen_pull_requests)):
        raise ValueError("existing monitor state has duplicate seen pull-request keys")
    for key in seen_pull_requests:
        _split_pull_request_key(key)
    pull_request_activity = payload.get("pull_request_activity", {})
    if not isinstance(pull_request_activity, dict):
        raise ValueError("existing monitor state has invalid pull-request activity")
    if set(pull_request_activity) - set(seen_pull_requests):
        raise ValueError("pull-request activity is outside the seen key set")
    for key, activity in pull_request_activity.items():
        _split_pull_request_key(key)
        if not isinstance(activity, dict):
            raise ValueError("existing monitor state has invalid pull-request activity")
        _timestamp(activity.get("updated_at"), "pull-request activity updated_at")
        _nonnegative_int(
            activity.get("comment_count"), "pull-request activity comment total"
        )
        _nonnegative_int(
            activity.get("review_count"), "pull-request activity review total"
        )
        if activity.get("state") not in {"OPEN", "CLOSED", "MERGED"}:
            raise ValueError("existing monitor state has invalid pull-request state")
    stored_external_allowlist = payload.get("external_thread_allowlist", [])
    current_external_allowlist = [
        external_thread_key(*item) for item in EXTERNAL_ISSUES
    ]
    external_allowlist_is_current_or_prefix = (
        isinstance(stored_external_allowlist, list)
        and all(isinstance(key, str) for key in stored_external_allowlist)
        and stored_external_allowlist
        == current_external_allowlist[: len(stored_external_allowlist)]
    )
    if not external_allowlist_is_current_or_prefix:
        raise ValueError("existing monitor state has an invalid external issue allowlist")
    external_thread_activity = payload.get("external_thread_activity", {})
    if not isinstance(external_thread_activity, dict):
        raise ValueError("existing monitor state has invalid external issue activity")
    if set(external_thread_activity) - set(stored_external_allowlist):
        raise ValueError("external issue activity is outside the stored allowlist")
    for key, activity in external_thread_activity.items():
        _external_thread_sort_key(key)
        if not isinstance(activity, dict):
            raise ValueError("existing monitor state has invalid external issue activity")
        _timestamp(activity.get("updated_at"), "external issue activity updated_at")
        _nonnegative_int(
            activity.get("comment_count"), "external issue activity comment total"
        )
        if activity.get("state") not in {"OPEN", "CLOSED"}:
            raise ValueError("existing monitor state has invalid external issue state")
    return payload


def write_private_json(
    path: Path,
    payload: dict[str, Any],
    *,
    root: Path | None = None,
) -> None:
    """Atomically replace one regular state file with mode 0600."""
    if root is None:
        local_ancestors = [parent for parent in path.parents if parent.name == ".local"]
        root = local_ancestors[-1].parent if local_ancestors else path.parent
    root = root.resolve()
    relative = path.relative_to(root)
    _reject_symlink_components(root, relative)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    _reject_symlink_components(root, relative)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            descriptor = -1
            json.dump(payload, output, ensure_ascii=False, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        if path.exists() or path.is_symlink():
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ValueError("refusing to replace an unsafe state path")
        os.replace(temporary, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def build_state(
    observation: dict[str, Any],
    previous: dict[str, Any] | None,
    *,
    checked_at: str | None = None,
) -> dict[str, Any]:
    checked_at = checked_at or utc_now()
    repositories = observation.get("repositories")
    external_threads = observation.get("external_threads")
    if (
        observation.get("owner") != OWNER
        or not isinstance(repositories, list)
        or not isinstance(external_threads, list)
    ):
        raise ValueError("issue observation is invalid")
    current_external_allowlist = [
        external_thread_key(*item) for item in EXTERNAL_ISSUES
    ]
    if [thread.get("key") for thread in external_threads] != current_external_allowlist:
        raise ValueError("external issue observation does not match the fixed allowlist")
    current_issues = [
        issue for repository in repositories for issue in repository.get("issues", [])
    ]
    current_pull_requests = [
        pull_request
        for repository in repositories
        for pull_request in repository.get("pull_requests", [])
    ]
    current_keys = {issue["key"] for issue in current_issues}
    previous_keys = set(previous["seen_issue_keys"]) if previous else set()
    current_pull_request_keys = {
        pull_request["key"] for pull_request in current_pull_requests
    }
    previous_pull_request_keys = (
        set(previous.get("seen_pull_request_keys", [])) if previous else set()
    )
    previous_pull_request_activity = (
        dict(previous.get("pull_request_activity", {})) if previous else {}
    )
    previous_external_allowlist = (
        list(previous.get("external_thread_allowlist", [])) if previous else []
    )
    newly_allowlisted_external_threads = set(current_external_allowlist) - set(
        previous_external_allowlist
    )
    previous_external_activity = (
        dict(previous.get("external_thread_activity", {})) if previous else {}
    )
    is_baseline = previous is None
    pull_request_baseline = is_baseline or (
        previous is not None and "seen_pull_request_keys" not in previous
    )
    new_keys = set() if is_baseline else current_keys - previous_keys
    newly_allowlisted_repositories = set()
    if previous:
        newly_allowlisted_repositories = set(REPOSITORIES) - set(
            previous["repository_allowlist"]
        )
    alerts = []
    for issue in current_issues:
        if (
            issue["key"] not in new_keys
            or issue["repository"] in newly_allowlisted_repositories
        ):
            continue
        alerts.append(
            {
                "kind": "new_public_issue_observed",
                **issue,
                "action": (
                    "Review the public issue manually for project relevance; do not "
                    "reply automatically or treat it as commercial evidence."
                ),
            }
        )
    for pull_request in current_pull_requests:
        key = pull_request["key"]
        if (
            pull_request_baseline
            or pull_request["repository"] in newly_allowlisted_repositories
        ):
            continue
        previous_activity = previous_pull_request_activity.get(key)
        if key not in previous_pull_request_keys:
            kind = "new_public_pull_request_observed"
        elif previous_activity and previous_activity.get("updated_at") != pull_request[
            "updated_at"
        ]:
            kind = "public_pull_request_activity_observed"
        else:
            continue
        alerts.append(
            {
                "kind": kind,
                **pull_request,
                "action": (
                    "Review the public pull request manually for project relevance; "
                    "do not reply or merge automatically or treat it as commercial "
                    "evidence."
                ),
            }
        )
    for thread in external_threads:
        key = thread["key"]
        if key in newly_allowlisted_external_threads:
            continue
        previous_activity = previous_external_activity.get(key)
        if previous_activity is None:
            continue
        current_activity = {
            "updated_at": thread["updated_at"],
            "comment_count": thread["comment_count"],
            "state": thread["state"],
        }
        if current_activity == previous_activity:
            continue
        alerts.append(
            {
                "kind": "external_public_issue_activity_observed",
                **thread,
                "action": (
                    "Open this exact public issue for manual reply review; do not fetch "
                    "comment bodies, reply automatically, or treat activity as a lead."
                ),
            }
        )
    seen_keys = sorted(previous_keys | current_keys, key=_split_issue_key)
    seen_pull_request_keys = sorted(
        previous_pull_request_keys | current_pull_request_keys,
        key=_split_pull_request_key,
    )
    pull_request_activity = dict(previous_pull_request_activity)
    for pull_request in current_pull_requests:
        pull_request_activity[pull_request["key"]] = {
            "updated_at": pull_request["updated_at"],
            "comment_count": pull_request["comment_count"],
            "review_count": pull_request["review_count"],
            "state": pull_request["state"],
        }
    external_thread_activity = dict(previous_external_activity)
    for thread in external_threads:
        external_thread_activity[thread["key"]] = {
            "updated_at": thread["updated_at"],
            "comment_count": thread["comment_count"],
            "state": thread["state"],
        }
    return {
        "version": 1,
        "initialized": True,
        "checked_at": checked_at,
        "baseline_created": is_baseline,
        "allowlist_expanded": sorted(newly_allowlisted_repositories),
        "owner": OWNER,
        "repository_allowlist": list(REPOSITORIES),
        "external_thread_allowlist": current_external_allowlist,
        "policy": {
            "graphql_operation": "query",
            "issue_bodies_requested": False,
            "pull_request_bodies_requested": False,
            "comment_or_review_bodies_requested": False,
            "external_issue_or_comment_bodies_requested": False,
            "github_mutations_performed": False,
            "automatic_comments_or_replies": False,
            "issue_is_lead_evidence": False,
            "issue_is_revenue_evidence": False,
            "pull_request_is_lead_evidence": False,
            "pull_request_is_revenue_evidence": False,
            "external_issue_activity_is_lead_evidence": False,
            "external_issue_activity_is_revenue_evidence": False,
        },
        "repositories": repositories,
        "external_threads": external_threads,
        "seen_issue_keys": seen_keys,
        "seen_pull_request_keys": seen_pull_request_keys,
        "pull_request_activity": pull_request_activity,
        "external_thread_activity": external_thread_activity,
        "alerts": alerts,
        "summary": {
            "repositories_checked": len(repositories),
            "issues_in_current_windows": len(current_issues),
            "pull_requests_in_current_windows": len(current_pull_requests),
            "seen_issue_keys": len(seen_keys),
            "seen_pull_request_keys": len(seen_pull_request_keys),
            "new_issue_alerts": sum(
                alert["kind"] == "new_public_issue_observed" for alert in alerts
            ),
            "pull_request_alerts": sum(
                "pull_request" in alert["kind"] for alert in alerts
            ),
            "external_threads_checked": len(external_threads),
            "external_thread_alerts": sum(
                alert["kind"] == "external_public_issue_activity_observed"
                for alert in alerts
            ),
            "truncated_repository_windows": sum(
                bool(repository.get("window_truncated"))
                or bool(repository.get("pull_request_window_truncated"))
                for repository in repositories
            ),
        },
    }


def monitor_once(
    *,
    state_path: Path = DEFAULT_STATE_PATH,
    root: Path = ROOT,
    runner: Runner = default_runner,
    checked_at: str | None = None,
) -> dict[str, Any]:
    destination = validate_state_path(state_path, root=root, runner=runner)
    previous = load_state(destination)
    observation = fetch_public_issues(runner=runner)
    report = build_state(observation, previous, checked_at=checked_at)
    # Recheck after the network call so a newly introduced link is refused.
    destination = validate_state_path(destination, root=root, runner=runner)
    write_private_json(destination, report, root=root)
    return report


def _lock_path(state_path: Path) -> Path:
    return state_path.with_suffix(".lock")


@contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    if path.is_symlink():
        raise ValueError("monitor lock must not be a symbolic link")
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("monitor lock must be a regular private file")
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("GitHub inbound monitor is already running") from exc
        yield
    finally:
        os.close(descriptor)


def monitor_loop(
    interval_minutes: int,
    *,
    state_path: Path = DEFAULT_STATE_PATH,
    root: Path = ROOT,
    runner: Runner = default_runner,
) -> None:
    if interval_minutes < MINIMUM_INTERVAL_MINUTES:
        raise ValueError("interval must be at least 15 minutes")
    destination = validate_state_path(state_path, root=root, runner=runner)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with exclusive_lock(_lock_path(destination)):
        while True:
            try:
                report = monitor_once(
                    state_path=destination,
                    root=root,
                    runner=runner,
                )
                print(
                    json.dumps(report, ensure_ascii=False, sort_keys=True), flush=True
                )
            except Exception as exc:
                # Keep errors generic where a CLI failure might contain account data.
                print(
                    json.dumps(
                        {"ok": False, "checked_at": utc_now(), "error": str(exc)},
                        sort_keys=True,
                    ),
                    file=sys.stderr,
                    flush=True,
                )
            time.sleep(interval_minutes * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    once = subparsers.add_parser("once", help="Run one read-only observation pass.")
    once.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    continuous = subparsers.add_parser("loop", help="Repeat read-only observations.")
    continuous.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    continuous.add_argument("--interval-minutes", type=int, default=15)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "once":
            report = monitor_once(state_path=args.state)
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            monitor_loop(args.interval_minutes, state_path=args.state)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
