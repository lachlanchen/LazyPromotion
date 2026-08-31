import tempfile
import unittest
from datetime import datetime, timedelta, timezone
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

    def test_tool_announcement_is_not_a_help_request(self):
        body = "Open-source tool turns a topic into a full HD video with voice and subtitles"
        self.assertEqual(promotion.rank_projects(body), [])

    def test_game_mod_subtitles_do_not_match_video_editing(self):
        body = "Is there a mod to change commander voiceovers or add subtitles?"
        self.assertEqual(promotion.rank_projects(body), [])

    def test_hiring_post_is_out_of_scope(self):
        body = "[HIRING] Need a video editor to add subtitles to short clips"
        self.assertEqual(promotion.rank_projects(body), [])

    def test_old_candidate_is_marked_stale(self):
        published = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/old/help/",
            author="reader",
            body="I need advice on a Japanese graded reader for language learning practice",
            published_at=published,
            comment_count=13,
            source_score=23,
        )
        self.assertEqual(candidate["status"], "stale")
        self.assertEqual(candidate["comment_count"], 13)
        self.assertEqual(candidate["source_score"], 23)

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

    def test_exact_long_crosspost_is_marked_duplicate(self):
        body = (
            "I need help learning from these Susskind classical mechanics lectures. "
            "What prerequisites and extra resources should I use to understand the derivations "
            "and practice the ideas instead of only watching the videos?"
        )
        first = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/one/comments/abc/question/",
            author="same_author",
            body=body,
        )
        second = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/two/comments/def/question/",
            author="same_author",
            body=body,
        )
        refreshed = promotion.row_dict(
            self.db.execute("SELECT * FROM candidates WHERE id=?", (second["id"],)).fetchone()
        )
        self.assertEqual(refreshed["status"], "duplicate")
        self.assertEqual(refreshed["duplicate_of"], first["id"])

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
