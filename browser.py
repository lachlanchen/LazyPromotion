#!/usr/bin/env python3
"""Drive one visible Chrome tab over CDP for discovery and review-gated replies."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse

from playwright.sync_api import Locator, Page, sync_playwright

import promotion


ROOT = Path(__file__).resolve().parent
DEFAULT_CDP = "http://127.0.0.1:9436"
EVIDENCE = ROOT / ".local" / "evidence"
PLATFORM_HOSTS = {
    "reddit": {"reddit.com", "www.reddit.com"},
    "x": {"x.com", "www.x.com", "twitter.com", "www.twitter.com"},
    "instagram": {"instagram.com", "www.instagram.com"},
}


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def current_page(browser) -> Page:
    contexts = browser.contexts
    if not contexts:
        raise RuntimeError("CDP browser has no context")
    pages = contexts[0].pages
    return pages[-1] if pages else contexts[0].new_page()


def page_for(
    browser,
    *,
    platform: str = "",
    target_url: str = "",
    create: bool = True,
    front: bool = True,
) -> Page:
    contexts = browser.contexts
    if not contexts:
        raise RuntimeError("CDP browser has no context")
    context = contexts[0]
    hosts = PLATFORM_HOSTS.get(platform, set())
    target_host = (urlparse(target_url).hostname or "").casefold()
    if target_host:
        hosts = {*hosts, target_host}
    for page in context.pages:
        if (urlparse(page.url).hostname or "").casefold() in hosts:
            if front:
                page.bring_to_front()
            return page
    if not create:
        label = platform or target_url or "requested"
        raise RuntimeError(f"no open {label} page was found")
    page = context.new_page()
    if front:
        page.bring_to_front()
    return page


def candidate_destination(candidate_id: str) -> dict:
    db = promotion.open_db()
    candidate = promotion.row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone())
    if not candidate:
        raise ValueError(f"candidate not found: {candidate_id}")
    return candidate


def evidence(page: Page, operation: str) -> str:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / f"{stamp()}-{re.sub(r'[^a-z0-9-]+', '-', operation.casefold()).strip('-')}.png"
    page.screenshot(path=str(path), full_page=False)
    return str(path)


def wait_ready(page: Page) -> None:
    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(2500)


def search_url(platform: str, query: str) -> str:
    if platform == "reddit":
        return f"https://www.reddit.com/search/?q={quote_plus(query)}&sort=new&type=posts"
    if platform == "x":
        return f"https://x.com/search?q={quote_plus(query)}&src=typed_query&f=live"
    tag = re.sub(r"[^A-Za-z0-9_]", "", query.lstrip("#").replace(" ", ""))
    if not tag:
        raise ValueError("Instagram discovery requires one hashtag-like query")
    return f"https://www.instagram.com/explore/tags/{tag}/"


def extract_reddit(page: Page, limit: int) -> list[dict[str, str]]:
    rows = page.locator("shreddit-post").evaluate_all(
        """(nodes, limit) => nodes.slice(0, limit).map((n) => ({
          url: n.getAttribute('content-href') || n.getAttribute('permalink') ||
            n.querySelector('a[href*="/comments/"]')?.href || '',
          author: n.getAttribute('author') || '',
          published_at: n.getAttribute('created-timestamp') || '',
          comment_count: n.getAttribute('comment-count') || '0',
          source_score: n.getAttribute('score') || '0',
          body: [n.getAttribute('post-title') || '', n.innerText || ''].join(' ').trim()
        }))""",
        limit,
    )
    if rows:
        return rows
    return page.locator('a[href*="/comments/"]').evaluate_all(
        """(nodes, limit) => nodes.slice(0, limit).map((a) => ({
          url: a.href, author: '', published_at: '', comment_count: '0', source_score: '0',
          body: (a.innerText || a.closest('article')?.innerText || '').trim()
        }))""",
        limit,
    )


def extract_x(page: Page, limit: int) -> list[dict[str, str]]:
    return page.locator('article[data-testid="tweet"]').evaluate_all(
        """(nodes, limit) => nodes.slice(0, limit).map((n) => ({
          url: n.querySelector('a[href*="/status/"]')?.href || '',
          author: n.querySelector('[data-testid="User-Name"]')?.innerText || '',
          body: n.innerText || ''
        }))""",
        limit,
    )


def extract_instagram(page: Page, limit: int) -> list[dict[str, str]]:
    return page.locator("article").evaluate_all(
        """(nodes, limit) => nodes.slice(0, limit).map((n) => ({
          url: n.querySelector('a[href*="/p/"], a[href*="/reel/"]')?.href || '',
          author: n.querySelector('header a')?.innerText || '',
          body: n.innerText || ''
        }))""",
        limit,
    )


def safe_int(value: object) -> int:
    try:
        return int(str(value or "0").replace(",", ""))
    except ValueError:
        return 0


def dedupe(rows: list[dict[str, str]], limit: int) -> list[dict[str, object]]:
    result = []
    seen = set()
    for row in rows:
        url = str(row.get("url") or "").split("?")[0]
        body = promotion.compact(str(row.get("body") or ""))
        if not url or not body or url in seen:
            continue
        seen.add(url)
        result.append({
            "url": url,
            "author": promotion.compact(str(row.get("author") or "")),
            "body": body,
            "published_at": str(row.get("published_at") or ""),
            "comment_count": safe_int(row.get("comment_count")),
            "source_score": safe_int(row.get("source_score")),
        })
        if len(result) >= limit:
            break
    return result


def discover(page: Page, platform: str, query: str, limit: int) -> dict[str, object]:
    target = search_url(platform, query)
    page.goto(target, wait_until="domcontentloaded", timeout=45000)
    wait_ready(page)
    if platform == "reddit":
        rows = extract_reddit(page, limit)
    elif platform == "x":
        rows = extract_x(page, limit)
    else:
        rows = extract_instagram(page, limit)
    rows = dedupe(rows, limit)
    db = promotion.open_db()
    candidates = [
        promotion.ingest_candidate(
            db, platform=platform, source_url=row["url"], body=row["body"],
            author=row["author"], query=query, published_at=row["published_at"],
            comment_count=row["comment_count"], source_score=row["source_score"],
        )
        for row in rows
    ]
    screenshot = evidence(page, f"search-{platform}")
    return {
        "ok": True,
        "platform": platform,
        "query": query,
        "url": page.url,
        "title": page.title(),
        "found": len(candidates),
        "candidates": candidates,
        "screenshot": screenshot,
    }


def inspect_candidate(page: Page, candidate_id: str) -> dict[str, object]:
    db = promotion.open_db()
    candidate = promotion.row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone())
    if not candidate:
        raise ValueError(f"candidate not found: {candidate_id}")
    page.goto(candidate["source_url"], wait_until="domcontentloaded", timeout=45000)
    wait_ready(page)
    author = candidate["author"]
    community = ""
    rules_url = ""
    if candidate["platform"] == "reddit":
        root = page.locator("shreddit-post").first
        if not root.count():
            raise RuntimeError("Reddit post root was not found")
        title = root.get_attribute("post-title") or ""
        author = root.get_attribute("author") or author
        community = root.get_attribute("subreddit-prefixed-name") or ""
        published_at = root.get_attribute("created-timestamp") or ""
        comment_count = safe_int(root.get_attribute("comment-count"))
        source_score = safe_int(root.get_attribute("score"))
        content = root.locator("shreddit-post-text-body").first
        body = content.inner_text() if content.count() else root.inner_text()
        if community.startswith("r/"):
            rules_url = f"https://www.reddit.com/{community}/about/rules/"
    elif candidate["platform"] == "x":
        root = page.locator('article[data-testid="tweet"]').first
        if not root.count():
            raise RuntimeError("X post root was not found")
        title = ""
        body = root.inner_text()
        name = root.locator('[data-testid="User-Name"]').first
        author = name.inner_text() if name.count() else author
    else:
        root = page.locator("article").first
        if not root.count():
            raise RuntimeError("Instagram post root was not found")
        title = ""
        body = root.inner_text()
        name = root.locator("header a").first
        author = name.inner_text() if name.count() else author
    full_body = promotion.compact(f"{title} {body}")
    updated = promotion.ingest_candidate(
        db,
        platform=candidate["platform"],
        source_url=candidate["source_url"],
        body=full_body,
        author=author,
        query=candidate["query"],
        published_at=published_at if candidate["platform"] == "reddit" else candidate.get("published_at", ""),
        comment_count=comment_count if candidate["platform"] == "reddit" else candidate.get("comment_count", 0),
        source_score=source_score if candidate["platform"] == "reddit" else candidate.get("source_score", 0),
    )
    screenshot = evidence(page, f"inspect-{candidate['platform']}-{candidate_id}")
    return {
        "ok": True,
        "candidate": updated,
        "community": community,
        "rules_url": rules_url,
        "url": page.url,
        "title": page.title(),
        "screenshot": screenshot,
    }


def visible_first(locators: list[Locator]) -> Locator:
    for locator in locators:
        count = min(locator.count(), 8)
        for index in range(count):
            item = locator.nth(index)
            try:
                if item.is_visible():
                    return item
            except Exception:
                continue
    raise RuntimeError("no visible reply composer was found")


def composer(page: Page, platform: str, *, activate: bool = True) -> Locator:
    if platform == "reddit":
        # Reddit replaces its textarea-like trigger with a Lexical editor. Find
        # only an editor inside the active composer so validation never reads
        # the now-hidden trigger after activation.
        locators = [
            page.locator('shreddit-composer [contenteditable="true"][role="textbox"]'),
            page.locator("shreddit-composer textarea"),
        ]
    elif platform == "x":
        locators = [page.locator('[data-testid="tweetTextarea_0"]'), page.locator('div[contenteditable="true"][role="textbox"]')]
    else:
        locators = [page.locator('textarea[placeholder*="comment" i]'), page.locator('textarea[aria-label*="comment" i]')]
    try:
        return visible_first(locators)
    except RuntimeError:
        if not activate:
            raise
        if platform == "reddit":
            triggers = [
                page.locator('comment-composer-host faceplate-textarea-input[data-testid="trigger-button"]'),
                page.locator('textarea[placeholder*="conversation" i]'),
                page.get_by_role("button", name=re.compile(r"^(add a )?comment$|^reply$", re.I)),
            ]
        elif platform == "x":
            triggers = [page.locator('[data-testid="reply"]')]
        else:
            triggers = [page.get_by_role("button", name=re.compile(r"comment", re.I))]
        trigger = visible_first(triggers)
        trigger.click()
        page.wait_for_timeout(700)
        return composer(page, platform, activate=False)


def fill_composer(locator: Locator, body: str) -> None:
    tag = locator.evaluate("el => el.tagName.toLowerCase()")
    if tag == "textarea":
        locator.fill(body)
    else:
        locator.click()
        locator.press("Control+A")
        locator.fill(body)


def composer_text(locator: Locator) -> str:
    tag = locator.evaluate("el => el.tagName.toLowerCase()")
    value = locator.input_value() if tag in {"textarea", "input"} else locator.inner_text()
    return promotion.compact(value)


def load_candidate_and_draft(candidate_id: str, draft_id: str) -> tuple[dict, dict]:
    db = promotion.open_db()
    candidate = promotion.row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone())
    draft = promotion.row_dict(db.execute("SELECT * FROM drafts WHERE id=? AND candidate_id=?", (draft_id, candidate_id)).fetchone())
    if not candidate or not draft:
        raise ValueError("candidate/draft pair not found")
    return candidate, draft


def prepare_reply(page: Page, candidate_id: str, draft_id: str) -> dict[str, object]:
    candidate, draft = load_candidate_and_draft(candidate_id, draft_id)
    page.goto(candidate["source_url"], wait_until="domcontentloaded", timeout=45000)
    wait_ready(page)
    target = composer(page, candidate["platform"])
    fill_composer(target, draft["body"])
    if composer_text(target) != promotion.compact(draft["body"]):
        raise RuntimeError("visible composer text does not match the reviewed draft")
    screenshot = evidence(page, f"prepared-{candidate['platform']}-{candidate_id}")
    db = promotion.open_db()
    now = promotion.utc_now()
    db.execute("UPDATE drafts SET status='prepared', updated_at=? WHERE id=?", (now, draft_id))
    db.execute(
        "INSERT INTO events(candidate_id, draft_id, kind, detail, created_at) VALUES (?, ?, 'reply_prepared', ?, ?)",
        (candidate_id, draft_id, json.dumps({"url": page.url, "screenshot": screenshot}, sort_keys=True), now),
    )
    db.commit()
    return {
        "ok": True,
        "state": "prepared_not_sent",
        "candidate_id": candidate_id,
        "draft_id": draft_id,
        "url": page.url,
        "title": page.title(),
        "screenshot": screenshot,
        "next": "Review the visible composer, then create a short-lived approval token before send.",
    }


def submit_button(page: Page, platform: str) -> Locator:
    if platform == "reddit":
        return visible_first([
            page.get_by_role("button", name=re.compile(r"^(comment|reply)$", re.I)),
            page.locator('button[type="submit"]'),
        ])
    if platform == "x":
        return visible_first([page.locator('[data-testid="tweetButton"]'), page.locator('[data-testid="tweetButtonInline"]')])
    return visible_first([page.get_by_role("button", name=re.compile(r"^post$", re.I))])


def send_reply(page: Page, candidate_id: str, draft_id: str, token: str, confirm: bool) -> dict[str, object]:
    if not confirm:
        raise ValueError("send requires --confirm-public-write")
    candidate, draft = load_candidate_and_draft(candidate_id, draft_id)
    db = promotion.open_db()
    promotion.validate_approval(db, draft_id, token)
    if candidate["source_url"].split("?")[0] not in page.url.split("?")[0]:
        raise RuntimeError("the active tab is not the approved candidate page; run prepare again")
    target = composer(page, candidate["platform"])
    if composer_text(target) != promotion.compact(draft["body"]):
        raise RuntimeError("visible composer differs from the approved draft")
    # Rich-text editors can leave link or formatting popovers above the submit
    # control. Dismiss the transient UI, then re-resolve and revalidate the
    # composer before the one public click.
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    target = composer(page, candidate["platform"], activate=False)
    if composer_text(target) != promotion.compact(draft["body"]):
        raise RuntimeError("visible composer changed while dismissing editor popovers")
    button = submit_button(page, candidate["platform"])
    if not button.is_enabled():
        raise RuntimeError("visible submit button is disabled")
    before = page.url
    button.click(no_wait_after=True, timeout=10000)
    if candidate["platform"] == "reddit":
        excerpt = promotion.compact(draft["body"])[:120]
        posted = page.locator("shreddit-comment").filter(has_text=excerpt).first
        try:
            posted.wait_for(state="visible", timeout=20000)
        except Exception as exc:
            raise RuntimeError(
                "the public click was issued, but Reddit did not show the posted comment; "
                "do not retry until the destination is inspected manually"
            ) from exc
    else:
        page.wait_for_timeout(2500)
    screenshot = evidence(page, f"sent-{candidate['platform']}-{candidate_id}")
    detail = {"url_before": before, "url_after": page.url, "screenshot": screenshot}
    promotion.mark_sent(db, draft_id, token, detail)
    return {"ok": True, "state": "sent", "candidate_id": candidate_id, "draft_id": draft_id, **detail}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp", default=DEFAULT_CDP)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    opening = sub.add_parser("open")
    opening.add_argument("url")
    search = sub.add_parser("search")
    search.add_argument("--platform", choices=("reddit", "x", "instagram"), required=True)
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=12)
    search.add_argument("--background", action="store_true", help="do not take focus from the active review/login tab")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("candidate_id")
    inspect.add_argument("--background", action="store_true", help="inspect without taking focus from the active tab")
    prepare = sub.add_parser("prepare")
    prepare.add_argument("candidate_id")
    prepare.add_argument("draft_id")
    send = sub.add_parser("send")
    send.add_argument("candidate_id")
    send.add_argument("draft_id")
    send.add_argument("--approval-token", required=True)
    send.add_argument("--confirm-public-write", action="store_true", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(args.cdp)
        if args.command == "status":
            tabs = [
                {"url": page.url, "title": page.title()}
                for context in browser.contexts for page in context.pages
            ]
            emit({"ok": True, "cdp": args.cdp, "pages": tabs})
        elif args.command == "open":
            page = page_for(browser, target_url=args.url)
            page.goto(args.url, wait_until="domcontentloaded", timeout=45000)
            wait_ready(page)
            emit({"ok": True, "url": page.url, "title": page.title(), "screenshot": evidence(page, "open")})
        elif args.command == "search":
            page = page_for(browser, platform=args.platform, front=not args.background)
            emit(discover(page, args.platform, args.query, max(1, min(args.limit, 50))))
        elif args.command == "inspect":
            candidate = candidate_destination(args.candidate_id)
            page = page_for(
                browser,
                platform=candidate["platform"],
                target_url=candidate["source_url"],
                front=not args.background,
            )
            emit(inspect_candidate(page, args.candidate_id))
        elif args.command == "prepare":
            candidate = candidate_destination(args.candidate_id)
            page = page_for(browser, platform=candidate["platform"], target_url=candidate["source_url"])
            emit(prepare_reply(page, args.candidate_id, args.draft_id))
        elif args.command == "send":
            candidate = candidate_destination(args.candidate_id)
            page = page_for(
                browser,
                platform=candidate["platform"],
                target_url=candidate["source_url"],
                create=False,
            )
            emit(send_reply(page, args.candidate_id, args.draft_id, args.approval_token, args.confirm_public_write))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        emit({"ok": False, "error": str(exc), "type": type(exc).__name__})
        raise SystemExit(1)
