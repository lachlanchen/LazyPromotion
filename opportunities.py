#!/usr/bin/env python3
"""Validate and render evidence-led compound portfolio opportunities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "portfolio-opportunities.json"
GITHUB = ROOT / "github-repos.json"
OUTPUT = ROOT / "docs" / "compound-opportunities.md"
SCORE_FIELDS = (
    "buyer_pain",
    "proof",
    "delivery_readiness",
    "low_support",
    "repeatability",
)
WEIGHTS = {
    "buyer_pain": 0.30,
    "proof": 0.25,
    "delivery_readiness": 0.20,
    "low_support": 0.10,
    "repeatability": 0.15,
}
STATES = {"active", "candidate", "evidence-building", "gated"}


def load_registry(path: Path = REGISTRY, github_path: Path = GITHUB) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    github = json.loads(github_path.read_text(encoding="utf-8"))
    public_names = {repo["name"] for repo in github["repositories"]}
    ids: set[str] = set()
    for item in payload["opportunities"]:
        opportunity_id = item["id"]
        if opportunity_id in ids:
            raise ValueError(f"duplicate opportunity id: {opportunity_id}")
        ids.add(opportunity_id)
        if item["state"] not in STATES:
            raise ValueError(f"invalid opportunity state: {item['state']}")
        unknown = sorted(set(item["projects"]) - public_names)
        if unknown:
            raise ValueError(f"{opportunity_id} contains non-public projects: {unknown}")
        if len(item["projects"]) < 2:
            raise ValueError(f"{opportunity_id} must combine at least two public projects")
        if not item["proof"] or not item["gates"]:
            raise ValueError(f"{opportunity_id} requires proof and gates")
        scores = item["scores"]
        if set(scores) != set(SCORE_FIELDS):
            raise ValueError(f"{opportunity_id} has an invalid score contract")
        if any(not isinstance(scores[field], int) or not 1 <= scores[field] <= 5 for field in SCORE_FIELDS):
            raise ValueError(f"{opportunity_id} scores must be integers from one to five")
    return payload


def weighted_score(item: dict) -> float:
    return round(sum(item["scores"][field] * WEIGHTS[field] for field in SCORE_FIELDS), 2)


def escape(value: str) -> str:
    return " ".join(str(value).split()).replace("|", "\\|")


def render(payload: dict) -> str:
    ranked = sorted(
        payload["opportunities"],
        key=lambda item: (-weighted_score(item), item["title"].casefold()),
    )
    lines = [
        "# Compound opportunities across the LazyingArt portfolio",
        "",
        (
            "This map combines existing public code, books, knowledge systems, and media "
            "into buyer-shaped hypotheses. It excludes private repositories and forks. "
            "Scores organize research; they are not market validation, delivery promises, "
            "or revenue forecasts."
        ),
        "",
        f"> {payload['policy']}",
        "",
        "## Ranked research queue",
        "",
        "| Opportunity | State | Buyer need | First bounded test | Score / 5 |",
        "|---|---|---|---|---:|",
    ]
    for item in ranked:
        lines.append(
            f"| [{escape(item['title'])}](#{item['id']}) | {item['state']} | "
            f"{escape(item['need'])} | {escape(item['first_test'])} | "
            f"{weighted_score(item):.2f} |"
        )
    lines.extend(["", "## Opportunity contracts", ""])
    for item in ranked:
        projects = ", ".join(
            f"[{name}](https://github.com/lachlanchen/{name})" for name in item["projects"]
        )
        lines.extend(
            [
                f"### {item['title']}",
                "",
                f"**State:** {item['state']}",
                "",
                f"**Buyer:** {item['buyer']}",
                "",
                f"**Need:** {item['need']}",
                "",
                f"**Existing work:** {projects}",
                "",
                f"**First deliverable:** {item['first_deliverable']}",
                "",
                f"**First demand test:** {item['first_test']}",
                "",
                "Evidence:",
                "",
            ]
        )
        lines.extend(f"- <{url}>" for url in item["proof"])
        lines.extend(["", "Gates:", ""])
        lines.extend(f"- {gate}" for gate in item["gates"])
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            (
                "LKT, manuscript redline, the bilingual lecture pack, and the story clip pilot "
                "are the four active USD 250 routes because each has an exact scope, public "
                "proof, price, and pre-transfer qualification route. Candidate and gated "
                "opportunities should advance only after a current "
                "explicit need, a rights-safe sample, and a written delivery boundary exist."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--github", type=Path, default=GITHUB)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    payload = load_registry(args.registry, args.github)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"ok": True, "opportunities": len(payload["opportunities"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
