import tempfile
import unittest
from pathlib import Path

import promotion


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = promotion.open_db(Path(self.tmp.name) / "test.sqlite3")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_subtitle_need_matches_lazyedit(self):
        ranked = promotion.rank_projects("I can't understand this Instagram video. How can I add English subtitles?")
        self.assertEqual(ranked[0]["project"]["id"], "lazyedit")
        self.assertGreaterEqual(ranked[0]["score"], 5)

    def test_language_reader_matches_pocketpolyglot(self):
        ranked = promotion.rank_projects("Looking for a bilingual Japanese reader with furigana for reading practice")
        self.assertEqual(ranked[0]["project"]["id"], "pocketpolyglot")

    def test_irrelevant_post_has_no_match(self):
        self.assertEqual(promotion.rank_projects("Lovely weather at the beach today"), [])

    def test_candidate_ingest_is_idempotent(self):
        one = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/abc/test/",
            body="Need help adding subtitles to a video",
        )
        two = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/abc/test/",
            body="Need help adding subtitles to a video please",
        )
        self.assertEqual(one["id"], two["id"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 1)

    def test_approval_is_bound_to_exact_content(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/xyz/test/",
            body="Looking for a bilingual Japanese reader",
        )
        draft = promotion.save_draft(
            self.db,
            candidate["id"],
            {"reply": "Useful answer. I maintain https://example.test", "why": "direct match", "confidence": "high", "include_link": True},
        )
        approval = promotion.approve_draft(self.db, draft["id"], 30)
        promotion.validate_approval(self.db, draft["id"], approval["approval_token"])
        self.db.execute("UPDATE drafts SET body='changed' WHERE id=?", (draft["id"],))
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "changed after approval"):
            promotion.validate_approval(self.db, draft["id"], approval["approval_token"])


if __name__ == "__main__":
    unittest.main()
