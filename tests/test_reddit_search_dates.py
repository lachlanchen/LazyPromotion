"""Exercise the actual DOM extractors, including Reddit's pre-hydration dates."""

from datetime import datetime, timezone
import shutil
import unittest

from playwright.sync_api import sync_playwright

import browser
import promotion


CHROME = shutil.which("google-chrome") or shutil.which("chromium")
STAMP = "2026-07-29T23:04:52.879000+0000"
HYDRATED = "2026-07-29T23:04:52.879Z"
POST_URL = "https://www.reddit.com/r/example/comments/abc123/test/"
COMMENT_URL = POST_URL + "def456/"


@unittest.skipUnless(CHROME, "Chrome is required for the synthetic DOM contract")
class RedditSearchDateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        cls.chrome = cls.playwright.chromium.launch(executable_path=CHROME, headless=True)
        cls.addClassCleanup(cls.chrome.close)

    def setUp(self):
        self.page = self.chrome.new_page()
        self.addCleanup(self.page.close)
        self.page.route("**/*", lambda route: route.abort())

    def post(self, date_markup):
        return f'''<article data-testid="search-post-unit">
          <search-telemetry-tracker data-faceplate-tracking-context='{{"profile":{{"name":"maker"}}}}'>
          </search-telemetry-tracker>
          <a data-testid="post-title-text" href="{POST_URL}">Need a reading tool</a>
          {date_markup}
          <div data-testid="search-counter-row">
            <faceplate-number number="4"></faceplate-number>
            <faceplate-number number="2"></faceplate-number>
          </div></article>'''

    def comment(self, date_markup):
        return f'''<search-telemetry-tracker view-events="search/view/comment"
          data-faceplate-tracking-context='{{"comment":{{"id":"t1_def456"}}}}'>
          <article data-testid="search-sdui-comment-unit">
            <time datetime="2026-09-25T00:00:00Z">parent post date</time>
            <faceplate-timeago ts="2026-09-25T00:00:00Z"></faceplate-timeago>
            <div data-testid="search-comment-content">
              <faceplate-hovercard data-id="user-hover-card"><a>reader</a></faceplate-hovercard>
              <a aria-labelledby="comment-content-def456" href="{COMMENT_URL}">Comment</a>
              <div id="search-comment-def456-post-rtjson-content">I have the same question</div>
              {date_markup}<p><faceplate-number number="3"></faceplate-number></p>
            </div>
          </article></search-telemetry-tracker>'''

    def test_unhydrated_post_has_absolute_date_and_retains_other_fields(self):
        self.page.set_content(self.post(f'<faceplate-timeago ts="{STAMP}">2mo ago</faceplate-timeago>'))
        rows = browser.extract_reddit(self.page, 10)
        self.assertEqual(rows, [{
            "url": POST_URL, "author": "maker", "published_at": STAMP,
            "source_score": "4", "comment_count": "2", "body": "Need a reading tool",
        }])
        parsed = promotion.parse_source_time(rows[0]["published_at"])
        self.assertEqual(parsed, datetime(2026, 7, 29, 23, 4, 52, 879000, timezone.utc))
        self.assertTrue(promotion.is_stale(
            rows[0]["published_at"], now=datetime(2026, 9, 26, tzinfo=timezone.utc),
        ))

    def test_hydrated_post_prefers_canonical_time(self):
        self.page.set_content(self.post(
            f'<faceplate-timeago ts="{STAMP}"><time datetime="{HYDRATED}">2mo ago</time></faceplate-timeago>',
        ))
        self.assertEqual(browser.extract_reddit(self.page, 1)[0]["published_at"], HYDRATED)

    def test_missing_absolute_post_date_stays_unknown_and_limit_is_kept(self):
        self.page.set_content(
            '<time datetime="2026-09-25T00:00:00Z">outside card</time>'
            + self.post('<faceplate-timeago>1h ago</faceplate-timeago>') * 2,
        )
        rows = browser.extract_reddit(self.page, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["published_at"], "")
        self.assertIsNone(promotion.parse_source_time(rows[0]["published_at"]))

    def test_unhydrated_comment_uses_its_date_not_parent_post_date(self):
        self.page.set_content(self.comment(f'<faceplate-timeago ts="{STAMP}"></faceplate-timeago>'))
        rows = browser.extract_reddit_comments(self.page, 10)
        self.assertEqual(rows, [{
            "url": COMMENT_URL, "author": "reader", "published_at": STAMP,
            "comment_count": "0", "source_score": "3", "body": "I have the same question",
            "comment_id": "t1_def456",
        }])

    def test_hydrated_comment_prefers_canonical_time(self):
        self.page.set_content(self.comment(
            f'<faceplate-timeago ts="{STAMP}"><time datetime="{HYDRATED}">2mo ago</time></faceplate-timeago>',
        ))
        self.assertEqual(browser.extract_reddit_comments(self.page, 1)[0]["published_at"], HYDRATED)

    def test_missing_comment_date_does_not_borrow_parent_or_relative_label(self):
        self.page.set_content(self.comment('<faceplate-timeago>1h ago</faceplate-timeago>') * 2)
        rows = browser.extract_reddit_comments(self.page, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["published_at"], "")

    def test_shreddit_timestamp_attribute_is_unchanged(self):
        self.page.set_content(
            f'<shreddit-post created-timestamp="{STAMP}" content-href="{POST_URL}" '
            'author="maker" post-title="Question" comment-count="2" score="4"></shreddit-post>',
        )
        self.assertEqual(browser.extract_reddit(self.page, 1)[0]["published_at"], STAMP)


if __name__ == "__main__":
    unittest.main()
