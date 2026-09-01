#!/usr/bin/env python3
"""Monitor owned Postiz posts without confusing engagement with customers.

The monitor uses only the official Postiz CLI and the Python standard library.
It keeps raw Postiz and integration IDs in memory only, stores observations in
an ignored SQLite database, and emits review alerts instead of replying.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import html
import json
import os
import re
import sqlite3
import subprocess
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CAMPAIGNS = ROOT / "campaigns"
RUNTIME = ROOT / ".local"
DB_PATH = RUNTIME / "owned-monitor.sqlite3"
STATUS_PATH = RUNTIME / "owned-monitor-status.json"
LOG_PATH = RUNTIME / "owned-monitor.jsonl"
LOCK_PATH = RUNTIME / "owned-monitor.lock"

PENDING_STATES = frozenset({"DRAFT", "QUEUE"})
FAILED_STATES = frozenset({"ERROR", "FAILED"})
PROVIDERS = frozenset({"x", "instagram-standalone", "reddit"})
Runner = Callable[[list[str]], Any]


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_time(value: str) -> datetime | None:
    value = str(value or "").strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def canonical_text(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return re.sub(r"\s+", " ", value).strip()


def stable_post_key(provider: str, publish_at: str, content: str) -> str:
    identity = "\n".join((provider, publish_at, canonical_text(content)))
    return "owned_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]


def content_hash(content: str) -> str:
    return hashlib.sha256(canonical_text(content).encode("utf-8")).hexdigest()


def extract_json(output: str) -> Any:
    decoder = json.JSONDecoder()
    for position, character in enumerate(output):
        if character not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(output[position:])
            return value
        except json.JSONDecodeError:
            continue
    raise ValueError("Postiz returned no JSON payload")


def default_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def run_postiz(
    args: list[str], *, runner: Runner = default_runner, expect_json: bool = True
) -> Any:
    result = runner(["postiz", *args])
    if int(result.returncode) != 0:
        # CLI stderr can contain account-specific context. Keep errors sanitized.
        raise RuntimeError(f"Postiz command failed: {' '.join(args[:2])}")
    if not expect_json:
        return str(result.stdout or "")
    return extract_json(str(result.stdout or ""))


def verify_auth(*, runner: Runner = default_runner) -> None:
    output = run_postiz(["auth:status"], runner=runner, expect_json=False)
    if "Credentials are valid" not in output:
        raise RuntimeError("Postiz credentials could not be verified")


def route_index(campaign_dir: Path = CAMPAIGNS) -> dict[tuple[str, str], dict]:
    providers = {
        "x": "x",
        "instagram": "instagram-standalone",
        "reddit": "reddit",
    }
    routes: dict[tuple[str, str], dict] = {}
    for path in sorted(campaign_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        campaign_id = str(payload.get("id") or "")
        for channel_name, channel in (payload.get("channels") or {}).items():
            provider = providers.get(channel_name)
            if not provider or not isinstance(channel, dict):
                continue
            candidates = [("product", channel.get("content"))]
            candidates.extend(
                (name, value.get("content"))
                for name, value in channel.items()
                if isinstance(value, dict) and value.get("content")
            )
            for route, content in candidates:
                normalized = canonical_text(str(content or ""))
                if normalized:
                    routes[(provider, normalized)] = {
                        "campaign_id": campaign_id,
                        "route": route,
                    }
    return routes


def route_for_post(provider: str, content: str, routes: dict) -> dict:
    return routes.get(
        (provider, canonical_text(content)),
        {"campaign_id": "", "route": "unmatched_owned_post"},
    )


def metric_snapshot(payload: Any) -> dict[str, dict]:
    if isinstance(payload, dict):
        payload = payload.get("output", payload.get("metrics", []))
    if not isinstance(payload, list):
        return {}
    result: dict[str, dict] = {}
    for metric in payload:
        if not isinstance(metric, dict):
            continue
        label = str(metric.get("label") or metric.get("name") or "").strip()
        points = metric.get("data") or metric.get("values") or []
        if not label or not isinstance(points, list):
            continue
        latest = points[-1] if points and isinstance(points[-1], dict) else {}
        total = latest.get("total", latest.get("value"))
        result[label] = {
            "latest": total if isinstance(total, (int, float)) else None,
            "date": str(latest.get("date") or ""),
            "points": len(points),
            "percentage_change": metric.get(
                "percentageChange", metric.get("percentage")
            ),
        }
    return result


def metric_value(metrics: dict[str, dict], label: str) -> int:
    for name, value in metrics.items():
        if name.casefold() == label.casefold():
            latest = value.get("latest")
            return int(latest) if isinstance(latest, (int, float)) else 0
    return 0


def open_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS owned_post_observations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          observed_at TEXT NOT NULL,
          post_key TEXT NOT NULL,
          provider TEXT NOT NULL,
          campaign_id TEXT NOT NULL DEFAULT '',
          route TEXT NOT NULL,
          publish_at TEXT NOT NULL,
          state TEXT NOT NULL,
          content_hash TEXT NOT NULL,
          release_url TEXT NOT NULL DEFAULT '',
          comments INTEGER NOT NULL DEFAULT 0,
          replies INTEGER NOT NULL DEFAULT 0,
          metrics_json TEXT NOT NULL DEFAULT '{}',
          needs_release_connection INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS owned_post_observations_post
          ON owned_post_observations(post_key, id DESC);
        """
    )
    return db


def previous_observation(db: sqlite3.Connection, post_key: str) -> dict | None:
    row = db.execute(
        """
        SELECT * FROM owned_post_observations
        WHERE post_key=? ORDER BY id DESC LIMIT 1
        """,
        (post_key,),
    ).fetchone()
    return dict(row) if row else None


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def append_log(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _integration_rows(payload: Any) -> list[dict]:
    if isinstance(payload, dict):
        payload = payload.get("integrations") or payload.get("output") or []
    return [row for row in payload if isinstance(row, dict)] if isinstance(payload, list) else []


def _post_rows(payload: Any) -> list[dict]:
    if isinstance(payload, dict):
        payload = payload.get("posts") or payload.get("output") or []
    return [row for row in payload if isinstance(row, dict)] if isinstance(payload, list) else []


def _provider(row: dict) -> str:
    integration = row.get("integration") or {}
    return str(
        integration.get("providerIdentifier")
        or integration.get("identifier")
        or row.get("providerIdentifier")
        or ""
    )


def monitor_once(
    *,
    db_path: Path = DB_PATH,
    status_path: Path = STATUS_PATH,
    runner: Runner = default_runner,
    now: datetime | None = None,
    days: int = 30,
) -> dict:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    checked_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    verify_auth(runner=runner)

    integrations = _integration_rows(
        run_postiz(["integrations:list"], runner=runner)
    )
    integration_ids: dict[str, str] = {}
    for integration in integrations:
        provider = str(
            integration.get("identifier")
            or integration.get("providerIdentifier")
            or ""
        )
        if provider in PROVIDERS and integration.get("id"):
            integration_ids[provider] = str(integration["id"])

    start = (now - timedelta(days=days)).isoformat().replace("+00:00", "Z")
    end = (now + timedelta(days=days)).isoformat().replace("+00:00", "Z")
    posts = _post_rows(
        run_postiz(
            ["posts:list", "--startDate", start, "--endDate", end],
            runner=runner,
        )
    )

    platform_metrics: dict[str, dict] = {}
    for provider, integration_id in sorted(integration_ids.items()):
        analytics = run_postiz(
            ["analytics:platform", integration_id, "-d", str(days)],
            runner=runner,
        )
        platform_metrics[provider] = metric_snapshot(analytics)

    routes = route_index()
    db = open_db(db_path)
    observed = []
    alerts = []
    try:
        for post in posts:
            provider = _provider(post)
            if provider not in PROVIDERS:
                continue
            content = str(post.get("content") or "")
            publish_at = str(post.get("publishDate") or "")
            state = str(post.get("state") or "UNKNOWN").upper()
            key = stable_post_key(provider, publish_at, content)
            route = route_for_post(provider, content, routes)
            release_url = str(post.get("releaseURL") or "")
            release_id = str(post.get("releaseId") or "")
            metrics: dict[str, dict] = {}
            needs_connection = False

            is_published = bool(release_url or release_id) or (
                state not in PENDING_STATES | FAILED_STATES | {"UNKNOWN"}
            )
            raw_post_id = str(post.get("id") or "")
            if is_published and raw_post_id:
                analytics = run_postiz(
                    ["analytics:post", raw_post_id, "-d", str(days)],
                    runner=runner,
                )
                needs_connection = bool(
                    isinstance(analytics, dict) and analytics.get("missing") is True
                )
                if not needs_connection:
                    metrics = metric_snapshot(analytics)

            comments = metric_value(metrics, "Comments")
            replies = metric_value(metrics, "Replies")
            previous = previous_observation(db, key)
            previous_comments = int(previous["comments"]) if previous else 0
            previous_replies = int(previous["replies"]) if previous else 0

            public_summary = {
                "post_key": key,
                "provider": provider,
                "campaign_id": route["campaign_id"],
                "route": route["route"],
                "publish_at": publish_at,
                "state": state,
                "content_sha256": content_hash(content),
                "release_url": release_url,
                "comments": comments,
                "replies": replies,
                "needs_release_connection": needs_connection,
            }
            observed.append(public_summary)

            published_at = parse_time(publish_at)
            if state == "QUEUE" and published_at and published_at < now - timedelta(minutes=20):
                alerts.append(
                    {
                        "kind": "publication_overdue",
                        **public_summary,
                        "action": "Review the Postiz workflow visibly; do not resubmit the post.",
                    }
                )
            if state in FAILED_STATES:
                alerts.append(
                    {
                        "kind": "publication_failed",
                        **public_summary,
                        "action": "Inspect the provider error and visible calendar before any retry.",
                    }
                )
            if (
                previous
                and str(previous.get("state") or "").upper() in PENDING_STATES
                and is_published
                and state not in FAILED_STATES
            ):
                alerts.append(
                    {
                        "kind": "publication_observed",
                        **public_summary,
                        "action": (
                            "Open the exact release URL in the visible browser and verify "
                            "the tracked destination; do not reply automatically."
                        ),
                    }
                )
            if needs_connection:
                alerts.append(
                    {
                        "kind": "release_connection_required",
                        **public_summary,
                        "action": "Review provider content before explicitly connecting a release ID.",
                    }
                )
            elif is_published and not release_url:
                alerts.append(
                    {
                        "kind": "release_url_missing",
                        **public_summary,
                        "action": (
                            "Inspect the published item in Postiz and the provider visibly; "
                            "do not reconnect or resubmit until the exact release is identified."
                        ),
                    }
                )
            if comments > previous_comments or replies > previous_replies:
                alerts.append(
                    {
                        "kind": "engagement_increased",
                        **public_summary,
                        "comment_delta": comments - previous_comments,
                        "reply_delta": replies - previous_replies,
                        "action": "Inspect public responses in the visible browser; do not reply automatically or record a lead.",
                    }
                )

            db.execute(
                """
                INSERT INTO owned_post_observations
                  (observed_at, post_key, provider, campaign_id, route,
                   publish_at, state, content_hash, release_url, comments,
                   replies, metrics_json, needs_release_connection)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checked_at,
                    key,
                    provider,
                    route["campaign_id"],
                    route["route"],
                    publish_at,
                    state,
                    content_hash(content),
                    release_url,
                    comments,
                    replies,
                    json.dumps(metrics, ensure_ascii=False, sort_keys=True),
                    int(needs_connection),
                ),
            )
        db.commit()
    finally:
        db.close()

    report = {
        "checked_at": checked_at,
        "policy": {
            "engagement_is_not_a_lead": True,
            "automatic_public_reply": False,
            "raw_postiz_ids_persisted": False,
        },
        "posts": observed,
        "alerts": alerts,
        "platform_metrics": platform_metrics,
        "summary": {
            "observed_posts": len(observed),
            "alerts": len(alerts),
            "queued": sum(post["state"] == "QUEUE" for post in observed),
            "drafts": sum(post["state"] == "DRAFT" for post in observed),
            "published": sum(
                post["state"] not in PENDING_STATES | FAILED_STATES | {"UNKNOWN"}
                for post in observed
            ),
        },
    }
    atomic_write_json(status_path, report)
    return report


def loop(interval_minutes: int) -> None:
    if interval_minutes < 5:
        raise ValueError("interval must be at least five minutes")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("owned-post monitor is already running") from exc
        while True:
            try:
                report = monitor_once()
                append_log(LOG_PATH, report)
            except Exception as exc:  # keep the monitor alive; status is sanitized
                failure = {"checked_at": utc_now(), "error": str(exc)}
                atomic_write_json(STATUS_PATH, failure)
                append_log(LOG_PATH, failure)
            time.sleep(interval_minutes * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only publication and engagement monitor for owned Postiz posts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    once = subparsers.add_parser("once", help="Run one read-only observation pass.")
    once.add_argument("--days", type=int, default=30)
    continuous = subparsers.add_parser("loop", help="Repeat observations locally.")
    continuous.add_argument("--interval-minutes", type=int, default=15)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "once":
        report = monitor_once(days=max(1, args.days))
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        loop(args.interval_minutes)


if __name__ == "__main__":
    main()
