#!/usr/bin/env python3
"""Collect aggregate GitHub portfolio attention signals into private evidence.

The report is deliberately local-only.  A destination must be a JSON file
inside this repository that Git considers ignored, and the file is written
with owner-only permissions.  GitHub traffic is an aggregate attention signal;
this module never classifies it as a lead, customer, sale, or revenue.
An existing authenticated ``gh`` CLI session is required; all API calls use
explicit HTTP GET requests.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
DEFAULT_CATALOG = ROOT / "github-repos.json"
DEFAULT_OUTPUT = ROOT / ".local" / "evidence" / "github-portfolio-signals.json"
API_VERSION = "2022-11-28"
Runner = Callable[..., subprocess.CompletedProcess[str]]

SCORE_WEIGHTS = {
    "stars": 4.0,
    "forks": 3.0,
    "unique_visitors": 2.0,
    "unique_cloners": 2.0,
    "views": 0.5,
    "clones": 0.5,
    "open_issues": 0.25,
}


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


def _run_read_only(
    command: list[str], *, runner: Runner, timeout: int
) -> subprocess.CompletedProcess[str]:
    return runner(
        command,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def validate_private_output_path(
    output_path: Path,
    *,
    root: Path = ROOT,
    runner: Runner = default_runner,
) -> Path:
    """Return a safe output path or refuse a public/tracked destination."""

    root = root.resolve()
    candidate = output_path if output_path.is_absolute() else root / output_path
    if candidate.suffix.casefold() != ".json":
        raise ValueError("output must be a JSON file")
    if candidate.is_symlink():
        raise ValueError("output must not be a symbolic link")
    candidate = candidate.resolve(strict=False)
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("output must stay inside the repository") from exc

    tracked = _run_read_only(
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
        timeout=30,
    )
    if tracked.returncode == 0:
        raise ValueError("output must not be tracked by Git")
    if tracked.returncode not in {0, 1}:
        raise RuntimeError("could not verify whether the output is tracked")

    ignored = _run_read_only(
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
        timeout=30,
    )
    if ignored.returncode == 1:
        raise ValueError("output must be ignored by Git")
    if ignored.returncode != 0:
        raise RuntimeError("could not verify that the output is ignored")
    return candidate


def load_catalog(path: Path = DEFAULT_CATALOG) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("GitHub repository catalog must use version 1")
    if payload.get("visibility") != "public":
        raise ValueError(
            "GitHub repository catalog must contain only public repositories"
        )
    if payload.get("includes_forks") is not False:
        raise ValueError(
            "GitHub repository catalog must contain source repositories only"
        )
    owner = payload.get("owner")
    repositories = payload.get("repositories")
    if not isinstance(owner, str) or not owner.strip():
        raise ValueError("GitHub repository catalog owner is required")
    if not isinstance(repositories, list) or not repositories:
        raise ValueError(
            "GitHub repository catalog repositories must be a non-empty list"
        )

    names: set[str] = set()
    for repository in repositories:
        if not isinstance(repository, dict):
            raise ValueError("GitHub repository catalog entries must be objects")
        name = repository.get("name")
        url = repository.get("url")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("every catalog repository must have a name")
        if name.casefold() in names:
            raise ValueError(f"duplicate repository in catalog: {name}")
        names.add(name.casefold())
        expected_url = f"https://github.com/{owner}/{name}"
        if (
            not isinstance(url, str)
            or url.rstrip("/").casefold() != expected_url.casefold()
        ):
            raise ValueError(f"repository URL does not match catalog owner: {name}")
    return payload


def gh_api_get(endpoint: str, *, runner: Runner = default_runner) -> Any:
    """Call one authenticated, explicitly read-only GitHub REST endpoint."""

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
    completed = _run_read_only(command, runner=runner, timeout=60)
    if completed.returncode != 0:
        # Do not relay gh stderr: it may contain account-specific diagnostics.
        raise RuntimeError(f"GitHub API request failed for {endpoint}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GitHub API returned invalid JSON for {endpoint}") from exc


def _nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _traffic_series(
    payload: Any,
    *,
    series_key: str,
    uniques_key: str,
    label: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{label} traffic response must be an object")
    points = payload.get(series_key)
    if not isinstance(points, list):
        raise ValueError(f"{label} traffic series must be a list")
    daily: list[dict[str, Any]] = []
    for point in points:
        if not isinstance(point, dict) or not isinstance(point.get("timestamp"), str):
            raise ValueError(f"{label} traffic points must include a timestamp")
        daily.append(
            {
                "timestamp": point["timestamp"],
                "count": _nonnegative_int(point.get("count"), f"{label} daily count"),
                "uniques": _nonnegative_int(
                    point.get("uniques"), f"{label} daily uniques"
                ),
            }
        )
    daily.sort(key=lambda point: point["timestamp"])
    return {
        "count": _nonnegative_int(payload.get("count"), f"{label} count"),
        uniques_key: _nonnegative_int(payload.get("uniques"), f"{label} uniques"),
        "window_starts_at": daily[0]["timestamp"] if daily else None,
        "window_ends_at": daily[-1]["timestamp"] if daily else None,
        "daily": daily,
    }


def _popular_referrers(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError("popular referrers response must be a list")
    result = []
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("referrer"), str):
            raise ValueError("popular referrers must include a referrer")
        result.append(
            {
                "referrer": item["referrer"],
                "count": _nonnegative_int(item.get("count"), "referrer count"),
                "uniques": _nonnegative_int(item.get("uniques"), "referrer uniques"),
            }
        )
    return sorted(
        result,
        key=lambda item: (
            -item["count"],
            -item["uniques"],
            item["referrer"].casefold(),
        ),
    )


def _popular_paths(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError("popular paths response must be a list")
    result = []
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("popular paths must include a path")
        title = item.get("title")
        if title is not None and not isinstance(title, str):
            raise ValueError("popular path title must be a string")
        result.append(
            {
                "path": item["path"],
                "title": title or "",
                "count": _nonnegative_int(item.get("count"), "path count"),
                "uniques": _nonnegative_int(item.get("uniques"), "path uniques"),
            }
        )
    return sorted(
        result,
        key=lambda item: (-item["count"], -item["uniques"], item["path"].casefold()),
    )


def collect_repository(
    owner: str, catalog_repository: dict[str, Any], *, runner: Runner = default_runner
) -> dict[str, Any]:
    name = str(catalog_repository["name"])
    base = f"repos/{quote(owner, safe='')}/{quote(name, safe='')}"
    repository = gh_api_get(base, runner=runner)
    if not isinstance(repository, dict):
        raise ValueError(f"repository response must be an object: {name}")
    if repository.get("private") is not False:
        raise ValueError(
            f"refusing owner-visible data for a non-public repository: {name}"
        )
    if repository.get("fork") is not False:
        raise ValueError(f"refusing data for a fork repository: {name}")

    views = _traffic_series(
        gh_api_get(f"{base}/traffic/views", runner=runner),
        series_key="views",
        uniques_key="unique_visitors",
        label="views",
    )
    clones = _traffic_series(
        gh_api_get(f"{base}/traffic/clones", runner=runner),
        series_key="clones",
        uniques_key="unique_cloners",
        label="clones",
    )
    referrers = _popular_referrers(
        gh_api_get(f"{base}/traffic/popular/referrers", runner=runner)
    )
    paths = _popular_paths(gh_api_get(f"{base}/traffic/popular/paths", runner=runner))
    return {
        "name": name,
        "url": str(catalog_repository["url"]),
        "public_metrics": {
            "stars": _nonnegative_int(repository.get("stargazers_count"), "stars"),
            "forks": _nonnegative_int(repository.get("forks_count"), "forks"),
            "open_issues": _nonnegative_int(
                repository.get("open_issues_count"), "open issues"
            ),
        },
        "owner_visible_traffic": {
            "views": views,
            "clones": clones,
            "top_referrers": referrers,
            "top_paths": paths,
        },
    }


def attention_score(repository: dict[str, Any]) -> float:
    public = repository["public_metrics"]
    traffic = repository["owner_visible_traffic"]
    values = {
        "stars": public["stars"],
        "forks": public["forks"],
        "open_issues": public["open_issues"],
        "views": traffic["views"]["count"],
        "unique_visitors": traffic["views"]["unique_visitors"],
        "clones": traffic["clones"]["count"],
        "unique_cloners": traffic["clones"]["unique_cloners"],
    }
    score = sum(SCORE_WEIGHTS[key] * math.log1p(value) for key, value in values.items())
    return round(score, 6)


def rank_repositories(repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = []
    for repository in repositories:
        item = dict(repository)
        item["attention_score"] = attention_score(repository)
        scored.append(item)
    scored.sort(
        key=lambda item: (
            -item["attention_score"],
            -item["public_metrics"]["stars"],
            item["name"].casefold(),
        )
    )
    for rank, repository in enumerate(scored, start=1):
        repository["attention_rank"] = rank
    return scored


def build_report(
    catalog: dict[str, Any],
    *,
    runner: Runner = default_runner,
    generated_at: str | None = None,
) -> dict[str, Any]:
    owner = catalog["owner"]
    collected = [
        collect_repository(owner, repository, runner=runner)
        for repository in catalog["repositories"]
    ]
    ranked = rank_repositories(collected)
    return {
        "version": 1,
        "generated_at": generated_at or utc_now(),
        "owner": owner,
        "repository_count": len(ranked),
        "scope": {
            "visibility": "public",
            "source_repositories_only": True,
            "api_access": "authenticated gh api HTTP GET requests",
            "traffic": "owner-visible aggregate rolling traffic returned by GitHub",
            "credentials_stored": False,
        },
        "interpretation": {
            "classification": "relative_portfolio_attention_signal",
            "traffic_is_lead_evidence": False,
            "traffic_is_customer_evidence": False,
            "traffic_is_sales_evidence": False,
            "traffic_is_revenue_evidence": False,
            "statement": (
                "Ranks compare aggregate repository attention only. They do not "
                "identify or estimate leads, customers, sales, or revenue."
            ),
        },
        "ranking_method": {
            "name": "log_weighted_attention_score",
            "formula": "sum(weight * ln(1 + metric))",
            "weights": SCORE_WEIGHTS,
            "open_issues_note": (
                "GitHub's open_issues_count can include open pull requests; it is "
                "a low-weight activity signal, not a demand or conversion count."
            ),
        },
        "repositories": ranked,
    }


def write_private_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            descriptor = -1
            json.dump(payload, output, ensure_ascii=False, indent=2, sort_keys=True)
            output.write("\n")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    path.chmod(0o600)


def run_audit(
    *,
    output_path: Path = DEFAULT_OUTPUT,
    catalog_path: Path = DEFAULT_CATALOG,
    root: Path = ROOT,
    runner: Runner = default_runner,
    generated_at: str | None = None,
) -> dict[str, Any]:
    destination = validate_private_output_path(output_path, root=root, runner=runner)
    catalog = load_catalog(catalog_path)
    report = build_report(catalog, runner=runner, generated_at=generated_at)
    destination = validate_private_output_path(destination, root=root, runner=runner)
    write_private_json(destination, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            "ignored private JSON destination; relative paths are resolved from "
            "the repository root (default: .local/evidence/github-portfolio-signals.json)"
        ),
    )
    args = parser.parse_args(argv)
    try:
        report = run_audit(output_path=args.output)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    destination = args.output if args.output.is_absolute() else ROOT / args.output
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(destination.resolve()),
                "repositories": report["repository_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
