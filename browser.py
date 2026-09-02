#!/usr/bin/env python3
"""Drive one visible Chrome tab over CDP for discovery and review-gated replies."""

from __future__ import annotations

import argparse
import fcntl
import json
import re
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

from playwright.sync_api import Locator, Page, sync_playwright

import promotion


ROOT = Path(__file__).resolve().parent
DEFAULT_CDP = "http://127.0.0.1:9436"
EVIDENCE = ROOT / ".local" / "evidence"
BROWSER_LOCK_PATH = ROOT / ".local" / "runtime" / "browser-operation.lock"
DISCOVERY_PLAN = ROOT / "discovery-plan.json"
PLATFORM_HOSTS = {
    "reddit": {"reddit.com", "www.reddit.com"},
    "x": {"x.com", "www.x.com", "twitter.com", "www.twitter.com"},
    "instagram": {"instagram.com", "www.instagram.com"},
    "hackernews": {"news.ycombinator.com", "hn.algolia.com"},
}


@contextmanager
def browser_operation_lock(
    *,
    timeout_seconds: float = 900.0,
    poll_seconds: float = 0.2,
):
    """Serialize all automation against the single shared CDP browser stack."""
    if timeout_seconds < 0 or poll_seconds <= 0:
        raise ValueError("browser lock timing must be positive")
    BROWSER_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    stream = BROWSER_LOCK_PATH.open("a+", encoding="utf-8")
    deadline = time.monotonic() + timeout_seconds
    try:
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("timed out waiting for the shared browser operation lock")
                time.sleep(min(poll_seconds, max(0.0, deadline - time.monotonic())))
        yield
    finally:
        try:
            fcntl.flock(stream, fcntl.LOCK_UN)
        finally:
            stream.close()


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
    try:
        page.screenshot(
            path=str(path),
            full_page=False,
            animations="disabled",
            caret="hide",
            timeout=10000,
        )
    except Exception as exc:
        # Screenshots are valuable evidence, but discovery is still useful when
        # a graphics-heavy page or CDP renderer cannot capture one in time.
        failure = path.with_suffix(".error.txt")
        failure.write_text(promotion.compact(str(exc))[:2000], encoding="utf-8")
        return ""
    return str(path)


def wait_ready(page: Page) -> None:
    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(2500)


def search_url(platform: str, query: str, content_kind: str = "posts") -> str:
    if platform == "reddit":
        if content_kind not in {"posts", "comments"}:
            raise ValueError(f"unsupported Reddit content kind: {content_kind}")
        return (
            f"https://www.reddit.com/search/?q={quote_plus(query)}&sort=new"
            f"&type={content_kind}"
        )
    if platform == "x":
        return f"https://x.com/search?q={quote_plus(query)}&src=typed_query&f=live"
    if platform == "hackernews":
        if content_kind not in {"posts", "comments"}:
            raise ValueError(f"unsupported Hacker News content kind: {content_kind}")
        result_type = "story" if content_kind == "posts" else "comment"
        return (
            "https://hn.algolia.com/?dateRange=pastMonth&page=0&prefix=false"
            f"&query={quote_plus(query)}&sort=byDate&type={result_type}"
        )
    tag = re.sub(r"[^A-Za-z0-9_]", "", query.lstrip("#").replace(" ", ""))
    if not tag:
        raise ValueError("Instagram discovery requires one hashtag-like query")
    return f"https://www.instagram.com/explore/tags/{tag}/"


def hackernews_comment_query(query: str) -> str:
    """Turn an Ask HN story query into a topic query for discussion comments."""
    topic = re.sub(r"^Ask\s+HN:?\s*", "", query, flags=re.I).strip()
    return topic or query


def load_discovery_plan(path: Path = DISCOVERY_PLAN) -> dict[str, object]:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("version") != 1 or not isinstance(plan.get("queries"), dict):
        raise ValueError("discovery plan must contain version 1 and a queries object")
    known_projects = {project["id"] for project in promotion.load_catalog()["projects"]}
    project_topics = plan.get("project_topics", {})
    if not isinstance(project_topics, dict):
        raise ValueError("discovery plan project_topics must be an object")
    for project_id, topic in project_topics.items():
        if project_id not in known_projects:
            raise ValueError(f"unknown project topic override: {project_id}")
        if not promotion.compact(str(topic)):
            raise ValueError(f"empty project topic override: {project_id}")
    for platform in PLATFORM_HOSTS:
        queries = plan["queries"].get(platform)
        if not isinstance(queries, list):
            raise ValueError(f"discovery plan is missing a {platform} query list")
        for item in queries:
            if not isinstance(item, dict):
                raise ValueError(f"{platform} discovery entries must be objects")
            if item.get("project_id") not in known_projects:
                raise ValueError(f"unknown project in discovery plan: {item.get('project_id')}")
            if not promotion.compact(str(item.get("query") or "")):
                raise ValueError(f"{platform} discovery entry has an empty query")
            if not promotion.compact(str(item.get("purpose") or "")):
                raise ValueError(f"{platform} discovery entry has an empty purpose")
            if "comment_query" in item and not promotion.compact(str(item["comment_query"])):
                raise ValueError(f"{platform} discovery entry has an empty comment query")
            groups = item.get("required_body_groups", [])
            if not isinstance(groups, list) or any(
                not isinstance(group, list)
                or not group
                or any(not promotion.compact(str(value)) for value in group)
                for group in groups
            ):
                raise ValueError(
                    f"{platform} discovery entry has invalid required body groups"
                )
            excluded = item.get("excluded_body_any", [])
            if not isinstance(excluded, list) or any(
                not promotion.compact(str(value)) for value in excluded
            ):
                raise ValueError(
                    f"{platform} discovery entry has invalid body exclusions"
                )
    return plan


def automatic_query(platform: str, project: dict[str, object], topic_override: str = "") -> str:
    overridden = promotion.normalized(topic_override).strip()
    if overridden:
        need = f'"{overridden}"' if " " in overridden else overridden
        if platform == "reddit":
            return f"{need} (help OR advice OR recommend)"
        if platform == "x":
            return f"{need} (help OR advice OR recommend) -filter:retweets"
        if platform == "hackernews":
            return f"Ask HN {need}"
        return ""
    project_name = promotion.normalized(str(project["name"])).strip()
    keywords = sorted({
        promotion.normalized(str(keyword)).strip()
        for keyword in project.get("keywords", [])
        if promotion.normalized(str(keyword)).strip()
    })
    phrases = [keyword for keyword in keywords if " " in keyword and keyword != project_name]
    if phrases:
        topic = sorted(phrases, key=lambda value: (abs(len(value.split()) - 2), -len(value), value))[0]
        need = f'"{topic}"'
    else:
        singles = sorted(
            (keyword for keyword in keywords if keyword != project_name),
            key=lambda value: (-len(value), value),
        )
        need = " ".join(singles[:2])
    if not need:
        return ""
    if platform == "reddit":
        return f"{need} (help OR advice OR recommend)"
    if platform == "x":
        return f"{need} (help OR advice OR recommend) -filter:retweets"
    if platform == "hackernews":
        return f"Ask HN {need}"
    return ""


def discovery_queries(platform: str) -> list[dict[str, str]]:
    plan = load_discovery_plan()
    planned = [dict(item) for item in plan["queries"][platform]]
    covered = {item["project_id"] for item in planned}
    project_topics = plan.get("project_topics", {})
    if platform not in {"reddit", "x", "hackernews"}:
        return planned
    for project in promotion.load_catalog()["projects"]:
        if project["id"] in covered:
            continue
        query = automatic_query(platform, project, str(project_topics.get(project["id"], "")))
        if not query:
            continue
        planned.append({
            "project_id": str(project["id"]),
            "query": query,
            "purpose": f"Automatically derived from public GitHub metadata for {project['name']}",
        })
    return planned


def discovery_query_lanes(platform: str) -> dict[str, list[dict[str, str]]]:
    """Split reviewed high-yield routes from generated repository coverage."""
    plan = load_discovery_plan()
    core = [dict(item) for item in plan["queries"][platform]]
    all_queries = discovery_queries(platform)
    return {"core": core, "long_tail": all_queries[len(core):]}


def route_body_qualified(body: str, route: dict[str, object]) -> bool:
    """Apply reviewed evidence gates after a search result has been hydrated."""
    haystack = promotion.normalized(body)
    groups = route.get("required_body_groups", [])
    for group in groups if isinstance(groups, list) else []:
        if not any(
            promotion.keyword_present(promotion.normalized(str(term)).strip(), haystack)
            for term in group
        ):
            return False
    excluded = route.get("excluded_body_any", [])
    return not any(
        promotion.keyword_present(promotion.normalized(str(term)).strip(), haystack)
        for term in excluded if promotion.normalized(str(term)).strip()
    )


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
    rows = page.locator('[data-testid="search-post-unit"]').evaluate_all(
        """(nodes, limit) => nodes.slice(0, limit).map((n) => {
          const tracking = n.querySelector('search-telemetry-tracker[data-faceplate-tracking-context]');
          let context = {};
          try { context = JSON.parse(tracking?.getAttribute('data-faceplate-tracking-context') || '{}'); }
          catch (_) {}
          const counters = [...n.querySelectorAll('[data-testid="search-counter-row"] faceplate-number')]
            .map(el => el.getAttribute('number') || '0');
          const title = n.querySelector('[data-testid="post-title-text"]');
          return {
            url: title?.href || n.querySelector('[data-testid="post-title"]')?.href || '',
            author: context.profile?.name || '',
            published_at: n.querySelector('time[datetime]')?.getAttribute('datetime') || '',
            source_score: counters[0] || '0',
            comment_count: counters[1] || '0',
            body: (title?.innerText || '').trim()
          };
        })""",
        limit,
    )
    if rows:
        return rows
    return page.locator('main a[data-testid="post-title-text"][href*="/comments/"]').evaluate_all(
        """(nodes, limit) => nodes.slice(0, limit).map((a) => ({
          url: a.href, author: '', published_at: '', comment_count: '0', source_score: '0',
          body: (a.innerText || a.closest('article')?.innerText || '').trim()
        }))""",
        limit,
    )


def extract_reddit_comments(page: Page, limit: int) -> list[dict[str, str]]:
    return page.locator('[data-testid="search-sdui-comment-unit"]').evaluate_all(
        """(nodes, limit) => nodes.slice(0, limit).map((n) => {
          const tracker = n.closest('search-telemetry-tracker[view-events="search/view/comment"]');
          let context = {};
          try { context = JSON.parse(tracker?.getAttribute('data-faceplate-tracking-context') || '{}'); }
          catch (_) {}
          const contentBox = n.querySelector('[data-testid="search-comment-content"]');
          const content = contentBox?.querySelector('[id^="search-comment-"][id$="-post-rtjson-content"]');
          const permalink = contentBox?.querySelector('a[aria-labelledby^="comment-content-"][href*="/comments/"]');
          const author = contentBox?.querySelector('faceplate-hovercard[data-id="user-hover-card"] a');
          const time = contentBox?.querySelector('time[datetime]');
          const score = contentBox?.querySelector('p faceplate-number');
          return {
            url: permalink?.href || '',
            author: (author?.innerText || '').trim(),
            published_at: time?.getAttribute('datetime') || '',
            comment_count: '0',
            source_score: score?.getAttribute('number') || '0',
            body: (content?.innerText || '').trim(),
            comment_id: context.comment?.id || ''
          };
        }).filter(row => row.url && row.body)""",
        limit,
    )


def extract_x(page: Page, limit: int) -> list[dict[str, str]]:
    return page.locator('article[data-testid="tweet"]').evaluate_all(
        """(nodes, limit) => nodes.slice(0, limit).map((n) => {
          const count = (testid) => {
            const label = n.querySelector(`[data-testid="${testid}"]`)?.getAttribute('aria-label') || '';
            return label.match(/[\\d,]+/)?.[0] || '0';
          };
          return {
            url: n.querySelector('a[href*="/status/"]')?.href || '',
            author: n.querySelector('[data-testid="User-Name"]')?.innerText || '',
            published_at: n.querySelector('time[datetime]')?.getAttribute('datetime') || '',
            comment_count: count('reply'),
            source_score: count('like'),
            body: n.innerText || ''
          };
        })""",
        limit,
    )


def extract_instagram(page: Page, limit: int) -> list[dict[str, str]]:
    return page.locator('a[href*="/p/"], a[href*="/reel/"]').evaluate_all(
        """(nodes, limit) => nodes.slice(0, limit * 4).map((a) => ({
          url: a.href || '',
          author: '',
          published_at: '',
          comment_count: '0',
          source_score: '0',
          body: (a.querySelector('img[alt]')?.getAttribute('alt') || a.innerText || '').trim()
        }))""",
        limit,
    )


def instagram_destination_ids(url: str) -> tuple[str, str]:
    parts = [part for part in urlparse(url).path.split("/") if part]
    if len(parts) < 2 or parts[0] not in {"p", "reel"}:
        return "", ""
    shortcode = parts[1]
    try:
        comment_start = parts.index("c", 2)
    except ValueError:
        return shortcode, ""
    comment_id = parts[comment_start + 1] if len(parts) > comment_start + 1 else ""
    return shortcode, comment_id


def instagram_comment_id(url: str) -> str:
    return instagram_destination_ids(url)[1]


def extract_instagram_comments(page: Page, limit: int) -> list[dict[str, str]]:
    return page.locator('a[href*="/c/"]').evaluate_all(
        """(anchors, limit) => anchors.map((anchor) => {
          let root = anchor;
          const isCommentRoot = (node) => {
            const hasReply = [...node.querySelectorAll('[role="button"], button')]
              .some(button => (button.innerText || '').trim() === 'Reply');
            const hasProfile = [...node.querySelectorAll('a[href^="/"]')]
              .some(link => /^\/[A-Za-z0-9._]+\/$/.test(link.getAttribute('href') || ''));
            const hasBody = [...node.querySelectorAll('span[dir="auto"]')]
              .some(span => !span.querySelector('span') && !span.closest('a'));
            return hasReply && hasProfile && hasBody;
          };
          while (root && !isCommentRoot(root)) {
            root = root.parentElement;
          }
          if (!root) return null;
          const profile = [...root.querySelectorAll('a[href^="/"]')]
            .find(link => /^\/[A-Za-z0-9._]+\/$/.test(link.getAttribute('href') || ''));
          const author = (profile?.innerText || '').trim();
          const time = anchor.querySelector('time[datetime]');
          const bodyParts = [...root.querySelectorAll('span[dir="auto"]')]
            .filter(span => !span.querySelector('span') && !span.closest('a'))
            .map(span => (span.innerText || '').trim())
            .filter(text => text && text !== 'Reply' && text !== author);
          const body = bodyParts.sort((a, b) => b.length - a.length)[0] || '';
          return {
            url: anchor.href || '',
            author,
            published_at: time?.getAttribute('datetime') || '',
            comment_count: '0',
            source_score: '0',
            source_kind: 'comment',
            body
          };
        }).filter(row => row && row.url && row.author && row.body).slice(0, limit)""",
        limit,
    )


def instagram_post_data(page: Page) -> dict[str, str]:
    post_time = page.locator("time[datetime]").first
    if not post_time.count():
        raise RuntimeError("Instagram post timestamp was not found")
    data = post_time.evaluate(
        """(time) => {
          const container = time.parentElement?.parentElement?.parentElement;
          const profile = [...(container?.querySelectorAll('a[href^="/"]') || [])]
            .find(a => /^\/[A-Za-z0-9._]+\/$/.test(a.getAttribute('href') || ''));
          return {
            author: (profile?.innerText || '').trim(),
            body: (container?.innerText || '').trim(),
            published_at: time.getAttribute('datetime') || ''
          };
        }"""
    )
    if not promotion.compact(str(data.get("body") or "")):
        raise RuntimeError("Instagram post caption was not found")
    return data


def hydrate_instagram_rows(page: Page, rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    posts = []
    comments = []
    for row in rows[:limit]:
        try:
            page.goto(row["url"], wait_until="domcontentloaded", timeout=45000)
            wait_ready(page)
            posts.append({**row, **instagram_post_data(page), "source_kind": "post"})
            comments.extend(extract_instagram_comments(page, limit))
        except Exception:
            continue
    # Comment questions carry more explicit consent than parent captions, so
    # preserve them first when the per-query candidate limit is applied.
    return comments + posts


def extract_hackernews(page: Page, limit: int, content_kind: str = "posts") -> list[dict[str, str]]:
    if content_kind == "comments":
        return page.locator("article.Story").evaluate_all(
            """(nodes, limit) => nodes.map((n) => {
              const meta = n.querySelector('.Story_meta');
              const metaText = meta?.innerText || '';
              const permalink = [...(meta?.querySelectorAll('a') || [])]
                .find(a => /^https:\/\/news\.ycombinator\.com\/item\?id=\d+/.test(a.href));
              return {
                url: permalink?.href || '',
                author: meta?.querySelector('a[href*="/user?id="]')?.innerText || '',
                published_at: '',
                comment_count: metaText.match(/(\d+)\s+comments?/i)?.[1] || '0',
                source_score: '0',
                body: (n.querySelector('.Story_comment')?.innerText || '').trim()
              };
            }).filter(row => row.url && row.body).slice(0, limit)""",
            limit,
        )
    return page.locator("article.Story").evaluate_all(
        """(nodes, limit) => nodes.map((n) => {
          const titleBox = n.querySelector('.Story_title');
          const title = (titleBox?.innerText || '').trim();
          const titleLink = [...(titleBox?.querySelectorAll('a') || [])]
            .find(a => a.href.includes('news.ycombinator.com/item?id='));
          const meta = n.querySelector('.Story_meta');
          const metaText = meta?.innerText || '';
          const author = meta?.querySelector('a[href*="/user?id="]')?.innerText || '';
          return {
            url: titleLink?.href || '',
            author,
            published_at: '',
            comment_count: metaText.match(/(\\d+)\\s+comments?/i)?.[1] || '0',
            source_score: metaText.match(/(\\d+)\\s+points?/i)?.[1] || '0',
            body: [title, n.querySelector('.Story_comment')?.innerText || ''].join(' ').trim(),
            is_ask: /^Ask HN:/i.test(title)
          };
        }).filter(row => row.is_ask).slice(0, limit)""",
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
        raw_url = str(row.get("url") or "")
        if re.match(r"^https://news\.ycombinator\.com/item\?id=\d+", raw_url):
            url = raw_url.split("&", 1)[0]
        else:
            url = raw_url.split("?", 1)[0]
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
            "source_kind": str(row.get("source_kind") or "post"),
        })
        if len(result) >= limit:
            break
    return result


def discover(
    page: Page,
    platform: str,
    query: str,
    limit: int,
    content_kind: str = "posts",
) -> dict[str, object]:
    if content_kind != "posts" and platform not in {"reddit", "hackernews"}:
        raise ValueError(f"{platform} does not support {content_kind} discovery")
    target = search_url(platform, query, content_kind)
    page.goto(target, wait_until="domcontentloaded", timeout=45000)
    wait_ready(page)
    search_title = page.title()
    search_destination = page.url
    screenshot = evidence(page, f"search-{platform}-{content_kind}")
    if platform == "reddit":
        rows = extract_reddit_comments(page, limit) if content_kind == "comments" else extract_reddit(page, limit)
    elif platform == "x":
        rows = extract_x(page, limit)
    elif platform == "hackernews":
        rows = extract_hackernews(page, limit, content_kind)
    else:
        grid_rows = dedupe(extract_instagram(page, limit), limit)
        rows = hydrate_instagram_rows(page, grid_rows, limit)
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
    return {
        "ok": True,
        "platform": platform,
        "content_kind": content_kind,
        "query": query,
        "url": search_destination,
        "title": search_title,
        "found": len(candidates),
        "found_by_source_kind": {
            kind: sum(1 for row in rows if row["source_kind"] == kind)
            for kind in sorted({str(row["source_kind"]) for row in rows})
        },
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
        post_root = page.locator("shreddit-post").first
        if not post_root.count():
            raise RuntimeError("Reddit post root was not found")
        comment_id = reddit_comment_id(candidate["source_url"])
        if comment_id:
            root = page.locator(f'shreddit-comment[thingid="t1_{comment_id}"]').first
            if not root.count():
                raise RuntimeError("Reddit target comment was not found")
            title = ""
            author = root.get_attribute("author") or author
            published_at = root.get_attribute("created") or ""
            comment_count = reddit_direct_reply_count(
                reddit_comment_records(page), comment_id
            )
            source_score = safe_int(root.get_attribute("score"))
            content = root.locator(f"#t1_{comment_id}-comment-rtjson-content").first
            body = content.inner_text() if content.count() else ""
        else:
            root = post_root
            title = root.get_attribute("post-title") or ""
            author = root.get_attribute("author") or author
            published_at = root.get_attribute("created-timestamp") or ""
            comment_count = safe_int(root.get_attribute("comment-count"))
            source_score = safe_int(root.get_attribute("score"))
            content = root.locator("shreddit-post-text-body").first
            body = content.inner_text() if content.count() else root.inner_text()
        community = post_root.get_attribute("subreddit-prefixed-name") or ""
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
    elif candidate["platform"] == "instagram":
        title = ""
        comment_id = instagram_comment_id(candidate["source_url"])
        if comment_id:
            rows = extract_instagram_comments(page, 100)
            data = next(
                (row for row in rows if instagram_comment_id(row["url"]) == comment_id),
                None,
            )
            if not data:
                raise RuntimeError("Instagram target comment was not found")
        else:
            data = instagram_post_data(page)
        body = data["body"]
        author = data["author"] or author
        published_at = data["published_at"]
    else:
        story_root = page.locator(".titleline").first
        if story_root.count():
            title = story_root.inner_text()
            body_node = page.locator(".toptext").first
            body = body_node.inner_text() if body_node.count() else ""
            name = page.locator(".subtext .hnuser").first
            age = page.locator(".subtext .age").first
            score = page.locator(".subtext .score").first
            source_score = safe_int(score.inner_text().split()[0]) if score.count() else 0
        else:
            comment_root = page.locator("table.fatitem tr.athing").first
            if not comment_root.count():
                raise RuntimeError("Hacker News story or comment root was not found")
            title = ""
            body_node = comment_root.locator(".commtext").first
            body = body_node.inner_text() if body_node.count() else ""
            name = comment_root.locator(".hnuser").first
            age = comment_root.locator(".age").first
            source_score = 0
        author = name.inner_text() if name.count() else author
        published_at = (age.get_attribute("title") or "") if age.count() else ""
        comment_count = page.locator("tr.comtr").count()
        community = "Hacker News"
        rules_url = "https://news.ycombinator.com/newsguidelines.html"
    full_body = promotion.compact(f"{title} {body}")
    updated = promotion.ingest_candidate(
        db,
        platform=candidate["platform"],
        source_url=candidate["source_url"],
        body=full_body,
        author=author,
        query=candidate["query"],
        published_at=published_at if candidate["platform"] in {"reddit", "instagram", "hackernews"} else candidate.get("published_at", ""),
        comment_count=comment_count if candidate["platform"] in {"reddit", "hackernews"} else candidate.get("comment_count", 0),
        source_score=source_score if candidate["platform"] in {"reddit", "hackernews"} else candidate.get("source_score", 0),
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


def hydrate_candidates(page: Page, candidates: list[dict], limit: int) -> list[dict[str, object]]:
    hydrated = []
    for candidate in candidates:
        if len(hydrated) >= limit:
            break
        if candidate.get("status") != "discovered" or promotion.is_stale(str(candidate.get("published_at") or "")):
            continue
        try:
            result = inspect_candidate(page, str(candidate["id"]))
            hydrated.append({"ok": True, "candidate": result["candidate"], "community": result["community"]})
        except Exception as exc:
            hydrated.append({"ok": False, "candidate_id": candidate.get("id", ""), "error": str(exc)})
    return hydrated


def run_discovery_cycle(
    page: Page,
    platform: str,
    *,
    max_queries: int,
    limit_per_query: int,
    hydrate_per_query: int,
    start_query: int = 0,
    queries: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    queue = discovery_queries(platform) if queries is None else queries
    if queue:
        start_query %= len(queue)
        count = min(max_queries, len(queue))
        planned = (queue + queue)[start_query:start_query + count]
    else:
        start_query = 0
        planned = []
    results: list[dict[str, object]] = []
    eligible_ids: list[str] = []
    triage_ids: list[str] = []
    for item in planned:
        project_id = str(item["project_id"])
        query = str(item["query"])
        summary: dict[str, object] = {
            "project_id": project_id,
            "query": query,
            "purpose": item["purpose"],
        }
        try:
            searches = [("posts", query)]
            if platform == "reddit":
                searches.append(("comments", query))
            elif platform == "hackernews":
                comment_query = promotion.compact(
                    str(item.get("comment_query") or hackernews_comment_query(query))
                )
                searches.append(("comments", comment_query))
            discoveries = [
                discover(page, platform, search_query, limit_per_query, content_kind)
                for content_kind, search_query in searches
            ]
            found_candidates = [
                candidate
                for found in discoveries
                for candidate in found["candidates"]
            ]
            hydrated = [
                item
                for found in discoveries
                for item in hydrate_candidates(page, found["candidates"], hydrate_per_query)
            ]
            db = promotion.open_db()
            refreshed = [
                promotion.row_dict(db.execute("SELECT * FROM candidates WHERE id=?", (candidate["id"],)).fetchone())
                for candidate in found_candidates
            ]
            route_qualified = [
                candidate for candidate in refreshed
                if candidate and route_body_qualified(str(candidate.get("body") or ""), item)
            ]
            matching = [
                str(candidate["id"])
                for candidate in route_qualified
                if candidate.get("status") == "discovered"
                and int(candidate.get("score") or 0) >= 5
                and candidate.get("suggested_tool") == project_id
                and not promotion.is_stale(str(candidate.get("published_at") or ""))
            ]
            triageable = [
                str(candidate["id"])
                for candidate in route_qualified
                if candidate.get("status") == "discovered"
                and promotion.is_triageable_request(
                    str(candidate.get("platform") or ""),
                    str(candidate.get("source_url") or ""),
                    str(candidate.get("body") or ""),
                )
                and promotion.compact(str(candidate.get("author") or "")).casefold() not in promotion.BOT_AUTHORS
                and not promotion.is_stale(str(candidate.get("published_at") or ""))
            ]
            promotion.mark_triage_requested(db, triageable)
            eligible_ids.extend(candidate_id for candidate_id in matching if candidate_id not in eligible_ids)
            triage_ids.extend(candidate_id for candidate_id in triageable if candidate_id not in triage_ids)
            summary.update({
                "ok": True,
                "found": len(found_candidates),
                "found_by_kind": {
                    str(found["content_kind"]): int(found["found"])
                    for found in discoveries
                },
                "hydrated": len(hydrated),
                "route_qualified": len(route_qualified),
                "route_filtered": len(refreshed) - len(route_qualified),
                "hydrate_errors": [row for row in hydrated if not row["ok"]],
                "eligible_candidate_ids": matching,
                "triage_candidate_ids": triageable,
            })
        except Exception as exc:
            summary.update({"ok": False, "error": str(exc)})
        results.append(summary)
    note = ""
    if not planned and platform == "instagram":
        note = (
            "Instagram has no configured help-request queries: hashtag feeds mostly expose "
            "promotional posts, which are not sufficient consent for a project pitch."
        )
    return {
        "ok": all(result["ok"] for result in results),
        "platform": platform,
        "available_queries": len(queue),
        "start_query": start_query,
        "next_query": (start_query + len(results)) % len(queue) if queue else 0,
        "queries_run": len(results),
        "results": results,
        "eligible_candidate_ids": eligible_ids,
        "triage_candidate_ids": triage_ids,
        "next": "Run model triage on eligible candidates; this cycle never drafts or posts.",
        "note": note,
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
    elif platform == "hackernews":
        locators = [page.locator('form[action="comment"] textarea[name="text"]')]
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
    if candidate["platform"] in promotion.AI_COMMENT_BLOCKED_PLATFORMS:
        raise ValueError("Hacker News prohibits generated or AI-edited comments")
    page.goto(candidate["source_url"], wait_until="domcontentloaded", timeout=45000)
    wait_ready(page)
    comment_id = reddit_comment_id(candidate["source_url"]) if candidate["platform"] == "reddit" else ""
    if comment_id:
        root = page.locator(f'shreddit-comment[thingid="t1_{comment_id}"]').first
        if not root.count():
            raise RuntimeError("Reddit target comment was not found before composer activation")
        trigger = root.get_by_role("button", name=re.compile(r"^reply$", re.I)).first
        if not trigger.count():
            raise RuntimeError("Reddit target comment reply button was not found")
        trigger.click()
        page.wait_for_timeout(700)
        target = reddit_comment_composer(page, comment_id)
    elif candidate["platform"] == "instagram" and instagram_comment_id(candidate["source_url"]):
        target_comment_id = instagram_comment_id(candidate["source_url"])
        anchor = page.locator(f'a[href*="/c/{target_comment_id}/"]').first
        if not anchor.count():
            raise RuntimeError("Instagram target comment was not found before composer activation")
        root = anchor.locator(
            'xpath=ancestor::div[.//*[@role="button" and normalize-space(.)="Reply"]][1]'
        )
        trigger = root.get_by_role("button", name="Reply", exact=True).first
        if not trigger.count():
            raise RuntimeError("Instagram target comment reply button was not found")
        trigger.click()
        page.wait_for_timeout(700)
        target = composer(page, candidate["platform"], activate=False)
    else:
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


def reddit_destination_ids(url: str) -> tuple[str, str]:
    parts = [part for part in urlparse(url).path.split("/") if part]
    try:
        start = parts.index("comments")
    except ValueError:
        return "", ""
    post_id = parts[start + 1] if len(parts) > start + 1 else ""
    tail = parts[start + 2:]
    comment_id = tail[-1] if len(tail) >= 2 else ""
    return post_id, comment_id


def reddit_comment_id(url: str) -> str:
    return reddit_destination_ids(url)[1]


def reddit_comment_composer(page: Page, comment_id: str) -> Locator:
    if not re.fullmatch(r"[a-z0-9]+", comment_id, flags=re.I):
        raise ValueError("invalid Reddit comment id")
    host = f'shreddit-composer[aria-describedby="comment-composer-message-t1_{comment_id}"]'
    return visible_first([
        page.locator(f'{host} [contenteditable="true"][role="textbox"]'),
        page.locator(f"{host} textarea"),
    ])


def destination_matches(candidate_url: str, active_url: str, platform: str) -> bool:
    candidate_parsed = urlparse(candidate_url)
    active_parsed = urlparse(active_url)
    if candidate_parsed.hostname != active_parsed.hostname:
        return False
    if platform == "reddit":
        candidate_ids = reddit_destination_ids(candidate_url)
        active_ids = reddit_destination_ids(active_url)
        return bool(candidate_ids[0] and candidate_ids == active_ids)
    if platform == "hackernews":
        candidate_id = parse_qs(candidate_parsed.query).get("id", [""])[0]
        active_id = parse_qs(active_parsed.query).get("id", [""])[0]
        return bool(candidate_id and candidate_id == active_id)
    if platform == "instagram":
        candidate_ids = instagram_destination_ids(candidate_url)
        active_ids = instagram_destination_ids(active_url)
        return bool(candidate_ids[0] and candidate_ids == active_ids)
    candidate_base = candidate_url.split("?", 1)[0].rstrip("/")
    active_base = active_url.split("?", 1)[0].rstrip("/")
    return active_base == candidate_base or active_base.startswith(f"{candidate_base}/")


def reddit_posted_reply_selector(parent_comment_id: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+", parent_comment_id, flags=re.I):
        raise ValueError("invalid Reddit parent comment id")
    return (
        f'shreddit-comment[parentid="t1_{parent_comment_id}"] '
        '> details div[slot="comment"], '
        f'shreddit-comment[parentid="t1_{parent_comment_id}"] '
        '> div[slot="comment"]'
    )


def reddit_comment_records(page: Page) -> list[dict[str, str]]:
    """Read delivered Reddit comments without including any open composer."""
    return page.locator("shreddit-comment").evaluate_all(
        """nodes => nodes.map(node => ({
          thingid: node.getAttribute('thingid') || '',
          parentid: node.getAttribute('parentid') || '',
          body: (
            node.querySelector(':scope > details div[slot="comment"]')?.innerText ||
            node.querySelector(':scope > div[slot="comment"]')?.innerText ||
            ''
          ).trim()
        })).filter(row => row.thingid && row.body)"""
    )


def reddit_direct_reply_count(
    records: list[dict[str, str]], parent_comment_id: str
) -> int:
    """Count only delivered direct replies to one exact Reddit comment."""
    if not re.fullmatch(r"[a-z0-9]+", parent_comment_id, flags=re.I):
        raise ValueError("invalid Reddit parent comment id")
    expected_parent = f"t1_{parent_comment_id}"
    return sum(
        1
        for record in records
        if str(record.get("parentid") or "") == expected_parent
        and re.fullmatch(
            r"t1_[a-z0-9]+", str(record.get("thingid") or ""), flags=re.I
        )
        and promotion.compact(str(record.get("body") or ""))
    )


def reddit_delivery_ids(
    records: list[dict[str, str]],
    body: str,
    *,
    parent_comment_id: str = "",
) -> set[str]:
    """Return exact delivered comment IDs at the approved Reddit destination."""
    expected_body = promotion.compact(body)
    expected_parent = f"t1_{parent_comment_id}" if parent_comment_id else ""
    delivered = set()
    for record in records:
        thingid = str(record.get("thingid") or "")
        parentid = str(record.get("parentid") or "")
        if not re.fullmatch(r"t1_[a-z0-9]+", thingid, flags=re.I):
            continue
        if expected_parent and parentid != expected_parent:
            continue
        if not expected_parent and parentid.startswith("t1_"):
            continue
        if promotion.compact(str(record.get("body") or "")) == expected_body:
            delivered.add(thingid)
    return delivered


def submit_button(page: Page, platform: str, *, target: Locator | None = None) -> Locator:
    if platform == "reddit":
        if target is None:
            raise ValueError("Reddit submit requires the exact reviewed composer")
        host = target.locator("xpath=ancestor::shreddit-composer[1]")
        return visible_first([host.locator('button[type="submit"]')])
    if platform == "x":
        return visible_first([page.locator('[data-testid="tweetButton"]'), page.locator('[data-testid="tweetButtonInline"]')])
    if platform == "hackernews":
        return visible_first([page.locator('form[action="comment"] input[type="submit"]')])
    return visible_first([page.get_by_role("button", name=re.compile(r"^post$", re.I))])


def send_reply(page: Page, candidate_id: str, draft_id: str, token: str, confirm: bool) -> dict[str, object]:
    if not confirm:
        raise ValueError("send requires --confirm-public-write")
    candidate, draft = load_candidate_and_draft(candidate_id, draft_id)
    if candidate["platform"] in promotion.AI_COMMENT_BLOCKED_PLATFORMS:
        raise ValueError("Hacker News prohibits generated or AI-edited comments")
    db = promotion.open_db()
    promotion.validate_approval(db, draft_id, token)
    if not destination_matches(candidate["source_url"], page.url, candidate["platform"]):
        raise RuntimeError("the active tab is not the approved candidate page; run prepare again")
    target_comment_id = (
        reddit_comment_id(candidate["source_url"])
        if candidate["platform"] == "reddit" else ""
    )
    target = (
        reddit_comment_composer(page, target_comment_id)
        if target_comment_id else composer(page, candidate["platform"])
    )
    if composer_text(target) != promotion.compact(draft["body"]):
        raise RuntimeError("visible composer differs from the approved draft")
    # Rich-text editors can leave link or formatting popovers above the submit
    # control. Dismiss the transient UI, then re-resolve and revalidate the
    # composer before the one public click.
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    target = (
        reddit_comment_composer(page, target_comment_id)
        if target_comment_id else composer(page, candidate["platform"], activate=False)
    )
    if composer_text(target) != promotion.compact(draft["body"]):
        raise RuntimeError("visible composer changed while dismissing editor popovers")
    button = submit_button(page, candidate["platform"], target=target)
    if not button.is_enabled():
        raise RuntimeError("visible submit button is disabled")
    prior_reddit_ids = (
        reddit_delivery_ids(
            reddit_comment_records(page),
            draft["body"],
            parent_comment_id=target_comment_id,
        )
        if candidate["platform"] == "reddit" else set()
    )
    before = page.url
    button.click(no_wait_after=True, timeout=10000)
    reddit_thing_id = ""
    if candidate["platform"] == "reddit":
        deadline = time.monotonic() + 20.0
        while time.monotonic() < deadline:
            delivered = reddit_delivery_ids(
                reddit_comment_records(page),
                draft["body"],
                parent_comment_id=target_comment_id,
            )
            new_ids = delivered - prior_reddit_ids
            if new_ids:
                reddit_thing_id = sorted(new_ids)[0]
                break
            page.wait_for_timeout(250)
        if not reddit_thing_id:
            raise RuntimeError(
                "the public click was issued, but Reddit did not show the posted comment; "
                "do not retry until the destination is inspected manually"
            )
    elif candidate["platform"] == "hackernews":
        excerpt = promotion.compact(draft["body"])[:120]
        posted = page.locator(".commtext").filter(has_text=excerpt).first
        try:
            posted.wait_for(state="visible", timeout=20000)
        except Exception as exc:
            raise RuntimeError(
                "the public click was issued, but Hacker News did not show the posted comment; "
                "do not retry until the destination is inspected manually"
            ) from exc
    else:
        page.wait_for_timeout(2500)
    screenshot = evidence(page, f"sent-{candidate['platform']}-{candidate_id}")
    detail = {"url_before": before, "url_after": page.url, "screenshot": screenshot}
    if reddit_thing_id:
        detail["reddit_thing_id"] = reddit_thing_id
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
    search.add_argument("--platform", choices=tuple(PLATFORM_HOSTS), required=True)
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=12)
    search.add_argument("--hydrate", type=int, default=0, help="inspect the full body of up to N fresh results")
    search.add_argument("--kind", choices=("posts", "comments"), default="posts")
    search.add_argument("--background", action="store_true", help="do not take focus from the active review/login tab")
    cycle = sub.add_parser("cycle")
    cycle.add_argument("--platform", choices=tuple(PLATFORM_HOSTS), required=True)
    cycle.add_argument("--max-queries", type=int, default=5)
    cycle.add_argument("--start-query", type=int, default=0)
    cycle.add_argument("--limit-per-query", type=int, default=12)
    cycle.add_argument("--hydrate-per-query", type=int, default=3)
    cycle.add_argument("--background", action="store_true", help="do not take focus from the active review/login tab")
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
    with browser_operation_lock(), sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(
            args.cdp,
            timeout=30_000,
            no_defaults=True,
        )
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
            result = discover(
                page, args.platform, args.query, max(1, min(args.limit, 50)), args.kind
            )
            if args.hydrate:
                result["hydrated"] = hydrate_candidates(page, result["candidates"], max(1, min(args.hydrate, 10)))
            emit(result)
        elif args.command == "cycle":
            page = page_for(browser, platform=args.platform, front=not args.background)
            emit(run_discovery_cycle(
                page,
                args.platform,
                max_queries=max(1, min(args.max_queries, 20)),
                limit_per_query=max(1, min(args.limit_per_query, 50)),
                hydrate_per_query=max(0, min(args.hydrate_per_query, 10)),
                start_query=max(0, args.start_query),
            ))
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
