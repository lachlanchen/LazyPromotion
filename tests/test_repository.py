import json
import unittest
from pathlib import Path

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

    def test_private_runtime_paths_are_ignored(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".local/", ignored)
        self.assertIn("handoff/", ignored)


if __name__ == "__main__":
    unittest.main()
