#!/usr/bin/env python3
"""Monitor matching application threads in iCloud Mail without opening mail."""

from __future__ import annotations

import argparse
import fcntl
import json
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlsplit

import browser
import inbound_monitor


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local"
CONFIG_PATH = RUNTIME / "private" / "application-inbox-monitor.json"
DB_PATH = RUNTIME / "application-inbox-monitor.sqlite3"
STATUS_PATH = RUNTIME / "application-inbox-monitor-status.json"
LOG_PATH = RUNTIME / "application-inbox-monitor.jsonl"
LOCK_PATH = RUNTIME / "application-inbox-monitor.lock"

CAMPAIGN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
MAX_CAMPAIGNS = 100
MAX_TERMS_PER_FIELD = 20
MAX_FOLDER_LENGTH = 160
MAX_TERM_LENGTH = 500
RECENT_BASELINE_OBSERVATIONS = 2


def _safe_string(
    value: object,
    *,
    field: str,
    maximum: int,
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field} contains a control character")
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > maximum:
        raise ValueError(f"{field} has an invalid length")
    return normalized


def _validate_terms(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    if len(value) > MAX_TERMS_PER_FIELD:
        raise ValueError(f"{field} contains too many terms")
    terms = [
        _safe_string(item, field=field, maximum=MAX_TERM_LENGTH) for item in value
    ]
    if len({normalize_text(item) for item in terms}) != len(terms):
        raise ValueError(f"{field} contains duplicate terms")
    return terms


def validate_config(payload: object) -> dict:
    """Validate and copy private matching configuration without doing any I/O."""
    if not isinstance(payload, dict):
        raise ValueError("configuration must be an object")
    if set(payload) != {"folder_name", "campaigns"}:
        raise ValueError("configuration fields are invalid")

    folder_name = _safe_string(
        payload["folder_name"],
        field="folder_name",
        maximum=MAX_FOLDER_LENGTH,
    )
    campaigns = payload["campaigns"]
    if not isinstance(campaigns, list) or not campaigns:
        raise ValueError("campaigns must be a non-empty list")
    if len(campaigns) > MAX_CAMPAIGNS:
        raise ValueError("configuration contains too many campaigns")

    validated_campaigns = []
    seen_ids = set()
    for rule in campaigns:
        if not isinstance(rule, dict) or set(rule) != {
            "campaign_id",
            "participant_terms",
            "subject_terms",
        }:
            raise ValueError("campaign matching fields are invalid")
        campaign_id = _safe_string(
            rule["campaign_id"],
            field="campaign_id",
            maximum=128,
        )
        if not CAMPAIGN_ID_RE.fullmatch(campaign_id):
            raise ValueError("campaign_id is unsafe")
        if campaign_id in seen_ids:
            raise ValueError("campaign_id values must be unique")
        seen_ids.add(campaign_id)
        validated_campaigns.append(
            {
                "campaign_id": campaign_id,
                "participant_terms": _validate_terms(
                    rule["participant_terms"], field="participant_terms"
                ),
                "subject_terms": _validate_terms(
                    rule["subject_terms"], field="subject_terms"
                ),
            }
        )

    return {"folder_name": folder_name, "campaigns": validated_campaigns}


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load configuration from ignored private storage."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "the private application inbox configuration is unavailable"
        ) from exc
    try:
        return validate_config(payload)
    except ValueError as exc:
        # Do not put a private match term in an exception that the loop persists.
        raise RuntimeError(
            "the private application inbox configuration is invalid"
        ) from exc


def normalize_text(value: str) -> str:
    """Normalize visible Mail metadata for deterministic contains matching."""
    if not isinstance(value, str):
        raise ValueError("mail metadata must be a string")
    return " ".join(value.lower().split())


def _matches_any(value: str, terms: list[str]) -> bool:
    return any(normalize_text(term) in value for term in terms)


def match_rows(config: object, rows: object) -> list[dict]:
    """Pure reference matcher returning no participant, subject, or time strings."""
    validated = validate_config(config)
    if not isinstance(rows, list):
        raise ValueError("mail rows must be a list")

    normalized_rows = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "participants",
            "subject",
            "timestamp",
            "unread",
        }:
            raise ValueError("mail row fields are invalid")
        participants = normalize_text(row["participants"])
        subject = normalize_text(row["subject"])
        if not isinstance(row["timestamp"], str):
            raise ValueError("mail row timestamp must be a string")
        if not isinstance(row["unread"], bool):
            raise ValueError("mail row unread state must be a boolean")
        normalized_rows.append((participants, subject, row["unread"]))

    results = []
    for rule in validated["campaigns"]:
        participant_terms = rule["participant_terms"]
        subject_terms = rule["subject_terms"]
        matched = [
            unread
            for participants, subject, unread in normalized_rows
            if _matches_any(participants, participant_terms)
            and _matches_any(subject, subject_terms)
        ]
        matching_count = len(matched)
        unread_count = sum(matched)
        results.append(
            {
                "campaign_id": rule["campaign_id"],
                "matching_thread_count": matching_count,
                "unread_matching_thread_count": unread_count,
                "has_matching_thread": matching_count > 0,
                "has_unread_matching_thread": unread_count > 0,
            }
        )
    return results


def icloud_mail_targets(targets: list[dict]) -> list[dict]:
    """Return attachable top-level iCloud Mail pages without changing focus."""
    matches = []
    for target in targets:
        if target.get("type") != "page":
            continue
        parsed = urlsplit(str(target.get("url") or ""))
        if (
            parsed.hostname == inbound_monitor.MAIL_PAGE_HOST
            and parsed.path.startswith("/mail")
            and target.get("webSocketDebuggerUrl")
        ):
            matches.append(target)
    if not matches:
        raise RuntimeError("the authenticated iCloud Mail page is not open")
    return matches


def application_rows_expression(config: object) -> str:
    """Build read-only JS that returns aggregates, never visible metadata text."""
    validated = validate_config(config)
    browser_config = {
        "folderName": validated["folder_name"],
        "campaigns": [
            {
                "campaignId": item["campaign_id"],
                "participantTerms": item["participant_terms"],
                "subjectTerms": item["subject_terms"],
            }
            for item in validated["campaigns"]
        ],
    }
    encoded = json.dumps(browser_config, ensure_ascii=False).replace("</", "<\\/")
    return f"""(() => {{
      'use strict';
      const config = {encoded};
      const normalize = (value) => String(value || '')
        .toLowerCase().replace(/\\s+/g, ' ').trim();
      const folderSelector = '[role="option"][aria-label="' +
        CSS.escape(config.folderName) + '"]';
      const folders = Array.from(document.querySelectorAll(folderSelector));
      const folderFound = folders.length === 1;
      const folderSelected = folderFound &&
        folders[0].getAttribute('aria-selected') === 'true';
      const tree = document.querySelector('[role="tree"][aria-label="Messages"]');
      const treeFound = Boolean(tree);
      if (!folderSelected || !treeFound) {{
        return {{folderFound, folderSelected, treeFound, campaigns: []}};
      }}

      const rows = Array.from(document.querySelectorAll(
        '[role="tree"][aria-label="Messages"] [role="treeitem"]'
      )).map((row) => {{
        const participants = row.querySelector('.thread-participants');
        const subject = row.querySelector('.thread-subject');
        const timestamp = row.querySelector('.thread-timestamp');
        const unread = row.querySelector('.adornment-unread');
        return {{
          participants: participants ? normalize(participants.textContent) : '',
          subject: subject ? normalize(subject.textContent) : '',
          metadataComplete: Boolean(participants && subject && timestamp),
          unread: Boolean(unread),
        }};
      }});

      const campaigns = config.campaigns.map((campaign) => {{
        const participantTerms = campaign.participantTerms.map(normalize);
        const subjectTerms = campaign.subjectTerms.map(normalize);
        const matches = rows.filter((row) => row.metadataComplete &&
          participantTerms.some((term) => row.participants.includes(term)) &&
          subjectTerms.some((term) => row.subject.includes(term)));
        const unreadCount = matches.filter((row) => row.unread).length;
        return {{
          campaignId: campaign.campaignId,
          matchingThreadCount: matches.length,
          unreadMatchingThreadCount: unreadCount,
          hasMatchingThread: matches.length > 0,
          hasUnreadMatchingThread: unreadCount > 0,
        }};
      }});
      return {{folderFound, folderSelected, treeFound, campaigns}};
    }})()"""


def read_tab_summary(connection, *, config: dict, world_number: int) -> dict:
    """Read one tab in an isolated world using only the approved DOM fields."""
    tree = connection.command("Page.getFrameTree").get("frameTree")
    if not isinstance(tree, dict):
        raise RuntimeError("the iCloud Mail frame tree is unavailable")
    frame = inbound_monitor.find_mail_app_frame(tree)
    frame_id = frame.get("id")
    if not frame_id:
        raise RuntimeError("the iCloud Mail application frame is unavailable")
    isolated = connection.command(
        "Page.createIsolatedWorld",
        {
            "frameId": frame_id,
            "worldName": f"lazypromotion-application-inbox-{world_number}",
            "grantUniveralAccess": False,
        },
    )
    context_id = isolated.get("executionContextId")
    if not context_id:
        raise RuntimeError("the application inbox context is unavailable")
    evaluated = connection.command(
        "Runtime.evaluate",
        {
            "contextId": context_id,
            "expression": application_rows_expression(config),
            "returnByValue": True,
            "awaitPromise": False,
        },
    )
    if evaluated.get("exceptionDetails"):
        raise RuntimeError("iCloud did not expose the application inbox summary")
    payload = evaluated.get("result", {}).get("value")
    if not isinstance(payload, dict):
        raise RuntimeError("iCloud exposed an invalid application inbox summary")
    if set(payload) != {
        "folderFound",
        "folderSelected",
        "treeFound",
        "campaigns",
    } or not all(
        isinstance(payload[field], bool)
        for field in ("folderFound", "folderSelected", "treeFound")
    ):
        raise RuntimeError("iCloud exposed invalid application inbox fields")
    if payload["folderSelected"] and not payload["folderFound"]:
        raise RuntimeError("iCloud exposed an inconsistent application inbox folder")
    if not payload["folderSelected"] and payload["campaigns"] != []:
        raise RuntimeError("iCloud exposed application data from an unselected folder")
    return payload


def _nonnegative_integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError("iCloud exposed invalid application inbox counts")
    return value


def validate_campaign_summaries(value: object, *, campaign_ids: list[str]) -> list[dict]:
    """Validate the privacy-limited value returned from the browser."""
    if not isinstance(value, list) or len(value) != len(campaign_ids):
        raise RuntimeError("iCloud exposed an incomplete application inbox summary")
    summaries = []
    for expected_id, item in zip(campaign_ids, value):
        if not isinstance(item, dict) or set(item) != {
            "campaignId",
            "matchingThreadCount",
            "unreadMatchingThreadCount",
            "hasMatchingThread",
            "hasUnreadMatchingThread",
        }:
            raise RuntimeError("iCloud exposed invalid application inbox fields")
        if item["campaignId"] != expected_id:
            raise RuntimeError("iCloud exposed an unexpected campaign summary")
        matching_count = _nonnegative_integer(item["matchingThreadCount"])
        unread_count = _nonnegative_integer(item["unreadMatchingThreadCount"])
        has_match = item["hasMatchingThread"]
        has_unread = item["hasUnreadMatchingThread"]
        if (
            not isinstance(has_match, bool)
            or not isinstance(has_unread, bool)
            or unread_count > matching_count
            or has_match != (matching_count > 0)
            or has_unread != (unread_count > 0)
        ):
            raise RuntimeError("iCloud exposed inconsistent application inbox counts")
        summaries.append(
            {
                "campaign_id": expected_id,
                "matching_thread_count": matching_count,
                "unread_matching_thread_count": unread_count,
                "has_matching_thread": has_match,
                "has_unread_matching_thread": has_unread,
            }
        )
    return summaries


def read_application_counts(*, cdp: str, config: object) -> list[dict]:
    """Read aggregates from exactly one tab with the exact folder selected."""
    validated = validate_config(config)
    campaign_ids = [item["campaign_id"] for item in validated["campaigns"]]
    with browser.browser_operation_lock():
        targets = icloud_mail_targets(inbound_monitor.load_cdp_targets(cdp))
        selected = []
        for index, target in enumerate(targets):
            with inbound_monitor.open_cdp_target(
                str(target["webSocketDebuggerUrl"])
            ) as connection:
                payload = read_tab_summary(
                    connection,
                    config=validated,
                    world_number=index,
                )
            if payload.get("folderSelected"):
                selected.append(payload)

    if len(selected) != 1:
        raise RuntimeError(
            "exactly one iCloud Mail tab must have the configured folder selected"
        )
    payload = selected[0]
    if payload.get("folderFound") is not True or payload.get("treeFound") is not True:
        raise RuntimeError("the configured application inbox folder is unavailable")
    return validate_campaign_summaries(
        payload.get("campaigns"), campaign_ids=campaign_ids
    )


def open_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS application_inbox_observations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          observed_at TEXT NOT NULL,
          campaign_id TEXT NOT NULL,
          matching_thread_count INTEGER NOT NULL CHECK (matching_thread_count >= 0),
          unread_matching_thread_count INTEGER NOT NULL
            CHECK (unread_matching_thread_count >= 0),
          has_matching_thread INTEGER NOT NULL CHECK (has_matching_thread IN (0, 1)),
          has_unread_matching_thread INTEGER NOT NULL
            CHECK (has_unread_matching_thread IN (0, 1)),
          CHECK (unread_matching_thread_count <= matching_thread_count)
        );
        CREATE INDEX IF NOT EXISTS application_inbox_observations_latest
          ON application_inbox_observations(campaign_id, id DESC);
        """
    )
    return db


def _previous_summaries(db: sqlite3.Connection, campaign_ids: list[str]) -> dict:
    """Return a short high-water baseline for virtualized-mail resilience.

    iCloud may temporarily unload a matching row from the DOM as its message
    list virtualizes. Comparing only with the latest observation turns a
    one-pass disappearance and reappearance into a false alert. Taking the
    maximum over the last two observations debounces that transient state
    while still allowing a sustained count decrease to become the baseline.
    """
    previous = {}
    for campaign_id in campaign_ids:
        rows = db.execute(
            """
            SELECT matching_thread_count, unread_matching_thread_count,
                   has_matching_thread, has_unread_matching_thread
            FROM application_inbox_observations
            WHERE campaign_id=? ORDER BY id DESC LIMIT ?
            """,
            (campaign_id, RECENT_BASELINE_OBSERVATIONS),
        ).fetchall()
        if rows:
            matching_count = max(row["matching_thread_count"] for row in rows)
            unread_count = max(row["unread_matching_thread_count"] for row in rows)
            previous[campaign_id] = {
                "matching_thread_count": matching_count,
                "unread_matching_thread_count": unread_count,
                "has_matching_thread": matching_count > 0,
                "has_unread_matching_thread": unread_count > 0,
            }
    return previous


def record_observation(
    summaries: object,
    *,
    db_path: Path = DB_PATH,
    status_path: Path = STATUS_PATH,
    observed_at: str | None = None,
) -> dict:
    """Persist only campaign identifiers and aggregate counts/booleans."""
    if not isinstance(summaries, list) or not summaries:
        raise ValueError("application inbox summaries must be a non-empty list")
    campaign_ids = []
    canonical = []
    for item in summaries:
        if not isinstance(item, dict) or set(item) != {
            "campaign_id",
            "matching_thread_count",
            "unread_matching_thread_count",
            "has_matching_thread",
            "has_unread_matching_thread",
        }:
            raise ValueError("application inbox summary fields are invalid")
        campaign_id = item["campaign_id"]
        if not isinstance(campaign_id, str) or not CAMPAIGN_ID_RE.fullmatch(campaign_id):
            raise ValueError("application inbox campaign_id is unsafe")
        if campaign_id in campaign_ids:
            raise ValueError("application inbox campaign_id values must be unique")
        campaign_ids.append(campaign_id)
        try:
            matching_count = _nonnegative_integer(item["matching_thread_count"])
            unread_count = _nonnegative_integer(item["unread_matching_thread_count"])
        except RuntimeError as exc:
            raise ValueError("application inbox counts are invalid") from exc
        has_match = item["has_matching_thread"]
        has_unread = item["has_unread_matching_thread"]
        if (
            not isinstance(has_match, bool)
            or not isinstance(has_unread, bool)
            or unread_count > matching_count
            or has_match != (matching_count > 0)
            or has_unread != (unread_count > 0)
        ):
            raise ValueError("application inbox counts are inconsistent")
        canonical.append(
            {
                "campaign_id": campaign_id,
                "matching_thread_count": matching_count,
                "unread_matching_thread_count": unread_count,
                "has_matching_thread": has_match,
                "has_unread_matching_thread": has_unread,
            }
        )

    observed_at = observed_at or inbound_monitor.utc_now()
    db = open_db(db_path)
    try:
        previous = _previous_summaries(db, campaign_ids)
        alerts = []
        for item in canonical:
            before = previous.get(item["campaign_id"])
            if before and (
                item["matching_thread_count"] > before["matching_thread_count"]
                or item["unread_matching_thread_count"]
                > before["unread_matching_thread_count"]
            ):
                alerts.append(
                    {
                        "campaign_id": item["campaign_id"],
                        "matching_thread_count_increased": (
                            item["matching_thread_count"]
                            > before["matching_thread_count"]
                        ),
                        "unread_matching_thread_count_increased": (
                            item["unread_matching_thread_count"]
                            > before["unread_matching_thread_count"]
                        ),
                    }
                )
            db.execute(
                """
                INSERT INTO application_inbox_observations
                  (observed_at, campaign_id, matching_thread_count,
                   unread_matching_thread_count, has_matching_thread,
                   has_unread_matching_thread)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    observed_at,
                    item["campaign_id"],
                    item["matching_thread_count"],
                    item["unread_matching_thread_count"],
                    int(item["has_matching_thread"]),
                    int(item["has_unread_matching_thread"]),
                ),
            )
        db.commit()
    finally:
        db.close()

    report = {
        "checked_at": observed_at,
        "ok": True,
        "campaigns": canonical,
        "summary": {
            "campaign_count": len(canonical),
            "campaigns_with_matching_threads": sum(
                item["has_matching_thread"] for item in canonical
            ),
            "campaigns_with_unread_matching_threads": sum(
                item["has_unread_matching_thread"] for item in canonical
            ),
            "matching_thread_count": sum(
                item["matching_thread_count"] for item in canonical
            ),
            "unread_matching_thread_count": sum(
                item["unread_matching_thread_count"] for item in canonical
            ),
        },
        "alerts": alerts,
        "policy": {
            "mail_opened": False,
            "row_activated": False,
            "message_preview_read": False,
            "sender_or_subject_persisted": False,
            "automatic_reply_is_not_human_reply": True,
            "match_is_not_human_reply": True,
            "match_is_not_a_qualified_lead": True,
            "transient_dom_drop_debounce_observations": (
                RECENT_BASELINE_OBSERVATIONS
            ),
        },
    }
    inbound_monitor.atomic_write_json(status_path, report)
    return report


def monitor_once(
    *,
    config_path: Path = CONFIG_PATH,
    db_path: Path = DB_PATH,
    status_path: Path = STATUS_PATH,
    cdp: str = browser.DEFAULT_CDP,
) -> dict:
    config = load_config(config_path)
    summaries = read_application_counts(cdp=cdp, config=config)
    return record_observation(
        summaries,
        db_path=db_path,
        status_path=status_path,
    )


def failure_report() -> dict:
    """Return a constant failure record that cannot leak private match data."""
    return {
        "checked_at": inbound_monitor.utc_now(),
        "ok": False,
        "error": "application inbox observation failed closed",
    }


def loop(interval_minutes: int) -> None:
    if interval_minutes < 5:
        raise ValueError("interval must be at least five minutes")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("application inbox monitor is already running") from exc
        while True:
            try:
                report = monitor_once()
            except Exception:
                report = failure_report()
                inbound_monitor.atomic_write_json(STATUS_PATH, report)
            inbound_monitor.append_log(LOG_PATH, report)
            time.sleep(interval_minutes * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("once", help="Read and record one private aggregate snapshot.")
    continuous = commands.add_parser("loop", help="Repeat private aggregate snapshots.")
    continuous.add_argument("--interval-minutes", type=int, default=15)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "once":
        print(json.dumps(monitor_once(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        loop(args.interval_minutes)


if __name__ == "__main__":
    main()
