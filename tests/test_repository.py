import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_x_go_route_is_qualified_as_the_board_game(self):
        route = next(
            item for item in browser.discovery_queries("x")
            if item["project_id"] == "lazyweiqi"
        )
        query = route["query"].casefold()
        self.assertTrue(any(term in query for term in ("weiqi", "baduk", "board game")))
        self.assertNotEqual(query, '"learn go" (advice or resources) -filter:retweets')

    def test_generated_brand_routes_use_need_oriented_topic_overrides(self):
        expected = {
            "github-cellist": "python environment import verification",
            "github-glassagent-wearable-releases": "ai glasses setup",
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
        self.assertEqual(campaign["version"], 1)
        self.assertEqual(campaign["channels"]["x"]["state"], "postiz_draft")
        self.assertEqual(campaign["channels"]["instagram"]["state"], "postiz_draft")
        self.assertLessEqual(len(campaign["channels"]["x"]["content"]), 280)
        self.assertLessEqual(len(campaign["channels"]["instagram"]["content"]), 2200)
        self.assertIn("utm_source=instagram", campaign["channels"]["instagram"]["content"])
        self.assertNotIn("integration_id", serialized.casefold())
        self.assertNotIn("post_id", serialized.casefold())

    def test_eink_campaign_has_a_truthful_measurable_offer(self):
        path = ROOT / "campaigns" / "eink-multilingual-reading.json"
        campaign = json.loads(path.read_text(encoding="utf-8"))
        serialized = path.read_text(encoding="utf-8")
        self.assertEqual(campaign["version"], 1)
        self.assertEqual(campaign["source_evidence"]["offer_stage"], "pre-order")
        self.assertEqual(campaign["source_evidence"]["public_price"], "USD 128 / CNY 999")
        self.assertIn("email inquiry", campaign["source_evidence"]["current_order_mode"])
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
        self.assertEqual(
            campaign["source_evidence"]["offer_stage"],
            "founding collection-fit sprint",
        )
        self.assertEqual(campaign["source_evidence"]["public_price"], "USD 250")
        self.assertIn("free fit check", campaign["source_evidence"]["current_order_mode"])
        self.assertEqual(campaign["channels"]["hackernews"]["state"], "research_only")
        self.assertIn("no detected software license", serialized)
        self.assertIn("four confirmed usd 250 payments", serialized)
        self.assertIn("confirmed payment", serialized)
        self.assertNotIn("integration_id", serialized)
        self.assertNotIn("post_id", serialized)

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
