#!/usr/bin/env python3
"""Continuously discover genuine needs and build a private human-review queue."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

import browser as browser_control
import promotion


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local"
STATE_PATH = RUNTIME / "worker-state.json"
QUEUE_PATH = RUNTIME / "review-queue.json"
LOG_PATH = RUNTIME / "worker.jsonl"
LOCK_PATH = RUNTIME / "worker.lock"
DEFAULT_PLATFORMS = ("reddit", "x", "hackernews", "instagram")
STOP = False


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def load_state(path: Path = STATE_PATH) -> dict:
    if not path.exists():
        return {
            "version": 1,
            "cycles": 0,
            "cursors": {platform: 0 for platform in DEFAULT_PLATFORMS},
            "core_cursors": {platform: 0 for platform in DEFAULT_PLATFORMS},
        }
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("version") != 1 or not isinstance(state.get("cursors"), dict):
        raise ValueError("worker state is invalid")
    core_cursors = state.setdefault("core_cursors", {})
    if not isinstance(core_cursors, dict):
        raise ValueError("worker core cursor state is invalid")
    for platform in DEFAULT_PLATFORMS:
        state["cursors"].setdefault(platform, 0)
        core_cursors.setdefault(platform, 0)
    return state


def log_event(payload: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"at": utc_now(), **payload}, ensure_ascii=False, sort_keys=True) + "\n")


def review_queue(db) -> list[dict]:
    rows = db.execute(
        """
        SELECT d.id AS draft_id, d.body AS reply, d.why, d.confidence,
               d.include_link, d.status AS draft_status, d.created_at,
               c.id AS candidate_id, c.platform, c.source_url, c.author,
               c.body AS source_body, c.suggested_tool, c.triage_reason,
               c.triage_confidence, c.comment_count, c.source_score
        FROM drafts d
        JOIN candidates c ON c.id=d.candidate_id
        WHERE d.status IN ('draft', 'prepared', 'approved') AND c.status != 'replied'
        ORDER BY d.created_at DESC
        """
    ).fetchall()
    return [
        {
            **dict(row),
            "include_link": bool(row["include_link"]),
            "project": promotion.project_by_id(row["suggested_tool"]),
        }
        for row in rows
    ]


def pending_candidate_ids(db, preferred_ids: list[str], limit: int) -> list[str]:
    if limit <= 0:
        return []
    rows = {
        row["id"]: dict(row)
        for row in db.execute(
            """
            SELECT * FROM candidates
            WHERE status='discovered' AND published_at != ''
            ORDER BY published_at DESC, score DESC, updated_at DESC
            LIMIT 500
            """
        ).fetchall()
    }
    ordered = [*preferred_ids, *rows]
    selected = []
    for candidate_id in ordered:
        candidate = rows.get(candidate_id)
        if not candidate or candidate_id in selected:
            continue
        if promotion.compact(candidate["author"]).casefold() in promotion.BOT_AUTHORS:
            continue
        if promotion.is_stale(candidate["published_at"]):
            continue
        if not promotion.is_triageable_request(
            candidate["platform"], candidate["source_url"], candidate["body"]
        ):
            continue
        selected.append(candidate_id)
        if len(selected) >= limit:
            break
    return selected


def next_route_cursor(current: int, result: dict) -> int:
    """Keep a failed discovery route at the head of the next cycle."""
    return int(result["next_query"]) if result["ok"] else current


def run_models(candidate_ids: list[str], *, max_triage: int, max_drafts: int) -> dict:
    db = promotion.open_db()
    selected_ids = pending_candidate_ids(db, candidate_ids, max_triage)
    triaged = []
    drafted = []
    errors = []
    for candidate_id in selected_ids:
        candidate = promotion.row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone())
        if not candidate or candidate["status"] != "discovered":
            continue
        try:
            result = promotion.triage_candidate(db, candidate)
            triaged.append({
                "candidate_id": candidate_id,
                "status": result["status"],
                "reason": result["triage_reason"],
                "confidence": result["triage_confidence"],
            })
        except Exception as exc:
            errors.append({"stage": "triage", "candidate_id": candidate_id, "error": str(exc)})
    accepted = [row for row in triaged if row["status"] == "triaged"]
    for row in accepted[:max_drafts]:
        candidate_id = row["candidate_id"]
        candidate = promotion.row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone())
        if not candidate or candidate["status"] != "triaged":
            continue
        try:
            result = promotion.run_codex_draft(candidate, promotion.project_by_id(candidate["suggested_tool"]))
            draft = promotion.save_draft(db, candidate_id, result)
            drafted.append({"candidate_id": candidate_id, "draft_id": draft["id"]})
        except Exception as exc:
            errors.append({"stage": "draft", "candidate_id": candidate_id, "error": str(exc)})
    queue = review_queue(db)
    write_json(QUEUE_PATH, {"updated_at": utc_now(), "count": len(queue), "items": queue})
    return {
        "selected_candidate_ids": selected_ids,
        "triaged": triaged,
        "drafted": drafted,
        "errors": errors,
        "review_queue_size": len(queue),
    }


def run_cycle(args, state: dict) -> dict:
    discovered: list[str] = []
    platform_results = []
    with sync_playwright() as playwright:
        connected = playwright.chromium.connect_over_cdp(args.cdp)
        for platform in args.platforms:
            try:
                page = browser_control.page_for(connected, platform=platform, front=False)
                lanes = browser_control.discovery_query_lanes(platform)
                lane_specs = []
                if args.core_queries_per_platform and lanes["core"]:
                    lane_specs.append((
                        "core",
                        "core_cursors",
                        args.core_queries_per_platform,
                        lanes["core"],
                    ))
                if args.queries_per_platform and lanes["long_tail"]:
                    lane_specs.append((
                        "long_tail",
                        "cursors",
                        args.queries_per_platform,
                        lanes["long_tail"],
                    ))
                lane_results = []
                eligible_ids = []
                triage_ids = []
                for lane_name, cursor_key, max_queries, lane_queries in lane_specs:
                    cursor = max(0, int(state[cursor_key].get(platform, 0)))
                    result = browser_control.run_discovery_cycle(
                        page,
                        platform,
                        max_queries=max_queries,
                        limit_per_query=args.limit_per_query,
                        hydrate_per_query=args.hydrate_per_query,
                        start_query=cursor,
                        queries=lane_queries,
                    )
                    # Retry a transiently failed route next cycle. Advancing here
                    # would postpone it until its entire lane wraps.
                    state[cursor_key][platform] = next_route_cursor(cursor, result)
                    lane_results.append({"lane": lane_name, **result})
                    for candidate_id in result["eligible_candidate_ids"]:
                        if candidate_id not in eligible_ids:
                            eligible_ids.append(candidate_id)
                    for candidate_id in result["triage_candidate_ids"]:
                        if candidate_id not in triage_ids:
                            triage_ids.append(candidate_id)
                        if candidate_id not in discovered:
                            discovered.append(candidate_id)
                platform_results.append({
                    "platform": platform,
                    "ok": all(result["ok"] for result in lane_results),
                    "queries_run": sum(int(result["queries_run"]) for result in lane_results),
                    "next_query": state["cursors"][platform],
                    "next_core_query": state["core_cursors"][platform],
                    "available_queries": sum(len(items) for items in lanes.values()),
                    "core_available_queries": len(lanes["core"]),
                    "long_tail_available_queries": len(lanes["long_tail"]),
                    "eligible_candidate_ids": eligible_ids,
                    "triage_candidate_ids": triage_ids,
                    "lanes": [
                        {
                            "lane": result["lane"],
                            "ok": result["ok"],
                            "queries_run": result["queries_run"],
                            "available_queries": result["available_queries"],
                        }
                        for result in lane_results
                    ],
                    "query_errors": [
                        {
                            "lane": result["lane"],
                            "project_id": query_result["project_id"],
                            "query": query_result["query"],
                            "error": query_result.get("error", "unknown discovery error"),
                        }
                        for result in lane_results
                        for query_result in result["results"] if not query_result["ok"]
                    ],
                })
            except Exception as exc:
                platform_results.append({"platform": platform, "ok": False, "error": str(exc)})
    model_results = (
        run_models(discovered, max_triage=args.max_triage, max_drafts=args.max_drafts)
        if not args.no_model else {"skipped": True}
    )
    state["cycles"] = int(state.get("cycles", 0)) + 1
    state["last_cycle_at"] = utc_now()
    state["last_result"] = {
        "platforms": platform_results,
        "triage_candidate_ids": discovered,
        "models": model_results,
    }
    write_json(args.state, state)
    log_event({"kind": "cycle", **state["last_result"]})
    return state["last_result"]


def stop_handler(_signum, _frame) -> None:
    global STOP
    STOP = True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp", default=browser_control.DEFAULT_CDP)
    parser.add_argument("--platforms", nargs="+", choices=DEFAULT_PLATFORMS, default=list(DEFAULT_PLATFORMS))
    parser.add_argument("--queries-per-platform", type=int, default=1)
    parser.add_argument(
        "--core-queries-per-platform",
        type=int,
        default=1,
        help="reviewed high-yield routes to run per platform in addition to long-tail coverage",
    )
    parser.add_argument("--limit-per-query", type=int, default=10)
    parser.add_argument("--hydrate-per-query", type=int, default=2)
    parser.add_argument("--max-triage", type=int, default=3)
    parser.add_argument("--max-drafts", type=int, default=1)
    parser.add_argument("--interval-minutes", type=float, default=60.0)
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--max-cycles", type=int, default=0)
    parser.add_argument("--no-model", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.queries_per_platform < 0 or args.core_queries_per_platform < 0 or args.limit_per_query < 1:
        raise SystemExit("query limits cannot be negative and result limits must be positive")
    if not args.queries_per_platform and not args.core_queries_per_platform:
        raise SystemExit("at least one core or long-tail query must be enabled")
    if args.hydrate_per_query < 0 or args.max_triage < 0 or args.max_drafts < 0:
        raise SystemExit("hydrate/model limits cannot be negative")
    if args.interval_minutes < 1 and not args.once:
        raise SystemExit("continuous mode requires --interval-minutes >= 1")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    lock_stream = LOCK_PATH.open("w", encoding="utf-8")
    try:
        fcntl.flock(lock_stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise SystemExit("another LazyPromoter worker already owns the runtime lock") from exc
    lock_stream.write(str(os.getpid()))
    lock_stream.flush()
    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)
    state = load_state(args.state)
    while not STOP:
        result = run_cycle(args, state)
        print(json.dumps({"at": utc_now(), **result}, ensure_ascii=False, sort_keys=True), flush=True)
        if args.once or (args.max_cycles and state["cycles"] >= args.max_cycles):
            break
        remaining = args.interval_minutes * 60
        while remaining > 0 and not STOP:
            chunk = min(60, remaining)
            time.sleep(chunk)
            remaining -= chunk
    log_event({"kind": "worker_stopped", "cycles": state.get("cycles", 0)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
