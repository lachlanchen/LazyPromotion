#!/usr/bin/env python3
"""Read-only client projection of explicitly curated public app campaigns.

No database, browser, provider credentials, network requests or send operations.
The input is reviewed repository content, not a secret-scrubbing upload service.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent
CAMPAIGNS = ROOT / "campaigns"
SOURCES = {
    "l-and-n": (
        "l-and-n-sideproject-introduction",
        "l-and-n-cantonese-introduction",
    ),
    "bunko": (
        "bunko-classics-introduction",
        "bunko-japanese-reader-introduction",
    ),
}
PRODUCTS = {
    "l-and-n": {
        "name": "L & N: Speech Practice",
        "links": {
            "apple": "https://apps.apple.com/us/app/l-n-speech-practice/id6808872450",
            "google": "https://play.google.com/store/apps/details?id=art.lazying.landn",
            "video": "https://www.youtube.com/shorts/Nlsx_5U6g6U",
            "repository": "https://github.com/lachlanchen/L-and-N",
        },
    },
    "bunko": {
        "name": "Bunko: Classics with Ruby",
        "links": {
            "apple": "https://apps.apple.com/us/app/bunko-classics-with-ruby/id6815137919",
            "reader": "https://lachlan.lazying.art/Bunko/",
            "video": "https://www.youtube.com/shorts/pSWnOwzyc-4",
            "repository": "https://github.com/lachlanchen/Bunko",
        },
    },
}


def text(value: object, *, limit: int = 20000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError("Missing or invalid public campaign text")
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ValueError("Control character in public campaign text")
    return value


def publication_url(value: object, platform: str) -> str:
    value = text(value, limit=2048)
    url = urlsplit(value)
    hosts = {"reddit": {"www.reddit.com", "reddit.com"}, "x": {"x.com", "twitter.com"}}
    if (
        url.scheme != "https" or url.netloc not in hosts[platform]
        or url.query or url.fragment or "%" in url.path
        or any(char.isspace() for char in value)
    ):
        raise ValueError("Invalid public publication URL")
    pattern = (
        r"/r/[A-Za-z0-9_]+/comments/[a-z0-9]+/(?:[A-Za-z0-9_-]+/|comment/[a-z0-9]+/)"
        if platform == "reddit" else r"/[A-Za-z0-9_]+/status/[0-9]+/?"
    )
    if not re.fullmatch(pattern, url.path):
        raise ValueError("Publication URL is not a post or comment")
    return value


def project_publications(campaign: dict, campaign_id: str) -> list[dict]:
    if campaign.get("id") != campaign_id or not isinstance(campaign.get("channels"), dict):
        raise ValueError("Campaign identity or channels do not match")
    checked = text(campaign.get("checked_on"), limit=10)
    date.fromisoformat(checked)
    result = []
    for platform in ("reddit", "x"):
        post = campaign["channels"].get(platform)
        if post is None:
            continue
        if not isinstance(post, dict):
            raise ValueError("Invalid channel record")
        if post.get("state") != "published":
            continue
        body = text(post.get("content"))
        digest = hashlib.sha256(body.encode()).hexdigest()
        if post.get("content_sha256") != digest:
            raise ValueError("Published copy does not match its recorded hash")
        published = text(post.get("publish_at"), limit=20)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", published):
            raise ValueError("Publication time must be UTC")
        datetime.fromisoformat(published.replace("Z", "+00:00"))
        verification = post.get("publication_verification", {})
        if not isinstance(verification, dict):
            raise ValueError("Invalid publication verification")
        account_checked = any(verification.get(key) is True for key in (
            "exact_text_verified_after_reload", "live_page_reviewed",
        ))
        public_checked = account_checked and verification.get("logged_out_visibility_verified") is True
        result.append({
            "id": f"{campaign_id}:{platform}",
            "platform": platform,
            "community": text(post["community"], limit=120) if "community" in post else None,
            "title": text(post["title"], limit=300) if "title" in post else None,
            "body": body,
            "bodySha256": digest,
            "publishedAt": published,
            "recordCheckedOn": checked,
            "url": publication_url(post.get("release_url"), platform),
            "visibilityEvidence": (
                "public_verified" if public_checked else
                "account_verified" if account_checked else "unverified"
            ),
        })
    return result


def load_campaigns(project_ids: list[str]) -> dict[str, dict]:
    records = {}
    for project_id in project_ids:
        for campaign_id in SOURCES[project_id]:
            path = CAMPAIGNS / f"{campaign_id}.json"
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
                raise ValueError("Missing or unsafe curated campaign file")
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record, dict):
                raise ValueError("Invalid curated campaign")
            records[campaign_id] = record
    return records


def workspace(project_ids: list[str] | None = None, *, records: dict | None = None) -> dict:
    selected = list(SOURCES) if project_ids is None else list(project_ids)
    if not selected or len(set(selected)) != len(selected) or any(p not in SOURCES for p in selected):
        raise ValueError("Select distinct supported product IDs")
    records = load_campaigns(selected) if records is None else records
    projects = []
    for project_id in selected:
        publications = []
        for campaign_id in SOURCES[project_id]:
            campaign = records.get(campaign_id)
            if not isinstance(campaign, dict):
                raise ValueError("Missing selected public campaign")
            publications.extend(project_publications(campaign, campaign_id))
        projects.append({
            "id": project_id,
            "name": PRODUCTS[project_id]["name"],
            "links": dict(PRODUCTS[project_id]["links"]),
            "publications": sorted(publications, key=lambda p: (p["publishedAt"], p["id"])),
            "outcomes": {
                key: {"state": "not_connected", "value": None}
                for key in ("installs", "customers", "receivedGrossUsd")
            },
        })
    return {
        "version": 1,
        "mode": "public_campaign_preview",
        "capabilities": {
            "readPublishedCampaigns": True,
            "discover": False,
            "draft": False,
            "approve": False,
            "publish": False,
            "paymentAttribution": False,
        },
        "projects": projects,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", action="append", choices=tuple(SOURCES))
    args = parser.parse_args()
    try:
        result = workspace(args.project)
    except (ValueError, OSError):
        parser.exit(1, "Cannot build the reviewed public campaign view; inspect the curated records.\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
