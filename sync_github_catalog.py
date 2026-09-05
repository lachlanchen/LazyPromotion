#!/usr/bin/env python3
"""Build a deterministic, public-only index of lachlanchen source repositories."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "github-repos.json"


def fetch(owner: str) -> list[dict]:
    fields = (
        "name,url,description,repositoryTopics,isArchived,homepageUrl,"
        "primaryLanguage,pushedAt,updatedAt"
    )
    completed = subprocess.run(
        [
            "gh", "repo", "list", owner, "--limit", "1000", "--source",
            "--visibility", "public", "--json", fields,
        ],
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "gh repo list failed")
    return json.loads(completed.stdout)


def normalize(repositories: list[dict]) -> list[dict]:
    result = []
    for repo in repositories:
        if repo.get("isArchived"):
            continue
        language = repo.get("primaryLanguage") or {}
        result.append({
            "name": str(repo["name"]),
            "url": str(repo["url"]),
            "description": str(repo.get("description") or "").strip(),
            "homepage": str(repo.get("homepageUrl") or "").strip(),
            "primary_language": str(language.get("name") or ""),
            "pushed_at": str(repo.get("pushedAt") or ""),
            "updated_at": str(repo.get("updatedAt") or ""),
            "topics": sorted(
                str(topic["name"]) for topic in (repo.get("repositoryTopics") or [])
                if topic.get("name")
            ),
        })
    return sorted(result, key=lambda repo: repo["name"].casefold())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="lachlanchen")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = {
        "version": 1,
        "owner": args.owner,
        "visibility": "public",
        "includes_forks": False,
        "repositories": normalize(fetch(args.owner)),
    }
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "output": str(args.output), "repositories": len(payload["repositories"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
