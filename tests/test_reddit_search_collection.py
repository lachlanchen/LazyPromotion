"""Bounded, read-only pagination; sparse results never mean complete coverage."""

import unittest
from unittest.mock import patch

import browser


def row(number):
    return {"url": f"https://www.reddit.com/r/example/comments/post{number}/question/",
            "body": f"Reader question {number}", "published_at": "2026-09-25T00:00:00Z"}


class FakeSearchPage:
    def __init__(self, batches, *, timeout=False, redirected=False):
        self.batches = batches
        self.batch = 0
        self.url = "https://www.reddit.com/search/?q=reading"
        self.timeout = timeout
        self.redirected = redirected
        self.mouse = self
        self.last = self
        self.scroll_calls = 0
        self.selectors = []

    def locator(self, selector):
        self.selectors.append(selector)
        return self

    def count(self):
        return len(self.batches[self.batch])

    def scroll_into_view_if_needed(self, **kwargs):
        self.scroll_calls += 1

    def wheel(self, x, y):
        pass

    def wait_for_function(self, expression, *, arg, timeout):
        if self.timeout or self.batch + 1 == len(self.batches):
            raise browser.PlaywrightTimeoutError("No additional cards observed")
        self.batch += 1
        if self.redirected:
            self.url = "https://www.reddit.com/login/"

    def extract(self, page, limit):
        return self.batches[self.batch][:limit]


class RedditSearchCollectionTests(unittest.TestCase):
    def collect(self, page, limit=12, kind="posts", max_scrolls=3):
        name = "extract_reddit_comments" if kind == "comments" else "extract_reddit"
        with patch.object(browser, name, side_effect=page.extract):
            return browser.collect_reddit_search(page, limit, kind, max_scrolls=max_scrolls)

    def test_initial_batch_is_not_mistaken_for_the_requested_limit(self):
        page = FakeSearchPage([[row(i) for i in range(7)], [row(i) for i in range(14)]])
        rows, receipt = self.collect(page)
        self.assertEqual(len(rows), 12)
        self.assertEqual(receipt["initial_count"], 7)
        self.assertEqual(receipt["scrolls"], 1)
        self.assertEqual(receipt["stop_reason"], "requested_limit")
        self.assertFalse(receipt["exhaustive"])
        self.assertTrue(all(r["published_at"] == "2026-09-25T00:00:00Z" for r in rows))

    def test_already_loaded_limit_needs_no_scroll(self):
        page = FakeSearchPage([[row(1), row(2)]])
        rows, receipt = self.collect(page, 2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(page.scroll_calls, 0)
        self.assertEqual(receipt["stop_reason"], "requested_limit")

    def test_empty_or_unrecognized_page_does_not_trigger_a_scroll_loop(self):
        page = FakeSearchPage([[]])
        rows, receipt = self.collect(page)
        self.assertEqual(rows, [])
        self.assertEqual(page.scroll_calls, 0)
        self.assertEqual(receipt["stop_reason"], "no_loaded_cards")
        self.assertFalse(receipt["exhaustive"])

    def test_timeout_keeps_existing_rows_without_claiming_exhaustion(self):
        page = FakeSearchPage([[row(1)]], timeout=True)
        rows, receipt = self.collect(page)
        self.assertEqual(len(rows), 1)
        self.assertEqual(page.scroll_calls, 1)
        self.assertEqual(receipt["stop_reason"], "load_timeout")
        self.assertFalse(receipt["exhaustive"])

    def test_duplicate_cards_stop_without_duplicate_candidates(self):
        page = FakeSearchPage([[row(1)], [row(1), row(1)]])
        rows, receipt = self.collect(page)
        self.assertEqual(len(rows), 1)
        self.assertEqual(receipt["stop_reason"], "no_new_unique_results")

    def test_maximum_scroll_budget_is_enforced(self):
        page = FakeSearchPage([[row(i) for i in range(n)] for n in range(1, 7)])
        rows, receipt = self.collect(page)
        self.assertEqual(len(rows), 4)
        self.assertEqual(page.scroll_calls, 3)
        self.assertEqual(receipt["stop_reason"], "scroll_limit")

    def test_comment_search_uses_its_own_cards(self):
        page = FakeSearchPage([[row(1)], [row(1), row(2)]])
        rows, receipt = self.collect(page, 2, "comments")
        self.assertEqual(len(rows), 2)
        self.assertEqual(page.selectors, ['[data-testid="search-sdui-comment-unit"]'])

    def test_redirect_is_not_followed_or_read_as_more_results(self):
        page = FakeSearchPage([[row(1)], [row(2), row(3)]], redirected=True)
        rows, receipt = self.collect(page)
        self.assertEqual([r["body"] for r in rows], ["Reader question 1"])
        self.assertEqual(receipt["stop_reason"], "source_changed")

    def test_invalid_arguments_and_non_search_pages_are_rejected(self):
        page = FakeSearchPage([[row(1)]])
        for kwargs in ({"limit": 0}, {"max_scrolls": 6}, {"kind": "unknown"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.collect(page, **kwargs)
        page.url = "https://example.com/search/"
        with self.assertRaises(ValueError):
            self.collect(page)

    def test_discovery_ingests_collected_rows_and_reports_coverage(self):
        page = FakeSearchPage([[row(1)]])
        page.goto = lambda *args, **kwargs: None
        page.title = lambda: "Reddit Search"
        rows = browser.dedupe([row(1), row(2)], 2)
        receipt = {"initial_count": 1, "collected_count": 2, "exhaustive": False}
        with patch.object(browser, "wait_ready"), \
                patch.object(browser, "collect_reddit_search", return_value=(rows, receipt)) as collect, \
                patch.object(browser, "evidence", return_value="private-screenshot"), \
                patch.object(browser.promotion, "open_db"), \
                patch.object(browser.promotion, "ingest_candidate", side_effect=["first", "second"]) as ingest:
            result = browser.discover(page, "reddit", "reading", 2)
        collect.assert_called_once_with(page, 2, "posts")
        self.assertEqual(ingest.call_count, 2)
        self.assertEqual(result["candidates"], ["first", "second"])
        self.assertEqual(result["collection"], receipt)
        self.assertEqual(result["screenshot"], "private-screenshot")

    def test_other_platform_search_evidence_still_precedes_hydration(self):
        page = FakeSearchPage([[row(1)]])
        page.goto = lambda *args, **kwargs: None
        page.title = lambda: "Search"
        steps = []
        with patch.object(browser, "wait_ready"), \
                patch.object(browser, "collect_reddit_search") as collect, \
                patch.object(browser, "evidence", side_effect=lambda *args: steps.append("search_evidence")), \
                patch.object(browser, "extract_instagram", return_value=[row(1)]), \
                patch.object(browser, "hydrate_instagram_rows", side_effect=lambda *args: steps.append("hydrate") or [row(1)]), \
                patch.object(browser.promotion, "open_db"), \
                patch.object(browser.promotion, "ingest_candidate", return_value="first"):
            result = browser.discover(page, "instagram", "reading", 1)
        collect.assert_not_called()
        self.assertEqual(steps, ["search_evidence", "hydrate"])
        self.assertIsNone(result["collection"])


if __name__ == "__main__":
    unittest.main()
