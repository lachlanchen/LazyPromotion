import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from zipfile import ZipFile

import browser
import promotion


ROOT = Path(__file__).resolve().parents[1]
READMES = [
    ROOT / "README.md",
    *(ROOT / "i18n" / name for name in (
        "README.ar.md",
        "README.es.md",
        "README.fr.md",
        "README.ja.md",
        "README.ko.md",
        "README.vi.md",
        "README.zh-Hans.md",
        "README.zh-Hant.md",
        "README.de.md",
        "README.ru.md",
    )),
]


class RepositoryTests(unittest.TestCase):
    def test_browser_operations_are_serialized_across_clients(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            browser, "BROWSER_LOCK_PATH", Path(tmp) / "browser-operation.lock"
        ):
            with browser.browser_operation_lock(timeout_seconds=0.1, poll_seconds=0.01):
                with self.assertRaisesRegex(RuntimeError, "shared browser operation lock"):
                    with browser.browser_operation_lock(
                        timeout_seconds=0.03,
                        poll_seconds=0.01,
                    ):
                        pass
            with browser.browser_operation_lock(timeout_seconds=0.1, poll_seconds=0.01):
                pass

    def test_desktop_restores_one_maximized_review_workspace(self):
        script = (ROOT / "scripts" / "desktop.sh").read_text(encoding="utf-8")
        self.assertIn('DISPLAY_WIDTH=1920', script)
        self.assertIn('DISPLAY_HEIGHT=1080', script)
        self.assertIn('https://www.icloud.com/mail/', script)
        self.assertIn('https://platform.postiz.com/launches', script)
        self.assertIn('https://www.lingq.com/settings/referrals', script)
        self.assertIn('https://bookshop.org/affiliates/profile/introduction', script)
        self.assertIn('https://partners.dub.co/postiz/apply', script)
        self.assertIn('restore_browser_workspace', script)
        self.assertIn('main.window', script)
        self.assertIn('viewer.window', script)
        self.assertIn('register-viewer', script)
        self.assertIn('refresh_registered_viewers', script)
        self.assertIn('maximize_firefox_viewer', script)
        self.assertIn('wmctrl -ir "$window_id" -b remove,fullscreen', script)
        self.assertIn('wmctrl -ir "$window_id" -b add,maximized_vert,maximized_horz', script)
        self.assertNotIn('wmctrl -ir "$window_id" -b add,fullscreen', script)
        self.assertNotIn('AFFILIATE_NOVNC_PORT', script)
        self.assertNotIn('CAMPAIGN_NOVNC_PORT', script)
        self.assertIn('resize=scale', script)
        self.assertIn('reconnect=0', script)
        self.assertIn('wait_process_exit', script)
        self.assertIn('wait_reserved_runtime_release', script)
        self.assertIn("#{pane_pid}", script)
        self.assertIn('save_browser_workspace', script)
        self.assertIn('workspace.urls', script)
        self.assertIn('access_token', script)
        self.assertIn('workspace_url_is_baseline', script)
        self.assertIn('wait_cdp_pages_stable', script)
        self.assertIn('deduplicate_browser_tabs', script)
        self.assertIn('close_redundant_reddit_home', script)

    def test_screenshot_failure_does_not_discard_discovery(self):
        class BrokenPage:
            def screenshot(self, **kwargs):
                raise TimeoutError("renderer timeout")

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(browser, "EVIDENCE", Path(tmp)):
            self.assertEqual(browser.evidence(BrokenPage(), "test-failure"), "")
            failures = list(Path(tmp).glob("*.error.txt"))
            self.assertEqual(len(failures), 1)
            self.assertIn("renderer timeout", failures[0].read_text(encoding="utf-8"))

    def test_all_eleven_readmes_have_shared_public_panels(self):
        self.assertEqual(len(READMES), 11)
        for path in READMES:
            with self.subTest(path=path.name):
                body = path.read_text(encoding="utf-8")
                header = body.splitlines()[0]
                self.assertEqual(header.count("]("), 11)
                self.assertIn("figs/banner.png", body)
                self.assertIn("chat.lazying.art/donate", body)
                self.assertIn("paypal.me/RongzhouChen", body)
                self.assertIn("buy.stripe.com/", body)
                self.assertIn("CITATION.cff", body)
                self.assertIn("@software{chen_lazypromotion_2026", body)
                self.assertIn("python promotion.py triage CANDIDATE_ID", body)

    def test_readme_language_links_resolve(self):
        for path in READMES:
            header = path.read_text(encoding="utf-8").splitlines()[0]
            for target in header.split("](")[1:]:
                relative = target.split(")", 1)[0]
                with self.subTest(source=path.name, target=relative):
                    self.assertTrue((path.parent / relative).resolve().is_file())

    def test_catalog_has_unique_grounded_projects(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        projects = catalog["projects"]
        ids = [project["id"] for project in projects]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("localknowledgeterminal", ids)
        self.assertIn("video2book", ids)
        self.assertIn("paperagent", ids)
        self.assertIn("l-and-n", ids)
        for project in projects:
            with self.subTest(project=project["id"]):
                self.assertTrue(project["url"].startswith("https://github.com/lachlanchen/"))
                self.assertTrue(project["summary"].strip())
                self.assertTrue(project["keywords"])
        by_id = {project["id"]: project for project in projects}
        self.assertIn("文言文", by_id["pocketpolyglot"]["keywords"])
        self.assertEqual(
            by_id["lingualleaf"]["homepage"],
            "https://lachlanchen.github.io/LinguaLeaf/website/",
        )
        self.assertEqual(
            by_id["video2book"]["homepage"],
            "https://lazying.art/lecture-pack/",
        )
        self.assertIn(
            "https://lazying.art/lecture-pack/#example",
            by_id["video2book"]["reply_context"],
        )
        self.assertIn("41.191-second synthetic source", by_id["video2book"]["reply_context"])
        self.assertEqual(
            by_id["paperagent"]["homepage"],
            "https://lazying.art/manuscript-sprint/",
        )
        self.assertEqual(
            by_id["l-and-n"]["homepage"],
            "https://l-and-n.lazying.art/",
        )
        self.assertIn("test builds", by_id["l-and-n"]["reply_context"])

    def test_discovery_plan_uses_known_projects(self):
        known = {project["id"] for project in promotion.load_catalog()["projects"]}
        plan = json.loads((ROOT / "discovery-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["version"], 1)
        self.assertTrue(plan["queries"]["reddit"])
        for project_id, topic in plan["project_topics"].items():
            with self.subTest(project_topic=project_id):
                self.assertIn(project_id, known)
                self.assertTrue(topic.strip())
        for platform, queries in plan["queries"].items():
            for query in queries:
                with self.subTest(platform=platform, query=query["query"]):
                    self.assertIn(query["project_id"], known)
                    self.assertTrue(query["purpose"])
                    if "comment_query" in query:
                        self.assertEqual(platform, "hackernews")
                        self.assertTrue(query["comment_query"].strip())

    def test_terminology_discovery_requires_collection_owner_intent(self):
        plan = json.loads((ROOT / "discovery-plan.json").read_text(encoding="utf-8"))
        route = next(
            item
            for item in plan["queries"]["reddit"]
            if item["purpose"].startswith("Collection owners asking how to search")
        )
        self.assertEqual(route["project_id"], "localknowledgeterminal")
        self.assertIn('"my glossary"', route["query"])
        self.assertIn("required_body_groups", route)
        self.assertEqual(len(route["required_body_groups"]), 3)
        self.assertIn("i built", route["excluded_body_any"])

    def test_x_go_route_is_qualified_as_the_board_game(self):
        route = next(
            item for item in browser.discovery_queries("x")
            if item["project_id"] == "lazyweiqi"
        )
        query = route["query"].casefold()
        self.assertTrue(any(term in query for term in ("weiqi", "baduk", "board game")))
        self.assertNotEqual(query, '"learn go" (advice or resources) -filter:retweets')

    def test_brand_routes_use_need_oriented_topic_overrides(self):
        expected = {
            "github-cellist": "python environment import verification",
            "github-glassagent-wearable-releases": "ai glasses setup",
            "l-and-n": "l n pronunciation",
            "github-microquant": "metatrader5 ohlc analysis",
            "github-yinghan": "organoid segmentation",
        }
        for platform in ("reddit", "x", "hackernews"):
            routes = {route["project_id"]: route["query"] for route in browser.discovery_queries(platform)}
            for project_id, topic in expected.items():
                with self.subTest(platform=platform, project=project_id):
                    self.assertIn(f'"{topic}"', routes[project_id])

    def test_public_github_index_covers_owner_source_repositories(self):
        index = json.loads((ROOT / "github-repos.json").read_text(encoding="utf-8"))
        self.assertEqual(index["owner"], "lachlanchen")
        self.assertEqual(index["visibility"], "public")
        self.assertFalse(index["includes_forks"])
        self.assertGreaterEqual(len(index["repositories"]), 100)
        for repo in index["repositories"]:
            with self.subTest(repo=repo["name"]):
                self.assertTrue(repo["url"].startswith("https://github.com/lachlanchen/"))
                self.assertNotIn("private", repo)
                self.assertRegex(repo["pushed_at"], r"^20\d{2}-\d{2}-\d{2}T")
                self.assertRegex(repo["updated_at"], r"^20\d{2}-\d{2}-\d{2}T")

    def test_rotating_routes_cover_every_evidence_backed_project(self):
        project_ids = {project["id"] for project in promotion.load_catalog()["projects"]}
        for platform in ("reddit", "x", "hackernews"):
            routes = browser.discovery_queries(platform)
            with self.subTest(platform=platform):
                self.assertEqual({route["project_id"] for route in routes}, project_ids)

    def test_discovery_lanes_keep_reviewed_routes_frequent_and_long_tail_complete(self):
        project_ids = {project["id"] for project in promotion.load_catalog()["projects"]}
        for platform in ("reddit", "x", "hackernews"):
            lanes = browser.discovery_query_lanes(platform)
            with self.subTest(platform=platform):
                self.assertTrue(lanes["core"])
                self.assertTrue(lanes["long_tail"])
                core_ids = {route["project_id"] for route in lanes["core"]}
                tail_ids = {route["project_id"] for route in lanes["long_tail"]}
                self.assertFalse(core_ids & tail_ids)
                self.assertEqual(core_ids | tail_ids, project_ids)

        instagram = browser.discovery_query_lanes("instagram")
        self.assertEqual(len(instagram["core"]), 5)
        self.assertIn("classicalchinese", {route["query"] for route in instagram["core"]})
        self.assertIn("chinesehistory", {route["query"] for route in instagram["core"]})
        self.assertEqual(instagram["long_tail"], [])

    def test_primary_lkt_offer_has_frequent_distinct_need_routes(self):
        for platform in ("reddit", "x", "hackernews"):
            core = browser.discovery_query_lanes(platform)["core"]
            routes = [
                route for route in core
                if route["project_id"] == "localknowledgeterminal"
            ]
            with self.subTest(platform=platform):
                self.assertGreaterEqual(len(routes), 4)
                self.assertGreaterEqual(len(routes) * 5, len(core))
                self.assertEqual(len({route["query"] for route in routes}), len(routes))
                combined = " ".join(route["query"].casefold() for route in routes)
                self.assertIn("private", combined)
                self.assertTrue(any(term in combined for term in ("offline", "local")))
                self.assertTrue(any(term in combined for term in ("pdf", "book", "document")))

        reddit = browser.discovery_query_lanes("reddit")["core"]
        self.assertTrue(any(
            route["project_id"] == "localknowledgeterminal"
            and "subreddit:rag" in route["query"].casefold()
            for route in reddit
        ))

    def test_primary_lkt_offer_has_owned_collection_evidence_gates(self):
        for platform in ("reddit", "x"):
            routes = [
                route for route in browser.discovery_query_lanes(platform)["core"]
                if "owned-collection buyer intent" in route["purpose"].casefold()
            ]
            with self.subTest(platform=platform):
                self.assertEqual(len(routes), 1)
                route = routes[0]
                self.assertEqual(route["project_id"], "localknowledgeterminal")
                self.assertEqual(len(route["required_body_groups"]), 3)
                self.assertIn("i built", route["excluded_body_any"])
                self.assertTrue(browser.route_body_qualified(
                    "I have PDFs from my own collection. What should I use to "
                    "search them locally without cloud upload?",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I built a private local PDF search tool and launched it today.",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I have a private photo collection and need editing advice.",
                    route,
                ))

    def test_meeting_knowledge_routes_require_owned_source_and_explicit_need(self):
        for platform in ("reddit", "x"):
            routes = [
                route for route in browser.discovery_query_lanes(platform)["core"]
                if "meeting-knowledge buyer intent" in route["purpose"].casefold()
            ]
            with self.subTest(platform=platform):
                self.assertEqual(len(routes), 1)
                route = routes[0]
                self.assertEqual(route["project_id"], "localknowledgeterminal")
                self.assertEqual(len(route["required_body_groups"]), 3)
                self.assertIn("i built", route["excluded_body_any"])
                self.assertTrue(browser.route_body_qualified(
                    "We have our meeting transcripts and need help turning them "
                    "into traceable decisions and action items.",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I built a meeting transcript knowledge-base tool and launched it today.",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I've built a dashboard that extracts action items from my meeting transcripts.",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I need a transcript of a podcast episode.",
                    route,
                ))

        hackernews = [
            route for route in browser.discovery_query_lanes("hackernews")["core"]
            if "meeting transcripts" in route.get("comment_query", "")
            and "decisions" in route.get("comment_query", "")
        ]
        self.assertEqual(len(hackernews), 1)
        self.assertIn("Research-only", hackernews[0]["purpose"])

    def test_paid_book_media_and_code_sprints_have_frequent_buyer_intent_routes(self):
        for platform in ("reddit", "x", "hackernews"):
            core = browser.discovery_query_lanes(platform)["core"]
            with self.subTest(platform=platform):
                self.assertTrue(any(route["project_id"] == "video2book" for route in core))
                self.assertTrue(any(route["project_id"] == "paperagent" for route in core))

        for platform in ("reddit", "x"):
            core = browser.discovery_query_lanes(platform)["core"]
            lecture = next(
                route for route in core
                if route["project_id"] == "video2book"
                and "buyer intent" in route["purpose"].casefold()
            )
            manuscript = next(
                route for route in core
                if route["project_id"] == "paperagent"
                and "buyer intent" in route["purpose"].casefold()
            )
            with self.subTest(platform=platform, offer="lecture"):
                self.assertTrue(browser.route_body_qualified(
                    "I need an editor for my course video: correct the transcript, "
                    "add bilingual subtitles, and make it easier to study.",
                    lecture,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I built my service for automatic lecture subtitles.",
                    lecture,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I made my app for course video transcripts and am available for work.",
                    lecture,
                ))
            with self.subTest(platform=platform, offer="manuscript"):
                self.assertTrue(browser.route_body_qualified(
                    "My LaTeX manuscript fails to compile in Overleaf. I need help "
                    "fixing the build and producing a latexdiff redline.",
                    manuscript,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I am available for work and offer a LaTeX manuscript service.",
                    manuscript,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "Written with AI. My editor compiles your LaTeX thesis and shows a redline.",
                    manuscript,
                ))

    def test_classical_chinese_routes_require_a_reader_request(self):
        for platform in ("reddit", "x"):
            routes = [
                route for route in browser.discovery_query_lanes(platform)["core"]
                if route["project_id"] == "pocketpolyglot"
                and "Classical Chinese learners" in route["purpose"]
            ]
            with self.subTest(platform=platform):
                self.assertEqual(len(routes), 1)
                route = routes[0]
                self.assertEqual(len(route["required_body_groups"]), 3)
                self.assertIn("i built", route["excluded_body_any"])
                self.assertTrue(browser.route_body_qualified(
                    "I am studying Classical Chinese and need a bilingual reader. "
                    "Which edition would you recommend?",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I built a Classical Chinese translation app and launched it today.",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "Classical Chinese was important across East Asia.",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I need help choosing a bilingual French reader.",
                    route,
                ))

    def test_eink_routes_require_multilingual_purchase_intent(self):
        for platform in ("reddit", "x"):
            routes = [
                route for route in browser.discovery_query_lanes(platform)["core"]
                if route["project_id"] == "lazyingart-eink"
            ]
            with self.subTest(platform=platform):
                self.assertEqual(len(routes), 1)
                route = routes[0]
                self.assertEqual(len(route["required_body_groups"]), 3)
                self.assertTrue(browser.route_body_qualified(
                    "I want to buy an e-ink reader for learning Chinese. Which "
                    "one has good bilingual dictionary support?",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "E-readers are fantastic for language learning; I recommend a Kobo.",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I need help choosing an e-reader for black-and-white comics.",
                    route,
                ))
                self.assertFalse(browser.route_body_qualified(
                    "I launched my new multilingual e-ink reading app today.",
                    route,
                ))

    def test_hacker_news_item_id_survives_canonicalization(self):
        rows = browser.dedupe(
            [{
                "url": "https://news.ycombinator.com/item?id=12345&utm_source=test",
                "author": "reader",
                "body": "Ask HN: How should I solve this?",
            }],
            5,
        )
        self.assertEqual(rows[0]["url"], "https://news.ycombinator.com/item?id=12345")

    def test_hacker_news_comment_search_and_destination_are_exact(self):
        url = browser.search_url("hackernews", "video subtitles", "comments")
        self.assertIn("type=comment", url)
        self.assertEqual(browser.hackernews_comment_query("Ask HN video subtitles"), "video subtitles")
        self.assertTrue(browser.destination_matches(
            "https://news.ycombinator.com/item?id=12345",
            "https://news.ycombinator.com/item?id=12345",
            "hackernews",
        ))
        self.assertFalse(browser.destination_matches(
            "https://news.ycombinator.com/item?id=12345",
            "https://news.ycombinator.com/item?id=67890",
            "hackernews",
        ))

    def test_reddit_comment_search_and_destination_are_exact(self):
        url = browser.search_url("reddit", "subtitles help", "comments")
        self.assertIn("type=comments", url)
        candidate = "https://www.reddit.com/r/example/comments/post123/a_title/comment456/"
        redirected = "https://www.reddit.com/r/example/comments/post123/comment/comment456/"
        sibling = "https://www.reddit.com/r/example/comments/post123/comment/other789/"
        self.assertEqual(browser.reddit_destination_ids(candidate), ("post123", "comment456"))
        self.assertTrue(browser.destination_matches(candidate, redirected, "reddit"))
        self.assertFalse(browser.destination_matches(candidate, sibling, "reddit"))
        self.assertEqual(
            browser.reddit_posted_reply_selector("comment456"),
            'shreddit-comment[parentid="t1_comment456"] > details div[slot="comment"], '
            'shreddit-comment[parentid="t1_comment456"] > div[slot="comment"]',
        )

    def test_reddit_post_search_card_requires_full_body_hydration(self):
        post = {
            "id": "cand_post",
            "source_url": "https://www.reddit.com/r/example/comments/post123/help/",
        }
        comment = {
            "id": "cand_comment",
            "source_url": "https://www.reddit.com/r/example/comments/post123/help/comment456/",
        }
        self.assertFalse(browser.candidate_context_ready("reddit", post, set()))
        self.assertTrue(
            browser.candidate_context_ready("reddit", post, {"cand_post"})
        )
        self.assertTrue(browser.candidate_context_ready("reddit", comment, set()))
        self.assertTrue(browser.candidate_context_ready("x", post, set()))

    def test_reddit_delivery_ids_cover_post_comments_and_exact_replies(self):
        body = "A useful exact answer."
        records = [
            {"thingid": "t1_before", "parentid": "", "body": body},
            {"thingid": "t1_top", "parentid": "", "body": body},
            {"thingid": "t1_child", "parentid": "t1_comment456", "body": body},
            {"thingid": "t1_sibling", "parentid": "t1_other", "body": body},
            {"thingid": "not-a-thing", "parentid": "", "body": body},
            {"thingid": "t1_different", "parentid": "", "body": "Different text"},
        ]
        self.assertEqual(
            browser.reddit_delivery_ids(records, body),
            {"t1_before", "t1_top"},
        )
        self.assertEqual(
            browser.reddit_delivery_ids(
                records,
                body,
                parent_comment_id="comment456",
            ),
            {"t1_child"},
        )
        prior = {"t1_before"}
        self.assertEqual(
            browser.reddit_delivery_ids(records, body) - prior,
            {"t1_top"},
        )

    def test_reddit_direct_reply_count_excludes_siblings_and_empty_shells(self):
        records = [
            {"thingid": "t1_child1", "parentid": "t1_comment456", "body": "One"},
            {"thingid": "t1_child2", "parentid": "t1_comment456", "body": "Two"},
            {"thingid": "t1_empty", "parentid": "t1_comment456", "body": ""},
            {"thingid": "t1_sibling", "parentid": "t1_other", "body": "Other"},
            {"thingid": "invalid", "parentid": "t1_comment456", "body": "Bad"},
        ]
        self.assertEqual(browser.reddit_direct_reply_count(records, "comment456"), 2)
        with self.assertRaisesRegex(ValueError, "invalid Reddit parent comment id"):
            browser.reddit_direct_reply_count(records, "../bad")

    def test_reddit_submit_is_bound_to_reviewed_composer(self):
        page = mock.MagicMock()
        target = mock.MagicMock()
        host = mock.MagicMock()
        button_group = mock.MagicMock()
        button = mock.MagicMock()
        target.locator.return_value = host
        host.locator.return_value = button_group
        button_group.count.return_value = 1
        button_group.nth.return_value = button
        button.is_visible.return_value = True

        self.assertIs(browser.submit_button(page, "reddit", target=target), button)
        target.locator.assert_called_once_with("xpath=ancestor::shreddit-composer[1]")
        host.locator.assert_called_once_with('button[type="submit"]')
        page.get_by_role.assert_not_called()

    def test_reddit_composer_is_bound_to_target_comment_id(self):
        page = mock.MagicMock()
        group = mock.MagicMock()
        item = mock.MagicMock()
        page.locator.return_value = group
        group.count.return_value = 1
        group.nth.return_value = item
        item.is_visible.return_value = True

        self.assertIs(browser.reddit_comment_composer(page, "p636j6g"), item)
        page.locator.assert_has_calls([
            mock.call(
                'shreddit-composer[aria-describedby="comment-composer-message-t1_p636j6g"] '
                '[contenteditable="true"][role="textbox"]'
            ),
            mock.call(
                'shreddit-composer[aria-describedby="comment-composer-message-t1_p636j6g"] textarea'
            ),
        ])

    def test_instagram_grid_alt_text_is_canonical_candidate_body(self):
        rows = browser.dedupe(
            [{
                "url": "https://www.instagram.com/p/example/?img_index=1",
                "author": "",
                "body": "Can someone recommend a bilingual Japanese reader?",
            }],
            5,
        )
        self.assertEqual(rows[0]["url"], "https://www.instagram.com/p/example/")
        self.assertTrue(promotion.is_help_request(rows[0]["body"]))

    def test_instagram_comment_destination_is_exact(self):
        candidate = "https://www.instagram.com/p/post123/c/comment456/"
        sibling = "https://www.instagram.com/p/post123/c/comment789/"
        parent = "https://www.instagram.com/p/post123/"
        self.assertEqual(browser.instagram_destination_ids(candidate), ("post123", "comment456"))
        self.assertTrue(browser.destination_matches(candidate, candidate, "instagram"))
        self.assertFalse(browser.destination_matches(candidate, sibling, "instagram"))
        self.assertFalse(browser.destination_matches(candidate, parent, "instagram"))

    def test_private_runtime_paths_are_ignored(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".local/", ignored)
        self.assertIn("handoff/", ignored)

    def test_wenyan_campaign_is_reviewable_and_contains_no_private_ids(self):
        path = ROOT / "campaigns" / "wenyan-history.json"
        campaign = json.loads(path.read_text(encoding="utf-8"))
        serialized = path.read_text(encoding="utf-8")
        self.assertEqual(campaign["version"], 5)
        bridge = campaign["channels"]["owned_conversion_bridge"]
        self.assertEqual(bridge["state"], "live_verified")
        self.assertEqual(
            bridge["website_commit"],
            "6e6a2a79bca7ddc0a164f6a2b27b912bed7609cb",
        )
        self.assertEqual(bridge["attribution"]["utm_source"], "wenyan")
        self.assertIn("not a lead or revenue", bridge["policy"])
        self.assertEqual(campaign["channels"]["x"]["state"], "postiz_queue")
        self.assertEqual(campaign["channels"]["instagram"]["state"], "postiz_queue")
        self.assertLessEqual(len(campaign["channels"]["x"]["content"]), 280)
        self.assertLessEqual(len(campaign["channels"]["instagram"]["content"]), 2200)
        self.assertIn("six black-and-white parts", campaign["channels"]["x"]["content"])
        self.assertIn("utm_source=x", campaign["channels"]["x"]["content"])
        self.assertNotIn("https://", campaign["channels"]["x"]["content"])
        self.assertNotIn("in color and B&W", campaign["channels"]["x"]["content"])
        self.assertIn(
            "Each of the other named histories has color and black-and-white editions",
            campaign["channels"]["instagram"]["content"],
        )
        self.assertIn(
            "six black-and-white parts",
            campaign["channels"]["instagram"]["content"],
        )
        self.assertIn("utm_source=instagram", campaign["channels"]["instagram"]["content"])
        self.assertIn(
            "no color link",
            campaign["source_evidence"]["format_inventory"]["zizhi_tongjian"],
        )
        self.assertEqual(
            campaign["source_evidence"]["owned_guide"],
            "https://lazying.art/wenyan/",
        )
        guwen = campaign["source_evidence"]["guwen_guanzhi_evidence"]
        self.assertEqual(guwen["state"], "structurally_verified_not_semantically_certified")
        self.assertEqual(guwen["fresh_read_only_gate"]["errors"], 0)
        self.assertEqual(guwen["fresh_read_only_gate"]["assembled_units"], 19502)
        self.assertEqual(
            sorted(guwen["fresh_read_only_gate"]["color_variants_checked"]),
            ["blackwhite", "color"],
        )
        self.assertIn("does not certify translation accuracy", guwen["policy"])
        self.assertTrue(campaign["channels"]["x"]["visible_review"]["stored_text_exact"])
        self.assertTrue(
            campaign["channels"]["instagram"]["visible_review"][
                "stored_text_normalized_exact"
            ]
        )
        self.assertEqual(
            campaign["channels"]["x"]["content"],
            campaign["channels"]["x"]["postiz_content"],
        )
        self.assertEqual(
            campaign["channels"]["instagram"]["content"],
            campaign["channels"]["instagram"]["postiz_content"],
        )
        self.assertNotIn("integration_id", serialized.casefold())
        self.assertNotIn("post_id", serialized.casefold())

    def test_landn_campaign_keeps_pwa_story_draft_truthful_and_unpublished(self):
        path = ROOT / "campaigns" / "l-and-n-pronunciation-launch.json"
        serialized = path.read_text(encoding="utf-8")
        campaign = json.loads(serialized)
        self.assertEqual(campaign["version"], 1)
        self.assertEqual(campaign["source_evidence"]["pwa"], "https://l-and-n.lazying.art/")
        releases = campaign["source_evidence"]["release_state"]
        self.assertEqual(releases["pwa"], "live")
        self.assertEqual(releases["google_play_internal_test"], "available_to_internal_testers")
        self.assertEqual(releases["google_play_production"], "changes_in_review")
        self.assertEqual(releases["testflight_external"], "waiting_for_review")
        self.assertEqual(releases["apple_app_store"], "waiting_for_review")
        test_build = campaign["source_evidence"]["android_test_build"]
        self.assertTrue(test_build["first_party_apk"].startswith("https://l-and-n.lazying.art/"))
        self.assertEqual(len(test_build["sha256"]), 64)
        linkedin = campaign["channels"]["linkedin"]
        self.assertEqual(linkedin["state"], "postiz_draft")
        self.assertIn("I have trouble pronouncing L and N", linkedin["content"])
        self.assertIn("English, Mandarin, and Cantonese", linkedin["content"])
        self.assertEqual(linkedin["destination"], campaign["source_evidence"]["pwa"])
        self.assertTrue(linkedin["visible_review"]["stored_text_normalized_exact"])
        self.assertTrue(linkedin["visible_review"]["original_url_preserved"])
        self.assertFalse(linkedin["visible_review"]["release_present"])
        self.assertEqual(campaign["funnel"]["verified_received_gross_usd"], 0)
        self.assertNotIn("integration_id", serialized.casefold())
        self.assertNotIn("post_id", serialized.casefold())

    def test_lazyedit_video_pipeline_opportunity_stays_feasibility_first(self):
        path = ROOT / "campaigns" / "lazyedit-video-pipeline-opportunity.json"
        serialized = path.read_text(encoding="utf-8")
        campaign = json.loads(serialized)
        self.assertEqual(campaign["version"], 2)
        self.assertEqual(campaign["source_need"]["state"], "public_listing_visible")
        self.assertEqual(campaign["source_need"]["public_rate"], "not shown")
        self.assertEqual(
            campaign["fit"]["verified_public_commit"],
            "29307f919d8f1505937bb8ada1547bbdd3895af0",
        )
        gaps = " ".join(campaign["fit"]["not_proven"]).casefold()
        self.assertIn("hebrew", gaps)
        self.assertIn("bidirectional", gaps)
        self.assertIn("two gigabytes", gaps)
        renderer = campaign["fit"]["renderer_feasibility_proof"]
        self.assertEqual(renderer["state"], "public_reproducible_fixture")
        self.assertIn("3c31cdd5d0b390bd", renderer["url"])
        self.assertEqual(len(renderer["video_sha256"]), 64)
        self.assertTrue(renderer["frames_visually_inspected"])
        self.assertFalse(renderer["native_language_review"])
        self.assertIn("not Hebrew or Arabic ASR", renderer["claim_boundary"])
        milestone = campaign["recommended_first_milestone"]
        self.assertEqual(milestone["state"], "proposal_only")
        self.assertIn("paid caption-core feasibility", milestone["scope"])
        channel = campaign["channel"]
        self.assertEqual(channel["state"], "application_prepared_login_required")
        self.assertFalse(channel["application_submitted"])
        self.assertEqual(channel["connects_spent"], 0)
        self.assertFalse(campaign["funnel"]["payment_confirmed"])
        self.assertEqual(campaign["funnel"]["received_revenue_usd"], 0)
        self.assertIsNone(
            re.search(
                r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
                serialized,
                re.IGNORECASE,
            )
        )

    def test_content_repurposing_application_is_sent_but_not_a_lead(self):
        path = ROOT / "campaigns" / "content-repurposing-pilot.json"
        serialized = path.read_text(encoding="utf-8")
        campaign = json.loads(serialized)
        self.assertEqual(campaign["version"], 5)
        self.assertEqual(campaign["id"], "content-repurposing-pilot")
        source = campaign["source_need"]
        self.assertEqual(source["state"], "public_explicit_hiring_post")
        self.assertEqual(source["company"], "Smukti")
        self.assertEqual(source["compensation"], "not stated publicly")
        self.assertEqual(source["verified_public_presence"]["site"], "https://smukti.com/")
        self.assertEqual(
            source["verified_public_presence"]["youtube"],
            "https://www.youtube.com/@smuktiindia",
        )
        samples = campaign["fit"]["public_samples"]
        self.assertGreaterEqual(len(samples), 3)
        self.assertTrue(all(sample["url"].startswith("https://") for sample in samples))
        gaps = " ".join(campaign["fit"]["not_proven"]).casefold()
        self.assertIn("travel-client", gaps)
        application = campaign["application"]
        self.assertEqual(application["state"], "sent_awaiting_reply")
        self.assertEqual(application["subject"], "Content and social media creator")
        self.assertIn("paid fit test", application["proposal"])
        self.assertIn("not travel-client work", application["claim_boundary"])
        self.assertEqual(
            application["follow_up_gate"]["review_not_before"],
            "2026-09-12",
        )
        self.assertFalse(application["follow_up_gate"]["automatic_send"])
        self.assertFalse(application["delivery_or_contract_started"])
        offer = campaign["owned_offer"]
        self.assertEqual(offer["state"], "live")
        self.assertEqual(offer["url"], "https://lazying.art/story-clip/")
        self.assertEqual(offer["price"], "USD 250")
        self.assertEqual(
            offer["website_commit"],
            "c7a20d4f2152f063b4da53fc0b987b89ecd5c7ce",
        )
        self.assertIn("Aggregate unread-badge", offer["inquiry_monitor"])
        self.assertFalse(offer["checkout_created"])
        self.assertFalse(offer["social_post_created"])
        self.assertTrue(offer["deployment_verified"])
        discovery = campaign["search_discovery"]
        self.assertEqual(
            discovery["indexing_request"],
            "accepted_into_priority_crawl_queue",
        )
        self.assertEqual(discovery["request_count"], 1)
        self.assertFalse(discovery["resubmit"])
        self.assertIn("not indexing", discovery["claim_boundary"])
        funnel = campaign["funnel"]
        self.assertEqual(funnel["state"], "application_sent")
        self.assertTrue(funnel["application_sent"])
        self.assertFalse(funnel["buyer_reply_observed"])
        self.assertFalse(funnel["qualified_lead_observed"])
        self.assertFalse(funnel["scope_accepted"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)
        self.assertIn("Do not send repeated", campaign["policy"])
        self.assertIsNone(
            re.search(
                r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
                serialized,
                re.IGNORECASE,
            )
        )

    def test_postiz_affiliate_campaign_starts_at_zero_and_requires_disclosure(self):
        path = ROOT / "campaigns" / "postiz-affiliate-pilot.json"
        campaign = json.loads(path.read_text(encoding="utf-8"))
        serialized = path.read_text(encoding="utf-8").casefold()
        self.assertEqual(campaign["version"], 1)
        self.assertEqual(campaign["state"], "pre_application")
        self.assertEqual(
            campaign["source_evidence"]["program_page"],
            "https://partners.dub.co/postiz",
        )
        self.assertEqual(
            campaign["source_evidence"]["public_reward_claim"],
            "Earn 30% per sale for the customer's lifetime.",
        )
        baseline = campaign["zero_baseline_2026_09_01"]
        self.assertFalse(baseline["affiliate_url_issued"])
        for key in (
            "useful_assets_published",
            "tracked_outbound_clicks",
            "signups_or_trials",
            "paid_referrals_confirmed",
            "commission_pending_minor",
            "commission_received_minor",
            "commission_reversed_minor",
        ):
            self.assertEqual(baseline[key], 0)
        checkpoint = campaign["current_checkpoint_2026_09_02"]
        self.assertEqual(checkpoint["useful_assets_published"], 1)
        self.assertFalse(checkpoint["affiliate_url_issued"])
        self.assertEqual(checkpoint["commission_received_minor"], 0)
        published = campaign["useful_content_plan"]["published_assets"]
        self.assertEqual(len(published), 1)
        self.assertEqual(published[0]["tracking"], "ordinary untracked links only")
        self.assertTrue(published[0]["url"].startswith("https://blog.lazying.art/"))
        self.assertIn("may earn a commission", campaign["disclosures"]["blog"])
        self.assertIn("received commission", campaign["funnel"]["truth_policy"])
        self.assertIn(
            "affiliate_commission_received",
            campaign["acceptance_criteria"]["success"],
        )
        self.assertEqual(campaign["channels"]["hackernews"]["state"], "research_only")
        self.assertEqual(
            campaign["channels"]["reddit"]["state"],
            "value_only_community_replies",
        )
        self.assertNotIn('"affiliate_url":', serialized)
        self.assertNotIn("integration_id", serialized)
        self.assertNotIn("post_id", serialized)

    def test_eink_campaign_has_a_truthful_measurable_offer(self):
        path = ROOT / "campaigns" / "eink-multilingual-reading.json"
        campaign = json.loads(path.read_text(encoding="utf-8"))
        serialized = path.read_text(encoding="utf-8")
        self.assertEqual(campaign["version"], 2)
        self.assertEqual(campaign["source_evidence"]["offer_stage"], "pre-order")
        self.assertEqual(campaign["source_evidence"]["public_price"], "USD 128 / CNY 999")
        self.assertIn("email inquiry", campaign["source_evidence"]["current_order_mode"])
        self.assertEqual(
            campaign["source_evidence"]["hero_asset_repository"],
            "https://github.com/lachlanchen/LazyingArtWebsite",
        )
        self.assertEqual(campaign["channels"]["x"]["state"], "postiz_draft")
        self.assertEqual(campaign["channels"]["instagram"]["state"], "postiz_draft")
        self.assertLessEqual(len(campaign["channels"]["x"]["content"]), 280)
        self.assertLessEqual(len(campaign["channels"]["instagram"]["content"]), 2200)
        self.assertIn("utm_source=instagram", campaign["channels"]["instagram"]["content"])
        self.assertEqual(campaign["channels"]["hackernews"]["state"], "research_only")
        self.assertNotIn("integration_id", serialized.casefold())
        self.assertNotIn("post_id", serialized.casefold())

    def test_lkt_campaign_is_fit_first_and_never_invents_a_sale(self):
        path = ROOT / "campaigns" / "local-knowledge-terminal-pilot.json"
        campaign = json.loads(path.read_text(encoding="utf-8"))
        serialized = path.read_text(encoding="utf-8").casefold()
        self.assertEqual(campaign["version"], 15)
        self.assertEqual(
            campaign["source_evidence"]["offer_stage"],
            "founding collection-fit sprint",
        )
        self.assertEqual(campaign["source_evidence"]["public_price"], "USD 250")
        included_scope = campaign["source_evidence"]["included_scope"]
        self.assertIn(
            "an agreed representative sample capped at 12 source units and 20 test questions",
            included_scope,
        )
        self.assertIn(
            "up to two cited browser cards when the material is usable",
            included_scope,
        )
        self.assertIn("one factual correction pass", included_scope)
        excluded_scope = campaign["source_evidence"]["excluded_scope"]
        self.assertIn("bulk conversion", excluded_scope)
        self.assertIn("ongoing support", excluded_scope)
        scope_contract = campaign["source_evidence"]["service_scope_contract"]
        self.assertEqual(scope_contract["state"], "live_verified")
        self.assertEqual(scope_contract["sample_cap"], "12 agreed source units and 20 test questions")
        self.assertEqual(len(scope_contract["live_routes_verified"]), 3)
        self.assertIn("larger sample", scope_contract["policy"])
        terms = campaign["source_evidence"]["working_terms_contract"]
        self.assertEqual(terms["state"], "live_verified")
        self.assertEqual(
            terms["website_commit"],
            "65cdc8669fca7aaf059462f69b760ff5299012df",
        )
        self.assertEqual(terms["maximum_concurrent_sprints"], 1)
        self.assertEqual(sum(terms["deliverable_allocation_usd"].values()), 250)
        self.assertEqual(terms["source_copy_retention_days"], 14)
        self.assertTrue(terms["live_verification"]["fit_check_links_to_terms"])
        self.assertEqual(terms["live_verification"]["deployment_conclusion"], "success")
        explanation = campaign["source_evidence"]["fit_check_explanation_contract"]
        self.assertEqual(explanation["state"], "live_verified")
        self.assertEqual(
            explanation["website_commit"],
            "4317e47b682a2f7f29d52cf5bd4afb59104b636e",
        )
        self.assertEqual(len(explanation["routes"]), 2)
        self.assertIn("explicit Send", explanation["policy"])
        self.assertIn("encrypted private intake", explanation["policy"])
        self.assertIn("email and copy remain available", explanation["policy"])
        currency = campaign["source_evidence"]["currency_contract"]
        self.assertEqual(currency["state"], "live")
        self.assertEqual(currency["exact_price"], "USD 250")
        self.assertEqual(currency["website_commit"], "6bf0b6a")
        self.assertIn("free fit check", campaign["source_evidence"]["current_order_mode"])
        self.assertEqual(
            campaign["source_evidence"]["practical_guide"],
            "https://blog.lazying.art/html/computer_internet/3619/search-confidential-pdfs-locally-without-overbuilding-rag.html",
        )
        consultation = campaign["source_evidence"]["enterprise_architecture_consultation_need"]
        self.assertEqual(consultation["state"], "application_prepared_login_required")
        self.assertIn("USD 200", consultation["budget"])
        self.assertIn("human-approved state", consultation["need"])
        self.assertFalse(consultation["application_submitted"])
        self.assertEqual(consultation["connects_spent"], 0)
        self.assertIn("not a lead", consultation["policy"])
        meeting = campaign["source_evidence"]["enterprise_meeting_intelligence_mission"]
        self.assertEqual(meeting["state"], "application_packet_ready_login_required")
        self.assertEqual(meeting["proposed_scope"]["fixed_price_usd"], 8000)
        self.assertEqual(sum(meeting["proposed_scope"]["milestones_usd"]), 8000)
        self.assertEqual(meeting["proposed_scope"]["pilot_meeting_cap"], 3)
        self.assertEqual(meeting["proposed_scope"]["minutes_per_meeting_cap"], 60)
        self.assertIn("explicitly agreed Chinese variant", meeting["proposed_scope"]["language_boundary"])
        proof = meeting["meeting_proof"]
        self.assertEqual(proof["state"], "live_verified")
        self.assertEqual(proof["url"], "https://lazying.art/meeting-intelligence/")
        self.assertEqual(
            proof["website_commit"],
            "a984487b7cab7a42168619888749e3bf51b143ec",
        )
        self.assertEqual(
            proof["repository_commit"],
            "907e0b3ba6a48cc1d42e37cdaa22b28416264ab6",
        )
        self.assertEqual(
            proof["artifact_sha256"],
            "b75713fcd7520fb904b56a02e513405ecbd8f4e8e62097cf04cbc4b35ef0358e",
        )
        self.assertIn("scripted", proof["proof_boundary"])
        self.assertIn("not recorded meeting audio", proof["proof_boundary"])
        self.assertEqual(
            proof["search_indexing"]["state"],
            "priority_crawl_requested_not_indexed",
        )
        self.assertIn("Do not resubmit", proof["search_indexing"]["policy"])
        self.assertIn("https://lazying.art/meeting-intelligence/", meeting["public_proof"])
        guide = meeting["practical_guide"]
        self.assertEqual(guide["state"], "published_and_verified")
        self.assertEqual(
            guide["url"],
            "https://blog.lazying.art/html/computer_internet/3802/meeting-transcripts-decisions-action-items-audit-trail.html",
        )
        self.assertEqual(guide["languages"], ["en", "zh-hant", "ja"])
        self.assertEqual(guide["source_commit"], "d06ee28")
        self.assertIn("source spans", guide["supported_copy"])
        self.assertIn("scripted 54.8-second", guide["proof_boundary"])
        self.assertIn("does not claim", guide["proof_boundary"])
        self.assertFalse(guide["lead_or_sale_observed"])
        self.assertEqual(guide["verified_received_gross_usd"], 0)
        self.assertIn("standalone help", guide["policy"])
        self.assertIn("not a lead", guide["policy"])
        self.assertIn(guide["url"], meeting["public_proof"])
        self.assertEqual(
            meeting["architecture_attachment"]["sha256"],
            "5a28f7033b9e6c780c11cc8314ac9e8e0b79c3eca2c215ad9c48aac1d8633323",
        )
        self.assertFalse(meeting["application_submitted"])
        self.assertEqual(meeting["connects_spent"], 0)
        self.assertFalse(meeting["contract_observed"])
        self.assertFalse(meeting["payment_observed"])
        self.assertIn("not a lead", meeting["policy"])
        self.assertIn("Do not claim", meeting["policy"])
        self.assertEqual(
            promotion.project_by_id("localknowledgeterminal")["reply_url"],
            campaign["source_evidence"]["fit_check"],
        )
        discovery = campaign["search_discovery"]
        self.assertEqual(discovery["current_state"], "url_is_on_google")
        self.assertTrue(discovery["indexed"])
        self.assertFalse(discovery["traffic_observed"])
        self.assertIn("not ranking", discovery["policy"])
        self.assertEqual(
            campaign["source_evidence"]["fit_check"],
            "https://lazying.art/lkt/fit-check/",
        )
        intake_sources = campaign["source_evidence"]["encrypted_intake_sources"]
        self.assertEqual(
            intake_sources["endpoint"],
            "https://blog.lazying.art/wp-json/lazyingart/v1/lkt-fit-check",
        )
        self.assertEqual(
            intake_sources["backend_commit"],
            "https://github.com/lachlanchen/myblog/commit/c8d3c0669b54ddbeef936b8f613d7d376d065936",
        )
        self.assertEqual(
            intake_sources["frontend_commit"],
            "https://github.com/lachlanchen/LazyingArtWebsite/commit/12e65ae269de4730b0bae5d230ba1017950ea251",
        )
        self.assertEqual(
            intake_sources["receiver_commit"],
            "https://github.com/lachlanchen/LazyPromotion/commit/d04488c08a815b9e21d6ca6d3059c142f38d049a",
        )
        self.assertEqual(intake_sources["record_schema"], "fit-check/v2")
        self.assertEqual(
            intake_sources["supported_offers"], ["lkt", "manuscript", "lecture"]
        )
        self.assertEqual(
            campaign["source_evidence"]["sample_fit_report"],
            "https://lazying.art/lkt/sample-report/",
        )
        self.assertEqual(
            campaign["source_evidence"]["sample_fit_report_source"],
            "https://github.com/lachlanchen/LocalKnowledgeTerminal/blob/main/docs/sample-fit-report.md",
        )
        provenance = campaign["source_evidence"]["passage_provenance_proof"]
        self.assertEqual(provenance["state"], "live_verified")
        self.assertEqual(
            provenance["viewer"], "https://lazying.art/lkt/passage-graph/"
        )
        self.assertEqual(
            provenance["source_commit"],
            "02334df74094a3ad75cf9073a7096794db79a5f4",
        )
        self.assertEqual(
            provenance["website_commit"],
            "b30af19ecd8eb2e64ddbd1515d19cb8a96288fbb",
        )
        self.assertEqual(
            provenance["artifact_sha256"],
            "801dfb0f3edb0c7aaf54c644352e5bd6a647914c0d2b9e350c4cd4c116106ef9",
        )
        self.assertEqual(
            provenance["projection_hash"],
            "e30d01ab3579fef5aa2eade0f1b3d153af0f9d60079c5fc904934df8dfee6240",
        )
        self.assertEqual(
            provenance["counts"],
            {"nodes": 8, "reviewed_edges": 8, "exact_unit_evidence_records": 3},
        )
        self.assertEqual(
            provenance["not_claimed"],
            [
                "automatic extraction",
                "full-book ingestion",
                "customer result",
                "translation benchmark",
            ],
        )
        demand = campaign["source_evidence"]["textbook_graph_demand_signal"]
        self.assertEqual(demand["state"], "research_only")
        self.assertEqual(demand["community_state"], "restricted")
        self.assertFalse(demand["public_reply_sent"])
        self.assertFalse(demand["direct_message_sent"])
        self.assertFalse(demand["lead_or_sale_observed"])
        self.assertIn("not permission to contact", demand["policy"])
        self.assertEqual(campaign["funnel"]["verified_received_gross_usd"], 0)
        direct_intake = campaign["conversion_readiness"]["encrypted_direct_intake"]
        self.assertEqual(direct_intake["state"], "live_verified")
        self.assertEqual(
            direct_intake["current_live_path"],
            "encrypted_direct_intake_with_email_fallback",
        )
        self.assertEqual(
            direct_intake["endpoint"],
            "https://blog.lazying.art/wp-json/lazyingart/v1/lkt-fit-check",
        )
        self.assertIn(
            "c8d3c0669b54ddbeef936b8f613d7d376d065936",
            direct_intake["backend_source"],
        )
        self.assertIn(
            "12e65ae269de4730b0bae5d230ba1017950ea251",
            direct_intake["frontend_source"],
        )
        self.assertIn(
            "d04488c08a815b9e21d6ca6d3059c142f38d049a",
            direct_intake["receiver_source"],
        )
        transport = direct_intake["transport_verification"]
        self.assertTrue(transport["allowed_options_exact_acao"])
        self.assertFalse(transport["foreign_options_acao_present"])
        self.assertEqual(transport["malformed_allowed_post_status"], 400)
        self.assertEqual(
            transport["inquiry_content_storage"],
            "encrypted_envelope_outside_webroot",
        )
        self.assertIn("no inquiry content", transport["operational_state"])
        live_verification = direct_intake["live_verification"]
        self.assertEqual(
            live_verification["state"], "synthetic_browser_round_trip_verified"
        )
        self.assertTrue(live_verification["explicitly_labeled_synthetic"])
        self.assertEqual(
            live_verification["visible_success_reference"],
            "cc078babd1b32b0c08e796e88886201f",
        )
        self.assertTrue(
            live_verification["receiver_authenticated_decrypted_and_saved"]
        )
        self.assertEqual(live_verification["private_copy_mode"], "0600")
        self.assertTrue(
            live_verification[
                "remote_envelope_deleted_only_after_unchanged_verification"
            ]
        )
        self.assertTrue(live_verification["synthetic_local_payload_artifacts_removed"])
        self.assertTrue(live_verification["remote_spool_empty"])
        transition = direct_intake["v2_transition"]
        self.assertEqual(transition["state"], "live_verified")
        self.assertEqual(transition["record_schema"], "fit-check-record/v2")
        self.assertEqual(transition["source_schema"], "fit-check/v2")
        self.assertEqual(
            transition["supported_offers"], ["lkt", "manuscript", "lecture"]
        )
        self.assertTrue(transition["cached_lkt_v1_frontend_compatible"])
        self.assertTrue(transition["manuscript_and_lecture_visible_round_trips_verified"])
        self.assertTrue(transition["synthetic_local_payload_artifacts_removed"])
        self.assertTrue(transition["remote_spool_empty"])
        self.assertFalse(transition["lead_or_sale_observed"])
        self.assertEqual(transition["verified_received_gross_usd"], 0)
        self.assertEqual(
            direct_intake["receiver_runtime"],
            {
                "state": "healthy",
                "session": "lazypromotion-lkt-inbox",
                "interval_minutes": 15,
                "latest_state": "no_pending",
            },
        )
        self.assertEqual(
            direct_intake["sanitized_status_fields"], ["receipt", "time", "state"]
        )
        self.assertFalse(direct_intake["automatic_reply"])
        self.assertFalse(direct_intake["automatic_qualification"])
        self.assertFalse(direct_intake["lead_or_sale_observed"])
        self.assertEqual(direct_intake["verified_received_gross_usd"], 0)
        serialized_intake = json.dumps(direct_intake).casefold()
        self.assertNotIn("private.pem", serialized_intake)
        self.assertNotIn("ssh_key", serialized_intake)
        self.assertNotIn(".local/", serialized_intake)
        self.assertIn("not a customer result", serialized)
        self.assertTrue(
            any(
                "not a customer result" in limit.casefold()
                for limit in campaign["source_evidence"]["limits"]
            )
        )
        self.assertIn("explicitly submit an encrypted request", serialized)
        self.assertEqual(
            campaign["conversion_readiness"]["mail_routing"],
            "icloud_mx_confirmed",
        )
        self.assertEqual(
            campaign["conversion_readiness"]["mailbox_monitoring"],
            "operator_access_verified_folder_ready",
        )
        self.assertEqual(
            campaign["conversion_readiness"]["delivery_probe"],
            "visible_in_authenticated_icloud_mail",
        )
        self.assertEqual(
            campaign["conversion_readiness"]["intake_folder"],
            "LKT Fit Checks",
        )
        routing_rule = campaign["conversion_readiness"]["routing_rule"]
        self.assertEqual(routing_rule["state"], "active")
        self.assertEqual(routing_rule["condition"], "subject_contains")
        self.assertEqual(
            routing_rule["value"],
            "Local Knowledge Terminal — free collection fit check",
        )
        self.assertEqual(routing_rule["action"], "move_to_folder")
        self.assertEqual(routing_rule["destination"], "LKT Fit Checks")
        self.assertEqual(
            routing_rule["runtime_probe"],
            "exact_subject_delivered_to_destination",
        )
        self.assertRegex(
            routing_rule["runtime_probe_checked_at"],
            r"^2026-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
        )
        self.assertIn(
            "do not promise a response time",
            campaign["conversion_readiness"]["policy"].casefold(),
        )
        monitor = campaign["conversion_readiness"]["aggregate_monitor"]
        self.assertEqual(monitor["state"], "healthy")
        self.assertFalse(monitor["message_content_opened"])
        self.assertFalse(monitor["message_metadata_persisted"])
        self.assertFalse(monitor["automatic_reply"])
        self.assertFalse(monitor["lead_or_sale_observed"])
        smoke = campaign["conversion_readiness"]["fit_check_smoke"]
        self.assertEqual(smoke["state"], "historical_local_review_panel_verified")
        self.assertTrue(smoke["historical"])
        self.assertEqual(
            smoke["superseded_by"], "encrypted_direct_intake.live_verification"
        )
        self.assertEqual(smoke["price"], "USD 250")
        self.assertEqual(smoke["website_commit"], "8541e9c")
        self.assertTrue(smoke["visible_recipient"])
        self.assertTrue(smoke["copy_fallback"])
        self.assertTrue(smoke["next_steps_visible"])
        self.assertFalse(smoke["source_files_requested_before_fit"])
        self.assertFalse(smoke["payment_before_scope_acceptance"])
        self.assertEqual(smoke["network_mutations"], 0)
        self.assertFalse(smoke["automatic_submission"])
        self.assertFalse(smoke["customer_data_used"])
        self.assertFalse(smoke["lead_or_sale_observed"])
        attribution = campaign["conversion_readiness"]["attribution_bridge"]
        self.assertEqual(attribution["state"], "live")
        self.assertEqual(attribution["plugin_version"], "0.4.13")
        self.assertEqual(
            attribution["destination_scope"],
            [
                "https://lazying.art/lkt/sample-report/",
                "https://lazying.art/lkt/fit-check/",
            ],
        )
        self.assertEqual(
            attribution["allowlisted_parameters"],
            ["utm_source", "utm_medium", "utm_campaign", "utm_content"],
        )
        self.assertEqual(attribution["website_commit"], "17e85ef")
        self.assertEqual(
            attribution["verified_paths"],
            [
                "reddit_profile_guide_to_lazyblog_to_sample_report_to_fit_check",
                "reddit_profile_guide_to_lazyblog_to_fit_check_to_local_email_review",
                "instagram_product_to_sample_report_to_fit_check",
            ],
        )
        self.assertIn("send a form", attribution["policy"])
        self.assertIn("do not forward arbitrary", attribution["policy"].casefold())
        payment_request = campaign["conversion_readiness"]["payment_request"]
        self.assertEqual(
            payment_request["state"], "live_account_and_fixed_config_verified"
        )
        self.assertEqual(payment_request["price"], "USD 250")
        self.assertEqual(payment_request["quantity"], 1)
        self.assertFalse(payment_request["public_export"])
        self.assertFalse(payment_request["mutates_stripe"])
        self.assertIn("free fit check", payment_request["policy"])
        self.assertEqual(campaign["channels"]["x"]["state"], "postiz_queue")
        self.assertEqual(campaign["channels"]["instagram"]["state"], "postiz_queue")
        x_sample = campaign["channels"]["x"]["sample_report_post"]
        self.assertEqual(x_sample["known_owned_replies"], 1)
        self.assertEqual(x_sample["analytics_observation"]["provider_reply_count"], 1)
        self.assertEqual(x_sample["analytics_observation"]["known_owned_reply_count"], 1)
        self.assertEqual(x_sample["analytics_observation"]["external_reply_count"], 0)
        self.assertFalse(x_sample["analytics_observation"]["lead_or_sale_observed"])
        self.assertEqual(
            x_sample["analytics_observation"]["verified_received_gross_usd"], 0
        )
        instagram_sample = campaign["channels"]["instagram"]["sample_report_post"]
        self.assertEqual(instagram_sample["analytics_observation"]["views"], 31)
        self.assertEqual(instagram_sample["analytics_observation"]["reach"], 13)
        self.assertEqual(instagram_sample["analytics_observation"]["likes"], 1)
        self.assertEqual(instagram_sample["analytics_observation"]["comments"], 0)
        self.assertFalse(
            instagram_sample["analytics_observation"]["lead_or_sale_observed"]
        )
        self.assertEqual(
            instagram_sample["analytics_observation"]["verified_received_gross_usd"],
            0,
        )
        self.assertEqual(campaign["channels"]["lazyblog"]["state"], "published")
        self.assertEqual(
            sorted(campaign["channels"]["lazyblog"]["translations"]), ["ja", "zh"]
        )
        self.assertIn(
            "utm_source=lazyblog",
            campaign["channels"]["lazyblog"]["conversion_url"],
        )
        self.assertIn(
            "lazying.art/lkt/sample-report",
            campaign["channels"]["lazyblog"]["evidence_url"],
        )
        self.assertIn(
            "utm_content=confidential_pdf_sample_report",
            campaign["channels"]["lazyblog"]["evidence_url"],
        )
        demand_response = campaign["channels"]["lazyblog"]["demand_response"]
        self.assertEqual(
            demand_response["state"], "published_and_multilingual_verified"
        )
        self.assertEqual(
            demand_response["source_channel"], "hackernews_research_only"
        )
        self.assertEqual(
            demand_response["languages_verified"], ["en", "zh", "ja"]
        )
        self.assertEqual(len(demand_response["primary_sources"]), 3)
        self.assertEqual(
            demand_response["verified_links_per_language"]["primary_sources"], 3
        )
        self.assertEqual(
            demand_response["verified_links_per_language"]["lkt_fit_check"], 1
        )
        self.assertEqual(demand_response["blog_commit"], "1631e82")
        self.assertFalse(demand_response["public_reply_sent"])
        self.assertFalse(demand_response["direct_message_sent"])
        self.assertFalse(demand_response["lead_or_sale_observed"])
        self.assertIn("research-only", demand_response["policy"])
        ocr_guide = campaign["channels"]["lazyblog"]["multilingual_ocr_guide"]
        self.assertEqual(
            ocr_guide["state"], "published_and_multilingual_verified"
        )
        self.assertEqual(ocr_guide["wordpress_id"], 3791)
        self.assertEqual(ocr_guide["languages_verified"], ["en", "zh", "ja"])
        self.assertEqual(len(ocr_guide["primary_sources"]), 6)
        self.assertFalse(ocr_guide["public_reply_linked_owned_asset"])
        self.assertFalse(ocr_guide["lead_or_sale_observed"])
        linkedin_ocr = campaign["channels"]["linkedin"][
            "multilingual_ocr_guide_post"
        ]
        linkedin_offer = campaign["channels"]["linkedin"][
            "collection_fit_offer_post"
        ]
        self.assertEqual(linkedin_offer["state"], "postiz_queue")
        self.assertEqual(linkedin_offer["publish_at"], "2026-09-09T01:00:00Z")
        self.assertEqual(linkedin_offer["content"], linkedin_offer["postiz_content"])
        self.assertFalse(linkedin_offer["shortlink"])
        self.assertIn("four USD 250 collection-fit sprints", linkedin_offer["content"])
        self.assertIn("concept visual based on the current browser prototype", linkedin_offer["content"])
        self.assertNotIn("The image shows the current display prototype", linkedin_offer["content"])
        self.assertIn("does not include hardware", linkedin_offer["content"])
        self.assertTrue(linkedin_offer["verification"]["queue_state_verified"])
        self.assertTrue(linkedin_offer["verification"]["wording_update_saved"])
        self.assertTrue(
            linkedin_offer["verification"]["saved_via_original_url_confirmation"]
        )
        self.assertFalse(linkedin_offer["lead_or_sale_observed"])
        self.assertEqual(linkedin_ocr["state"], "postiz_queue")
        self.assertEqual(linkedin_ocr["publish_at"], "2026-09-22T02:00:00Z")
        self.assertFalse(linkedin_ocr["shortlink"])
        self.assertIn("not full-library OCR", linkedin_ocr["content"])
        self.assertEqual(
            campaign["channels"]["reddit"]["profile_guide"]["state"],
            "published",
        )
        self.assertEqual(
            campaign["channels"]["reddit"]["profile_guide"]["url"],
            "https://www.reddit.com/r/u_Ok-Perception1122/comments/1w3ydel/a_small_decision_tree_for_searching_confidential/",
        )
        profile_route = campaign["channels"]["reddit"]["profile_route"]
        self.assertEqual(profile_route["state"], "live")
        self.assertEqual(profile_route["link_label"], "Free LKT fit check")
        self.assertEqual(
            profile_route["destination"],
            "https://lazying.art/lkt/fit-check/?utm_source=reddit&utm_medium=profile&utm_campaign=local_knowledge_terminal_pilot&utm_content=profile_social_link",
        )
        self.assertIn("Local Knowledge Terminal", profile_route["bio"])
        self.assertIn("does not authorize", profile_route["policy"])
        self.assertEqual(
            campaign["channels"]["reddit"]["profile_guide"]["publish_at"],
            "2026-09-01T02:00:00Z",
        )
        self.assertEqual(
            campaign["channels"]["reddit"]["profile_guide"]["scope"],
            "own_profile",
        )
        self.assertIn(
            "utm_source=reddit",
            campaign["channels"]["reddit"]["profile_guide"]["destination"],
        )
        self.assertIn(
            "Disclosure: I maintain",
            campaign["channels"]["reddit"]["profile_guide"]["content"],
        )
        self.assertIn(
            "https://blog.lazying.art/",
            campaign["channels"]["reddit"]["profile_guide"]["content"],
        )
        self.assertIn(
            "blog.lazying.art/",
            campaign["channels"]["reddit"]["profile_guide"]["postiz_content"],
        )
        self.assertFalse(
            campaign["channels"]["reddit"]["profile_guide"]["verification"][
                "automatic_form_submission"
            ]
        )
        self.assertFalse(
            campaign["channels"]["reddit"]["profile_guide"]["verification"][
                "lead_or_sale_observed"
            ]
        )
        self.assertEqual(
            campaign["channels"]["x"]["publish_at"], "2026-09-08T01:00:00Z"
        )
        self.assertEqual(
            campaign["channels"]["x"]["guide_post"]["publish_at"],
            "2026-09-01T14:00:00Z",
        )
        self.assertEqual(
            campaign["channels"]["x"]["guide_post"]["state"], "postiz_queue"
        )
        self.assertIn(
            "utm_campaign=local_knowledge_terminal_pilot",
            campaign["channels"]["x"]["guide_post"]["destination"],
        )
        self.assertLessEqual(
            len(campaign["channels"]["x"]["guide_post"]["content"]), 280
        )
        self.assertEqual(
            campaign["channels"]["instagram"]["publish_at"],
            "2026-09-08T11:31:00Z",
        )
        self.assertLessEqual(len(campaign["channels"]["x"]["content"]), 280)
        self.assertLessEqual(len(campaign["channels"]["instagram"]["content"]), 2200)
        self.assertIn(
            "utm_source=instagram", campaign["channels"]["instagram"]["content"]
        )
        self.assertIn(
            "lazying.art/lkt/sample-report", campaign["channels"]["x"]["content"]
        )
        self.assertIn(
            "lazying.art/lkt/sample-report",
            campaign["channels"]["instagram"]["content"],
        )
        self.assertEqual(len(campaign["channels"]["x"]["content"]), 273)
        self.assertIn(
            "16,800 current-code records",
            campaign["channels"]["instagram"]["content"],
        )
        self.assertIn(
            "not a customer result or testimonial",
            campaign["channels"]["instagram"]["content"],
        )
        self.assertIn("concept", campaign["channels"]["x"]["content"])
        self.assertIn("not shipped inventory", campaign["channels"]["instagram"]["content"])
        self.assertEqual(campaign["channels"]["hackernews"]["state"], "research_only")
        self.assertIn("no detected software license", serialized)
        self.assertIn("four confirmed usd 250 payments", serialized)
        self.assertIn("confirmed payment", serialized)
        self.assertNotIn("integration_id", serialized)
        self.assertNotIn("post_id", serialized)

    def test_lkt_marketplace_packet_preserves_fit_and_revenue_gates(self):
        path = ROOT / "marketplace-channels.json"
        packet = json.loads(path.read_text(encoding="utf-8"))
        serialized = path.read_text(encoding="utf-8").casefold()
        self.assertEqual(packet["version"], 4)
        self.assertEqual(packet["offer"]["public_price"], "USD 250")
        self.assertIn("four confirmed", packet["offer"]["gross_milestone"].casefold())
        self.assertIn("must not invent", packet["offer"]["scope_policy"].casefold())
        channels = sorted(packet["channels"], key=lambda row: row["rank"])
        self.assertEqual(
            [row["id"] for row in channels],
            ["contra", "upwork_project_catalog", "fiverr"],
        )
        self.assertEqual(channels[0]["state"], "operator_registration_required")
        self.assertIn("usd 15", channels[0]["economics"].casefold())
        self.assertIn("0% to 15%", channels[1]["economics"])
        self.assertIn("80%", channels[2]["economics"])
        listing = packet["contra_listing_packet"]
        self.assertEqual(listing["state"], "draft_only_not_registered_or_published")
        self.assertEqual(listing["cover_asset"]["dimensions"], "1672x941")
        self.assertIn("hardware not included", listing["cover_asset"]["required_disclosure"].casefold())
        self.assertIn("not a customer result", listing["cover_asset"]["evidence_boundary"].casefold())
        self.assertIn("custom OCR", listing["description"])
        self.assertIn("source material", " ".join(listing["requirements"]))
        self.assertIn("first portfolio", listing["evidence"][0].casefold())
        self.assertIn("lazying.art/lkt/sample-report", listing["evidence"][0])
        self.assertEqual(
            listing["commercial_terms_state"],
            "selected_for_listing_draft_not_yet_contractual",
        )
        self.assertEqual(listing["public_terms"]["state"], "live_verified")
        self.assertEqual(listing["public_terms"]["url"], "https://lazying.art/lkt/#terms")
        self.assertTrue(listing["public_terms"]["fit_check_links_to_terms"])
        commitments = listing["publication_commitments"]
        self.assertIn("Ten business days", commitments["delivery_window"])
        self.assertEqual(commitments["maximum_concurrent_sprints"], 1)
        self.assertIn("up to ten items", commitments["correction_window"])
        self.assertEqual(
            sum(commitments["deliverable_allocation_usd"].values()),
            250,
        )
        self.assertIn("full refund", commitments["cancellation_and_refund"])
        self.assertIn("fourteen calendar days", commitments["confidentiality_and_retention"])
        self.assertIn("ongoing operation", commitments["support_boundary"])
        self.assertEqual(len(listing["remaining_live_editor_checks"]), 4)
        self.assertIn("pending payout", listing["revenue_policy"])
        self.assertNotIn("confirmed customer", serialized)
        self.assertNotIn("received usd", serialized)
        self.assertNotIn("account_id", serialized)
        self.assertNotIn("payout_id", serialized)

    def test_policy_coding_campaign_has_real_demand_and_synthetic_proof(self):
        path = ROOT / "campaigns" / "auditable-policy-content-coding.json"
        campaign = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(campaign["version"], 3)
        self.assertIn("USD 600", campaign["source_need"]["budget"])
        self.assertIn("five dropdown questions", campaign["source_need"]["scope"])
        self.assertIn("193", campaign["source_need"]["scope"])
        self.assertEqual(campaign["owned_proof"]["state"], "built_and_reproducible")
        self.assertIn("auditable-policy-coding", campaign["owned_proof"]["url"])
        upwork = campaign["channels"]["upwork"]
        linkedin = campaign["channels"]["linkedin"]
        self.assertEqual(linkedin["state"], "postiz_published")
        self.assertEqual(linkedin["visible_review"]["provider"], "linkedin")
        self.assertTrue(linkedin["visible_review"]["original_url_preserved"])
        self.assertTrue(linkedin["visible_review"]["release_present"])
        self.assertEqual(linkedin["visible_review"]["public_http_status"], 200)
        self.assertIn("linkedin.com/feed/update/", linkedin["release_url"])
        self.assertIn("synthetic text", linkedin["policy"])
        self.assertEqual(
            linkedin["content_sha256"],
            "f78244ce298b6a9975eed56b72463b4ebe91b80a98fe45d0b82e406df0c55efb",
        )
        self.assertEqual(upwork["state"], "application_prepared_login_required")
        self.assertFalse(upwork["application_submitted"])
        self.assertEqual(upwork["connects_spent"], 0)
        self.assertFalse(campaign["funnel"]["payment_confirmed"])
        self.assertEqual(campaign["funnel"]["received_revenue_usd"], 0)

    def test_manuscript_sprint_is_bounded_live_and_fit_first(self):
        path = ROOT / "campaigns" / "manuscript-sprint-pilot.json"
        campaign = json.loads(path.read_text(encoding="utf-8"))
        serialized = path.read_text(encoding="utf-8").casefold()

        self.assertEqual(campaign["version"], 11)
        offer = campaign["offer"]
        self.assertEqual(offer["state"], "live")
        self.assertEqual(offer["price"], "USD 250")
        self.assertEqual(offer["url"], "https://lazying.art/manuscript-sprint/")
        self.assertEqual(
            offer["fit_check"],
            "https://lazying.art/manuscript-sprint/fit-check/",
        )
        self.assertIn("7,500 words", offer["scope"])
        preview = offer["social_preview"]
        self.assertEqual(preview["state"], "deployed_verified")
        self.assertEqual(preview["dimensions"], "1200x630")
        self.assertEqual(len(preview["sha256"]), 64)
        self.assertIn("manuscript-sprint/assets/", preview["url"])
        self.assertIn("synthetic", preview["claim_boundary"])
        delivery = offer["sample_delivery"]
        self.assertEqual(delivery["state"], "deployed_verified")
        self.assertEqual(delivery["packet_bytes"], 503431)
        self.assertEqual(delivery["files"], 13)
        self.assertEqual(delivery["issue_ledger_rows"], 7)
        self.assertEqual(delivery["preview_dimensions"], "993x1404")
        self.assertEqual(len(delivery["packet_sha256"]), 64)
        self.assertEqual(len(delivery["preview_sha256"]), 64)
        self.assertIn("raw/183d64325f4e943f", delivery["packet_url"])
        self.assertIn("not customer work", delivery["claim_boundary"].casefold())
        exclusions = " ".join(offer["excluded"]).casefold()
        self.assertIn("ghostwriting", exclusions)
        self.assertIn("publication or acceptance guarantees", exclusions)
        terms = offer["working_terms"]
        self.assertEqual(terms["state"], "live_verified")
        self.assertEqual(
            terms["website_commit"],
            "da8fbf8322d3a81602a363fed1ff36f646c8db2a",
        )
        self.assertEqual(terms["maximum_concurrent_sprints"], 1)
        self.assertEqual(sum(terms["deliverable_allocation_usd"].values()), 250)
        self.assertEqual(terms["source_copy_retention_days"], 14)
        self.assertTrue(terms["verification"]["fit_check_links_to_terms"])
        self.assertEqual(terms["verification"]["deployment_conclusion"], "success")

        smoke = campaign["fit_check_smoke"]
        self.assertFalse(smoke["automatic_submission"])
        self.assertEqual(smoke["network_mutations"], 0)
        self.assertFalse(smoke["payment_before_scope_acceptance"])
        self.assertTrue(smoke["working_terms_linked"])
        direct_intake = campaign["encrypted_direct_intake"]
        self.assertEqual(direct_intake["state"], "live_verified")
        self.assertEqual(direct_intake["offer_route"], "manuscript")
        self.assertTrue(direct_intake["explicit_review_confirmation"])
        self.assertFalse(direct_intake["automatic_submission"])
        self.assertTrue(direct_intake["synthetic_visible_round_trip_verified"])
        self.assertTrue(direct_intake["receiver_authenticated_decrypted_and_saved"])
        self.assertTrue(direct_intake["synthetic_local_payload_artifacts_removed"])
        self.assertTrue(direct_intake["remote_spool_empty"])
        self.assertFalse(direct_intake["lead_or_sale_observed"])
        self.assertEqual(direct_intake["verified_received_gross_usd"], 0)
        self.assertFalse(campaign["funnel"]["payment_confirmed"])
        self.assertEqual(campaign["funnel"]["received_revenue_usd"], 0)

        homepage = campaign["channels"]["homepage"]
        self.assertEqual(homepage["state"], "live_and_verified")
        self.assertIn("utm_campaign=manuscript_sprint_pilot", homepage["destination"])
        self.assertIn("not a lead or sale", homepage["policy"].casefold())

        routing = campaign["intake_routing"]
        self.assertEqual(routing["state"], "active")
        self.assertEqual(routing["condition"], "subject_contains")
        self.assertEqual(
            routing["value"],
            "Manuscript Build & Redline Sprint — free fit check",
        )
        self.assertEqual(routing["destination"], "LKT Fit Checks")
        self.assertEqual(
            routing["runtime_probe"],
            "rule_visible_and_folder_counts_read_without_error",
        )
        self.assertFalse(routing["message_content_opened"])
        self.assertFalse(routing["customer_data_persisted"])

        discovery = campaign["search_discovery"]
        self.assertEqual(discovery["initial_state"], "url_unknown_to_google")
        self.assertEqual(
            discovery["historical_request_state"],
            "accepted_priority_crawl_request",
        )
        self.assertEqual(discovery["current_state"], "url_is_on_google")
        self.assertTrue(discovery["indexed"])
        self.assertFalse(discovery["traffic_observed"])
        self.assertIn("Do not resubmit", discovery["policy"])
        self.assertIn("not ranking", discovery["policy"])

        payment = campaign["payment_readiness"]
        self.assertEqual(payment["state"], "ready_for_reviewed_live_request")
        self.assertEqual(payment["price"], "USD 250")
        self.assertEqual(payment["quantity"], 1)
        self.assertEqual(payment["fulfillment_review_notes"], 8)
        self.assertEqual(payment["private_key_file_mode"], "600")
        self.assertTrue(payment["live_key_format_valid"])
        self.assertTrue(payment["account_authenticated"])
        self.assertTrue(payment["charges_enabled"])
        self.assertTrue(payment["payouts_enabled"])
        self.assertTrue(payment["details_submitted"])
        self.assertFalse(payment["stripe_objects_created"])
        self.assertFalse(payment["public_payment_link"])
        self.assertIn("real buyer", payment["remaining_gate"])

        upwork = campaign["channels"]["upwork"]
        self.assertEqual(upwork["state"], "not_applied")
        self.assertEqual(upwork["project_browser_account_state"], "logged_out")
        self.assertFalse(upwork["apply_control_visible"])
        self.assertFalse(upwork["connects_cost_visible"])
        self.assertIn("three manuscripts", upwork["scope_gap"])
        self.assertIn("Before proposing", upwork["proposal_draft"])
        lead = upwork["best_current_lead"]
        self.assertEqual(lead["title"], "Academic Editor Needed")
        self.assertIn("APA references", lead["scope"])
        self.assertIn("latex-redline", lead["evidence"][0])
        self.assertIn("domain", " ".join(lead["missing_submission_facts"]))
        self.assertIn("exact bid", " ".join(lead["missing_submission_facts"]))
        self.assertEqual(
            upwork["secondary_lead"]["title"],
            "Conversion: Docx to Overleaf Format",
        )
        self.assertEqual(upwork["application_packet"], "prepared_in_ignored_private_storage")
        self.assertIn("private draft", upwork["policy"].casefold())
        self.assertIn("keep communication and payment on upwork", upwork["policy"].casefold())

        x_channel = campaign["channels"]["x"]
        self.assertEqual(x_channel["state"], "covered_by_existing_queue")
        self.assertEqual(x_channel["existing_campaign_id"], "latex-redline-build")
        self.assertNotIn("content", x_channel)
        self.assertNotIn("postiz_content", x_channel)
        self.assertNotIn("integration_id", serialized)
        self.assertNotIn("post_id", serialized)

    def test_homepage_routes_all_active_sprints_without_inflating_revenue(self):
        expected = {
            "local-knowledge-terminal-pilot.json": "local_knowledge_terminal_pilot",
            "manuscript-sprint-pilot.json": "manuscript_sprint_pilot",
            "bilingual-lecture-pack-pilot.json": "bilingual_lecture_pack_pilot",
        }

        for filename, campaign_name in expected.items():
            campaign = json.loads((ROOT / "campaigns" / filename).read_text(encoding="utf-8"))
            homepage = campaign["channels"]["homepage"]
            self.assertEqual(homepage["state"], "live_and_verified")
            self.assertEqual(
                homepage["website_commit"],
                "99c04611eacf6e5dd080058b2de5b575011b61d0",
            )
            self.assertIn(f"utm_campaign={campaign_name}", homepage["destination"])
            self.assertIn("utm_content=service_chooser", homepage["destination"])
            self.assertIn("not a lead or sale", homepage["policy"].casefold())

    def test_github_profile_routes_all_active_sprints_to_public_proof_first(self):
        expected = {
            "local-knowledge-terminal-pilot.json": "local_knowledge_terminal_pilot",
            "manuscript-sprint-pilot.json": "manuscript_sprint_pilot",
            "bilingual-lecture-pack-pilot.json": "bilingual_lecture_pack_pilot",
        }

        for filename, campaign_name in expected.items():
            campaign = json.loads((ROOT / "campaigns" / filename).read_text(encoding="utf-8"))
            profile = campaign["channels"]["github_profile"]
            self.assertEqual(profile["state"], "live_and_verified")
            self.assertEqual(
                profile["profile_commit"],
                "76bb98a8e6dde319c50dca94ecdbb9dfca0ae7a6",
            )
            self.assertIn("utm_source=github", profile["destination"])
            self.assertIn("utm_medium=profile", profile["destination"])
            self.assertIn(f"utm_campaign={campaign_name}", profile["destination"])
            self.assertIn("not a lead or sale", profile["policy"].casefold())

    def test_bilingual_lecture_linkedin_queue_has_exact_bounded_offer(self):
        path = ROOT / "campaigns" / "bilingual-lecture-pack-pilot.json"
        campaign = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(campaign["version"], 28)
        discovery = campaign["search_discovery"]
        self.assertEqual(
            discovery["initial_state"],
            "discovered_currently_not_indexed",
        )
        self.assertEqual(discovery["request_state"], "accepted_priority_crawl_request")
        self.assertFalse(discovery["indexed"])
        self.assertFalse(discovery["traffic_observed"])
        self.assertIn("not indexing", discovery["policy"])

        marketplace = campaign["marketplace_leads"]["video_editor_for_meta_ads"]
        self.assertEqual(marketplace["state"], "application_prepared_login_required")
        self.assertTrue(marketplace["listing_visible_in_project_browser"])
        self.assertTrue(marketplace["project_browser_login_required"])
        self.assertFalse(marketplace["apply_control_visible"])
        self.assertFalse(marketplace["connects_cost_visible"])
        self.assertIn("Video-Editor-for-Meta-Ads", marketplace["source_url"])
        self.assertEqual(marketplace["proposed_rate"], "USD 18 per hour")
        self.assertIn("paid trial", marketplace["commercial_terms_seen"])
        self.assertIn("23K", marketplace["client_evidence"])
        self.assertIn("Traditional Chinese wording", marketplace["proposal_draft"])
        self.assertIn("won't claim ROAS", marketplace["proposal_draft"])
        sample = marketplace["prepared_sample"]
        self.assertEqual(sample["state"], "local_attachment_ready_not_published")
        self.assertEqual(sample["dimensions"], "1080x1920")
        self.assertEqual(sample["frame_rate"], 30)
        self.assertEqual(len(sample["sha256"]), 64)
        self.assertIn("Traditional Chinese", sample["content"])
        self.assertIn("AAC stereo", sample["audio"])
        self.assertFalse(sample["published"])
        self.assertFalse(sample["attached"])
        self.assertIn("not a customer ad", sample["claim_boundary"])
        self.assertFalse(marketplace["application_submitted"])
        self.assertFalse(marketplace["connects_spent"])
        self.assertFalse(marketplace["contract_observed"])
        self.assertFalse(marketplace["payment_observed"])
        self.assertIn("not a lead, contract, sale, or revenue", marketplace["policy"])

        sermon = campaign["marketplace_leads"]["cantonese_sermon_caption_delivery"]
        self.assertEqual(
            sermon["state"], "application_packet_ready_account_review_required"
        )
        self.assertIn("project-40689651", sermon["source_url"])
        self.assertIn("HKD 2,800", sermon["proposed_scope"]["price"])
        self.assertIn("funded Freelancer milestone", sermon["proposed_scope"]["start_gate"])
        self.assertEqual(
            sermon["proof"]["proof_commit"],
            "8db8e1722c85c626296f1306e7dca662439a6a6e",
        )
        self.assertEqual(len(sermon["proof"]["video_sha256"]), 64)
        self.assertIn("not a sermon", sermon["proof"]["claim_boundary"])
        self.assertEqual(
            sermon["application_packet"], "prepared_in_ignored_private_storage"
        )
        self.assertFalse(sermon["application_submitted"])
        self.assertEqual(sermon["bid_or_membership_spend"], 0)
        self.assertFalse(sermon["funded_milestone_observed"])
        self.assertFalse(sermon["contract_observed"])
        self.assertFalse(sermon["payment_observed"])
        self.assertIn("not a lead, contract, sale, or revenue", sermon["policy"])
        linkedin = campaign["channels"]["linkedin"]
        self.assertEqual(linkedin["state"], "postiz_queue")
        self.assertEqual(linkedin["publish_at"], "2026-09-15T02:00:00Z")
        self.assertEqual(linkedin["content"], linkedin["postiz_content"])
        self.assertIn("fixed USD 250 pack", linkedin["content"])
        self.assertIn("rights-cleared English lecture up to 20 minutes", linkedin["content"])
        self.assertIn("utm_source=linkedin", linkedin["destination"])
        self.assertFalse(linkedin["shortlink"])
        self.assertTrue(linkedin["verification"]["stored_text_exact"])
        self.assertIn("not leads or revenue", linkedin["policy"])

        x_analytics = campaign["channels"]["x"]["analytics_observation"]
        self.assertEqual(x_analytics["impressions"], 2)
        self.assertEqual(x_analytics["replies"], 0)
        self.assertFalse(x_analytics["lead_or_sale_observed"])

        guide = linkedin["practical_guide"]
        self.assertEqual(guide["state"], "postiz_queue")
        self.assertEqual(guide["publish_at"], "2026-09-24T02:00:00Z")
        self.assertEqual(guide["content"], guide["postiz_content"])
        self.assertIn("turn-lecture-into-bilingual-subtitles-study-guide", guide["destination"])
        self.assertIn("utm_source=linkedin", guide["destination"])
        self.assertFalse(guide["shortlink"])
        self.assertTrue(guide["verification"]["visible_editor_reviewed"])
        self.assertTrue(
            guide["verification"]["stored_text_exact_after_html_normalization"]
        )
        self.assertIn("not leads or revenue", guide["policy"])

        caption_post = linkedin["cantonese_caption_workflow"]
        self.assertEqual(caption_post["state"], "postiz_queue")
        self.assertEqual(caption_post["publish_at"], "2026-09-19T02:00:00Z")
        self.assertEqual(caption_post["content"], caption_post["postiz_content"])
        self.assertIn("Cantonese example", caption_post["content"])
        self.assertIn("rights-cleared", caption_post["content"])
        self.assertIn("8db8e1722c85c626296f1306e7dca662439a6a6e", caption_post["destination"])
        self.assertFalse(caption_post["shortlink"])
        self.assertEqual(len(caption_post["media_sha256"]), 64)
        self.assertTrue(caption_post["verification"]["postiz_media_upload_verified"])
        self.assertTrue(caption_post["verification"]["visible_editor_reviewed"])
        self.assertTrue(caption_post["verification"]["original_url_selected"])
        self.assertFalse(caption_post["lead_or_sale_observed"])
        self.assertEqual(caption_post["verified_received_gross_usd"], 0)
        self.assertIn("not claim sermon work", caption_post["policy"])

        blog_guide = campaign["channels"]["lazyblog"]["practical_workflow_guide"]
        self.assertEqual(
            blog_guide["search_discovery"]["request_state"],
            "accepted_priority_crawl_request",
        )
        self.assertFalse(blog_guide["search_discovery"]["indexed"])

        caption_guide = campaign["channels"]["lazyblog"][
            "cantonese_caption_workflow_guide"
        ]
        self.assertEqual(caption_guide["post_id"], 3803)
        self.assertEqual(caption_guide["blog_commit"], "3837aa6")
        self.assertEqual(caption_guide["source_commit"], "6191c8a")
        self.assertEqual(caption_guide["translations"], ["ja", "zh-hant"])
        self.assertEqual(
            caption_guide["search_discovery"]["request_state"],
            "accepted_priority_crawl_request",
        )
        self.assertFalse(caption_guide["search_discovery"]["indexed"])
        self.assertFalse(caption_guide["search_discovery"]["traffic_observed"])
        self.assertFalse(caption_guide["lead_or_sale_observed"])
        self.assertEqual(caption_guide["verified_received_gross_usd"], 0)
        self.assertIn("not customer work", caption_guide["policy"])

        sample = campaign["source_evidence"]["executed_media_sample"]
        preview = sample["social_preview"]
        self.assertEqual(preview["dimensions"], "1200x630")
        self.assertEqual(len(preview["sha256"]), 64)
        self.assertIn("lecture-pack/assets/", preview["url"])
        self.assertIn("project-owned", preview["claim_boundary"])

        delivery = campaign["source_evidence"]["complete_delivery_sample"]
        self.assertEqual(delivery["state"], "live_pinned_and_verified")
        self.assertEqual(delivery["archive_size_bytes"], 2542623)
        self.assertEqual(len(delivery["archive_sha256"]), 64)
        self.assertEqual(delivery["target_language"], "Traditional Chinese")
        self.assertIn("two-page A5", "\n".join(delivery["verified_outputs"]))
        self.assertEqual(delivery["transcript_review"]["resolved_items"], 5)
        self.assertEqual(delivery["transcript_review"]["unresolved_english_words"], 0)
        self.assertTrue(
            delivery["rebuild_verification"][
                "two_consecutive_builds_same_archive_sha256"
            ]
        )
        self.assertTrue(delivery["visible_live_review"]["media_playback_advanced"])
        self.assertFalse(delivery["customer_data_used"])
        self.assertFalse(delivery["lead_or_sale_observed"])
        self.assertEqual(delivery["verified_received_gross_usd"], 0)
        self.assertIn("not customer work", delivery["claim_boundary"])

        terms = campaign["source_evidence"]["working_terms_contract"]
        self.assertEqual(terms["state"], "live_verified")
        self.assertEqual(
            terms["website_commit"],
            "565421a3f4c08506a2fbb9c9af034f26199b598c",
        )
        self.assertEqual(terms["maximum_concurrent_packs"], 1)
        self.assertEqual(sum(terms["deliverable_allocation_usd"].values()), 250)
        self.assertEqual(terms["source_copy_retention_days"], 14)
        self.assertTrue(terms["verification"]["fit_check_links_to_terms"])
        self.assertEqual(terms["verification"]["deployment_conclusion"], "success")
        self.assertTrue(
            campaign["conversion_readiness"]["fit_check"]["working_terms_linked"]
        )
        fit_check = campaign["conversion_readiness"]["fit_check"]
        self.assertEqual(fit_check["offer_route"], "lecture")
        self.assertTrue(fit_check["explicit_review_confirmation"])
        self.assertFalse(fit_check["automatic_submission"])
        self.assertTrue(fit_check["direct_submit_available"])
        self.assertTrue(fit_check["synthetic_visible_round_trip_verified"])
        self.assertTrue(fit_check["receiver_authenticated_decrypted_and_saved"])
        self.assertTrue(fit_check["synthetic_local_payload_artifacts_removed"])
        self.assertTrue(fit_check["remote_spool_empty"])
        self.assertFalse(fit_check["lead_or_sale_observed"])
        self.assertEqual(fit_check["verified_received_gross_usd"], 0)
        payment = campaign["conversion_readiness"]["payment"]
        self.assertEqual(payment["state"], "ready_for_reviewed_live_request")
        self.assertEqual(payment["price"], "USD 250")
        self.assertEqual(payment["quantity"], 1)
        self.assertEqual(payment["fulfillment_review_notes"], 9)
        self.assertEqual(payment["private_key_file_mode"], "600")
        self.assertTrue(payment["live_key_format_valid"])
        self.assertTrue(payment["account_authenticated"])
        self.assertTrue(payment["charges_enabled"])
        self.assertTrue(payment["payouts_enabled"])
        self.assertTrue(payment["details_submitted"])
        self.assertFalse(payment["stripe_objects_created"])
        self.assertFalse(payment["public_payment_link"])
        self.assertIn("real buyer", payment["policy"].casefold())

        instagram = campaign["channels"]["instagram"]
        self.assertEqual(instagram["content"], instagram["postiz_content"])
        self.assertIn("15 timed lines", instagram["content"])
        self.assertIn("45 searchable language strings", instagram["content"])
        self.assertNotIn("45 searchable lines", instagram["content"])
        self.assertEqual(len(instagram["content_sha256"]), 64)
        self.assertTrue(instagram["visible_review"]["stored_text_exact"])
        self.assertTrue(instagram["visible_review"]["old_inaccurate_text_absent"])

    def test_bilingual_lecture_youtube_proof_completed_one_reviewed_publish(self):
        path = ROOT / "campaigns" / "bilingual-lecture-pack-pilot.json"
        campaign = json.loads(path.read_text(encoding="utf-8"))
        youtube = campaign["channels"]["youtube"]
        self.assertEqual(youtube["state"], "postiz_published")
        self.assertEqual(youtube["review"]["public_publish_attempts"], 1)
        self.assertTrue(youtube["review"]["visual_contact_sheet_checked"])
        self.assertTrue(youtube["review"]["metadata_checked"])
        self.assertTrue(youtube["review"]["hallucinated_caption_terms_removed"])
        self.assertEqual(len(youtube["video_sha256"]), 64)
        self.assertEqual(len(youtube["package_sha256"]), 64)
        self.assertEqual(youtube["publish_at"], "2026-09-05T02:30:00Z")
        self.assertEqual(youtube["content"], youtube["postiz_content"])
        self.assertEqual(
            youtube["content_sha256"],
            "ca984ae13b5b96f459f792dc39b0d726872abc3a09e0a55347d9cb708df25198",
        )
        self.assertEqual(
            youtube["release_url"],
            "https://www.youtube.com/watch?v=G9NKncZgRis",
        )
        self.assertTrue(youtube["review"]["postiz_media_upload_verified"])
        self.assertTrue(youtube["review"]["stored_text_exact"])
        self.assertFalse(youtube["review"]["shortlink"])
        self.assertEqual(youtube["review"]["stored_state"], "PUBLISHED")
        self.assertTrue(youtube["review"]["release_present"])
        self.assertEqual(youtube["review"]["public_visibility"], "public")
        self.assertTrue(youtube["review"]["public_title_exact"])
        self.assertTrue(youtube["review"]["public_playback_verified"])
        self.assertTrue(youtube["review"]["tracked_destinations_present"])
        self.assertIn("utm_source=youtube", youtube["destination"])
        self.assertIn("USD 250", youtube["policy"])
        self.assertIn("only publication route", youtube["queue_gate"])

        renderer = (ROOT / "scripts" / "render_lecture_pack_demo.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('item["start"] == "00:00:05.000"', renderer)
        self.assertIn('"Source and rights manifest"', renderer)
        self.assertIn('"One rights-cleared"', renderer)
        self.assertIn('"USD 250"', renderer)
        self.assertNotIn("customer result", renderer.casefold())

    def test_latex_redline_sample_matches_its_public_manifest(self):
        sample = ROOT / "examples" / "latex-redline"
        artifacts = sample / "artifacts"
        manifest = json.loads((artifacts / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["toolchain"]["latexdiff_tag"], "1.4.0")
        self.assertEqual(
            manifest["toolchain"]["latexdiff_commit"],
            "57d0ec532c41eb73645804d7f67667336da8bd01",
        )
        for name, path in {
            "baseline": sample / "baseline" / "main.tex",
            "revision": sample / "revision" / "main.tex",
        }.items():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, manifest["source_sha256"][name])
        for name in ("baseline", "revision", "redline"):
            pdf = artifacts / f"{name}.pdf"
            self.assertTrue(pdf.read_bytes().startswith(b"%PDF-"))
            digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
            self.assertEqual(digest, manifest["pdf_sha256"][name])
        self.assertEqual(manifest["verification"]["final_latex_errors"], 0)
        self.assertEqual(manifest["verification"]["final_undefined_references"], 0)
        for log in artifacts.glob("*-final.log"):
            content = log.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn("LaTeX Error", content)
            self.assertNotIn("There were undefined references", content)
            self.assertNotIn("Overfull", content)

    def test_latex_redline_delivery_packet_is_complete_and_verifiable(self):
        sample = ROOT / "examples" / "latex-redline"
        artifacts = sample / "artifacts"
        archive_path = artifacts / "sample-delivery.zip"
        checksum = (artifacts / "sample-delivery.zip.sha256").read_text(
            encoding="utf-8"
        ).split()[0]
        self.assertEqual(hashlib.sha256(archive_path.read_bytes()).hexdigest(), checksum)

        manifest = json.loads(
            (artifacts / "delivery-manifest.json").read_text(encoding="utf-8")
        )
        self.assertIn("Not customer work", manifest["evidence_boundary"])
        with ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            self.assertIn("DELIVERY.md", names)
            self.assertIn("ISSUE_LEDGER.md", names)
            self.assertIn("pdf/revision.pdf", names)
            self.assertIn("pdf/redline.pdf", names)
            self.assertIn("evidence/build-manifest.json", names)
            self.assertIn("evidence/delivery-manifest.json", names)
            self.assertEqual(
                json.loads(archive.read("evidence/delivery-manifest.json")), manifest
            )
            for name, digest in manifest["files"].items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
            self.assertIn(
                b"Unresolved build blockers in this synthetic sample: **0**",
                archive.read("ISSUE_LEDGER.md"),
            )

    def test_rtl_caption_fixture_is_bounded_and_verifiable(self):
        sample = ROOT / "examples" / "rtl-caption-feasibility"
        artifacts = sample / "artifacts"
        manifest = json.loads((artifacts / "manifest.json").read_text(encoding="utf-8"))

        self.assertIn("Renderer feasibility only", manifest["evidence_boundary"])
        self.assertIn("FriBidi", manifest["toolchain"]["shaping"])
        self.assertIn("HarfBuzz", manifest["toolchain"]["shaping"])
        verification = manifest["verification"]
        self.assertEqual(verification["duration_seconds"], 8)
        self.assertEqual(verification["dimensions"], "1080x1920")
        self.assertEqual(verification["video_codec"], "h264")
        self.assertEqual(verification["pixel_format"], "yuv420p")
        self.assertEqual(verification["frame_count"], 3)
        self.assertTrue(verification["directional_isolates_present"])
        self.assertFalse(verification["native_language_review"])

        subtitle = sample / "sample.ass"
        self.assertEqual(
            hashlib.sha256(subtitle.read_bytes()).hexdigest(),
            manifest["source_sha256"]["subtitles"],
        )
        outputs = {
            "video": artifacts / "rtl-caption-feasibility.mp4",
            "hebrew_frame": artifacts / "hebrew.png",
            "arabic_frame": artifacts / "arabic.png",
            "mixed_frame": artifacts / "mixed.png",
        }
        for name, path in outputs.items():
            with self.subTest(artifact=name):
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    manifest["output_sha256"][name],
                )
        self.assertEqual((artifacts / "rtl-caption-feasibility.mp4").read_bytes()[4:8], b"ftyp")
        for name in ("hebrew.png", "arabic.png", "mixed.png"):
            png = (artifacts / name).read_bytes()
            self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertEqual(int.from_bytes(png[16:20], "big"), 1080)
            self.assertEqual(int.from_bytes(png[20:24], "big"), 1920)

        build = (sample / "build.sh").read_text(encoding="utf-8")
        self.assertIn("directional_isolates_present", build)
        subtitles = subtitle.read_text(encoding="utf-8")
        self.assertIn("\u2067", subtitles)
        self.assertIn("\u2066", subtitles)
        self.assertIn("renderer test only", subtitles)

    def test_reply_prompt_uses_quiet_profile_led_promotion(self):
        candidate = {
            "platform": "reddit",
            "author": "reader",
            "source_url": "https://www.reddit.com/r/example/comments/voice/help/",
            "body": "How can I add subtitles to this video?",
        }
        prompt = promotion.draft_prompt(candidate, promotion.project_by_id("lazyedit"))
        self.assertIn("Let the account\n  profile carry", prompt)
        self.assertIn("Do not ask for stars, follows, votes, or DMs", prompt)
        self.assertIn("Prefer no reply", (ROOT / "docs" / "voice.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
