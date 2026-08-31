#!/usr/bin/env python3
"""Build the private LazyPromotion evidence graph and sanitized public snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import promotion


ROOT = Path(__file__).resolve().parent
CAMPAIGNS = ROOT / "campaigns"
PUBLIC_SNAPSHOT = ROOT / "promotion-network.public.json"


def graph_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def upsert_entity(
    db,
    entity_id: str,
    *,
    kind: str,
    label: str,
    url: str = "",
    visibility: str = "private",
    metadata: dict | None = None,
) -> str:
    if visibility not in {"public", "private"}:
        raise ValueError("entity visibility must be public or private")
    now = promotion.utc_now()
    payload = json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)
    db.execute(
        """
        INSERT INTO entities
          (id, kind, label, url, visibility, metadata_json, first_seen_at, last_seen_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          kind=excluded.kind, label=excluded.label, url=excluded.url,
          visibility=excluded.visibility, metadata_json=excluded.metadata_json,
          last_seen_at=excluded.last_seen_at
        """,
        (entity_id, kind, promotion.compact(label), url, visibility, payload, now, now),
    )
    return entity_id


def upsert_relationship(
    db,
    source_id: str,
    relation: str,
    target_id: str,
    *,
    evidence_url: str = "",
    confidence: float = 1.0,
    metadata: dict | None = None,
) -> str:
    if not 0 <= confidence <= 1:
        raise ValueError("relationship confidence must be between 0 and 1")
    identity = f"{source_id}\n{relation}\n{target_id}\n{evidence_url}"
    relationship_id = graph_id("link", identity)
    now = promotion.utc_now()
    db.execute(
        """
        INSERT INTO relationships
          (id, source_id, relation, target_id, evidence_url, confidence,
           metadata_json, first_seen_at, last_seen_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          confidence=excluded.confidence, metadata_json=excluded.metadata_json,
          last_seen_at=excluded.last_seen_at
        """,
        (
            relationship_id, source_id, relation, target_id, evidence_url,
            confidence, json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
            now, now,
        ),
    )
    return relationship_id


def url_entity(db, url: str, *, label: str = "", kind: str = "web_resource") -> str:
    parsed = urlparse(url)
    fallback = parsed.hostname or url
    return upsert_entity(
        db,
        graph_id("url", url),
        kind=kind,
        label=label or fallback,
        url=url,
        visibility="public",
    )


def repository_entity(db, url: str, *, label: str) -> str:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if parsed.hostname == "github.com" and len(parts) == 2:
        entity_id = f"repository:{parts[0]}/{parts[1]}"
    else:
        entity_id = graph_id("repository", url)
    return upsert_entity(
        db,
        entity_id,
        kind="repository",
        label=label,
        url=url,
        visibility="public",
    )


def sync_public_sources(db) -> dict[str, str]:
    projects = promotion.load_catalog()["projects"]
    project_by_url = {}
    for project in projects:
        entity_id = f"project:{project['id']}"
        upsert_entity(
            db,
            entity_id,
            kind="project",
            label=project["name"],
            url=project["url"],
            visibility="public",
            metadata={
                "summary": project["summary"],
                "generated": bool(project.get("generated")),
                "keywords": project.get("keywords", []),
            },
        )
        project_by_url[project["url"].rstrip("/").casefold()] = entity_id
        repo = repository_entity(db, project["url"], label=project["name"])
        upsert_relationship(db, entity_id, "backed_by", repo, evidence_url=project["url"])
        if project.get("homepage"):
            homepage = url_entity(db, project["homepage"], label=f"{project['name']} homepage")
            upsert_relationship(
                db, entity_id, "has_homepage", homepage, evidence_url=project["homepage"]
            )

    github = json.loads((ROOT / "github-repos.json").read_text(encoding="utf-8"))
    verified_public_repositories = set()
    for repo in github.get("repositories", []):
        repo_id = f"repository:{github['owner']}/{repo['name']}"
        verified_public_repositories.add(repo_id)
        upsert_entity(
            db,
            repo_id,
            kind="repository",
            label=repo["name"],
            url=repo["url"],
            visibility="public",
            metadata={
                "description": repo.get("description") or "",
                "topics": repo.get("topics") or [],
                "homepage": repo.get("homepage") or "",
                "updated_at": repo.get("updated_at") or "",
            },
        )
        project_id = project_by_url.get(repo["url"].rstrip("/").casefold())
        if project_id:
            upsert_relationship(db, project_id, "backed_by", repo_id, evidence_url=repo["url"])

    verified_public_repositories.update(
        entity_id
        for entity_id, in db.execute(
            """
            SELECT target_id FROM relationships
            WHERE relation='backed_by' AND target_id LIKE 'repository:%'
            """
        )
    )
    # A local checkout is not evidence that its GitHub repository is public.
    # Demote anything outside the verified public index/catalog before export.
    for entity_id, in db.execute("SELECT id FROM entities WHERE kind='repository'").fetchall():
        if entity_id not in verified_public_repositories:
            db.execute("UPDATE entities SET visibility='private' WHERE id=?", (entity_id,))

    for path in sorted(CAMPAIGNS.glob("*.json")):
        campaign = json.loads(path.read_text(encoding="utf-8"))
        campaign_id = f"campaign:{campaign['id']}"
        upsert_entity(
            db,
            campaign_id,
            kind="campaign",
            label=campaign["id"],
            visibility="public",
            metadata={"objective": campaign["objective"], "version": campaign["version"]},
        )
        for channel, details in campaign.get("channels", {}).items():
            channel_id = f"channel:{channel}"
            upsert_entity(
                db, channel_id, kind="channel", label=channel, visibility="public"
            )
            upsert_relationship(
                db,
                campaign_id,
                "targets",
                channel_id,
                metadata={"state": details.get("state", "")},
            )
        for key, value in campaign.get("source_evidence", {}).items():
            if isinstance(value, str) and value.startswith(("https://", "http://")):
                resource_id = url_entity(db, value, label=key.replace("_", " "))
                upsert_relationship(
                    db, campaign_id, "uses_evidence", resource_id, evidence_url=value
                )
                project_id = project_by_url.get(value.rstrip("/").casefold())
                if project_id:
                    upsert_relationship(
                        db, campaign_id, "promotes", project_id, evidence_url=value
                    )
    return project_by_url


def community_from_candidate(candidate: dict) -> str:
    parsed = urlparse(candidate["source_url"])
    parts = [part for part in parsed.path.split("/") if part]
    if candidate["platform"] == "reddit" and parts and parts[0] == "r":
        return f"r/{parts[1]}" if len(parts) > 1 else "reddit"
    return candidate["platform"]


def sync_private_activity(db) -> None:
    for candidate in db.execute("SELECT * FROM candidates").fetchall():
        candidate = dict(candidate)
        need_id = f"need:{candidate['id']}"
        upsert_entity(
            db,
            need_id,
            kind="need",
            label=promotion.compact(candidate["body"])[:160],
            url=candidate["source_url"],
            visibility="private",
            metadata={
                "author": candidate["author"],
                "body": candidate["body"],
                "status": candidate["status"],
                "published_at": candidate["published_at"],
                "score": candidate["score"],
            },
        )
        channel_id = f"channel:{candidate['platform']}"
        upsert_entity(db, channel_id, kind="channel", label=candidate["platform"], visibility="public")
        upsert_relationship(db, need_id, "found_on", channel_id, evidence_url=candidate["source_url"])
        community = community_from_candidate(candidate)
        community_id = f"community:{candidate['platform']}:{community.casefold()}"
        upsert_entity(
            db, community_id, kind="community", label=community, visibility="public"
        )
        upsert_relationship(
            db, need_id, "found_in", community_id, evidence_url=candidate["source_url"]
        )
        if candidate["suggested_tool"]:
            project_id = f"project:{candidate['suggested_tool']}"
            if db.execute("SELECT 1 FROM entities WHERE id=?", (project_id,)).fetchone():
                upsert_relationship(
                    db,
                    need_id,
                    "matches",
                    project_id,
                    evidence_url=candidate["source_url"],
                    confidence={"high": 0.9, "medium": 0.65, "low": 0.4}.get(
                        candidate["triage_confidence"], 0.5
                    ),
                    metadata={"status": candidate["status"]},
                )

    for draft in db.execute("SELECT * FROM drafts").fetchall():
        draft = dict(draft)
        draft_id = f"draft:{draft['id']}"
        upsert_entity(
            db,
            draft_id,
            kind="draft",
            label=promotion.compact(draft["body"])[:160],
            visibility="private",
            metadata={
                "body": draft["body"],
                "status": draft["status"],
                "include_link": bool(draft["include_link"]),
                "model": draft["model"],
            },
        )
        upsert_relationship(db, draft_id, "responds_to", f"need:{draft['candidate_id']}")
        if draft["project_id"]:
            upsert_relationship(db, draft_id, "mentions", f"project:{draft['project_id']}")

    for outcome in db.execute("SELECT * FROM outcomes").fetchall():
        outcome = dict(outcome)
        outcome_id = f"outcome:{outcome['id']}"
        upsert_entity(
            db,
            outcome_id,
            kind="outcome",
            label=outcome["kind"].replace("_", " "),
            url=outcome["evidence_url"],
            visibility="private",
            metadata={
                "kind": outcome["kind"],
                "amount_minor": outcome["amount_minor"],
                "currency": outcome["currency"],
                "note": outcome["note"],
                "occurred_at": outcome["occurred_at"],
            },
        )
        if outcome["candidate_id"]:
            upsert_relationship(
                db, outcome_id, "resulted_from", f"need:{outcome['candidate_id']}"
            )
        if outcome["draft_id"]:
            upsert_relationship(
                db, outcome_id, "resulted_from", f"draft:{outcome['draft_id']}"
            )
        if outcome["project_id"]:
            upsert_relationship(
                db, outcome_id, "credits", f"project:{outcome['project_id']}"
            )
        if outcome["campaign_id"]:
            upsert_relationship(
                db, outcome_id, "resulted_from", f"campaign:{outcome['campaign_id']}"
            )


def git_remote(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), "remote", "get-url", "origin"],
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def canonical_github_url(remote: str) -> str:
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote.split(":", 1)[1]
    if remote.startswith("https://github.com/"):
        return remote.removesuffix(".git").rstrip("/")
    return ""


def sync_workspace(db, parent: Path | None = None) -> int:
    parent = parent or ROOT.parent
    count = 0
    for path in sorted(parent.iterdir(), key=lambda item: item.name.casefold()):
        try:
            is_repo = path.is_dir() and (path / ".git").exists()
        except OSError:
            # Shared mounts can contain protected system directories such as
            # lost+found. They are not project inventory and must not abort a
            # read-only workspace scan.
            continue
        if not is_repo:
            continue
        remote = canonical_github_url(git_remote(path))
        workspace_id = graph_id("workspace", str(path.resolve()))
        upsert_entity(
            db,
            workspace_id,
            kind="workspace_checkout",
            label=path.name,
            visibility="private",
            metadata={"path": str(path.resolve()), "remote": remote},
        )
        if remote:
            parts = urlparse(remote).path.strip("/").split("/")
            if len(parts) == 2:
                repo_id = f"repository:{parts[0]}/{parts[1]}"
                existing = db.execute(
                    "SELECT visibility FROM entities WHERE id=?", (repo_id,)
                ).fetchone()
                if not existing:
                    upsert_entity(
                        db,
                        repo_id,
                        kind="repository",
                        label=parts[1],
                        url=remote,
                        visibility="private",
                    )
                upsert_relationship(db, workspace_id, "checks_out", repo_id, evidence_url=remote)
        count += 1
    return count


def sync_graph(db, *, include_workspace: bool = False) -> dict:
    sync_public_sources(db)
    sync_private_activity(db)
    workspaces = sync_workspace(db) if include_workspace else 0
    db.commit()
    return graph_report(db) | {"workspace_checkouts_scanned": workspaces}


def graph_report(db) -> dict:
    kinds = Counter(row[0] for row in db.execute("SELECT kind FROM entities"))
    relations = Counter(row[0] for row in db.execute("SELECT relation FROM relationships"))
    return {
        "entities": sum(kinds.values()),
        "relationships": sum(relations.values()),
        "entity_kinds": dict(sorted(kinds.items())),
        "relationship_kinds": dict(sorted(relations.items())),
    }


def public_snapshot(db) -> dict:
    entities = [
        {
            "id": row["id"],
            "kind": row["kind"],
            "label": row["label"],
            "url": row["url"],
            "metadata": json.loads(row["metadata_json"]),
        }
        for row in db.execute(
            "SELECT * FROM entities WHERE visibility='public' ORDER BY kind, label, id"
        )
    ]
    public_ids = {entity["id"] for entity in entities}
    relationships = [
        {
            "source": row["source_id"],
            "relation": row["relation"],
            "target": row["target_id"],
            "evidence_url": row["evidence_url"],
            "confidence": row["confidence"],
            "metadata": json.loads(row["metadata_json"]),
        }
        for row in db.execute("SELECT * FROM relationships ORDER BY source_id, relation, target_id")
        if row["source_id"] in public_ids and row["target_id"] in public_ids
    ]
    return {"version": 1, "entities": entities, "relationships": relationships}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sync = sub.add_parser("sync")
    sync.add_argument("--workspace", action="store_true")
    sub.add_parser("report")
    export = sub.add_parser("export-public")
    export.add_argument("--output", type=Path, default=PUBLIC_SNAPSHOT)
    args = parser.parse_args()
    db = promotion.open_db()
    if args.command == "sync":
        result = sync_graph(db, include_workspace=args.workspace)
    elif args.command == "report":
        result = graph_report(db)
    else:
        sync_graph(db)
        snapshot = public_snapshot(db)
        args.output.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result = {
            "output": str(args.output),
            "entities": len(snapshot["entities"]),
            "relationships": len(snapshot["relationships"]),
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
