#!/usr/bin/env python3
"""Watch direct replies to one allowlisted public Reddit comment.

The monitor uses an unauthenticated GET of Reddit's public HTML.  It parses only
``thingid`` and ``parentid`` attributes from ``shreddit-comment`` start tags;
comment bodies and authors are neither collected nor persisted.  New activity
creates a manual-review alert and can never send a reply or become lead/revenue
evidence by itself.
"""

from __future__ import annotations

import argparse
import codecs
import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parent
CAMPAIGN_PATH = ROOT / "campaigns" / "mcp-boundary-review.json"
DEFAULT_STATE = ROOT / ".local" / "reddit-reply-monitor-state.json"
DEFAULT_STATUS = ROOT / ".local" / "reddit-reply-monitor-status.json"
DEFAULT_LOG = ROOT / ".local" / "reddit-reply-monitor.jsonl"
DEFAULT_LOCK = ROOT / ".local" / "reddit-reply-monitor.lock"
DEFAULT_CDP = "http://127.0.0.1:9436"
MINIMUM_INTERVAL_MINUTES = 60
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024
USER_AGENT = (
    "LazyingArt-LazyPromotion/1.0 "
    "(read-only direct-reply monitor; contact: contact@lazying.art)"
)
ALLOWLISTED_TARGET_URL = (
    "https://www.reddit.com/r/mcp/comments/1we4buv/comment/p9cgosi/"
)
ID_PATTERN = re.compile(r"^[a-z0-9]+$")
SUBREDDIT_PATTERN = re.compile(r"^[A-Za-z0-9_]{2,21}$")
FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")
Opener = Callable[..., Any]


class RedditMonitorError(RuntimeError):
    """A sanitized public-read failure."""

    def __init__(self, reason: str, *, layout_unknown: bool = False):
        super().__init__(reason)
        self.reason = reason
        self.layout_unknown = layout_unknown


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_target_url(value: str) -> dict[str, str]:
    """Validate and canonicalize one exact public Reddit comment permalink."""
    parsed = urlsplit(str(value or "").strip())
    try:
        has_port = parsed.port is not None
    except ValueError as exc:
        raise ValueError(
            "Reddit target must be one plain HTTPS www.reddit.com URL"
        ) from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != "www.reddit.com"
        or has_port
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Reddit target must be one plain HTTPS www.reddit.com URL")
    parts = [part for part in parsed.path.split("/") if part]
    if not (
        len(parts) == 6
        and parts[0] == "r"
        and parts[2] == "comments"
        and SUBREDDIT_PATTERN.fullmatch(parts[1])
        and ID_PATTERN.fullmatch(parts[3])
        and parts[4]
        and parts[4] not in {".", ".."}
        and ID_PATTERN.fullmatch(parts[5])
    ):
        raise ValueError("Reddit target must identify one exact public comment")
    subreddit, post_id, slug, comment_id = parts[1], parts[3], parts[4], parts[5]
    canonical_path = f"/r/{subreddit}/comments/{post_id}/{slug}/{comment_id}/"
    return {
        "url": urlunsplit(("https", "www.reddit.com", canonical_path, "", "")),
        "subreddit": subreddit,
        "post_id": post_id,
        "comment_id": comment_id,
    }


def load_allowlisted_target(path: Path = CAMPAIGN_PATH) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        value = payload["channels"]["community_replies"][
            "reddit_kin_graph_design"
        ]["public_reply"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError("the allowlisted Reddit campaign target is unavailable") from exc
    target = parse_target_url(str(value))
    if target["url"] != ALLOWLISTED_TARGET_URL:
        raise ValueError("the Reddit campaign target is not allowlisted")
    return target


class NoRedirectHandler(HTTPRedirectHandler):
    """Prevent a public read from following the allowlisted URL elsewhere."""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        return None


def open_without_redirects(request: Request, *, timeout: int) -> Any:
    """Open one request without a cookie jar, auth handler, or redirect handler."""
    return build_opener(NoRedirectHandler()).open(request, timeout=timeout)


class RedditCommentMetadataParser(HTMLParser):
    """Collect comment relationship attributes while discarding all text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.records: list[dict[str, str]] = []
        self.invalid_comment_tags = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.casefold() != "shreddit-comment":
            return
        values = {str(name).casefold(): str(value or "") for name, value in attrs}
        thing_id = values.get("thingid", "")
        parent_id = values.get("parentid", "")
        if not thing_id or not parent_id:
            self.invalid_comment_tags += 1
            return
        self.records.append({"thingid": thing_id, "parentid": parent_id})

    def handle_data(self, data: str) -> None:
        # Deliberately ignore titles, authors, comment bodies, and script data.
        return


def reply_fingerprint(*, post_id: str, comment_id: str, reply_id: str) -> str:
    identity = "\0".join(
        ("reddit-direct-reply-v1", post_id, comment_id, reply_id)
    )
    return hashlib.sha256(identity.encode("ascii")).hexdigest()


def parse_comment_metadata(
    parser: RedditCommentMetadataParser, *, target: dict[str, str]
) -> dict[str, Any]:
    if parser.invalid_comment_tags:
        raise RedditMonitorError(
            "Reddit comment markup is incomplete", layout_unknown=True
        )
    seen_ids: set[str] = set()
    records = []
    for raw in parser.records:
        thing_id = raw.get("thingid", "")
        parent_id = raw.get("parentid", "")
        if (
            not re.fullmatch(r"t1_[a-z0-9]+", thing_id)
            or not re.fullmatch(r"t[13]_[a-z0-9]+", parent_id)
        ):
            raise RedditMonitorError(
                "Reddit comment markup changed", layout_unknown=True
            )
        if thing_id in seen_ids:
            raise RedditMonitorError(
                "Reddit returned duplicate comment metadata", layout_unknown=True
            )
        seen_ids.add(thing_id)
        records.append((thing_id, parent_id))

    expected_target = f"t1_{target['comment_id']}"
    expected_post = f"t3_{target['post_id']}"
    target_rows = [row for row in records if row[0] == expected_target]
    if len(target_rows) != 1 or target_rows[0][1] != expected_post:
        raise RedditMonitorError(
            "Reddit target comment was not present in the public page",
            layout_unknown=True,
        )

    reply_ids = sorted(
        thing_id.removeprefix("t1_")
        for thing_id, parent_id in records
        if parent_id == expected_target and thing_id != expected_target
    )
    fingerprints = [
        reply_fingerprint(
            post_id=target["post_id"],
            comment_id=target["comment_id"],
            reply_id=reply_id,
        )
        for reply_id in reply_ids
    ]
    return {
        "target_url": target["url"],
        "post_id": target["post_id"],
        "comment_id": target["comment_id"],
        "direct_reply_count": len(fingerprints),
        "direct_reply_fingerprints": fingerprints,
    }


def _response_content_type(response: Any) -> str:
    headers = getattr(response, "headers", None)
    if headers is None:
        return ""
    getter = getattr(headers, "get_content_type", None)
    if callable(getter):
        return str(getter() or "").casefold()
    return str(headers.get("Content-Type", "")).split(";", 1)[0].strip().casefold()


def fetch_public_comment(
    target: dict[str, str], *, opener: Opener = open_without_redirects
) -> dict[str, Any]:
    """Read public HTML once and return relationship metadata only."""
    request = Request(
        target["url"],
        headers={"Accept": "text/html", "User-Agent": USER_AGENT},
        method="GET",
    )
    parser = RedditCommentMetadataParser()
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    total = 0
    try:
        with opener(request, timeout=30) as response:
            status = int(getattr(response, "status", 200))
            if status != 200:
                raise RedditMonitorError(f"Reddit public read returned HTTP {status}")
            final_url = str(getattr(response, "geturl", lambda: target["url"])())
            try:
                final_target = parse_target_url(final_url)
            except ValueError as exc:
                raise RedditMonitorError("Reddit redirected the public read") from exc
            if final_target != target:
                raise RedditMonitorError("Reddit redirected the public read")
            if _response_content_type(response) != "text/html":
                raise RedditMonitorError("Reddit public read did not return HTML")
            while True:
                chunk = response.read(READ_CHUNK_BYTES)
                if not chunk:
                    break
                if not isinstance(chunk, bytes):
                    raise RedditMonitorError("Reddit public read returned invalid bytes")
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    raise RedditMonitorError("Reddit public page exceeded the size cap")
                parser.feed(decoder.decode(chunk))
            parser.feed(decoder.decode(b"", final=True))
            parser.close()
    except HTTPError as exc:
        if exc.code == 429:
            raise RedditMonitorError(
                "Reddit rate-limited the public read; wait for the next scheduled pass"
            ) from exc
        raise RedditMonitorError(
            f"Reddit public read returned HTTP {exc.code}"
        ) from exc
    except (OSError, URLError) as exc:
        raise RedditMonitorError("Reddit public read did not complete") from exc
    except UnicodeError as exc:
        raise RedditMonitorError("Reddit public read was not valid text") from exc
    return parse_comment_metadata(parser, target=target)


def _reject_symlink_components(root: Path, path: Path) -> None:
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError("runtime path must not contain symbolic links")


def validate_runtime_path(path: Path, *, root: Path = ROOT, suffix: str) -> Path:
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
    _reject_symlink_components(root, candidate)
    return candidate


def read_private_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("monitor state must be a regular file")
    metadata = path.stat()
    if stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1:
        raise ValueError("monitor state must be private and singly linked")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("monitor state is invalid") from exc
    if not isinstance(payload, dict):
        raise ValueError("monitor state is invalid")
    return payload


def validate_previous_state(
    payload: dict[str, Any] | None, *, target: dict[str, str]
) -> dict[str, Any] | None:
    if payload is None:
        return None
    if (
        payload.get("version") != 1
        or payload.get("initialized") is not True
        or payload.get("target_url") != target["url"]
        or payload.get("post_id") != target["post_id"]
        or payload.get("comment_id") != target["comment_id"]
    ):
        raise ValueError("monitor state does not match the allowlisted target")
    for key in ("current_reply_fingerprints", "seen_reply_fingerprints"):
        values = payload.get(key)
        if (
            not isinstance(values, list)
            or len(values) != len(set(values))
            or any(
                not isinstance(value, str)
                or not FINGERPRINT_PATTERN.fullmatch(value)
                for value in values
            )
        ):
            raise ValueError("monitor state contains invalid reply fingerprints")
    if set(payload["current_reply_fingerprints"]) - set(
        payload["seen_reply_fingerprints"]
    ):
        raise ValueError("current replies must be included in seen replies")
    return payload


def write_private_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
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
        if path.exists() or path.is_symlink():
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ValueError("refusing to replace an unsafe runtime file")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def append_private_log(path: Path, payload: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("monitor log must be a regular singly linked file")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
            descriptor = -1
            stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def build_success(
    observation: dict[str, Any],
    previous: dict[str, Any] | None,
    *,
    checked_at: str,
    source: str = "public_html",
) -> tuple[dict[str, Any], dict[str, Any]]:
    current = list(observation["direct_reply_fingerprints"])
    previous_seen = set(previous["seen_reply_fingerprints"]) if previous else set()
    baseline_created = previous is None
    new = [] if baseline_created else sorted(set(current) - previous_seen)
    seen = sorted(previous_seen | set(current))
    common = {
        "version": 1,
        "initialized": True,
        "checked_at": checked_at,
        "target_url": observation["target_url"],
        "post_id": observation["post_id"],
        "comment_id": observation["comment_id"],
        "baseline_created": baseline_created,
        "current_direct_reply_count": len(current),
        "new_direct_reply_count": len(new),
        "review_required": bool(new),
        "layout_unknown": False,
        "available": True,
        "source": source,
        "policy": {
            "http_method": "GET" if source == "public_html" else None,
            "authentication_used": False if source == "public_html" else None,
            "cookies_sent": False if source == "public_html" else None,
            "public_http_method": "GET" if source == "public_html" else None,
            "browser_session_used": source == "visible_browser",
            "authentication_data_persisted": False,
            "cookies_persisted": False,
            "comment_bodies_persisted": False,
            "authors_persisted": False,
            "automatic_reply": False,
            "activity_is_lead_evidence": False,
            "activity_is_revenue_evidence": False,
        },
    }
    state = {
        **common,
        "current_reply_fingerprints": current,
        "seen_reply_fingerprints": seen,
    }
    status = {
        **common,
        "action": (
            "Open the exact public Reddit comment for visible review; do not reply "
            "automatically or record a lead."
            if new
            else "No direct-reply review is required."
        ),
    }
    return state, status


def parse_visible_comment_metadata(
    records: list[dict[str, str]], *, target: dict[str, str]
) -> dict[str, Any]:
    """Resolve direct children from Reddit's ordered visible depth metadata."""
    normalized: list[tuple[str, int]] = []
    expected_post = f"t3_{target['post_id']}"
    for record in records:
        thing_id = str(record.get("thingid") or "")
        post_id = str(record.get("postid") or "")
        depth = str(record.get("depth") or "")
        if (
            not re.fullmatch(r"t1_[a-z0-9]+", thing_id)
            or post_id != expected_post
            or not depth.isdigit()
        ):
            raise RedditMonitorError(
                "Reddit visible comment markup changed", layout_unknown=True
            )
        normalized.append((thing_id, int(depth)))
    expected_target = f"t1_{target['comment_id']}"
    target_indexes = [
        index for index, (thing_id, _depth) in enumerate(normalized)
        if thing_id == expected_target
    ]
    if len(target_indexes) != 1:
        raise RedditMonitorError(
            "Reddit target comment was not present in the visible page",
            layout_unknown=True,
        )
    target_index = target_indexes[0]
    target_depth = normalized[target_index][1]
    replies: list[str] = []
    for thing_id, depth in normalized[target_index + 1:]:
        if depth <= target_depth:
            break
        if depth == target_depth + 1:
            replies.append(thing_id.removeprefix("t1_"))
    fingerprints = [
        reply_fingerprint(
            post_id=target["post_id"],
            comment_id=target["comment_id"],
            reply_id=reply_id,
        )
        for reply_id in replies
    ]
    return {
        "target_url": target["url"],
        "post_id": target["post_id"],
        "comment_id": target["comment_id"],
        "direct_reply_count": len(fingerprints),
        "direct_reply_fingerprints": fingerprints,
    }


def collect_visible_comment(*, target: dict[str, str], cdp: str) -> dict[str, Any]:
    """Read hierarchy attributes from one already-open visible Reddit tab."""
    from playwright.sync_api import sync_playwright

    import browser as browser_tools

    with browser_tools.browser_operation_lock():
        with sync_playwright() as playwright:
            connected = playwright.chromium.connect_over_cdp(cdp)
            candidates = []
            for context in connected.contexts:
                for page in context.pages:
                    try:
                        page_target = parse_target_url(page.url)
                    except ValueError:
                        continue
                    if page_target == target:
                        candidates.append(page)
            if len(candidates) != 1:
                raise RuntimeError(
                    "exactly one allowlisted Reddit comment tab must be open"
                )
            page = candidates[0]
            page.bring_to_front()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
            records = page.locator("shreddit-comment").evaluate_all(
                """elements => elements.map(element => ({
                    thingid: element.getAttribute('thingid') || '',
                    postid: element.getAttribute('postid') || '',
                    depth: element.getAttribute('depth') || ''
                }))"""
            )
    return parse_visible_comment_metadata(records, target=target)


def visible_monitor_once(
    *,
    campaign_path: Path = CAMPAIGN_PATH,
    state_path: Path = DEFAULT_STATE,
    status_path: Path = DEFAULT_STATUS,
    log_path: Path = DEFAULT_LOG,
    root: Path = ROOT,
    cdp: str = DEFAULT_CDP,
    checked_at: str | None = None,
    collector: Callable[..., dict[str, Any]] = collect_visible_comment,
) -> dict[str, Any]:
    """Clear a layout alert through one visible, read-only browser inspection."""
    checked_at = checked_at or utc_now()
    state_path = validate_runtime_path(state_path, root=root, suffix=".json")
    status_path = validate_runtime_path(status_path, root=root, suffix=".json")
    log_path = validate_runtime_path(log_path, root=root, suffix=".jsonl")
    target = load_allowlisted_target(campaign_path)
    previous = validate_previous_state(read_private_json(state_path), target=target)
    observation = collector(target=target, cdp=cdp)
    state, status = build_success(
        observation,
        previous,
        checked_at=checked_at,
        source="visible_browser",
    )
    state_path = validate_runtime_path(state_path, root=root, suffix=".json")
    status_path = validate_runtime_path(status_path, root=root, suffix=".json")
    log_path = validate_runtime_path(log_path, root=root, suffix=".jsonl")
    write_private_json(state_path, state)
    write_private_json(status_path, status)
    append_private_log(log_path, status)
    return status


def failure_status(
    error: RedditMonitorError, *, target: dict[str, str], checked_at: str
) -> dict[str, Any]:
    return {
        "version": 1,
        "checked_at": checked_at,
        "target_url": target["url"],
        "available": False,
        "layout_unknown": error.layout_unknown,
        "review_required": error.layout_unknown,
        "prior_state_preserved": True,
        "error": error.reason,
        "action": (
            "Review the exact public comment visibly before changing the monitor."
            if error.layout_unknown
            else "Wait for the next scheduled read; do not retry immediately."
        ),
        "policy": {
            "http_method": "GET",
            "authentication_used": False,
            "cookies_sent": False,
            "comment_bodies_persisted": False,
            "authors_persisted": False,
            "automatic_reply": False,
            "activity_is_lead_evidence": False,
            "activity_is_revenue_evidence": False,
        },
    }


def monitor_once(
    *,
    campaign_path: Path = CAMPAIGN_PATH,
    state_path: Path = DEFAULT_STATE,
    status_path: Path = DEFAULT_STATUS,
    log_path: Path = DEFAULT_LOG,
    root: Path = ROOT,
    opener: Opener = open_without_redirects,
    checked_at: str | None = None,
) -> dict[str, Any]:
    checked_at = checked_at or utc_now()
    state_path = validate_runtime_path(state_path, root=root, suffix=".json")
    status_path = validate_runtime_path(status_path, root=root, suffix=".json")
    log_path = validate_runtime_path(log_path, root=root, suffix=".jsonl")
    target = load_allowlisted_target(campaign_path)
    previous = validate_previous_state(read_private_json(state_path), target=target)
    try:
        observation = fetch_public_comment(target, opener=opener)
    except RedditMonitorError as exc:
        status = failure_status(exc, target=target, checked_at=checked_at)
        write_private_json(status_path, status)
        append_private_log(log_path, status)
        return status
    state, status = build_success(observation, previous, checked_at=checked_at)
    # Revalidate destinations after the network read before changing local state.
    state_path = validate_runtime_path(state_path, root=root, suffix=".json")
    status_path = validate_runtime_path(status_path, root=root, suffix=".json")
    log_path = validate_runtime_path(log_path, root=root, suffix=".jsonl")
    write_private_json(state_path, state)
    write_private_json(status_path, status)
    append_private_log(log_path, status)
    return status


@contextmanager
def monitor_lock(path: Path = DEFAULT_LOCK) -> Iterator[None]:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("monitor lock must not be a symbolic link")
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("monitor lock must be a regular private file")
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Reddit reply monitor is already running") from exc
        yield
    finally:
        os.close(descriptor)


def monitor_loop(interval_minutes: int, **kwargs: Any) -> None:
    if interval_minutes < MINIMUM_INTERVAL_MINUTES:
        raise ValueError("Reddit reply monitor interval must be at least 60 minutes")
    lock_path = kwargs.pop("lock_path", DEFAULT_LOCK)
    with monitor_lock(lock_path):
        while True:
            status = monitor_once(**kwargs)
            print(json.dumps(status, ensure_ascii=False, sort_keys=True), flush=True)
            time.sleep(interval_minutes * 60)


def status_summary(path: Path = DEFAULT_STATUS) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"available": False}
    allowed = {
        "checked_at",
        "available",
        "baseline_created",
        "current_direct_reply_count",
        "new_direct_reply_count",
        "review_required",
        "layout_unknown",
        "prior_state_preserved",
        "automatic_reply",
    }
    summary = {key: payload[key] for key in allowed if key in payload}
    policy = payload.get("policy")
    if isinstance(policy, dict):
        summary["automatic_reply"] = bool(policy.get("automatic_reply"))
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("once", help="Run one unauthenticated public read.")
    visible = subparsers.add_parser(
        "visible-once", help="Recover one layout alert from the isolated browser."
    )
    visible.add_argument("--cdp", default=DEFAULT_CDP)
    subparsers.add_parser("status", help="Print aggregate local status.")
    continuous = subparsers.add_parser("loop", help="Repeat conservative reads.")
    continuous.add_argument(
        "--interval-minutes", type=int, default=MINIMUM_INTERVAL_MINUTES
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "once":
            report = monitor_once()
        elif args.command == "visible-once":
            report = visible_monitor_once(cdp=args.cdp)
        elif args.command == "status":
            report = status_summary()
        else:
            monitor_loop(args.interval_minutes)
            return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"available": False, "error": str(exc)}), flush=True)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.get("available") is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
