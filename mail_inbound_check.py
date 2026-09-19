#!/usr/bin/env python3
"""Run a finite, metadata-only mail observation in an owned desktop lease."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import signal
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import TimeoutError as BrowserTimeout, sync_playwright

import application_inbox_monitor as applications
import browser
import desktop_lease
import gmail_application_monitor as gmail
import inbound_monitor as intake


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".local"
STATUS_PATH = RUNTIME / "mail-inbound-monitor-status.json"
OBSERVATION_PATH = RUNTIME / "mail-inbound-observation.json"
LOOP_LOCK = RUNTIME / "mail-inbound-monitor.lock"
LOG_PATH = RUNTIME / "mail-inbound-monitor.jsonl"
POLICY = {
    "application_thread_window": applications.MAX_SCAN_ROWS,
    "complete_mailbox_claimed": False,
    "message_bodies_read": False,
    "sender_or_subject_persisted": False,
    "automatic_reply": False,
    "gmail_coverage_reported_separately": True,
}
SUMMARY_FIELDS = {
    "campaign_count", "campaigns_with_matching_threads",
    "campaigns_with_unread_matching_threads", "matching_thread_count",
    "unread_matching_thread_count",
}


class MailSessionUnavailable(RuntimeError):
    pass


def failure_reason(error: Exception) -> str:
    """Classify failures without persisting browser logs or mailbox text."""
    if isinstance(error, BrowserTimeout):
        return "browser_timeout"
    return {
        "iCloud did not expose the application inbox summary": "application_summary_unavailable",
        "iCloud exposed incomplete application inbox coverage": "application_coverage_incomplete",
        "iCloud did not expose the expected folder count status": "folder_count_unavailable",
        "the dedicated intake folder is unavailable": "intake_folder_unavailable",
        "the dedicated intake folder is not selected": "intake_folder_not_selected",
        "the iCloud Mail application frame is unavailable": "mail_frame_unavailable",
        "the project mail session needs review": "mail_session_unavailable",
        "exactly one project mail tab is required": "mail_tab_ambiguous",
        "CDP command did not complete: Runtime.evaluate": "mail_evaluation_timeout",
    }.get(str(error), "unavailable_or_incomplete")


def private_json(path: Path, value: dict) -> None:
    if path.parent.is_symlink() or path.is_symlink():
        raise RuntimeError("unsafe private mail status path")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def private_status(path: Path) -> dict:
    if path.is_symlink():
        raise RuntimeError("unsafe private mail status path")
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def timestamp(value) -> str | None:
    if not isinstance(value, str) or len(value) > 32:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).isoformat()
    except ValueError:
        pass
    return None


def validated_observation(value: dict, run_id: str) -> dict:
    """Whitelist the child's aggregate schema; never forward arbitrary fields."""
    required = {"run_id", "checked_at", "ok", "applications", "fit_folder", "gmail", "alerts", "policy"}
    if set(value) != required or value["run_id"] != run_id or value["ok"] is not True:
        raise ValueError("invalid mail observation")
    checked_at = timestamp(value["checked_at"])
    if checked_at is None or value["policy"] != POLICY:
        raise ValueError("invalid observation policy or timestamp")
    for counts, fields in (
        (value["applications"], SUMMARY_FIELDS),
        (value["fit_folder"], {"message_count", "unread_count"}),
    ):
        if not isinstance(counts, dict) or set(counts) != fields:
            raise ValueError("invalid observation counts")
        if any(type(count) is not int or count < 0 for count in counts.values()):
            raise ValueError("invalid observation count")
    summary = value["applications"]
    fit = value["fit_folder"]
    if not (
        summary["campaigns_with_unread_matching_threads"] <= summary["campaigns_with_matching_threads"] <= summary["campaign_count"]
        and summary["unread_matching_thread_count"] <= summary["matching_thread_count"]
        and fit["unread_count"] <= fit["message_count"]
    ):
        raise ValueError("inconsistent observation counts")
    if not isinstance(value["alerts"], list):
        raise ValueError("invalid observation alerts")
    gmail_summary = gmail.validated_summary(value["gmail"])
    for alert in value["alerts"]:
        if not isinstance(alert, dict):
            raise ValueError("invalid observation alert")
        if alert.get("kind") == "application_mail_count_changed":
            if set(alert) != {"kind", "campaign_id", "matching_thread_count_increased", "unread_matching_thread_count_increased"}:
                raise ValueError("invalid application alert")
            if not isinstance(alert["campaign_id"], str) or not applications.CAMPAIGN_ID_RE.fullmatch(alert["campaign_id"]):
                raise ValueError("invalid campaign identifier")
            if any(type(alert[key]) is not bool for key in ("matching_thread_count_increased", "unread_matching_thread_count_increased")):
                raise ValueError("invalid change signal")
        elif alert.get("kind") == "inbound_count_increased":
            if set(alert) != {"kind", "message_delta"} or type(alert["message_delta"]) is not int or alert["message_delta"] < 1:
                raise ValueError("invalid fit-folder alert")
        elif alert.get("kind") == "gmail_application_activity_pending":
            if set(alert) != {"kind"} or gmail_summary.get("review_required") is not True:
                raise ValueError("invalid Gmail activity alert")
        else:
            raise ValueError("unknown observation alert")
    pending_gmail = sum(alert["kind"] == "gmail_application_activity_pending" for alert in value["alerts"])
    if pending_gmail != int(gmail_summary.get("review_required") is True):
        raise ValueError("inconsistent Gmail activity alert")
    return {
        "checked_at": checked_at, "ok": True,
        "applications": summary, "fit_folder": fit,
        "gmail": gmail_summary,
        "alerts": value["alerts"], "policy": dict(POLICY),
    }


def select_folder(frame, folder: str) -> None:
    option = frame.get_by_role("option", name=folder, exact=True)
    option.wait_for(state="visible", timeout=10_000)
    if option.count() != 1:
        raise MailSessionUnavailable("the required mail folder is unavailable")
    if option.get_attribute("aria-selected") != "true":
        option.click(timeout=10_000)
    frame.wait_for_function(
        "name => [...document.querySelectorAll('[role=option]')].filter(e => e.getAttribute('aria-label') === name && e.getAttribute('aria-selected') === 'true').length === 1",
        arg=folder, timeout=10_000,
    )
    # Allow the selected folder's virtualized list to settle. The collector then
    # independently checks completeness, row identities and the selected folder.
    frame.wait_for_timeout(2_000)


def folder_evidence(frame, folder: str, stage: str) -> None:
    """Optional validation screenshot of one folder label, never the inbox."""
    if stage not in {"before", "after", "failure"}:
        raise ValueError("invalid evidence stage")
    option = frame.get_by_role("option", name=folder, exact=True)
    box = option.bounding_box(timeout=5_000)
    if option.count() != 1 or not box or not (0 < box["width"] <= 400 and 0 < box["height"] <= 100):
        raise RuntimeError("folder-only screenshot boundary unavailable")
    destination = RUNTIME / "evidence" / f"mail-check-{stage}.png"
    if destination.parent.is_symlink() or destination.is_symlink():
        raise RuntimeError("unsafe private evidence path")
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    option.screenshot(path=str(destination), timeout=5_000)
    destination.chmod(0o600)


def collect_counts(config: dict, *, capture_evidence: bool = False) -> tuple[list[dict], tuple[int, int]]:
    with browser.browser_operation_lock(timeout_seconds=5), sync_playwright() as pw:
        connected = pw.chromium.connect_over_cdp(browser.DEFAULT_CDP, no_defaults=True)
        pages = [
            page for context in connected.contexts for page in context.pages
            if urlsplit(page.url).hostname == "www.icloud.com"
            and urlsplit(page.url).path.rstrip("/") == "/mail"
        ]
        if len(pages) != 1:
            raise MailSessionUnavailable("exactly one project mail tab is required")
        page = pages[0]
        page.bring_to_front()
        deadline = time.monotonic() + 15
        frames = []
        while time.monotonic() < deadline:
            frames = [
                frame for frame in page.frames
                if urlsplit(frame.url).path.startswith(intake.MAIL_APP_FRAME_PATH)
            ]
            if len(frames) == 1:
                break
            page.wait_for_timeout(250)
        if len(frames) != 1:
            raise MailSessionUnavailable("the project mail session needs review")
        frame = frames[0]
        select_folder(frame, config["folder_name"])
        if capture_evidence:
            folder_evidence(frame, config["folder_name"], "before")
        summaries = applications._read_application_counts_locked(
            cdp=browser.DEFAULT_CDP, config=config,
        )
        try:
            select_folder(frame, intake.FOLDER_NAME)
            counts = intake._read_folder_counts_locked(
                cdp=browser.DEFAULT_CDP, folder_name=intake.FOLDER_NAME,
            )
        finally:
            select_folder(frame, config["folder_name"])
        if capture_evidence:
            folder_evidence(frame, config["folder_name"], "after")
        return summaries, counts


def collect_once(run_id: str, *, capture_evidence: bool = False) -> dict:
    config = applications.load_config()
    summaries, (message_count, unread_count) = collect_counts(config, capture_evidence=capture_evidence)
    application_report = applications.record_observation(summaries)
    intake_report = intake.record_observation(message_count, unread_count)
    # This optional provider has independent status and failure handling. A
    # Gmail session failure must not pause or erase healthy iCloud coverage.
    try:
        gmail_report = gmail.check_optional()
    except Exception:
        gmail_report = {"state": "observation_failed"}
    return {
        "run_id": run_id,
        "checked_at": intake.utc_now(),
        "ok": True,
        "applications": application_report["summary"],
        "fit_folder": {"message_count": message_count, "unread_count": unread_count},
        "gmail": gmail_report,
        "alerts": [
            {"kind": "application_mail_count_changed", **alert}
            for alert in application_report["alerts"]
        ] + [{"kind": alert["kind"], "message_delta": alert["message_delta"]} for alert in intake_report["alerts"]]
        + ([{"kind": "gmail_application_activity_pending"}] if gmail_report.get("review_required") is True else []),
        "policy": dict(POLICY),
    }


def run_once(*, status_path: Path = STATUS_PATH, observation_path: Path = OBSERVATION_PATH, capture_evidence: bool = False) -> dict:
    run_id = secrets.token_hex(16)
    checked_at = intake.utc_now()
    previous = private_status(status_path)
    try:
        lifecycle = desktop_lease.run_owned_check([
            sys.executable, str(Path(__file__).resolve()), "_collect", "--run-id", run_id,
        ] + (["--capture-evidence"] if capture_evidence else []))
    except Exception:
        lifecycle = {"state": "desktop_preflight_failed", "desktop_started": False, "desktop_stopped": False}
    report = {
        "checked_at": checked_at,
        **lifecycle,
        "ok": False,
        "last_successful_checked_at": timestamp(previous.get("last_successful_checked_at")),
        "alerts": [],
    }
    if lifecycle["desktop_started"]:
        observation = private_status(observation_path)
        if observation.get("run_id") == run_id:
            if lifecycle["state"] == "checked" and lifecycle["desktop_stopped"] is True:
                try:
                    report.update(validated_observation(observation, run_id))
                    report["last_successful_checked_at"] = report["checked_at"]
                except (ValueError, TypeError, KeyError):
                    report["state"] = "observation_invalid"
            elif observation.get("needs_mail_review") is True:
                report["needs_mail_review"] = True
        elif lifecycle["state"] == "checked":
            report["state"] = "observation_missing_or_stale"
    private_json(status_path, report)
    return report


def interrupted(_signum, _frame):
    raise KeyboardInterrupt


def cooldown_seconds(interval_minutes: int) -> float:
    previous = private_status(STATUS_PATH)
    last_check = timestamp(previous.get("checked_at"))
    if last_check is None:
        return 0
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(last_check)).total_seconds()
    return min(interval_minutes * 60, max(0, interval_minutes * 60 - age))


def loop(interval_minutes: int) -> None:
    if interval_minutes < 60:
        raise ValueError("mail checks must be at least 60 minutes apart")
    with desktop_lease.lifecycle_lease(LOOP_LOCK):
        failures = 0
        delay = cooldown_seconds(interval_minutes)
        if delay:
            time.sleep(delay)
        while True:
            report = run_once()
            if LOG_PATH.is_symlink():
                raise RuntimeError("unsafe private mail log path")
            with LOG_PATH.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(report, sort_keys=True) + "\n")
            print(json.dumps(report), flush=True)
            if report["ok"]:
                failures = 0
            elif not report["state"].startswith("skipped_"):
                failures += 1
            if report.get("needs_mail_review") or failures >= 3 or report["state"] == "check_interrupted" or report["state"].startswith(("cleanup_", "desktop_cleanup_")):
                report["loop_paused"] = True
                private_json(STATUS_PATH, report)
                return
            time.sleep(interval_minutes * 60)


def main() -> None:
    os.umask(0o077)
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    once = commands.add_parser("once")
    once.add_argument("--capture-evidence", action="store_true")
    commands.add_parser("status")
    monitor = commands.add_parser("loop")
    monitor.add_argument("--interval-minutes", type=int, default=60)
    collect = commands.add_parser("_collect")
    collect.add_argument("--run-id", required=True)
    collect.add_argument("--capture-evidence", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "status":
            print(json.dumps(private_status(STATUS_PATH), indent=2))
            return
        if args.command == "_collect":
            try:
                report = collect_once(args.run_id, capture_evidence=args.capture_evidence)
            except Exception as error:
                report = {
                    "run_id": args.run_id, "checked_at": intake.utc_now(), "ok": False,
                    "needs_mail_review": isinstance(error, MailSessionUnavailable),
                    "error": "mail observation failed closed",
                    "failure_reason": failure_reason(error),
                }
            private_json(OBSERVATION_PATH, report)
            raise SystemExit(0 if report["ok"] else 1)
        if args.command == "once":
            report = run_once(capture_evidence=args.capture_evidence)
            print(json.dumps(report, indent=2))
            raise SystemExit(0 if report["ok"] or report["state"].startswith("skipped_") else 1)
        loop(args.interval_minutes)
    except KeyboardInterrupt:
        print("Mail check interrupted; private status records the last completed cleanup check.", flush=True)
    except Exception:
        print("Mail check failed closed; review the private aggregate status.", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
