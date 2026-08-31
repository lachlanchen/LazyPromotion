#!/usr/bin/env python3
"""Local candidate ledger, relevance matcher, and review-gated reply drafter."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / ".local" / "lazypromotion.sqlite3"
CATALOG_PATH = ROOT / "catalog.json"
SCHEMA_PATH = ROOT / "schemas" / "reply.json"
TRIAGE_SCHEMA_PATH = ROOT / "schemas" / "triage.json"
MODEL = "gpt-5.6-sol"
EFFORT = "low"
MAX_CANDIDATE_AGE_DAYS = 30

HELP_SIGNALS = {
    "how", "help", "need", "needs", "looking", "recommend", "recommendation",
    "suggest", "suggestion", "anyone", "where", "what", "which", "struggling",
    "problem", "issue", "can't", "cannot", "wish", "advice",
}
HELP_PHRASES = {
    "any way", "can anyone", "can someone", "could anyone", "could someone",
    "does anyone", "how can i", "how do i", "is there", "looking for",
    "need a", "need an", "what should i", "where can i", "would anyone",
}
SPAM_SIGNALS = {
    "promote your", "drop your link", "giveaway", "follow for follow", "f4f",
    "crypto pump", "buy followers", "growth hack",
}
OUT_OF_SCOPE_SIGNALS = {
    "[for hire]", "[hiring]", "for hire", "hiring", "job opening",
    "my new tool", "now open to all", "showcase", "we launched",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def open_db(path: Path = DEFAULT_DB) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS candidates (
          id TEXT PRIMARY KEY,
          platform TEXT NOT NULL,
          source_url TEXT NOT NULL UNIQUE,
          author TEXT NOT NULL DEFAULT '',
          body TEXT NOT NULL,
          query TEXT NOT NULL DEFAULT '',
          suggested_tool TEXT NOT NULL DEFAULT '',
          score INTEGER NOT NULL DEFAULT 0,
          rationale TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'discovered',
          duplicate_of TEXT NOT NULL DEFAULT '',
          published_at TEXT NOT NULL DEFAULT '',
          comment_count INTEGER NOT NULL DEFAULT 0,
          source_score INTEGER NOT NULL DEFAULT 0,
          triage_reason TEXT NOT NULL DEFAULT '',
          triage_confidence TEXT NOT NULL DEFAULT '',
          triage_risk_flags TEXT NOT NULL DEFAULT '[]',
          triaged_at TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS drafts (
          id TEXT PRIMARY KEY,
          candidate_id TEXT NOT NULL REFERENCES candidates(id),
          body TEXT NOT NULL,
          why TEXT NOT NULL DEFAULT '',
          confidence TEXT NOT NULL DEFAULT 'low',
          include_link INTEGER NOT NULL DEFAULT 0,
          model TEXT NOT NULL,
          effort TEXT NOT NULL,
          content_hash TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'draft',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approvals (
          token TEXT PRIMARY KEY,
          draft_id TEXT NOT NULL REFERENCES drafts(id),
          content_hash TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          used_at TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          candidate_id TEXT NOT NULL DEFAULT '',
          draft_id TEXT NOT NULL DEFAULT '',
          kind TEXT NOT NULL,
          detail TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL
        );
        """
    )
    columns = {row[1] for row in db.execute("PRAGMA table_info(candidates)")}
    migrations = {
        "duplicate_of": "TEXT NOT NULL DEFAULT ''",
        "published_at": "TEXT NOT NULL DEFAULT ''",
        "comment_count": "INTEGER NOT NULL DEFAULT 0",
        "source_score": "INTEGER NOT NULL DEFAULT 0",
        "triage_reason": "TEXT NOT NULL DEFAULT ''",
        "triage_confidence": "TEXT NOT NULL DEFAULT ''",
        "triage_risk_flags": "TEXT NOT NULL DEFAULT '[]'",
        "triaged_at": "TEXT NOT NULL DEFAULT ''",
    }
    for column, definition in migrations.items():
        if column not in columns:
            db.execute(f"ALTER TABLE candidates ADD COLUMN {column} {definition}")
    refresh_duplicates(db)
    db.commit()
    return db


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9+#' -]+", " ", value.casefold())


def parse_source_time(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    if value.endswith("+0000"):
        value = f"{value[:-5]}+00:00"
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_stale(published_at: str, *, now: datetime | None = None) -> bool:
    published = parse_source_time(published_at)
    if published is None:
        return False
    now = now or datetime.now(timezone.utc)
    return now - published > timedelta(days=MAX_CANDIDATE_AGE_DAYS)


def refresh_duplicates(db: sqlite3.Connection) -> None:
    """Mark exact long-form cross-posts while preserving the replied copy."""
    db.execute("UPDATE candidates SET status='discovered', duplicate_of='' WHERE status='duplicate'")
    rows = db.execute(
        "SELECT id, platform, author, body, status, created_at FROM candidates ORDER BY created_at, id"
    ).fetchall()
    groups: dict[tuple[str, str, str], list[sqlite3.Row]] = {}
    for row in rows:
        author = normalized(row["author"]).strip()
        body = normalized(row["body"]).strip()
        if not author or len(body) < 120:
            continue
        groups.setdefault((row["platform"], author, body), []).append(row)
    for group in groups.values():
        if len(group) < 2:
            continue
        canonical = sorted(
            group,
            key=lambda row: (row["status"] != "replied", row["created_at"], row["id"]),
        )[0]
        db.execute("UPDATE candidates SET duplicate_of='' WHERE id=?", (canonical["id"],))
        for row in group:
            if row["id"] == canonical["id"] or row["status"] not in {"discovered", "duplicate"}:
                continue
            db.execute(
                "UPDATE candidates SET status='duplicate', duplicate_of=? WHERE id=?",
                (canonical["id"], row["id"]),
            )


def rank_projects(body: str, catalog: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    catalog = catalog or load_catalog()
    haystack = normalized(body)
    tokens = set(haystack.split())
    intent_hits = sorted(HELP_SIGNALS & tokens)
    intent_hits.extend(sorted(phrase for phrase in HELP_PHRASES if phrase in haystack))
    intent_hits = sorted(set(intent_hits))
    spam_hits = sorted(signal for signal in SPAM_SIGNALS if signal in haystack)
    out_of_scope_hits = sorted(signal for signal in OUT_OF_SCOPE_SIGNALS if signal in haystack)
    if not intent_hits or spam_hits or out_of_scope_hits:
        return []
    ranked = []
    for project in catalog["projects"]:
        matches = []
        for keyword in project["keywords"]:
            needle = normalized(keyword).strip()
            if needle and needle in haystack:
                matches.append(keyword)
        if not matches:
            continue
        context_hits = sorted(
            context for context in project.get("required_any", [])
            if normalized(context).strip() in haystack
        )
        if project.get("required_any") and not context_hits:
            continue
        score = min(12, len(set(matches)) * 3) + min(6, len(intent_hits) * 2)
        ranked.append(
            {
                "project": project,
                "score": score,
                "matches": sorted(set(matches)),
                "intent_hits": intent_hits,
                "spam_hits": spam_hits,
                "out_of_scope_hits": out_of_scope_hits,
                "context_hits": context_hits,
            }
        )
    return sorted(ranked, key=lambda item: (-item["score"], item["project"]["id"]))


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]}"


def content_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def ingest_candidate(
    db: sqlite3.Connection,
    *,
    platform: str,
    source_url: str,
    body: str,
    author: str = "",
    query: str = "",
    published_at: str = "",
    comment_count: int = 0,
    source_score: int = 0,
) -> dict[str, Any]:
    body = compact(body)
    source_url = source_url.strip()
    if not source_url.startswith(("https://", "http://")):
        raise ValueError("source_url must be an absolute HTTP(S) URL")
    if not body:
        raise ValueError("candidate body is empty")
    ranking = rank_projects(body)
    best = ranking[0] if ranking else None
    candidate_id = stable_id("cand", f"{platform}\n{source_url}")
    existing = db.execute(
        "SELECT body, status, suggested_tool FROM candidates WHERE id=?",
        (candidate_id,),
    ).fetchone()
    now = utc_now()
    rationale = ""
    suggested_tool = ""
    score = 0
    if best:
        suggested_tool = best["project"]["id"]
        score = best["score"]
        rationale = json.dumps(
            {
                "matches": best["matches"],
                "intent_hits": best["intent_hits"],
                "spam_hits": best["spam_hits"],
                "out_of_scope_hits": best["out_of_scope_hits"],
                "context_hits": best["context_hits"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    db.execute(
        """
        INSERT INTO candidates
          (id, platform, source_url, author, body, query, suggested_tool, score, rationale,
           status, duplicate_of, published_at, comment_count, source_score, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered', '', ?, ?, ?, ?, ?)
        ON CONFLICT(source_url) DO UPDATE SET
          author=excluded.author,
          body=excluded.body,
          query=excluded.query,
          suggested_tool=excluded.suggested_tool,
          score=excluded.score,
          rationale=excluded.rationale,
          published_at=CASE WHEN excluded.published_at != '' THEN excluded.published_at ELSE candidates.published_at END,
          comment_count=excluded.comment_count,
          source_score=excluded.source_score,
          updated_at=excluded.updated_at
        """,
        (
            candidate_id, platform, source_url, compact(author), body, compact(query),
            suggested_tool, score, rationale, published_at.strip(), max(0, int(comment_count)),
            int(source_score), now, now,
        ),
    )
    current = db.execute("SELECT status, published_at FROM candidates WHERE id=?", (candidate_id,)).fetchone()
    triage_input_changed = existing and (
        compact(existing["body"]) != body or existing["suggested_tool"] != suggested_tool
    )
    if triage_input_changed and existing["status"] in {"triaged", "rejected"}:
        db.execute(
            """
            UPDATE candidates
            SET status='discovered', triage_reason='', triage_confidence='',
                triage_risk_flags='[]', triaged_at=''
            WHERE id=?
            """,
            (candidate_id,),
        )
        current = db.execute("SELECT status, published_at FROM candidates WHERE id=?", (candidate_id,)).fetchone()
    if current and current["status"] in {"discovered", "stale"}:
        status = "stale" if is_stale(current["published_at"]) else "discovered"
        db.execute("UPDATE candidates SET status=? WHERE id=?", (status, candidate_id))
    refresh_duplicates(db)
    db.execute(
        "INSERT INTO events(candidate_id, kind, detail, created_at) VALUES (?, 'candidate_ingested', ?, ?)",
        (candidate_id, json.dumps({"score": score, "tool": suggested_tool}, sort_keys=True), now),
    )
    db.commit()
    return row_dict(db.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()) or {}


def project_by_id(project_id: str) -> dict[str, Any]:
    for project in load_catalog()["projects"]:
        if project["id"] == project_id:
            return project
    raise ValueError(f"unknown project: {project_id}")


def draft_prompt(candidate: dict[str, Any], project: dict[str, Any]) -> str:
    return f"""Draft one genuinely useful public reply to a social-media post.

Platform: {candidate['platform']}
Author: {candidate['author'] or 'unknown'}
Post URL: {candidate['source_url']}
Post text:
{candidate['body']}

Relevant maintained project:
- Name: {project['name']}
- URL: {project['url']}
- Evidence-grounded summary: {project['summary']}
{f"- Additional reviewed context: {project['reply_context']}" if project.get('reply_context') else ""}

Return only the JSON object required by the supplied schema.

Requirements:
- Answer the person's concrete need before mentioning any project.
- Sound like a thoughtful peer, not a marketer. Be specific and natural.
- Mention this maintained project only when it is directly useful.
- Explicitly disclose affiliation in plain language, e.g. “I maintain…” or “I built…”.
- Use at most one project link. Do not ask for stars, follows, votes, or DMs.
- Do not invent capabilities, traction, users, benchmarks, endorsements, or personal experience.
- Do not repeat the post back to its author or use generic praise.
- If the match is weak, omit the link and say so through include_link=false.
- Keep the reply compact: <= 500 characters for X, <= 900 elsewhere.
- This is a draft only. Do not browse, post, message, or take any external action.
"""


def triage_prompt(candidate: dict[str, Any], project: dict[str, Any]) -> str:
    return f"""Review one possible social-media help request for a project maintainer.

Platform: {candidate['platform']}
Post URL: {candidate['source_url']}
Author: {candidate['author'] or 'unknown'}
Published at: {candidate.get('published_at') or 'unknown'}
Existing comments: {candidate.get('comment_count', 0)}
Post text:
{candidate['body']}

Potentially relevant maintained project:
- Name: {project['name']}
- URL: {project['url']}
- Grounded summary: {project['summary']}

Return only the JSON object required by the supplied schema.

Mark eligible=true only when the author is clearly asking for help and this
specific project can address that need without stretching its capabilities.
Reject announcements, hiring posts, resolved or saturated discussions, generic
keyword overlap, unrelated product categories, opportunities that would feel
like unsolicited advertising, and posts where an affiliation link would not
add genuine value. A useful answer must be possible before mentioning the
project, and affiliation must be disclosed. Do not browse, draft a reply,
navigate, post, vote, follow, or message anyone.
"""


def run_codex_structured(prompt: str, schema: Path, *, prefix: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
        output = Path(tmp) / "result.json"
        command = [
            "codex", "exec", "--ephemeral", "--json", "--model", MODEL,
            "-c", f'model_reasoning_effort="{EFFORT}"',
            "-c", "mcp_servers.lazypromotion_browser.enabled=false",
            "--sandbox", "read-only", "--skip-git-repo-check",
            "--output-schema", str(schema),
            "--output-last-message", str(output),
            "-C", str(ROOT), "-",
        ]
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=900,
            check=False,
            env=os.environ.copy(),
        )
        if completed.returncode != 0:
            tail = compact(completed.stderr[-2000:] or completed.stdout[-2000:])
            raise RuntimeError(f"Codex structured check failed ({completed.returncode}): {tail}")
        if not output.exists():
            raise RuntimeError("Codex completed without writing the structured result")
        return json.loads(output.read_text(encoding="utf-8"))


def run_codex_draft(candidate: dict[str, Any], project: dict[str, Any]) -> dict[str, Any]:
    return run_codex_structured(
        draft_prompt(candidate, project),
        SCHEMA_PATH,
        prefix="lazypromotion-draft-",
    )


def run_codex_triage(candidate: dict[str, Any], project: dict[str, Any]) -> dict[str, Any]:
    return run_codex_structured(
        triage_prompt(candidate, project),
        TRIAGE_SCHEMA_PATH,
        prefix="lazypromotion-triage-",
    )


def save_triage(db: sqlite3.Connection, candidate_id: str, result: dict[str, Any]) -> dict[str, Any]:
    candidate = row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone())
    if not candidate:
        raise ValueError(f"candidate not found: {candidate_id}")
    if candidate["status"] != "discovered":
        raise ValueError(f"candidate status is {candidate['status']}; triage is not allowed")
    confidence = str(result["confidence"])
    if confidence not in {"low", "medium", "high"}:
        raise ValueError("triage confidence is invalid")
    reason = compact(str(result["reason"]))
    if not reason:
        raise ValueError("triage reason is empty")
    if not isinstance(result["eligible"], bool):
        raise ValueError("triage eligibility is invalid")
    if not isinstance(result.get("risk_flags"), list):
        raise ValueError("triage risk flags are invalid")
    flags = sorted({compact(str(flag)) for flag in result["risk_flags"] if compact(str(flag))})
    status = "triaged" if result["eligible"] else "rejected"
    now = utc_now()
    db.execute(
        """
        UPDATE candidates
        SET status=?, triage_reason=?, triage_confidence=?, triage_risk_flags=?,
            triaged_at=?, updated_at=?
        WHERE id=?
        """,
        (status, reason, confidence, json.dumps(flags, ensure_ascii=False), now, now, candidate_id),
    )
    db.execute(
        "INSERT INTO events(candidate_id, kind, detail, created_at) VALUES (?, 'candidate_triaged', ?, ?)",
        (
            candidate_id,
            json.dumps(
                {
                    "eligible": status == "triaged",
                    "confidence": confidence,
                    "risk_flags": flags,
                    "model": MODEL,
                    "effort": EFFORT,
                },
                sort_keys=True,
            ),
            now,
        ),
    )
    db.commit()
    return row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone()) or {}


def triage_candidate(db: sqlite3.Connection, candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate["status"] != "discovered":
        raise ValueError(f"candidate status is {candidate['status']}; triage is not allowed")
    if int(candidate["score"]) < 5:
        raise ValueError("candidate did not pass deterministic relevance filtering")
    project_id = candidate["suggested_tool"]
    if not project_id:
        raise ValueError("candidate has no deterministic project match")
    result = run_codex_triage(candidate, project_by_id(project_id))
    return save_triage(db, candidate["id"], result)


def save_draft(db: sqlite3.Connection, candidate_id: str, result: dict[str, Any]) -> dict[str, Any]:
    body = compact(str(result["reply"]))
    candidate = row_dict(db.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone())
    if not candidate:
        raise ValueError(f"candidate not found: {candidate_id}")
    limit = 500 if candidate["platform"] == "x" else 1400
    if len(body) > limit:
        raise ValueError(f"draft is {len(body)} characters; platform safety limit is {limit}")
    digest = content_hash(body)
    draft_id = stable_id("draft", f"{candidate_id}\n{digest}")
    now = utc_now()
    db.execute(
        """
        INSERT INTO drafts
          (id, candidate_id, body, why, confidence, include_link, model, effort, content_hash, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          why=excluded.why, confidence=excluded.confidence, include_link=excluded.include_link,
          updated_at=excluded.updated_at
        """,
        (
            draft_id, candidate_id, body, compact(str(result["why"])), str(result["confidence"]),
            int(bool(result["include_link"])), MODEL, EFFORT, digest, now, now,
        ),
    )
    db.execute("UPDATE candidates SET status='drafted', updated_at=? WHERE id=?", (now, candidate_id))
    db.execute(
        "INSERT INTO events(candidate_id, draft_id, kind, detail, created_at) VALUES (?, ?, 'draft_created', ?, ?)",
        (candidate_id, draft_id, json.dumps({"model": MODEL, "effort": EFFORT}), now),
    )
    db.commit()
    return row_dict(db.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()) or {}


def approve_draft(db: sqlite3.Connection, draft_id: str, ttl_minutes: int) -> dict[str, Any]:
    draft = row_dict(db.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone())
    if not draft:
        raise ValueError(f"draft not found: {draft_id}")
    token = f"approve_{secrets.token_urlsafe(18)}"
    now_dt = datetime.now(timezone.utc).replace(microsecond=0)
    expires = now_dt + timedelta(minutes=ttl_minutes)
    db.execute(
        "INSERT INTO approvals(token, draft_id, content_hash, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            token, draft_id, draft["content_hash"],
            expires.isoformat().replace("+00:00", "Z"), now_dt.isoformat().replace("+00:00", "Z"),
        ),
    )
    db.execute("UPDATE drafts SET status='approved', updated_at=? WHERE id=?", (utc_now(), draft_id))
    db.commit()
    return {"draft_id": draft_id, "approval_token": token, "expires_at": expires.isoformat().replace("+00:00", "Z")}


def validate_approval(db: sqlite3.Connection, draft_id: str, token: str) -> dict[str, Any]:
    row = db.execute(
        """
        SELECT a.*, d.body, d.status AS draft_status, d.candidate_id, d.content_hash AS current_hash
        FROM approvals a JOIN drafts d ON d.id=a.draft_id
        WHERE a.token=? AND a.draft_id=?
        """,
        (token, draft_id),
    ).fetchone()
    approval = row_dict(row)
    if not approval:
        raise ValueError("approval token does not match this draft")
    if approval["used_at"]:
        raise ValueError("approval token was already used")
    expires = datetime.fromisoformat(approval["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) >= expires:
        raise ValueError("approval token has expired")
    if approval["content_hash"] != approval["current_hash"] or content_hash(approval["body"]) != approval["current_hash"]:
        raise ValueError("draft content changed after approval")
    return approval


def mark_sent(db: sqlite3.Connection, draft_id: str, token: str, detail: dict[str, Any]) -> None:
    approval = validate_approval(db, draft_id, token)
    now = utc_now()
    db.execute("UPDATE approvals SET used_at=? WHERE token=?", (now, token))
    db.execute("UPDATE drafts SET status='sent', updated_at=? WHERE id=?", (now, draft_id))
    db.execute("UPDATE candidates SET status='replied', updated_at=? WHERE id=?", (now, approval["candidate_id"]))
    db.execute(
        "INSERT INTO events(candidate_id, draft_id, kind, detail, created_at) VALUES (?, ?, 'reply_sent', ?, ?)",
        (approval["candidate_id"], draft_id, json.dumps(detail, ensure_ascii=False, sort_keys=True), now),
    )
    refresh_duplicates(db)
    db.commit()


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("catalog")

    ingest = sub.add_parser("ingest")
    ingest.add_argument("--platform", required=True, choices=("reddit", "x", "instagram"))
    ingest.add_argument("--url", required=True)
    ingest.add_argument("--body", required=True)
    ingest.add_argument("--author", default="")
    ingest.add_argument("--query", default="")

    listing = sub.add_parser("list")
    listing.add_argument("--status", default="")
    listing.add_argument("--min-score", type=int, default=0)
    listing.add_argument("--limit", type=int, default=50)

    show = sub.add_parser("show")
    show.add_argument("id")

    draft = sub.add_parser("draft")
    draft.add_argument("candidate_id")
    draft.add_argument("--project", default="")

    triage = sub.add_parser("triage")
    triage.add_argument("candidate_id")

    triage_pending = sub.add_parser("triage-pending")
    triage_pending.add_argument("--limit", type=int, default=5)

    approve = sub.add_parser("approve")
    approve.add_argument("draft_id")
    approve.add_argument("--ttl-minutes", type=int, default=30)
    approve.add_argument("--confirm-reviewed-exact-content", action="store_true", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    db = open_db(args.db)
    if args.command == "init":
        print_json({"ok": True, "database": str(args.db), "model": MODEL, "effort": EFFORT})
    elif args.command == "catalog":
        print_json(load_catalog())
    elif args.command == "ingest":
        print_json(
            ingest_candidate(
                db, platform=args.platform, source_url=args.url, body=args.body,
                author=args.author, query=args.query,
            )
        )
    elif args.command == "list":
        where = ["score >= ?"]
        values: list[Any] = [args.min_score]
        if args.status:
            where.append("status = ?")
            values.append(args.status)
        else:
            where.append("status NOT IN ('duplicate', 'stale', 'rejected')")
        values.append(args.limit)
        rows = db.execute(
            f"SELECT * FROM candidates WHERE {' AND '.join(where)} ORDER BY score DESC, created_at DESC LIMIT ?",
            values,
        ).fetchall()
        print_json({"candidates": [dict(row) for row in rows]})
    elif args.command == "show":
        candidate = row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (args.id,)).fetchone())
        draft = row_dict(db.execute("SELECT * FROM drafts WHERE id=?", (args.id,)).fetchone())
        print_json(candidate or draft or {"error": "not found", "id": args.id})
    elif args.command == "draft":
        candidate = row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (args.candidate_id,)).fetchone())
        if not candidate:
            raise SystemExit(f"candidate not found: {args.candidate_id}")
        if candidate["status"] != "triaged":
            raise SystemExit(f"candidate status is {candidate['status']}; model triage is required before drafting")
        project_id = args.project or candidate["suggested_tool"]
        if not project_id:
            raise SystemExit("candidate has no relevant project; choose --project only after manual review")
        if project_id != candidate["suggested_tool"]:
            raise SystemExit("draft project differs from the model-triaged project")
        result = run_codex_draft(candidate, project_by_id(project_id))
        print_json(save_draft(db, args.candidate_id, result))
    elif args.command == "triage":
        candidate = row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (args.candidate_id,)).fetchone())
        if not candidate:
            raise SystemExit(f"candidate not found: {args.candidate_id}")
        print_json(triage_candidate(db, candidate))
    elif args.command == "triage-pending":
        limit = max(1, min(args.limit, 10))
        candidates = [
            dict(row) for row in db.execute(
                """
                SELECT * FROM candidates
                WHERE status='discovered' AND score >= 5 AND suggested_tool != ''
                ORDER BY published_at DESC, score DESC, created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        ]
        results = []
        for candidate in candidates:
            try:
                results.append({"ok": True, "candidate": triage_candidate(db, candidate)})
            except Exception as exc:
                now = utc_now()
                db.execute(
                    "INSERT INTO events(candidate_id, kind, detail, created_at) VALUES (?, 'triage_failed', ?, ?)",
                    (candidate["id"], compact(str(exc)), now),
                )
                db.commit()
                results.append({"ok": False, "candidate_id": candidate["id"], "error": str(exc)})
        print_json({"model": MODEL, "effort": EFFORT, "processed": len(results), "results": results})
    elif args.command == "approve":
        if not (1 <= args.ttl_minutes <= 1440):
            raise SystemExit("--ttl-minutes must be between 1 and 1440")
        print_json(approve_draft(db, args.draft_id, args.ttl_minutes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
