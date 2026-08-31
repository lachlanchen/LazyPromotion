import json
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

    def test_incidental_help_word_is_not_a_request(self):
        body = "With a friend's help I added subtitles in the editor. Not bad."
        self.assertFalse(promotion.is_help_request(body))

    def test_promotional_caption_is_not_a_help_request(self):
        body = "Need a video editor? I got you. DM me and follow for more."
        self.assertFalse(promotion.is_help_request(body))

    def test_rhetorical_comment_is_not_a_triageable_request(self):
        body = "Why does it need a camera? I could understand subtitles, but why a camera?"
        url = "https://www.reddit.com/r/example/comments/post123/title/comment456/"
        self.assertTrue(promotion.is_help_request(body))
        self.assertTrue(promotion.is_comment_source("reddit", url, body))
        self.assertFalse(promotion.is_triageable_request("reddit", url, body))

    def test_direct_comment_request_is_triageable(self):
        body = "Does anyone know a reliable way to add subtitles automatically?"
        url = "https://news.ycombinator.com/item?id=12345"
        self.assertTrue(promotion.is_comment_source("hackernews", url, body))
        self.assertTrue(promotion.is_triageable_request("hackernews", url, body))

    def test_direct_instagram_comment_request_is_triageable(self):
        body = "Can someone recommend a reliable way to add subtitles automatically?"
        url = "https://www.instagram.com/p/post123/c/comment456/"
        self.assertTrue(promotion.is_comment_source("instagram", url, body))
        self.assertTrue(promotion.is_triageable_request("instagram", url, body))

    def test_ask_hn_title_is_an_explicit_request_without_question_mark(self):
        body = "Ask HN: Are third party GGUF models safe in a local production environment"
        self.assertTrue(promotion.is_help_request(body))

    def test_volunteer_opportunity_is_not_a_request_for_a_tool(self):
        body = "Volunteer opportunities: help us add subtitles and branding to our videos."
        self.assertFalse(promotion.is_help_request(body))

    def test_automoderator_candidate_has_no_project_match(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/bot/thread/",
            author="AutoModerator",
            body="What video editing software should I use for captions and subtitles?",
        )
        self.assertEqual(candidate["score"], 0)
        self.assertEqual(candidate["suggested_tool"], "")

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

    def test_model_triage_decision_controls_candidate_status(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/triage/help/",
            author="reader",
            body="How can I add accurate subtitles to my Instagram video?",
        )
        triaged = promotion.save_triage(
            self.db,
            candidate["id"],
            {"eligible": True, "confidence": "high", "reason": "Direct video subtitle need", "risk_flags": []},
        )
        self.assertEqual(triaged["status"], "triaged")
        self.assertEqual(triaged["triage_confidence"], "high")

    def test_rejected_triage_is_not_reviewable(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/reject/help/",
            author="reader",
            body="How can I add accurate subtitles to my Instagram video?",
        )
        rejected = promotion.save_triage(
            self.db,
            candidate["id"],
            {"eligible": False, "confidence": "high", "reason": "Already resolved", "risk_flags": ["resolved"]},
        )
        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(json.loads(rejected["triage_risk_flags"]), ["resolved"])

    def test_changed_candidate_resets_model_triage(self):
        url = "https://www.reddit.com/r/example/comments/edited/help/"
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url=url,
            author="reader",
            body="How can I add accurate subtitles to my Instagram video?",
        )
        promotion.save_triage(
            self.db,
            candidate["id"],
            {"eligible": True, "confidence": "high", "reason": "Direct need", "risk_flags": []},
        )
        refreshed = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url=url,
            author="reader",
            body="How can I add accurate subtitles to my longer Instagram video and review an SRT file?",
        )
        self.assertEqual(refreshed["status"], "discovered")
        self.assertEqual(refreshed["triage_reason"], "")
        self.assertEqual(refreshed["triaged_at"], "")

    def test_short_search_card_does_not_reset_rejected_full_post(self):
        url = "https://www.reddit.com/r/example/comments/card/help/"
        full = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url=url,
            author="reader",
            body=(
                "How can I add accurate subtitles to my Instagram video? "
                "I have tried the built-in editor and need an SRT workflow."
            ),
        )
        promotion.save_triage(
            self.db,
            full["id"],
            {"eligible": False, "confidence": "high", "reason": "Not a fit", "risk_flags": []},
        )
        rediscovered = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url=url,
            author="reader",
            body="How can I add accurate subtitles to my Instagram video?",
        )
        self.assertEqual(rediscovered["status"], "rejected")
        self.assertIn("SRT workflow", rediscovered["body"])

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

    def test_rejected_invalid_copy_does_not_hide_live_candidate(self):
        body = (
            "I need help choosing a local knowledge base for a small team. "
            "How should we share context and keep decisions current across machines?"
        )
        broken = promotion.ingest_candidate(
            self.db,
            platform="hackernews",
            source_url="https://news.ycombinator.com/item",
            author="same_author",
            body=body,
        )
        self.db.execute("UPDATE candidates SET status='rejected' WHERE id=?", (broken["id"],))
        self.db.commit()
        live = promotion.ingest_candidate(
            self.db,
            platform="hackernews",
            source_url="https://news.ycombinator.com/item?id=12345",
            author="same_author",
            body=body,
        )
        self.assertEqual(live["status"], "discovered")
        self.assertEqual(live["duplicate_of"], "")

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

    def test_instagram_comment_draft_includes_exact_target_mention(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="instagram",
            source_url="https://www.instagram.com/p/post123/c/comment456/",
            author="questioner",
            body="Can someone recommend a reliable way to add subtitles automatically?",
        )
        draft = promotion.save_draft(
            self.db,
            candidate["id"],
            {"reply": "A useful answer", "why": "direct", "confidence": "high", "include_link": False},
        )
        self.assertEqual(draft["body"], "@questioner A useful answer")

        revised = promotion.save_draft(
            self.db,
            candidate["id"],
            {"reply": "@questioner, Another useful answer", "why": "direct", "confidence": "high", "include_link": False},
        )
        self.assertEqual(revised["body"], "@questioner, Another useful answer")

    def test_new_draft_supersedes_old_approval(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/revision/test/",
            body="Looking for a bilingual Japanese reader",
        )
        first = promotion.save_draft(
            self.db,
            candidate["id"],
            {"reply": "First reviewed answer", "why": "first", "confidence": "high", "include_link": False},
        )
        approval = promotion.approve_draft(self.db, first["id"], 30)
        second = promotion.save_draft(
            self.db,
            candidate["id"],
            {"reply": "Improved reviewed answer", "why": "second", "confidence": "high", "include_link": False},
        )
        old = self.db.execute("SELECT status FROM drafts WHERE id=?", (first["id"],)).fetchone()
        self.assertEqual(old["status"], "superseded")
        self.assertEqual(second["status"], "draft")
        with self.assertRaisesRegex(ValueError, "no longer active"):
            promotion.validate_approval(self.db, first["id"], approval["approval_token"])


if __name__ == "__main__":
    unittest.main()
