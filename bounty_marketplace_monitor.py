#!/usr/bin/env python3
"""Poll Bounty's agent API without commenting, claiming, messaging, or submitting."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import stat
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
API_URL = "https://api.trybounty.ai/v1/agent/bounties"
TASKBOUNTY_FEED_URL = "https://www.task-bounty.com/api/v1/bounties.json?limit=100"
AGENTBOUNTIES_FEED_URL = (
    "https://api.agentbounties.app/v1/base/autonomous-bounties/feed"
    "?network=base-mainnet&claimable_only=true"
)
FREELANCER_ACTIVE_URL = "https://www.freelancer.com/api/projects/0.1/projects/active/"
FREELANCER_QUERY = "mcp playwright kicad rag llm ocr ssh"
FREELANCER_MATCH_PATTERNS = {
    "kicad": re.compile(r"\bkicad\b", re.IGNORECASE),
    "local_ai": re.compile(
        r"\b(?:rag|llm|ocr)\b|retrieval[- ]augmented", re.IGNORECASE
    ),
    "mcp": re.compile(r"\bmcp\b|model context protocol", re.IGNORECASE),
    "playwright": re.compile(r"\bplaywright\b", re.IGNORECASE),
    "remote_access": re.compile(r"\bssh\b|remote desktop|reverse tunnel", re.IGNORECASE),
}
FREELANCER_EXCLUSION_PATTERNS = {
    "commission_or_recruiting": re.compile(
        r"\b(?:commission[- ]only|recruit(?:er|ing|ment)?|talent acquisition)\b",
        re.IGNORECASE,
    ),
    "location_or_live_access": re.compile(
        r"\b(?:anydesk|teamviewer|on[- ]site|onsite|in[- ]person)\b",
        re.IGNORECASE,
    ),
    "ongoing_employment": re.compile(
        r"\b(?:full[- ]time|40\s*hours?\s*(?:a|per)\s*week)\b",
        re.IGNORECASE,
    ),
}
DEFAULT_CREDENTIALS = ROOT / ".local" / "private" / "CREDENTIALS.md"
DEFAULT_STATE = ROOT / ".local" / "bounty-marketplace-monitor-status.json"
DEFAULT_LOCK = ROOT / ".local" / "bounty-marketplace-monitor.lock"
MINIMUM_INTERVAL_MINUTES = 5
MAX_PAGES = 100
KEY_PATTERN = re.compile(r"^ak_[A-Za-z0-9_-]{20,}$")
Opener = Callable[..., Any]


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _safe_private_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    metadata = path.stat()
    if stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1:
        raise ValueError(f"{label} must be private and singly linked")
    return path


def load_api_key(path: Path = DEFAULT_CREDENTIALS) -> str:
    """Read the Bounty API key without returning any other credential data."""
    path = _safe_private_file(path, "credential file")
    section = re.search(
        r"(?ms)^## Bounty agent API\n(.*?)(?=^## |\Z)",
        path.read_text(encoding="utf-8"),
    )
    if not section:
        raise ValueError("Bounty agent API credential section is missing")
    match = re.search(r"(?m)^- API key: `?([^`\s]+)`?\s*$", section.group(1))
    if not match or not KEY_PATTERN.fullmatch(match.group(1)):
        raise ValueError("Bounty agent API key is missing or invalid")
    return match.group(1)


def _api_page(
    api_key: str,
    *,
    cursor: str | None = None,
    opener: Opener = urlopen,
) -> dict[str, Any]:
    if not KEY_PATTERN.fullmatch(api_key):
        raise ValueError("Bounty API key is invalid")
    url = API_URL
    if cursor:
        url += "?" + urlencode({"cursor": cursor})
    request = Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with opener(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Bounty read failed with HTTP {exc.code}") from exc
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise RuntimeError("Bounty read did not return valid JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Bounty returned an invalid response")
    return payload


def _summary(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RuntimeError("Bounty returned an invalid work summary")
    bounty_id = raw.get("_id") or raw.get("id")
    version = raw.get("version")
    if not isinstance(bounty_id, str) or not bounty_id.strip():
        raise RuntimeError("Bounty work summary has no ID")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise RuntimeError("Bounty work summary has no valid version")
    return {"bounty_id": bounty_id.strip(), "version": version}


def fetch_available_bounties(
    api_key: str,
    *,
    opener: Opener = urlopen,
    max_pages: int = MAX_PAGES,
) -> dict[str, Any]:
    """Read every available page. Listing work never creates a Claim."""
    if max_pages < 1:
        raise ValueError("max_pages must be positive")
    cursor: str | None = None
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for page_number in range(1, max_pages + 1):
        payload = _api_page(api_key, cursor=cursor, opener=opener)
        raw_rows = payload.get("bounties")
        is_done = payload.get("is_done")
        next_cursor = payload.get("next_cursor")
        if not isinstance(raw_rows, list) or not isinstance(is_done, bool):
            raise RuntimeError("Bounty returned an invalid page")
        for raw in raw_rows:
            row = _summary(raw)
            if row["bounty_id"] in seen_ids:
                raise RuntimeError("Bounty returned a duplicate work summary")
            seen_ids.add(row["bounty_id"])
            rows.append(row)
        if is_done:
            rows.sort(key=lambda row: (row["bounty_id"], row["version"]))
            return {"bounties": rows, "pages_read": page_number}
        if not isinstance(next_cursor, str) or not next_cursor or next_cursor == cursor:
            raise RuntimeError("Bounty pagination cannot advance")
        cursor = next_cursor
    raise RuntimeError("Bounty pagination exceeded the safety limit")


def fetch_taskbounty_open_tasks(*, opener: Opener = urlopen) -> dict[str, Any]:
    """Read TaskBounty's public JSON Feed without an account or API key."""
    request = Request(
        TASKBOUNTY_FEED_URL,
        headers={"Accept": "application/feed+json, application/json"},
        method="GET",
    )
    try:
        with opener(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"TaskBounty public read failed with HTTP {exc.code}") from exc
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise RuntimeError("TaskBounty public read did not return valid JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("TaskBounty returned an invalid public feed")
    version = payload.get("version")
    raw_rows = payload.get("items")
    if version != "https://jsonfeed.org/version/1.1" or not isinstance(raw_rows, list):
        raise RuntimeError("TaskBounty returned an invalid public feed")

    rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for raw in raw_rows:
        if not isinstance(raw, dict):
            raise RuntimeError("TaskBounty returned an invalid task summary")
        task_id = raw.get("id")
        title = raw.get("title", "")
        observed_at = raw.get("date_modified") or raw.get("date_published") or ""
        if not isinstance(task_id, str) or not task_id.strip():
            raise RuntimeError("TaskBounty task summary has no ID")
        if (
            not isinstance(title, str)
            or len(title) > 500
            or not isinstance(observed_at, str)
            or len(observed_at) > 128
        ):
            raise RuntimeError("TaskBounty returned an invalid task summary")
        task_id = task_id.strip()
        if task_id in seen_ids:
            raise RuntimeError("TaskBounty returned a duplicate task summary")
        seen_ids.add(task_id)
        fingerprint = hashlib.sha256(
            json.dumps(
                raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        row = {"task_id": task_id, "fingerprint": fingerprint}
        if title.strip():
            row["title"] = title.strip()
        if observed_at.strip():
            row["observed_at"] = observed_at.strip()
        rows.append(row)
    rows.sort(key=lambda row: row["task_id"])
    return {"tasks": rows, "pages_read": 1}


def fetch_agentbounties_claimable_work(*, opener: Opener = urlopen) -> dict[str, Any]:
    """Read the canonical claimable Base feed without a wallet or API key."""
    request = Request(
        AGENTBOUNTIES_FEED_URL,
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with opener(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(
            f"Agent Bounties canonical read failed with HTTP {exc.code}"
        ) from exc
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Agent Bounties canonical read did not return valid JSON"
        ) from exc
    if not isinstance(payload, list):
        raise RuntimeError("Agent Bounties returned an invalid canonical feed")

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    decimal = re.compile(r"^[0-9]{1,40}$")
    signed_decimal = re.compile(r"^-?[0-9]{1,40}$")
    for raw in payload:
        if not isinstance(raw, dict):
            raise RuntimeError("Agent Bounties returned an invalid work summary")
        bounty_id = raw.get("bounty_id")
        bounty_contract = raw.get("bounty_contract")
        terms_hash = raw.get("terms_hash")
        solver_reward = raw.get("solver_reward")
        gross_cash_margin = raw.get("gross_cash_margin")
        if (
            not isinstance(bounty_id, str)
            or not bounty_id.strip()
            or len(bounty_id) > 160
            or not isinstance(bounty_contract, str)
            or not re.fullmatch(r"0x[0-9a-fA-F]{40}", bounty_contract)
            or not isinstance(terms_hash, str)
            or not re.fullmatch(r"0x[0-9a-fA-F]{64}", terms_hash)
            or not isinstance(solver_reward, str)
            or not decimal.fullmatch(solver_reward)
            or not isinstance(gross_cash_margin, str)
            or not signed_decimal.fullmatch(gross_cash_margin)
            or raw.get("status") != "claimable"
            or raw.get("terms_valid") is not True
            or raw.get("verification_ready") is not True
        ):
            raise RuntimeError("Agent Bounties returned an invalid work summary")
        bounty_id = bounty_id.strip()
        if bounty_id in seen_ids:
            raise RuntimeError("Agent Bounties returned a duplicate work summary")
        seen_ids.add(bounty_id)
        fingerprint = hashlib.sha256(
            json.dumps(
                raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        rows.append(
            {
                "bounty_id": bounty_id,
                "bounty_contract": bounty_contract.lower(),
                "terms_hash": terms_hash.lower(),
                "solver_reward_usdc_base_units": solver_reward,
                "gross_cash_margin_usdc_base_units": gross_cash_margin,
                "profitable_before_gas_and_risk": int(gross_cash_margin) > 0,
                "fingerprint": fingerprint,
            }
        )
    rows.sort(key=lambda row: row["bounty_id"])
    return {"bounties": rows, "pages_read": 1}


def _freelancer_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"Freelancer project has invalid {label}")
    number = float(value)
    if not math.isfinite(number) or number < 0 or number > 1_000_000_000:
        raise RuntimeError(f"Freelancer project has invalid {label}")
    return number


def fetch_freelancer_candidate_projects(*, opener: Opener = urlopen) -> dict[str, Any]:
    """Read recent active projects from Freelancer's official public API."""
    url = FREELANCER_ACTIVE_URL + "?" + urlencode(
        {
            "query": FREELANCER_QUERY,
            "or_search_query": "true",
            "limit": 100,
            "compact": "true",
            "job_details": "true",
            "full_description": "true",
            "sort_field": "time_updated",
        }
    )
    request = Request(
        url,
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with opener(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(
            f"Freelancer public project read failed with HTTP {exc.code}"
        ) from exc
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Freelancer public project read did not return valid JSON"
        ) from exc
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise RuntimeError("Freelancer returned an invalid public project feed")
    result = payload.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("projects"), list):
        raise RuntimeError("Freelancer returned an invalid public project feed")

    rows: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for raw in result["projects"]:
        if not isinstance(raw, dict):
            raise RuntimeError("Freelancer returned an invalid project summary")
        project_id = raw.get("id")
        title = raw.get("title")
        description = raw.get("description", "")
        seo_url = raw.get("seo_url")
        project_type = raw.get("type")
        currency = raw.get("currency")
        budget = raw.get("budget")
        bid_stats = raw.get("bid_stats", {})
        jobs = raw.get("jobs", [])
        upgrades = raw.get("upgrades", {})
        if (
            isinstance(project_id, bool)
            or not isinstance(project_id, int)
            or project_id < 1
            or not isinstance(title, str)
            or not title.strip()
            or len(title) > 500
            or not isinstance(description, str)
            or len(description) > 200_000
            or not isinstance(seo_url, str)
            or not seo_url
            or len(seo_url) > 500
            or "://" in seo_url
            or seo_url.startswith("/")
            or ".." in seo_url.split("/")
            or project_type not in {"fixed", "hourly"}
            or not isinstance(currency, dict)
            or not isinstance(budget, dict)
            or not isinstance(bid_stats, dict)
            or not isinstance(jobs, list)
            or not isinstance(upgrades, dict)
        ):
            raise RuntimeError("Freelancer returned an invalid project summary")
        if project_id in seen_ids:
            raise RuntimeError("Freelancer returned a duplicate project summary")
        seen_ids.add(project_id)
        code = currency.get("code")
        if not isinstance(code, str) or not re.fullmatch(r"[A-Z]{3}", code):
            raise RuntimeError("Freelancer project has invalid currency")
        if (
            currency.get("exchange_rate") is None
            or budget.get("minimum") is None
            or budget.get("maximum") is None
        ):
            continue
        exchange_rate = _freelancer_number(
            currency.get("exchange_rate"), "currency exchange rate"
        )
        if exchange_rate == 0:
            raise RuntimeError("Freelancer project has invalid currency exchange rate")
        budget_min = _freelancer_number(budget.get("minimum"), "minimum budget")
        budget_max = _freelancer_number(budget.get("maximum"), "maximum budget")
        if budget_max < budget_min:
            raise RuntimeError("Freelancer project has invalid budget range")
        bid_count = bid_stats.get("bid_count", 0)
        if isinstance(bid_count, bool) or not isinstance(bid_count, int) or bid_count < 0:
            raise RuntimeError("Freelancer project has invalid bid count")
        job_names: list[str] = []
        for job in jobs:
            if not isinstance(job, dict) or not isinstance(job.get("name"), str):
                raise RuntimeError("Freelancer project has invalid job metadata")
            if len(job["name"]) > 200:
                raise RuntimeError("Freelancer project has invalid job metadata")
            job_names.append(job["name"])

        if (
            raw.get("status") != "active"
            or raw.get("frontend_project_status") != "open"
            or raw.get("deleted") is not False
            or raw.get("nonpublic") is not False
            or raw.get("local") is not False
        ):
            continue
        searchable = " ".join([title, description, *job_names])
        matched_terms = sorted(
            name
            for name, pattern in FREELANCER_MATCH_PATTERNS.items()
            if pattern.search(searchable)
        )
        excluded_terms = sorted(
            name
            for name, pattern in FREELANCER_EXCLUSION_PATTERNS.items()
            if pattern.search(searchable)
        )
        if not matched_terms or excluded_terms:
            continue
        budget_min_usd = round(budget_min * exchange_rate, 2)
        budget_max_usd = round(budget_max * exchange_rate, 2)
        if (
            (project_type == "fixed" and budget_max_usd < 250)
            or (project_type == "hourly" and budget_max_usd < 25)
            or bid_count > 25
            or raw.get("is_seller_kyc_required") is True
            or upgrades.get("pf_only") is True
        ):
            continue
        submitted = raw.get("time_submitted")
        if (
            isinstance(submitted, bool)
            or not isinstance(submitted, int)
            or submitted < 1
            or submitted > 4_102_444_800
        ):
            raise RuntimeError("Freelancer project has invalid submission time")
        submitted_at = (
            datetime.fromtimestamp(submitted, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "budget": budget,
                    "currency": {"code": code, "exchange_rate": exchange_rate},
                    "description": description,
                    "jobs": job_names,
                    "title": title,
                    "type": project_type,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        rows.append(
            {
                "project_id": project_id,
                "fingerprint": fingerprint,
                "title": title.strip(),
                "url": "https://www.freelancer.com/projects/" + seo_url,
                "project_type": project_type,
                "currency": code,
                "budget_min": budget_min,
                "budget_max": budget_max,
                "budget_min_usd": budget_min_usd,
                "budget_max_usd": budget_max_usd,
                "bid_count": bid_count,
                "matched_terms": matched_terms,
                "submitted_at": submitted_at,
            }
        )
    rows.sort(key=lambda row: row["project_id"])
    return {
        "projects": rows,
        "pages_read": 1,
        "projects_considered": len(result["projects"]),
    }


def validate_local_path(path: Path, *, root: Path = ROOT, suffix: str) -> Path:
    root = root.resolve()
    candidate = Path(os.path.abspath(os.fspath(path)))
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("runtime path must stay inside the repository") from exc
    if len(relative.parts) < 2 or relative.parts[0] != ".local":
        raise ValueError("runtime path must be below .local")
    if candidate.suffix != suffix:
        raise ValueError(f"runtime path must end in {suffix}")
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError("runtime path must not contain symbolic links")
    return candidate


def load_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    path = _safe_private_file(path, "monitor state")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("monitor state is invalid") from exc
    if not isinstance(payload, dict) or payload.get("version") not in {1, 2, 3, 4}:
        raise ValueError("monitor state is invalid")
    seen = payload.get("seen_bounty_versions")
    if not isinstance(seen, dict) or any(
        not isinstance(key, str)
        or not key
        or isinstance(version, bool)
        or not isinstance(version, int)
        or version < 1
        for key, version in seen.items()
    ):
        raise ValueError("monitor state contains invalid seen work")
    seen_taskbounty = payload.get("seen_taskbounty_fingerprints", {})
    if not isinstance(seen_taskbounty, dict) or any(
        not isinstance(key, str)
        or not key
        or not isinstance(fingerprint, str)
        or not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
        for key, fingerprint in seen_taskbounty.items()
    ):
        raise ValueError("monitor state contains invalid TaskBounty work")
    seen_agentbounties = payload.get("seen_agentbounties_fingerprints", {})
    if not isinstance(seen_agentbounties, dict) or any(
        not isinstance(key, str)
        or not key
        or not isinstance(fingerprint, str)
        or not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
        for key, fingerprint in seen_agentbounties.items()
    ):
        raise ValueError("monitor state contains invalid Agent Bounties work")
    seen_freelancer = payload.get("seen_freelancer_fingerprints", {})
    if not isinstance(seen_freelancer, dict) or any(
        not isinstance(key, str)
        or not key
        or not isinstance(fingerprint, str)
        or not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
        for key, fingerprint in seen_freelancer.items()
    ):
        raise ValueError("monitor state contains invalid Freelancer work")
    return payload


def write_private_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists() and (path.is_symlink() or not path.is_file()):
            raise ValueError("refusing unsafe monitor state path")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def build_state(
    observation: dict[str, Any],
    previous: dict[str, Any] | None,
    *,
    taskbounty_observation: dict[str, Any] | None = None,
    agentbounties_observation: dict[str, Any] | None = None,
    freelancer_observation: dict[str, Any] | None = None,
    checked_at: str | None = None,
) -> dict[str, Any]:
    rows = observation.get("bounties")
    pages_read = observation.get("pages_read")
    if not isinstance(rows, list) or not isinstance(pages_read, int) or pages_read < 1:
        raise ValueError("Bounty observation is invalid")
    current = {row["bounty_id"]: row["version"] for row in rows}
    if len(current) != len(rows):
        raise ValueError("Bounty observation contains duplicate IDs")
    taskbounty_observation = taskbounty_observation or {
        "tasks": [],
        "pages_read": 1,
    }
    taskbounty_rows = taskbounty_observation.get("tasks")
    taskbounty_pages = taskbounty_observation.get("pages_read")
    if (
        not isinstance(taskbounty_rows, list)
        or not isinstance(taskbounty_pages, int)
        or taskbounty_pages != 1
    ):
        raise ValueError("TaskBounty observation is invalid")
    taskbounty_current: dict[str, str] = {}
    for row in taskbounty_rows:
        if not isinstance(row, dict):
            raise ValueError("TaskBounty observation is invalid")
        task_id = row.get("task_id")
        fingerprint = row.get("fingerprint")
        if (
            not isinstance(task_id, str)
            or not task_id
            or not isinstance(fingerprint, str)
            or not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
        ):
            raise ValueError("TaskBounty observation is invalid")
        if task_id in taskbounty_current:
            raise ValueError("TaskBounty observation contains duplicate IDs")
        taskbounty_current[task_id] = fingerprint
    previous_seen = dict(previous["seen_bounty_versions"]) if previous else {}
    previous_taskbounty_seen = (
        dict(previous["seen_taskbounty_fingerprints"])
        if previous and "seen_taskbounty_fingerprints" in previous
        else {}
    )
    taskbounty_baseline_created = not (
        previous and "seen_taskbounty_fingerprints" in previous
    )
    agentbounties_observation = agentbounties_observation or {
        "bounties": [],
        "pages_read": 1,
    }
    agentbounties_rows = agentbounties_observation.get("bounties")
    agentbounties_pages = agentbounties_observation.get("pages_read")
    if (
        not isinstance(agentbounties_rows, list)
        or not isinstance(agentbounties_pages, int)
        or agentbounties_pages != 1
    ):
        raise ValueError("Agent Bounties observation is invalid")
    agentbounties_current: dict[str, str] = {}
    for row in agentbounties_rows:
        if not isinstance(row, dict):
            raise ValueError("Agent Bounties observation is invalid")
        bounty_id = row.get("bounty_id")
        fingerprint = row.get("fingerprint")
        if (
            not isinstance(bounty_id, str)
            or not bounty_id
            or not isinstance(fingerprint, str)
            or not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
            or not isinstance(row.get("profitable_before_gas_and_risk"), bool)
        ):
            raise ValueError("Agent Bounties observation is invalid")
        if bounty_id in agentbounties_current:
            raise ValueError("Agent Bounties observation contains duplicate IDs")
        agentbounties_current[bounty_id] = fingerprint
    previous_agentbounties_seen = (
        dict(previous["seen_agentbounties_fingerprints"])
        if previous and "seen_agentbounties_fingerprints" in previous
        else {}
    )
    agentbounties_baseline_created = not (
        previous and "seen_agentbounties_fingerprints" in previous
    )
    freelancer_observation = freelancer_observation or {
        "projects": [],
        "pages_read": 1,
        "projects_considered": 0,
    }
    freelancer_rows = freelancer_observation.get("projects")
    freelancer_pages = freelancer_observation.get("pages_read")
    freelancer_considered = freelancer_observation.get("projects_considered")
    if (
        not isinstance(freelancer_rows, list)
        or freelancer_pages != 1
        or isinstance(freelancer_considered, bool)
        or not isinstance(freelancer_considered, int)
        or freelancer_considered < len(freelancer_rows)
    ):
        raise ValueError("Freelancer observation is invalid")
    freelancer_current: dict[str, str] = {}
    for row in freelancer_rows:
        if not isinstance(row, dict):
            raise ValueError("Freelancer observation is invalid")
        project_id = row.get("project_id")
        fingerprint = row.get("fingerprint")
        if (
            isinstance(project_id, bool)
            or not isinstance(project_id, int)
            or project_id < 1
            or not isinstance(fingerprint, str)
            or not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
        ):
            raise ValueError("Freelancer observation is invalid")
        key = str(project_id)
        if key in freelancer_current:
            raise ValueError("Freelancer observation contains duplicate IDs")
        freelancer_current[key] = fingerprint
    previous_freelancer_seen = (
        dict(previous["seen_freelancer_fingerprints"])
        if previous and "seen_freelancer_fingerprints" in previous
        else {}
    )
    freelancer_baseline_created = not (
        previous and "seen_freelancer_fingerprints" in previous
    )
    alerts = []
    if previous is not None:
        for row in rows:
            old_version = previous_seen.get(row["bounty_id"])
            if old_version is None or row["version"] > old_version:
                alerts.append(
                    {
                        "kind": "available_bounty_changed"
                        if old_version
                        else "new_available_bounty",
                        **row,
                        "action": (
                            "Open the current terms and attachments for private fit review; "
                            "do not comment, claim, message, or submit automatically."
                        ),
                    }
                )
    if not taskbounty_baseline_created:
        for row in taskbounty_rows:
            old_fingerprint = previous_taskbounty_seen.get(row["task_id"])
            if old_fingerprint is None or row["fingerprint"] != old_fingerprint:
                alerts.append(
                    {
                        "kind": (
                            "taskbounty_task_changed"
                            if old_fingerprint
                            else "new_taskbounty_task"
                        ),
                        "provider": "taskbounty",
                        **row,
                        "action": (
                            "Open the current public issue, reward, competition, terms, "
                            "and payout eligibility for private fit review; do not register, "
                            "claim, fork, message, submit, or configure payout automatically."
                        ),
                    }
                )
    if not agentbounties_baseline_created:
        for row in agentbounties_rows:
            old_fingerprint = previous_agentbounties_seen.get(row["bounty_id"])
            if (
                (old_fingerprint is None or row["fingerprint"] != old_fingerprint)
                and row["profitable_before_gas_and_risk"]
            ):
                alerts.append(
                    {
                        "kind": (
                            "agentbounties_work_changed"
                            if old_fingerprint
                            else "new_agentbounties_work"
                        ),
                        "provider": "agentbounties",
                        **row,
                        "action": (
                            "Recheck canonical chain state, immutable terms, exact reward, "
                            "claim bond, deadline, gas, and wallet policy for private fit review; "
                            "do not register, claim, sign, approve, fund, message, submit, or "
                            "configure payout automatically."
                        ),
                    }
                )
    if not freelancer_baseline_created:
        for row in freelancer_rows:
            key = str(row["project_id"])
            old_fingerprint = previous_freelancer_seen.get(key)
            if old_fingerprint is None or row["fingerprint"] != old_fingerprint:
                alerts.append(
                    {
                        "kind": (
                            "freelancer_project_changed"
                            if old_fingerprint
                            else "new_freelancer_candidate"
                        ),
                        "provider": "freelancer",
                        **row,
                        "action": (
                            "Open the current official listing for private fit, duplicate, "
                            "scope, client, fee, and account-gate review; do not bid, message, "
                            "download files, accept terms, fund an account, or begin work "
                            "automatically."
                        ),
                    }
                )
    seen = dict(previous_seen)
    for bounty_id, version in current.items():
        seen[bounty_id] = max(version, seen.get(bounty_id, 0))
    seen_taskbounty = dict(previous_taskbounty_seen)
    seen_taskbounty.update(taskbounty_current)
    seen_agentbounties = dict(previous_agentbounties_seen)
    seen_agentbounties.update(agentbounties_current)
    seen_freelancer = dict(previous_freelancer_seen)
    seen_freelancer.update(freelancer_current)
    return {
        "version": 4,
        "initialized": True,
        "checked_at": checked_at or utc_now(),
        "baseline_created": previous is None,
        "taskbounty_baseline_created": taskbounty_baseline_created,
        "agentbounties_baseline_created": agentbounties_baseline_created,
        "freelancer_baseline_created": freelancer_baseline_created,
        "available_bounties": rows,
        "taskbounty_open_tasks": taskbounty_rows,
        "agentbounties_claimable_work": agentbounties_rows,
        "freelancer_candidate_projects": freelancer_rows,
        "seen_bounty_versions": dict(sorted(seen.items())),
        "seen_taskbounty_fingerprints": dict(sorted(seen_taskbounty.items())),
        "seen_agentbounties_fingerprints": dict(sorted(seen_agentbounties.items())),
        "seen_freelancer_fingerprints": dict(sorted(seen_freelancer.items())),
        "alerts": alerts,
        "summary": {
            "available_bounties": len(rows),
            "taskbounty_open_tasks": len(taskbounty_rows),
            "agentbounties_claimable_work": len(agentbounties_rows),
            "agentbounties_profitable_before_gas_and_risk": sum(
                1
                for row in agentbounties_rows
                if row["profitable_before_gas_and_risk"]
            ),
            "new_or_updated_alerts": len(alerts),
            "trybounty_pages_read": pages_read,
            "taskbounty_pages_read": taskbounty_pages,
            "agentbounties_pages_read": agentbounties_pages,
            "freelancer_candidate_projects": len(freelancer_rows),
            "freelancer_projects_considered": freelancer_considered,
            "freelancer_pages_read": freelancer_pages,
        },
        "policy": {
            "http_method": "GET",
            "taskbounty_public_feed_requires_authentication": False,
            "agentbounties_canonical_feed_requires_authentication": False,
            "freelancer_public_feed_requires_authentication": False,
            "api_credentials_persisted_in_state": False,
            "raw_attachments_requested": False,
            "comments_or_messages_written": False,
            "claims_created": False,
            "submissions_created": False,
            "freelancer_bids_created": False,
            "accounts_registered": False,
            "payout_methods_configured": False,
            "wallet_addresses_persisted_in_state": False,
            "wallet_signatures_requested": False,
            "chain_transactions_broadcast": False,
            "available_work_is_not_a_lead": True,
            "available_work_is_not_revenue": True,
        },
    }


def monitor_once(
    *,
    credentials_path: Path = DEFAULT_CREDENTIALS,
    state_path: Path = DEFAULT_STATE,
    root: Path = ROOT,
    opener: Opener = urlopen,
    taskbounty_opener: Opener | None = None,
    agentbounties_opener: Opener | None = None,
    freelancer_opener: Opener | None = None,
    checked_at: str | None = None,
) -> dict[str, Any]:
    state_path = validate_local_path(state_path, root=root, suffix=".json")
    previous = load_state(state_path)
    api_key = load_api_key(credentials_path)
    observation = fetch_available_bounties(api_key, opener=opener)
    taskbounty_observation = fetch_taskbounty_open_tasks(
        opener=taskbounty_opener or opener
    )
    agentbounties_observation = fetch_agentbounties_claimable_work(
        opener=agentbounties_opener or opener
    )
    freelancer_observation = fetch_freelancer_candidate_projects(
        opener=freelancer_opener or opener
    )
    report = build_state(
        observation,
        previous,
        taskbounty_observation=taskbounty_observation,
        agentbounties_observation=agentbounties_observation,
        freelancer_observation=freelancer_observation,
        checked_at=checked_at,
    )
    write_private_json(state_path, report)
    return report


@contextmanager
def monitor_lock(path: Path = DEFAULT_LOCK):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    os.chmod(path, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Bounty marketplace monitor is already running") from exc
        yield
    finally:
        os.close(descriptor)


def monitor_loop(interval_minutes: int, **kwargs: Any) -> None:
    if interval_minutes < MINIMUM_INTERVAL_MINUTES:
        raise ValueError(
            f"Bounty marketplace interval must be at least {MINIMUM_INTERVAL_MINUTES} minutes"
        )
    with monitor_lock():
        while True:
            try:
                report = monitor_once(**kwargs)
                print(
                    json.dumps(report, ensure_ascii=False, sort_keys=True), flush=True
                )
            except Exception:
                print(
                    json.dumps(
                        {
                            "checked_at": utc_now(),
                            "error": "Bounty marketplace read failed",
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
            time.sleep(interval_minutes * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    once = subparsers.add_parser("once")
    once.add_argument("--credentials", type=Path, default=DEFAULT_CREDENTIALS)
    once.add_argument("--state", type=Path, default=DEFAULT_STATE)
    loop = subparsers.add_parser("loop")
    loop.add_argument("--credentials", type=Path, default=DEFAULT_CREDENTIALS)
    loop.add_argument("--state", type=Path, default=DEFAULT_STATE)
    loop.add_argument("--interval-minutes", type=int, default=MINIMUM_INTERVAL_MINUTES)
    status = subparsers.add_parser("status")
    status.add_argument("--state", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args()
    if args.command == "once":
        print(
            json.dumps(
                monitor_once(credentials_path=args.credentials, state_path=args.state),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "loop":
        monitor_loop(
            args.interval_minutes,
            credentials_path=args.credentials,
            state_path=args.state,
        )
        return 0
    state_path = validate_local_path(args.state, suffix=".json")
    payload = load_state(state_path)
    if payload is None:
        raise SystemExit("Bounty marketplace monitor has no state yet")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
