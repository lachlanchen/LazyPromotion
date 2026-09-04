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
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / ".local" / "lazypromotion.sqlite3"
CATALOG_PATH = ROOT / "catalog.json"
GITHUB_CATALOG_PATH = ROOT / "github-repos.json"
SCHEMA_PATH = ROOT / "schemas" / "reply.json"
TRIAGE_SCHEMA_PATH = ROOT / "schemas" / "triage.json"
MODEL = "gpt-5.6-sol"
EFFORT = "low"
MAX_CANDIDATE_AGE_DAYS = 30
AI_COMMENT_BLOCKED_PLATFORMS = {"hackernews"}

HELP_SIGNALS = {
    "how", "help", "need", "needs", "looking", "recommend", "recommendation",
    "suggest", "suggestion", "anyone", "where", "what", "which", "struggling",
    "problem", "issue", "can't", "cannot", "wish", "advice",
}
HELP_PHRASES = {
    "any way", "can anyone", "can someone", "could anyone", "could someone",
    "does anyone", "how can i", "how do i", "is there", "looking for",
    "help me", "help needed", "need a", "need an", "please help",
    "what should i", "where can i", "would anyone",
    "怎么", "怎麼", "如何", "有没有", "有沒有", "哪里", "哪裡", "求助",
    "推荐", "推薦", "想学", "想學", "需要", "看不懂", "读不懂", "讀不懂",
    "どうやって", "おすすめ", "教えて", "困って", "読めない", "分からない",
}
SPAM_SIGNALS = {
    "promote your", "drop your link", "giveaway", "follow for follow", "f4f",
    "crypto pump", "buy followers", "growth hack",
}
OUT_OF_SCOPE_SIGNALS = {
    "[for hire]", "[hiring]", "for hire", "hiring", "job opening",
    "full-time", "full time", "résumé/cv", "resume/cv", "technologies:",
    "willing to relocate",
    "my new tool", "now open to all", "showcase", "volunteer opportunities",
    "we launched", "free to try", "link in bio", "follow for more", "save this",
    "dm me", "i got you", "apply now", "can i apply", "how can i apply",
    "where can i apply", "we're hiring", "we are hiring",
    "want to publish your own article", "upgrade to premium",
}
COMMENT_REQUEST_PHRASES = {
    "any advice", "any recommendations", "any recommendation", "any suggestions",
    "can anyone", "can someone", "could anyone", "could someone", "does anyone",
    "does anyone know", "has anyone", "help me", "help needed", "how can i",
    "how do i", "i can't", "i cannot", "i need", "i'm looking", "i am looking",
    "is there a tool", "is there an app", "is there a way", "looking for",
    "my issue", "my problem", "need help", "please help", "what can i",
    "what should i", "where can i", "which should i", "why can't i",
    "怎么", "怎麼", "如何", "有没有", "有沒有", "哪里", "哪裡", "求助",
    "推荐", "推薦", "想学", "想學", "需要", "看不懂", "读不懂", "讀不懂",
    "どうやって", "おすすめ", "教えて", "困って", "読めない", "分からない",
}
SELF_SOLUTION_PHRASES = {
    "i built", "i created", "i launched", "i tested", "my new tool", "my new app",
    "we built", "we created", "we launched", "we tested", "our new tool", "our new app",
    "free tutoring is available",
}
BOT_AUTHORS = {"automoderator"}
GENERIC_REPO_TOPICS = {
    "ai", "app", "automation", "cli", "code", "codex", "current", "currently",
    "education", "github", "language",
    "javascript", "learning", "linux", "model", "multilingual", "open source",
    "openai", "other", "pull", "python", "react", "research", "that", "tool", "tools",
    "typescript", "way", "web", "webapp", "website", "workflow", "workflows",
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
          triage_requested_at TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS drafts (
          id TEXT PRIMARY KEY,
          candidate_id TEXT NOT NULL REFERENCES candidates(id),
          project_id TEXT NOT NULL DEFAULT '',
          candidate_content_hash TEXT NOT NULL DEFAULT '',
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
        CREATE TABLE IF NOT EXISTS entities (
          id TEXT PRIMARY KEY,
          kind TEXT NOT NULL,
          label TEXT NOT NULL,
          url TEXT NOT NULL DEFAULT '',
          visibility TEXT NOT NULL DEFAULT 'private',
          metadata_json TEXT NOT NULL DEFAULT '{}',
          first_seen_at TEXT NOT NULL,
          last_seen_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS relationships (
          id TEXT PRIMARY KEY,
          source_id TEXT NOT NULL REFERENCES entities(id),
          relation TEXT NOT NULL,
          target_id TEXT NOT NULL REFERENCES entities(id),
          evidence_url TEXT NOT NULL DEFAULT '',
          confidence REAL NOT NULL DEFAULT 1.0,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          first_seen_at TEXT NOT NULL,
          last_seen_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_entities_kind ON entities(kind);
        CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_id, relation);
        CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_id, relation);
        CREATE TABLE IF NOT EXISTS outcomes (
          id TEXT PRIMARY KEY,
          kind TEXT NOT NULL,
          candidate_id TEXT NOT NULL DEFAULT '',
          draft_id TEXT NOT NULL DEFAULT '',
          campaign_id TEXT NOT NULL DEFAULT '',
          project_id TEXT NOT NULL DEFAULT '',
          amount_minor INTEGER NOT NULL DEFAULT 0,
          currency TEXT NOT NULL DEFAULT '',
          reference_hash TEXT NOT NULL DEFAULT '',
          evidence_url TEXT NOT NULL DEFAULT '',
          note TEXT NOT NULL DEFAULT '',
          occurred_at TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_outcomes_kind ON outcomes(kind, occurred_at);
        CREATE INDEX IF NOT EXISTS idx_outcomes_candidate ON outcomes(candidate_id);
        CREATE TABLE IF NOT EXISTS demand_signals (
          id TEXT PRIMARY KEY,
          source TEXT NOT NULL,
          signal_kind TEXT NOT NULL,
          subject TEXT NOT NULL,
          url TEXT NOT NULL DEFAULT '',
          project_id TEXT NOT NULL DEFAULT '',
          metric TEXT NOT NULL,
          value REAL NOT NULL,
          delta_value REAL,
          delta_unit TEXT NOT NULL DEFAULT '',
          period TEXT NOT NULL,
          observed_at TEXT NOT NULL,
          evidence_path TEXT NOT NULL DEFAULT '',
          metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_demand_signals_source
        ON demand_signals(source, period, signal_kind);
        CREATE INDEX IF NOT EXISTS idx_demand_signals_project
        ON demand_signals(project_id, metric, value);
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
        "triage_requested_at": "TEXT NOT NULL DEFAULT ''",
    }
    for column, definition in migrations.items():
        if column not in columns:
            db.execute(f"ALTER TABLE candidates ADD COLUMN {column} {definition}")
    outcome_columns = {row[1] for row in db.execute("PRAGMA table_info(outcomes)")}
    if "reference_hash" not in outcome_columns:
        db.execute(
            "ALTER TABLE outcomes ADD COLUMN reference_hash TEXT NOT NULL DEFAULT ''"
        )
    db.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_outcomes_reference
        ON outcomes(kind, reference_hash) WHERE reference_hash != ''
        """
    )
    draft_columns = {row[1] for row in db.execute("PRAGMA table_info(drafts)")}
    draft_migrations = {
        "project_id": "TEXT NOT NULL DEFAULT ''",
        "candidate_content_hash": "TEXT NOT NULL DEFAULT ''",
    }
    draft_schema_changed = not set(draft_migrations).issubset(draft_columns)
    unbound_active_candidates = []
    if draft_schema_changed:
        unbound_active_candidates = [
            row[0]
            for row in db.execute(
                """
                SELECT DISTINCT candidate_id FROM drafts
                WHERE status IN ('draft', 'prepared', 'approved')
                """
            )
        ]
    for column, definition in draft_migrations.items():
        if column not in draft_columns:
            db.execute(f"ALTER TABLE drafts ADD COLUMN {column} {definition}")
    # Legacy drafts were not bound to the candidate text and project used to
    # generate them. Run this backfill only while adding the columns: an empty
    # project_id is intentional for current value-only courtesy drafts.
    if draft_schema_changed:
        for row in db.execute(
            """
            SELECT d.id, c.suggested_tool, c.body
            FROM drafts d JOIN candidates c ON c.id=d.candidate_id
            WHERE d.project_id='' OR d.candidate_content_hash=''
            """
        ).fetchall():
            db.execute(
                """
                UPDATE drafts SET project_id=?, candidate_content_hash=? WHERE id=?
                """,
                (row[1], content_hash(compact(row[2])), row[0]),
            )
    if unbound_active_candidates:
        placeholders = ",".join("?" for _ in unbound_active_candidates)
        now = utc_now()
        db.execute(
            f"""
            UPDATE drafts SET status='superseded', updated_at=?
            WHERE candidate_id IN ({placeholders})
              AND status IN ('draft', 'prepared', 'approved')
            """,
            (now, *unbound_active_candidates),
        )
        db.execute(
            f"""
            UPDATE candidates
            SET status='discovered', triage_reason='', triage_confidence='',
                triage_risk_flags='[]', triaged_at='', updated_at=?
            WHERE id IN ({placeholders}) AND status != 'replied'
            """,
            (now, *unbound_active_candidates),
        )
        for candidate_id in unbound_active_candidates:
            db.execute(
                """
                INSERT INTO events(candidate_id, kind, detail, created_at)
                VALUES (?, 'draft_invalidated', ?, ?)
                """,
                (candidate_id, "legacy draft lacked immutable evidence binding", now),
            )
    refresh_duplicates(db)
    db.commit()
    return db


def load_catalog() -> dict[str, Any]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    projects = list(catalog["projects"])
    if not GITHUB_CATALOG_PATH.exists():
        return {**catalog, "projects": projects}
    indexed = json.loads(GITHUB_CATALOG_PATH.read_text(encoding="utf-8"))
    known_urls = {project["url"].rstrip("/").casefold() for project in projects}
    for repo in indexed.get("repositories", []):
        url = str(repo.get("url") or "").rstrip("/")
        description = compact(str(repo.get("description") or ""))
        if not url or not description or url.casefold() in known_urls:
            continue
        topics = []
        for value in repo.get("topics", []):
            topic = normalized(str(value).replace("-", " ")).strip()
            if topic and topic not in GENERIC_REPO_TOPICS:
                topics.append(topic)
        name = compact(str(repo.get("name") or ""))
        name_keyword = normalized(re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)).strip()
        keywords = sorted(set(topics + ([name_keyword] if name_keyword else [])))
        if not keywords:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
        projects.append({
            "id": f"github-{slug}",
            "name": name,
            "url": url,
            "summary": description,
            "keywords": keywords,
            "required_any": [],
            "generated": True,
        })
        known_urls.add(url.casefold())
    return {**catalog, "projects": projects}


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalized(value: str) -> str:
    folded = value.casefold()
    preserved = "".join(
        character if character.isalnum() or character in "+#' -" else " "
        for character in folded
    )
    return re.sub(r"\s+", " ", preserved)


def keyword_present(needle: str, haystack: str) -> bool:
    """Match ASCII keywords by token boundary and CJK keywords by substring."""
    if any(character.isalnum() and not character.isascii() for character in needle):
        return needle in haystack
    return f" {needle} " in f" {haystack} "


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


def help_request_signals(body: str) -> dict[str, list[str]]:
    haystack = normalized(body)
    tokens = set(haystack.split())
    intent_hits = sorted(HELP_SIGNALS & tokens)
    intent_hits.extend(sorted(
        phrase for phrase in HELP_PHRASES
        if keyword_present(normalized(phrase).strip(), haystack)
    ))
    direct_request_hits = sorted(
        phrase for phrase in COMMENT_REQUEST_PHRASES
        if keyword_present(normalized(phrase).strip(), haystack)
    )
    self_solution_hits = sorted(
        phrase for phrase in SELF_SOLUTION_PHRASES
        if keyword_present(normalized(phrase).strip(), haystack)
    )
    return {
        "intent_hits": sorted(set(intent_hits)),
        "spam_hits": sorted(
            signal for signal in SPAM_SIGNALS
            if keyword_present(normalized(signal).strip(), haystack)
        ),
        "out_of_scope_hits": sorted(
            signal for signal in OUT_OF_SCOPE_SIGNALS
            if keyword_present(normalized(signal).strip(), haystack)
        ),
        "existing_solution_hits": (
            self_solution_hits if self_solution_hits and not direct_request_hits else []
        ),
    }


def is_help_request(body: str) -> bool:
    signals = help_request_signals(body)
    haystack = normalized(body)
    ask_hn = haystack.startswith("ask hn ")
    direct_request = any(
        keyword_present(normalized(phrase).strip(), haystack)
        for phrase in COMMENT_REQUEST_PHRASES
    )
    explicit = (
        "?" in body
        or ask_hn
        or direct_request
        or any(
            keyword_present(normalized(phrase).strip(), haystack)
            for phrase in HELP_PHRASES
        )
    )
    return bool(
        (signals["intent_hits"] or ask_hn) and explicit
        and not signals["spam_hits"] and not signals["out_of_scope_hits"]
        and not signals["existing_solution_hits"]
    )


def is_comment_source(platform: str, source_url: str, body: str) -> bool:
    if platform == "hackernews":
        return not normalized(body).strip().startswith("ask hn ")
    if platform == "x":
        return bool(re.search(r"(?:^| )replying to [a-z0-9_]", normalized(body)))
    if platform == "instagram":
        parts = [part for part in urlparse(source_url).path.split("/") if part]
        return "c" in parts and parts.index("c") + 1 < len(parts)
    if platform != "reddit":
        return False
    parts = [part for part in urlparse(source_url).path.split("/") if part]
    try:
        start = parts.index("comments")
    except ValueError:
        return False
    return len(parts[start + 2:]) >= 2


def is_triageable_request(platform: str, source_url: str, body: str) -> bool:
    if not is_help_request(body):
        return False
    if not is_comment_source(platform, source_url, body):
        return True
    unquoted = re.sub(r'"[^"\n]*"|“[^”\n]*”', " ", body)
    haystack = normalized(unquoted)
    request_windows = compact(f"{haystack[:600]} {haystack[-300:]}")
    return any(
        keyword_present(normalized(phrase).strip(), request_windows)
        for phrase in COMMENT_REQUEST_PHRASES if phrase != "looking for"
    )


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
        priority = {
            "replied": 0,
            "drafted": 1,
            "triaged": 1,
            "discovered": 2,
            "stale": 3,
            "rejected": 4,
        }
        canonical = sorted(
            group,
            key=lambda row: (priority.get(row["status"], 3), row["created_at"], row["id"]),
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
    signals = help_request_signals(body)
    intent_hits = signals["intent_hits"]
    spam_hits = signals["spam_hits"]
    out_of_scope_hits = signals["out_of_scope_hits"]
    existing_solution_hits = signals["existing_solution_hits"]
    if not intent_hits or spam_hits or out_of_scope_hits or existing_solution_hits:
        return []
    ranked = []
    for project in catalog["projects"]:
        matches = []
        keyword_context_any = {
            normalized(str(keyword)).strip(): [
                normalized(str(context)).strip() for context in contexts
            ]
            for keyword, contexts in project.get("keyword_context_any", {}).items()
        }
        for keyword in project["keywords"]:
            needle = normalized(keyword).strip()
            if needle and keyword_present(needle, haystack):
                required_context = keyword_context_any.get(needle, [])
                if required_context and not any(
                    context and keyword_present(context, haystack)
                    for context in required_context
                ):
                    continue
                matches.append(keyword)
        if not matches:
            continue
        if project.get("generated"):
            strong_matches = [
                match for match in matches
                if " " in normalized(match).strip()
            ]
            if not strong_matches and len(set(matches)) < 2:
                continue
        context_hits = sorted(
            context for context in project.get("required_any", [])
            if normalized(context).strip() in haystack
        )
        if project.get("required_any") and not context_hits:
            continue
        curated_bonus = 0 if project.get("generated") else 6
        score = curated_bonus + min(12, len(set(matches)) * 3) + min(6, len(intent_hits) * 2)
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
    candidate_id = stable_id("cand", f"{platform}\n{source_url}")
    existing = db.execute(
        "SELECT body, status, suggested_tool FROM candidates WHERE id=?",
        (candidate_id,),
    ).fetchone()
    # Search cards are often title-only while inspection has already stored the
    # full post. Never let a shorter rediscovery erase richer reviewed context
    # or repeatedly reset a prior model decision.
    if existing and len(compact(existing["body"])) > len(body):
        body = compact(existing["body"])
    ranking = rank_projects(body)
    best = ranking[0] if ranking else None
    now = utc_now()
    rationale = ""
    suggested_tool = ""
    score = 0
    if compact(author).casefold() in BOT_AUTHORS:
        best = None
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
    if triage_input_changed:
        # A route admitted the earlier text, not this newly hydrated or changed
        # version. Require the current evidence to pass the route again.
        db.execute(
            "UPDATE candidates SET triage_requested_at='' WHERE id=?",
            (candidate_id,),
        )
    if triage_input_changed and existing["status"] in {"triaged", "rejected", "drafted"}:
        if existing["status"] == "drafted":
            db.execute(
                """
                UPDATE drafts SET status='superseded', updated_at=?
                WHERE candidate_id=? AND status IN ('draft', 'prepared', 'approved')
                """,
                (now, candidate_id),
            )
            db.execute(
                """
                INSERT INTO events(candidate_id, kind, detail, created_at)
                VALUES (?, 'draft_invalidated', ?, ?)
                """,
                (candidate_id, "candidate text or matched project changed", now),
            )
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


def mark_triage_requested(
    db: sqlite3.Connection,
    candidate_ids: list[str],
) -> list[str]:
    """Admit reviewed, discovered candidates to the retryable model queue."""
    requested = []
    now = utc_now()
    for candidate_id in dict.fromkeys(candidate_ids):
        row = db.execute(
            "SELECT status, triage_requested_at FROM candidates WHERE id=?",
            (candidate_id,),
        ).fetchone()
        if not row or row["status"] != "discovered":
            continue
        if not row["triage_requested_at"]:
            db.execute(
                "UPDATE candidates SET triage_requested_at=? WHERE id=?",
                (now, candidate_id),
            )
            db.execute(
                """
                INSERT INTO events(candidate_id, kind, detail, created_at)
                VALUES (?, 'triage_requested', 'reviewed discovery route admission', ?)
                """,
                (candidate_id, now),
            )
        requested.append(candidate_id)
    db.commit()
    return requested


def withdraw_untriageable_requests(db: sqlite3.Connection) -> list[dict[str, str]]:
    """Remove retry admission when current evidence no longer shows a safe request."""
    rows = db.execute(
        """
        SELECT id, platform, source_url, author, body, published_at
        FROM candidates
        WHERE status='discovered' AND triage_requested_at != ''
        """
    ).fetchall()
    withdrawn: list[dict[str, str]] = []
    now = utc_now()
    for row in rows:
        reason = ""
        if compact(row["author"]).casefold() in BOT_AUTHORS:
            reason = "automated author"
        elif is_stale(row["published_at"]):
            reason = "source became stale"
        elif not is_triageable_request(row["platform"], row["source_url"], row["body"]):
            reason = "current evidence is not an explicit request"
        if not reason:
            continue
        db.execute(
            "UPDATE candidates SET triage_requested_at='' WHERE id=?",
            (row["id"],),
        )
        db.execute(
            """
            INSERT INTO events(candidate_id, kind, detail, created_at)
            VALUES (?, 'triage_request_withdrawn', ?, ?)
            """,
            (row["id"], reason, now),
        )
        withdrawn.append({"candidate_id": row["id"], "reason": reason})
    db.commit()
    return withdrawn


def project_by_id(project_id: str) -> dict[str, Any]:
    for project in load_catalog()["projects"]:
        if project["id"] == project_id:
            return project
    raise ValueError(f"unknown project: {project_id}")


def draft_prompt(
    candidate: dict[str, Any],
    project: dict[str, Any],
    *,
    value_only: bool = False,
    required_prefix: str = "",
) -> str:
    targeting = ""
    if candidate["platform"] == "instagram" and is_comment_source(
        candidate["platform"], candidate["source_url"], candidate["body"]
    ) and compact(candidate.get("author") or ""):
        username = compact(candidate["author"]).lstrip("@")
        targeting = f"- Begin the reply with @{username} so the reviewed text targets the exact comment.\n"
    value_only_policy = ""
    if value_only:
        value_only_policy = """
Community/account policy for this draft:
- Provide value only. Do not name, mention, link, or allude to the maintained
  project, its maintainer, LazyingArt, the profile, a fit check, or any offer.
- Do not include any URL or call to action. Set include_link=false.
- You may use the reviewed project context only to avoid incorrect technical
  advice; the final reply must read as an independent peer contribution.
"""
    prefix_policy = ""
    required_prefix = compact(required_prefix)
    if required_prefix:
        prefix_policy = f"""
Community-specific disclosure requirement:
- Begin the reply with this exact text: {json.dumps(required_prefix, ensure_ascii=False)}
- Do not paraphrase, omit, or move that disclosure.
"""
    return f"""Draft one genuinely useful public reply to a social-media post.

Platform: {candidate['platform']}
Author: {candidate['author'] or 'unknown'}
Post URL: {candidate['source_url']}
Post text:
{candidate['body']}

Relevant maintained project:
- Name: {project['name']}
- URL: {project['url']}
{f"- Public homepage: {project['homepage']}" if project.get('homepage') else ""}
{f"- Preferred reply destination: {project['reply_url']}" if project.get('reply_url') else ""}
- Evidence-grounded summary: {project['summary']}
{f"- Additional reviewed context: {project['reply_context']}" if project.get('reply_context') else ""}

Return only the JSON object required by the supplied schema.

Requirements:
- Answer the person's concrete need before mentioning any project.
- Sound like a thoughtful peer, not a marketer. Be specific and natural.
- Mention this maintained project only when it is directly useful.
- Explicitly disclose affiliation in plain language, e.g. “I maintain…” or “I built…”.
- Keep affiliation and the project mention to one quiet sentence. Let the account
  profile carry the broader LazyingArt story; do not stack a project link, a
  profile pitch, and a brand pitch in the reply.
- Use at most one project link. Do not ask for stars, follows, votes, or DMs.
- Do not use teaser copy, engagement bait, “check it out,” “happy to help,” or a
  needy call to action. The useful answer should still feel complete if the
  affiliation sentence is removed.
- Do not invent capabilities, traction, users, benchmarks, endorsements, or personal experience.
- Do not repeat the post back to its author or use generic praise.
- Prefer plain sentences and concrete advice. Avoid headings, slogan-like
  fragments, canned marketing rhythm, and excessive colons or em dashes.
- If a term in the post is ambiguous or may be a typo, do not silently assign it a specific meaning.
- If the match is weak, the community discourages self-promotion, or the profile
  is enough context, omit the link and say so through include_link=false.
{targeting}- Keep the reply compact: <= 500 characters for X, <= 900 elsewhere.
- This is a draft only. Do not browse, post, message, or take any external action.
{value_only_policy}
{prefix_policy}
"""


def triage_prompt(candidate: dict[str, Any], projects: list[dict[str, Any]]) -> str:
    project_catalog = [
        {
            "id": project["id"],
            "name": project["name"],
            "url": project["url"],
            "summary": project["summary"],
            **({"homepage": project["homepage"]} if project.get("homepage") else {}),
            **({"reply_url": project["reply_url"]} if project.get("reply_url") else {}),
            **(
                {"reviewed_context": project["reply_context"]}
                if project.get("reply_context") else {}
            ),
        }
        for project in projects
    ]
    return f"""Review one possible social-media help request for a project maintainer.

Platform: {candidate['platform']}
Post URL: {candidate['source_url']}
Author: {candidate['author'] or 'unknown'}
Published at: {candidate.get('published_at') or 'unknown'}
Existing comments: {candidate.get('comment_count', 0)}
Post text:
{candidate['body']}

Current deterministic hint: {candidate.get('suggested_tool') or 'none'}

All evidence-backed public projects (choose only an exact id from this list):
{json.dumps(project_catalog, ensure_ascii=False)}

Return only the JSON object required by the supplied schema.

Mark eligible=true only when the author is clearly asking for help and one
specific listed project can address that need without stretching its
capabilities. Set project_id to that exact id. When no project is directly
useful, set eligible=false and project_id to an empty string.
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
            "-c", "mcp_servers.postiz.enabled=false",
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


def run_codex_draft(
    candidate: dict[str, Any],
    project: dict[str, Any],
    *,
    value_only: bool = False,
    required_prefix: str = "",
) -> dict[str, Any]:
    result = run_codex_structured(
        draft_prompt(
            candidate,
            project,
            value_only=value_only,
            required_prefix=required_prefix,
        ),
        SCHEMA_PATH,
        prefix="lazypromotion-draft-",
    )
    reply = compact(str(result.get("reply") or ""))
    required_prefix = compact(required_prefix)
    if required_prefix and not reply.startswith(required_prefix):
        raise ValueError("draft does not begin with the required disclosure")
    if value_only:
        normalized_reply = normalized(reply)
        forbidden = {
            normalized(str(project.get("name") or "")),
            "lazyingart",
            "lazying art",
            "fit check",
            "i maintain",
            "i built",
            "my project",
        }
        if bool(result.get("include_link")):
            raise ValueError("value-only draft cannot include a link")
        if re.search(r"(?:https?://|www\.)", reply, flags=re.I):
            raise ValueError("value-only draft cannot contain a URL")
        if any(phrase and phrase in normalized_reply for phrase in forbidden):
            raise ValueError("value-only draft cannot mention the project or affiliation")
    return result


def run_codex_triage(candidate: dict[str, Any], projects: list[dict[str, Any]]) -> dict[str, Any]:
    return run_codex_structured(
        triage_prompt(candidate, projects),
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
    project_id = compact(str(result.get("project_id") or ""))
    if result["eligible"]:
        if not project_id:
            project_id = candidate["suggested_tool"]
        project_by_id(project_id)
    else:
        project_id = ""
    flags = sorted({compact(str(flag)) for flag in result["risk_flags"] if compact(str(flag))})
    status = "triaged" if result["eligible"] else "rejected"
    now = utc_now()
    db.execute(
        """
        UPDATE candidates
        SET status=?, suggested_tool=CASE WHEN ? != '' THEN ? ELSE suggested_tool END,
            score=CASE WHEN ? != '' AND score < 5 THEN 5 ELSE score END,
            triage_reason=?, triage_confidence=?, triage_risk_flags=?, triaged_at=?, updated_at=?
        WHERE id=?
        """,
        (
            status, project_id, project_id, project_id, reason, confidence,
            json.dumps(flags, ensure_ascii=False), now, now, candidate_id,
        ),
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
                    "project_id": project_id,
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
    if compact(candidate.get("author") or "").casefold() in BOT_AUTHORS:
        raise ValueError("bot-authored candidates are not eligible for model triage")
    if not is_help_request(candidate["body"]):
        raise ValueError("candidate is not shaped like a genuine help request")
    if is_stale(candidate.get("published_at") or ""):
        raise ValueError("candidate is stale")
    result = run_codex_triage(candidate, load_catalog()["projects"])
    return save_triage(db, candidate["id"], result)


def save_draft(
    db: sqlite3.Connection,
    candidate_id: str,
    result: dict[str, Any],
    *,
    manual: bool = False,
) -> dict[str, Any]:
    body = compact(str(result["reply"]))
    candidate = row_dict(db.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone())
    if not candidate:
        raise ValueError(f"candidate not found: {candidate_id}")
    if candidate["platform"] in AI_COMMENT_BLOCKED_PLATFORMS:
        raise ValueError(
            "Hacker News prohibits generated or AI-edited comments; "
            "the agent may discover needs there but cannot draft a public reply"
        )
    project_id = "" if manual else compact(candidate.get("suggested_tool") or "")
    if not manual and not project_id:
        raise ValueError("candidate has no model-reviewed project")
    if project_id:
        project_by_id(project_id)
    if manual and bool(result.get("include_link")):
        raise ValueError("courtesy drafts cannot include a promotional link")
    candidate_content_hash = content_hash(compact(candidate["body"]))
    if candidate["platform"] == "instagram" and is_comment_source(
        candidate["platform"], candidate["source_url"], candidate["body"]
    ):
        username = compact(candidate.get("author") or "").lstrip("@")
        if not username:
            raise ValueError("Instagram comment drafts require a known target author")
        mention = f"@{username}"
        if not re.match(rf"^{re.escape(mention)}(?:\s|[,.:;!?])", body, flags=re.I):
            body = compact(f"{mention} {body}")
    limit = 500 if candidate["platform"] == "x" else 1400
    if len(body) > limit:
        raise ValueError(f"draft is {len(body)} characters; platform safety limit is {limit}")
    digest = content_hash(body)
    draft_id = stable_id(
        "draft",
        f"{candidate_id}\n{candidate_content_hash}\n{project_id}\n{digest}",
    )
    now = utc_now()
    draft_model = "human-directed" if manual else MODEL
    draft_effort = "n/a" if manual else EFFORT
    db.execute(
        """
        INSERT INTO drafts
          (id, candidate_id, project_id, candidate_content_hash, body, why,
           confidence, include_link, model, effort, content_hash, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          why=excluded.why, confidence=excluded.confidence, include_link=excluded.include_link,
          project_id=excluded.project_id,
          candidate_content_hash=excluded.candidate_content_hash,
          status='draft', updated_at=excluded.updated_at
        """,
        (
            draft_id, candidate_id, project_id, candidate_content_hash, body,
            compact(str(result["why"])), str(result["confidence"]),
            int(bool(result["include_link"])), draft_model, draft_effort, digest, now, now,
        ),
    )
    db.execute(
        """
        UPDATE drafts
        SET status='superseded', updated_at=?
        WHERE candidate_id=? AND id != ? AND status IN ('draft', 'prepared', 'approved')
        """,
        (now, candidate_id, draft_id),
    )
    db.execute("UPDATE candidates SET status='drafted', updated_at=? WHERE id=?", (now, candidate_id))
    db.execute(
        "INSERT INTO events(candidate_id, draft_id, kind, detail, created_at) VALUES (?, ?, 'draft_created', ?, ?)",
        (
            candidate_id,
            draft_id,
            json.dumps({"model": draft_model, "effort": draft_effort}),
            now,
        ),
    )
    db.commit()
    return row_dict(db.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()) or {}


def save_courtesy_draft(
    db: sqlite3.Connection,
    candidate_id: str,
    body: str,
    *,
    why: str,
) -> dict[str, Any]:
    """Save a user-directed, non-promotional reply with the normal safety binding."""
    return save_draft(
        db,
        candidate_id,
        {
            "reply": body,
            "why": why,
            "confidence": "high",
            "include_link": False,
        },
        manual=True,
    )


def approve_draft(db: sqlite3.Connection, draft_id: str, ttl_minutes: int) -> dict[str, Any]:
    draft = row_dict(
        db.execute(
            """
            SELECT d.*, c.platform FROM drafts d
            JOIN candidates c ON c.id=d.candidate_id
            WHERE d.id=?
            """,
            (draft_id,),
        ).fetchone()
    )
    if not draft:
        raise ValueError(f"draft not found: {draft_id}")
    if draft["platform"] in AI_COMMENT_BLOCKED_PLATFORMS:
        raise ValueError("Hacker News prohibits generated or AI-edited comments")
    if draft["status"] not in {"draft", "prepared"}:
        raise ValueError(f"draft status is {draft['status']}; approval is not allowed")
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
        SELECT a.*, d.body, d.status AS draft_status, d.candidate_id,
               d.content_hash AS current_hash, d.project_id,
               d.candidate_content_hash, c.body AS current_candidate_body,
               c.suggested_tool AS current_project_id
        FROM approvals a
        JOIN drafts d ON d.id=a.draft_id
        JOIN candidates c ON c.id=d.candidate_id
        WHERE a.token=? AND a.draft_id=?
        """,
        (token, draft_id),
    ).fetchone()
    approval = row_dict(row)
    if not approval:
        raise ValueError("approval token does not match this draft")
    if approval["used_at"]:
        raise ValueError("approval token was already used")
    if approval["draft_status"] != "approved":
        raise ValueError(f"draft status is {approval['draft_status']}; approval is no longer active")
    expires = datetime.fromisoformat(approval["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) >= expires:
        raise ValueError("approval token has expired")
    if approval["content_hash"] != approval["current_hash"] or content_hash(approval["body"]) != approval["current_hash"]:
        raise ValueError("draft content changed after approval")
    if content_hash(compact(approval["current_candidate_body"])) != approval["candidate_content_hash"]:
        raise ValueError("candidate context changed after approval")
    if approval["project_id"] and approval["current_project_id"] != approval["project_id"]:
        raise ValueError("candidate project changed after approval")
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


def reopen_unverified_send(
    db: sqlite3.Connection,
    draft_id: str,
    *,
    reason: str,
    evidence: str,
) -> dict[str, Any]:
    """Reopen a falsely acknowledged send without erasing its audit trail."""
    reason = compact(reason)
    evidence = compact(evidence)
    if not reason or not evidence:
        raise ValueError("recovery requires a reason and evidence")
    row = row_dict(
        db.execute(
            """
            SELECT d.id, d.status AS draft_status, d.candidate_id,
                   c.status AS candidate_status
            FROM drafts d
            JOIN candidates c ON c.id=d.candidate_id
            WHERE d.id=?
            """,
            (draft_id,),
        ).fetchone()
    )
    if not row:
        raise ValueError(f"draft not found: {draft_id}")
    if row["draft_status"] != "sent" or row["candidate_status"] != "replied":
        raise ValueError("only a sent/replied pair can be reopened")
    now = utc_now()
    db.execute("UPDATE drafts SET status='prepared', updated_at=? WHERE id=?", (now, draft_id))
    db.execute(
        "UPDATE candidates SET status='drafted', updated_at=? WHERE id=?",
        (now, row["candidate_id"]),
    )
    db.execute(
        """
        INSERT INTO events(candidate_id, draft_id, kind, detail, created_at)
        VALUES (?, ?, 'reply_send_reopened', ?, ?)
        """,
        (
            row["candidate_id"],
            draft_id,
            json.dumps({"reason": reason, "evidence": evidence}, ensure_ascii=False, sort_keys=True),
            now,
        ),
    )
    refresh_duplicates(db)
    db.commit()
    return {
        "candidate_id": row["candidate_id"],
        "draft_id": draft_id,
        "draft_status": "prepared",
        "candidate_status": "drafted",
        "previous_approval_reusable": False,
    }


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("catalog")

    ingest = sub.add_parser("ingest")
    ingest.add_argument("--platform", required=True, choices=("reddit", "x", "instagram", "hackernews"))
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
    draft.add_argument("--value-only", action="store_true")
    draft.add_argument("--required-prefix", default="")
    redraft = sub.add_parser("redraft")
    redraft.add_argument("candidate_id")
    redraft.add_argument("--value-only", action="store_true")
    redraft.add_argument("--required-prefix", default="")

    triage = sub.add_parser("triage")
    triage.add_argument("candidate_id")

    triage_pending = sub.add_parser("triage-pending")
    triage_pending.add_argument("--limit", type=int, default=5)

    approve = sub.add_parser("approve")
    approve.add_argument("draft_id")
    approve.add_argument("--ttl-minutes", type=int, default=30)
    approve.add_argument("--confirm-reviewed-exact-content", action="store_true", required=True)
    reopen = sub.add_parser("reopen-unverified-send")
    reopen.add_argument("draft_id")
    reopen.add_argument("--reason", required=True)
    reopen.add_argument("--evidence", required=True)
    reopen.add_argument("--confirm-no-public-reply-observed", action="store_true", required=True)
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
    elif args.command in {"draft", "redraft"}:
        candidate = row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (args.candidate_id,)).fetchone())
        if not candidate:
            raise SystemExit(f"candidate not found: {args.candidate_id}")
        allowed = {"triaged"} if args.command == "draft" else {"drafted"}
        if candidate["status"] not in allowed:
            raise SystemExit(f"candidate status is {candidate['status']}; {args.command} is not allowed")
        project_id = getattr(args, "project", "") or candidate["suggested_tool"]
        if not project_id:
            raise SystemExit("candidate has no relevant project; choose --project only after manual review")
        if project_id != candidate["suggested_tool"]:
            raise SystemExit("draft project differs from the model-triaged project")
        result = run_codex_draft(
            candidate,
            project_by_id(project_id),
            value_only=bool(args.value_only),
            required_prefix=args.required_prefix,
        )
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
                WHERE status='discovered' AND triage_requested_at != ''
                  AND lower(author) NOT IN ('automoderator')
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
    elif args.command == "reopen-unverified-send":
        print_json(
            reopen_unverified_send(
                db,
                args.draft_id,
                reason=args.reason,
                evidence=args.evidence,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
