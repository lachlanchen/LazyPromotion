#!/usr/bin/env python3
"""Render a truthful, deterministic portfolio map from the public GitHub index."""

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "github-repos.json"
OUTPUT = ROOT / "docs" / "portfolio-inventory.md"


CATEGORIES = OrderedDict(
    [
        (
            "Agentic automation and developer tools",
            {
                "AAPS", "AgentShell", "AgInTi", "aginti-browser",
                "AgInTi-LabCanvas", "AutoAppDev", "AutoNovelWriter",
                "grilling_chatgpt", "LazyingAgentWeb", "LazyingArtAgent",
                "LazyingArtBot", "LazyPromotion", "LazySkills", "LocalLLM",
                "novnc-manager", "paper-critique-skill", "paper-revision-skill",
                "PaperAgent", "PaperAgentDemo", "SoraRemote",
            },
        ),
        (
            "Media, music, storytelling, and publishing",
            {
                "aigi2vector", "AutoPublication", "AutoPublish", "AutoPubMonitor",
                "FuriganaSubtitles", "LalaMedias", "LalaStudio", "LazyEdit",
                "LocalVideoGen", "MultilingualWhisper", "Musia",
                "RaraXiaAndAyaChan", "VideoCaptionerWithClip",
                "VideoCaptionerWithVit",
            },
        ),
        (
            "Languages, books, reading, and learning",
            {
                "BigMe", "FujitsuQuaderno", "ImagizedLanguageModel", "Kindle",
                "LazyLanguageLearner", "LazyLearn", "LazyTravel", "leonardsusskind",
                "LinguaLeaf", "LocalKnowledgeTerminal", "PocketPolyglot",
                "the-art-of-lazying", "Video2Book", "WordOrigins", "WordsCardEink",
            },
        ),
        (
            "Scientific imaging, optics, and research",
            {
                "AgInTi-Spectrometer", "cellist", "CustomSensor",
                "discriminative-energy-component-analysis", "eca", "EventHolography",
                "HybridImager", "IDEAS", "kria-metavision-lab", "lazealoptix",
                "LifeReverseEngineering", "LightMind", "lightmind-privacy",
                "MetasurfaceInverseDeisgn", "nhi_hardware", "OpenHI",
                "OrganoidAgent", "OrganoidIntelligence", "OrganoidVision",
                "RapidOrganoidImaging", "SoftEventFrameAlignment",
                "SyncImagingSystem", "Yinghan",
            },
        ),
        (
            "Hardware, wearables, and robotics",
            {
                "AgInTi-HardwareConsole", "AI-Wearable", "GaugeHand",
                "GlassAgent-Wearable-Releases", "IdeasGlass", "IdeasRobot", "stm32dev",
            },
        ),
        (
            "Games and interactive learning",
            {
                "LazyChess", "LazyGame", "LazyGameWeb", "LazyMahjong", "LazyPoker",
                "LazyWeiqi", "ShiGame",
            },
        ),
        (
            "Finance, business, commerce, and creator platforms",
            {
                "Figurine", "HowYouGotRich", "LazyEarn", "LazyInvest",
                "LazyInvestReports", "MicroQuant", "onlyideas-aws",
                "onlyideas-react-native",
            },
        ),
        (
            "Infrastructure, networking, and workstation operations",
            {
                "astrill-lazy-policies", "astrill-lazy-router", "DomainAndIpManager",
                "hackintosh", "LazyEdge", "LazyRouter", "uu-remote-ubuntu-bridge",
                "WIFI2LAN",
            },
        ),
        (
            "LazyingArt identity and public web surfaces",
            {"lachlanchen", "LazyingArtWebsite"},
        ),
    ]
)


PRIORITIES = [
    {
        "work": "LazyingArt eInk",
        "need": "A dedicated multilingual reader without giving up a free Kindle/KOReader path",
        "audience": "Language learners and e-paper readers",
        "route": "Public $128 / ¥999 pre-order inquiry; payment checkout awaits fulfillment review",
        "url": "https://lazying.art/eink/",
    },
    {
        "work": "Figurine",
        "need": "A small multilingual shop for handmade LazyingArt objects and accessories",
        "audience": "Existing LazyingArt supporters and gift buyers",
        "route": "Live storefront and checkout",
        "url": "https://buy.lazying.art",
    },
    {
        "work": "LazyEdit + AutoPublish",
        "need": "Subtitles, transcription, highlights, metadata, and repeatable video publishing",
        "audience": "Video creators with a concrete editing or publishing bottleneck",
        "route": "Earn trust through a working open-source path; do not imply paid pricing that is not published",
        "url": "https://studio.lazying.art/",
    },
    {
        "work": "PocketPolyglot + LinguaLeaf",
        "need": "Readable multilingual, interlinear, ruby, pinyin, and furigana books",
        "audience": "Language learners, teachers, and readers of Classical Chinese",
        "route": "Free books and builder first; optional eInk pre-order or GitHub Sponsors later",
        "url": "https://learn.lazying.art",
    },
    {
        "work": "Susskind archive + LazyLearn",
        "need": "Searchable lecture notes and a bridge from physics intuition to practice",
        "audience": "Independent physics learners",
        "route": "Free educational value; sponsorship is secondary and never the reason for a reply",
        "url": "https://github.com/lachlanchen/leonardsusskind",
    },
    {
        "work": "Local Knowledge Terminal",
        "need": "Private, cited multilingual cards from a bounded book or dictionary collection",
        "audience": "Educators, language labs, libraries, exhibits, and private researchers",
        "route": "Fit-first pilot inquiry; no public price or ready-to-ship hardware claim",
        "url": "https://lazying.art/lkt/",
    },
    {
        "work": "Musia + LocalVideoGen",
        "need": "Local-first music localization and controllable video generation",
        "audience": "Creators who already have a specific song, stem, or video workflow problem",
        "route": "Find design partners and open-source users before making a commercial claim",
        "url": "https://fun.lazying.art",
    },
]


def escape_cell(value: str) -> str:
    return " ".join(str(value or "").split()).replace("|", "\\|")


def load_index(path: Path = INDEX) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("visibility") != "public" or payload.get("includes_forks"):
        raise ValueError("inventory source must be public-only and exclude forks")
    return payload


def categorized_repositories(payload: dict) -> OrderedDict[str, list[dict]]:
    repositories = payload["repositories"]
    names = {repo["name"] for repo in repositories}
    assigned = set().union(*CATEGORIES.values())
    missing = sorted(names - assigned, key=str.casefold)
    stale = sorted(assigned - names, key=str.casefold)
    duplicates = sorted(
        name
        for name in assigned
        if sum(name in members for members in CATEGORIES.values()) != 1
    )
    if missing or stale or duplicates:
        raise ValueError(
            f"category map mismatch: missing={missing}, stale={stale}, duplicates={duplicates}"
        )
    by_name = {repo["name"]: repo for repo in repositories}
    return OrderedDict(
        (
            category,
            [by_name[name] for name in sorted(members, key=str.casefold)],
        )
        for category, members in CATEGORIES.items()
    )


def render(payload: dict) -> str:
    grouped = categorized_repositories(payload)
    total = sum(len(repos) for repos in grouped.values())
    lines = [
        "# Lachlan Chen / LazyingArt public work inventory",
        "",
        (
            f"This is a public-only map of **{total} non-archived source repositories** "
            f"owned by [`{payload['owner']}`](https://github.com/{payload['owner']}) as of "
            f"{date.today().isoformat()}. It is generated from GitHub metadata, not a claim "
            "that every repository has received a deep product or security audit. Local-only "
            "checkouts, forks, credentials, people, messages, and promotion drafts are excluded."
        ),
        "",
        "## Where promotion should start",
        "",
        (
            "These are priority paths, not a license to force a mention. LazyPromotion should "
            "first establish a specific need, answer it usefully, and mention one relevant work "
            "only when the connection improves the answer."
        ),
        "",
        "| Work | Real need | Best-fit audience | Honest conversion route |",
        "|---|---|---|---|",
    ]
    for item in PRIORITIES:
        work = f"[{escape_cell(item['work'])}]({item['url']})"
        lines.append(
            f"| {work} | {escape_cell(item['need'])} | {escape_cell(item['audience'])} | "
            f"{escape_cell(item['route'])} |"
        )

    lines.extend(
        [
            "",
            "The immediate revenue route is an eInk order inquiry followed by reviewed "
            "payment, a fit-first Local Knowledge Terminal pilot, or an existing Figurine "
            "checkout. Open-source replies should optimize for a solved problem, "
            "not for extracting a donation. GitHub Sponsors and donations remain quiet "
            "secondary support routes on the project/profile pages.",
            "",
            "## Portfolio at a glance",
            "",
            "| Area | Public repositories |",
            "|---|---:|",
        ]
    )
    for category, repos in grouped.items():
        anchor = category.casefold().replace(" ", "-").replace(",", "").replace("and-", "and-")
        lines.append(f"| [{escape_cell(category)}](#{anchor}) | {len(repos)} |")

    lines.extend(["", "## Complete public repository inventory", ""])
    for category, repos in grouped.items():
        lines.extend(
            [
                f"### {category}",
                "",
                "| Repository | What its public metadata says | Language | Public surface |",
                "|---|---|---|---|",
            ]
        )
        for repo in repos:
            homepage = repo.get("homepage") or ""
            surface = f"[Open]({homepage})" if homepage else "Repository only"
            description = escape_cell(repo.get("description") or "No public description yet")
            language = escape_cell(repo.get("primary_language") or "Unspecified")
            lines.append(
                f"| [{escape_cell(repo['name'])}]({repo['url']}) | {description} | "
                f"{language} | {surface} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Maintenance and interpretation",
            "",
            "Refresh the source index and regenerate this document with:",
            "",
            "```bash",
            "python sync_github_catalog.py",
            "python inventory.py",
            "```",
            "",
            (
                "A public homepage means a visitor has somewhere beyond GitHub to inspect the "
                "work; it does not by itself prove product maturity, availability, pricing, or "
                "support. Promotion copy must verify those facts from current first-party evidence."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=INDEX)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    payload = load_index(args.index)
    content = render(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(args.output), "repositories": len(payload["repositories"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
