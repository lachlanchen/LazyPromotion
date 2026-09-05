import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

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

    def test_rights_cleared_lecture_package_matches_video2book(self):
        ranked = promotion.rank_projects(
            "I own a 15 minute lecture recording and need a bilingual study guide "
            "from the video with timestamped subtitles. What workflow should I use?"
        )
        self.assertEqual(ranked[0]["project"]["id"], "video2book")
        self.assertEqual(
            ranked[0]["project"]["homepage"],
            "https://lazying.art/lecture-pack/",
        )
        self.assertIn("rights-cleared English lecture", ranked[0]["project"]["reply_context"])

    def test_latex_build_and_redline_need_matches_paperagent(self):
        ranked = promotion.rank_projects(
            "I need help making my LaTeX manuscript compile in Overleaf and producing "
            "a clean latexdiff redline for the journal."
        )
        self.assertEqual(ranked[0]["project"]["id"], "paperagent")
        self.assertEqual(
            ranked[0]["project"]["reply_url"],
            "https://lazying.art/manuscript-sprint/fit-check/",
        )
        self.assertIn("does not include ghostwriting", ranked[0]["project"]["reply_context"])

    def test_language_reader_matches_pocketpolyglot(self):
        ranked = promotion.rank_projects("Looking for a bilingual Japanese reader with furigana for reading practice")
        self.assertEqual(ranked[0]["project"]["id"], "pocketpolyglot")

    def test_l_and_n_pronunciation_need_matches_focused_app(self):
        ranked = promotion.rank_projects(
            "I confuse L and N and need an L and N pronunciation app with minimal pairs."
        )
        self.assertEqual(ranked[0]["project"]["id"], "l-and-n")
        self.assertEqual(
            ranked[0]["project"]["homepage"],
            "https://l-and-n.lazying.art/",
        )
        self.assertIn("free no-signup PWA", ranked[0]["project"]["reply_context"])

    def test_multilingual_eink_purchase_need_matches_public_offer(self):
        ranked = promotion.rank_projects(
            "Can anyone recommend an e-ink reader for multilingual language learning?"
        )
        self.assertEqual(ranked[0]["project"]["id"], "lazyingart-eink")
        self.assertEqual(ranked[0]["project"]["homepage"], "https://lazying.art/eink/")

    def test_private_local_rag_fit_request_matches_bounded_lkt_service(self):
        ranked = promotion.rank_projects(
            "What is the best local RAG for confidential text logs and a PDF collection? "
            "I need simple document search on a CPU-only machine."
        )
        self.assertEqual(ranked[0]["project"]["id"], "localknowledgeterminal")
        self.assertIn("not a finished RAG application", ranked[0]["project"]["reply_context"])
        self.assertEqual(
            ranked[0]["project"]["reply_url"],
            "https://lazying.art/lkt/fit-check/",
        )

    def test_local_rag_keyword_requires_technical_context(self):
        technical = promotion.rank_projects(
            "I need help with a local RAG setup for an LLM."
        )
        self.assertEqual(technical[0]["project"]["id"], "localknowledgeterminal")

        newspaper = promotion.rank_projects(
            "I recommend the pizza place; our local rag of a newspaper reviewed it."
        )
        self.assertNotIn(
            "localknowledgeterminal",
            {item["project"]["id"] for item in newspaper},
        )

    def test_triage_sees_reviewed_offer_context_and_boundary(self):
        project = promotion.project_by_id("localknowledgeterminal")
        prompt = promotion.triage_prompt(
            {
                "platform": "reddit",
                "source_url": "https://www.reddit.com/r/Rag/comments/example/help/",
                "author": "reader",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "comment_count": 2,
                "body": "Can someone recommend a private local workflow for my PDFs?",
                "suggested_tool": "localknowledgeterminal",
            },
            [project],
        )
        self.assertIn("reviewed_context", prompt)
        self.assertIn('"reply_url": "https://lazying.art/lkt/fit-check/"', prompt)
        self.assertIn("private-by-design collection-fit service", prompt)
        self.assertIn("not a finished RAG application", prompt)
        self.assertIn("https://lazying.art/lkt/sample-report/", prompt)
        self.assertIn("docs/sample-fit-report.md", prompt)
        self.assertIn("not a customer result", prompt)

    def test_value_only_draft_policy_forbids_project_and_links(self):
        candidate = {
            "platform": "reddit",
            "author": "reader",
            "source_url": "https://www.reddit.com/r/Rag/comments/example/help/",
            "body": "What is a simple way to search local PDFs?",
        }
        project = promotion.project_by_id("localknowledgeterminal")
        prompt = promotion.draft_prompt(candidate, project, value_only=True)
        self.assertIn("Provide value only", prompt)
        self.assertIn("Set include_link=false", prompt)

        safe = {
            "reply": "Start with full-text search and measure misses before adding embeddings.",
            "why": "Direct answer.",
            "confidence": "high",
            "include_link": False,
        }
        with patch("promotion.run_codex_structured", return_value=safe):
            self.assertEqual(
                promotion.run_codex_draft(candidate, project, value_only=True),
                safe,
            )

        unsafe = {**safe, "reply": "I maintain LocalKnowledgeTerminal: https://example.com"}
        with patch("promotion.run_codex_structured", return_value=unsafe):
            with self.assertRaisesRegex(ValueError, "URL"):
                promotion.run_codex_draft(candidate, project, value_only=True)

    def test_draft_can_require_exact_community_disclosure_prefix(self):
        candidate = {
            "platform": "reddit",
            "author": "reader",
            "source_url": "https://www.reddit.com/r/degoogle/comments/example/help/",
            "body": "What is a simple way to search local PDFs?",
        }
        project = promotion.project_by_id("localknowledgeterminal")
        prefix = "AI-assisted recommendation; I checked the current docs before posting."
        prompt = promotion.draft_prompt(
            candidate,
            project,
            value_only=True,
            required_prefix=prefix,
        )
        self.assertIn(prefix, prompt)
        self.assertIn("Begin the reply with this exact text", prompt)

        safe = {
            "reply": f"{prefix} Start with full-text search and measure the misses.",
            "why": "Direct answer with the required disclosure.",
            "confidence": "high",
            "include_link": False,
        }
        with patch("promotion.run_codex_structured", return_value=safe):
            self.assertEqual(
                promotion.run_codex_draft(
                    candidate,
                    project,
                    value_only=True,
                    required_prefix=prefix,
                ),
                safe,
            )

        missing = {**safe, "reply": "Start with full-text search and measure the misses."}
        with patch("promotion.run_codex_structured", return_value=missing):
            with self.assertRaisesRegex(ValueError, "required disclosure"):
                promotion.run_codex_draft(
                    candidate,
                    project,
                    value_only=True,
                    required_prefix=prefix,
                )

    def test_chinese_wenyan_help_matches_multilingual_reading_projects(self):
        body = "我看不懂文言文，有没有带现代中文和英文的中国历史读本推荐？"
        self.assertTrue(promotion.is_help_request(body))
        ranked = promotion.rank_projects(body)
        self.assertTrue(ranked)
        self.assertIn(ranked[0]["project"]["id"], {"pocketpolyglot", "lingualleaf"})
        self.assertTrue({"文言文", "中国历史"} & set(ranked[0]["matches"]))

    def test_japanese_help_intent_is_recognized(self):
        body = "漢文が読めないので、現代語訳つきの中国史の本をおすすめしてください。"
        self.assertTrue(promotion.is_help_request(body))

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

    def test_job_application_comment_is_out_of_scope(self):
        body = "Sir how can I apply"
        url = "https://www.instagram.com/p/post123/c/comment456/"
        self.assertFalse(promotion.is_help_request(body))
        self.assertFalse(promotion.is_triageable_request("instagram", url, body))

    def test_incidental_help_word_is_not_a_request(self):
        body = "With a friend's help I added subtitles in the editor. Not bad."
        self.assertFalse(promotion.is_help_request(body))

    def test_promotional_caption_is_not_a_help_request(self):
        body = "Need a video editor? I got you. DM me and follow for more."
        self.assertFalse(promotion.is_help_request(body))

    def test_opinion_using_problem_word_does_not_spend_triage_quota(self):
        body = (
            "AI music has a short-term quality problem. AI can't play an "
            "instrument live, but listeners already ignore it and nothing "
            "consequential has shifted."
        )
        self.assertFalse(promotion.is_help_request(body))

    def test_promotional_needs_language_is_not_a_request(self):
        body = (
            "Intelligence needs tools to become useful. We launched a visual "
            "agent platform that turns analysis into action."
        )
        self.assertFalse(promotion.is_help_request(body))

    def test_hiring_listing_with_question_is_out_of_scope(self):
        body = (
            "InfoHawk | Software Engineer | Full-time | Technologies: Python, "
            "Playwright. Can you adapt scrapers when sources change?"
        )
        self.assertFalse(promotion.is_help_request(body))

    def test_direct_first_person_request_without_question_mark_is_kept(self):
        body = "I need help searching my private PDF collection offline"
        self.assertTrue(promotion.is_help_request(body))

    def test_existing_solution_announcement_does_not_spend_triage_quota(self):
        body = (
            "I created a private document search tool. You don't need to wait; "
            "my tool searches local meeting PDFs and I linked it below."
        )
        signals = promotion.help_request_signals(body)
        self.assertIn("i created", signals["existing_solution_hits"])
        self.assertFalse(promotion.is_help_request(body))
        self.assertEqual(promotion.rank_projects(body), [])

    def test_tested_product_caption_without_unresolved_request_is_filtered(self):
        body = (
            "What happens when you ask AI to make a product video? I tested "
            "three tools and published the results below."
        )
        self.assertFalse(promotion.is_help_request(body))

    def test_builder_with_direct_unresolved_request_can_still_be_triaged(self):
        body = (
            "I built a rough local PDF index, but I need help with citations. "
            "Can someone recommend a reliable design?"
        )
        self.assertEqual(promotion.help_request_signals(body)["existing_solution_hits"], [])
        self.assertTrue(promotion.is_help_request(body))

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

    def test_x_reply_requires_a_direct_request(self):
        url = "https://x.com/example/status/12345"
        commentary = "Replying to @someone: what an interesting use of generated video?"
        request = "Replying to @someone: can someone recommend a caption workflow?"
        self.assertTrue(promotion.is_comment_source("x", url, commentary))
        self.assertFalse(promotion.is_triageable_request("x", url, commentary))
        self.assertTrue(promotion.is_triageable_request("x", url, request))

    def test_long_advice_comment_does_not_match_embedded_request_language(self):
        body = (
            "Here is the design advice I promised. "
            + ("Explain each step and its tradeoffs. " * 40)
            + 'Ask "how do I get this result," then break it into processes.'
        )
        url = "https://www.reddit.com/r/example/comments/post123/title/comment456/"
        self.assertTrue(promotion.is_help_request(body))
        self.assertFalse(promotion.is_triageable_request("reddit", url, body))

    def test_contextual_comment_with_request_at_end_is_kept(self):
        body = (
            "I have a private research collection with several formats. "
            + ("The files contain technical names and citations. " * 20)
            + "Can someone recommend a reliable offline search workflow?"
        )
        url = "https://www.reddit.com/r/example/comments/post123/title/comment789/"
        self.assertTrue(promotion.is_triageable_request("reddit", url, body))

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
        promotion.mark_triage_requested(self.db, [candidate["id"]])
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
        self.assertEqual(refreshed["triage_requested_at"], "")

    def test_changed_drafted_candidate_invalidates_review_artifact(self):
        url = "https://www.reddit.com/r/example/comments/expanded/help/"
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url=url,
            author="reader",
            body="How can I add subtitles to a video?",
        )
        promotion.save_triage(
            self.db,
            candidate["id"],
            {
                "eligible": True,
                "project_id": "lazyedit",
                "confidence": "high",
                "reason": "Direct subtitle need",
                "risk_flags": [],
            },
        )
        draft = promotion.save_draft(
            self.db,
            candidate["id"],
            {
                "reply": "Use a reviewed SRT workflow. I maintain LazyEdit.",
                "why": "direct",
                "confidence": "high",
                "include_link": False,
            },
        )
        refreshed = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url=url,
            author="reader",
            body=(
                "How can I add subtitles to a video? I also need to translate the "
                "captions and review an SRT file before publishing."
            ),
        )
        saved_draft = self.db.execute(
            "SELECT status FROM drafts WHERE id=?", (draft["id"],)
        ).fetchone()
        self.assertEqual(refreshed["status"], "discovered")
        self.assertEqual(refreshed["triage_reason"], "")
        self.assertEqual(saved_draft["status"], "superseded")

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

    def test_approval_is_bound_to_candidate_context_and_project(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/context/test/",
            body="Looking for a bilingual Japanese reader",
        )
        draft = promotion.save_draft(
            self.db,
            candidate["id"],
            {
                "reply": "I maintain a directly relevant reader.",
                "why": "direct match",
                "confidence": "high",
                "include_link": False,
            },
        )
        approval = promotion.approve_draft(self.db, draft["id"], 30)
        self.db.execute(
            "UPDATE candidates SET body=body || ' Edited after review.' WHERE id=?",
            (candidate["id"],),
        )
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "candidate context changed"):
            promotion.validate_approval(self.db, draft["id"], approval["approval_token"])

    def test_unverified_send_can_be_reopened_without_reusing_approval(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/post/help/comment/",
            body="How can I add accurate subtitles to a short video?",
        )
        draft = promotion.save_draft(
            self.db,
            candidate["id"],
            {
                "reply": "Start by transcribing a clean audio track.",
                "why": "Direct answer.",
                "confidence": "high",
                "include_link": False,
            },
        )
        approval = promotion.approve_draft(self.db, draft["id"], 30)
        promotion.mark_sent(
            self.db,
            draft["id"],
            approval["approval_token"],
            {"screenshot": "before.png"},
        )

        recovered = promotion.reopen_unverified_send(
            self.db,
            draft["id"],
            reason="submit acknowledgement matched composer text instead of a posted comment",
            evidence="after.png",
        )
        self.assertEqual(recovered["draft_status"], "prepared")
        self.assertFalse(recovered["previous_approval_reusable"])
        live_draft = self.db.execute(
            "SELECT status FROM drafts WHERE id=?", (draft["id"],)
        ).fetchone()
        live_candidate = self.db.execute(
            "SELECT status FROM candidates WHERE id=?", (candidate["id"],)
        ).fetchone()
        self.assertEqual(live_draft["status"], "prepared")
        self.assertEqual(live_candidate["status"], "drafted")
        with self.assertRaisesRegex(ValueError, "already used"):
            promotion.validate_approval(self.db, draft["id"], approval["approval_token"])
        replacement = promotion.approve_draft(self.db, draft["id"], 30)
        self.assertNotEqual(replacement["approval_token"], approval["approval_token"])

    def test_hacker_news_generated_draft_is_blocked(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="hackernews",
            source_url="https://news.ycombinator.com/item?id=98765",
            author="asker",
            body="Ask HN: How should I deploy a private local LLM with GGUF?",
        )
        promotion.save_triage(
            self.db,
            candidate["id"],
            {
                "eligible": True,
                "project_id": "github-localllm",
                "confidence": "high",
                "reason": "Direct local LLM need",
                "risk_flags": [],
            },
        )
        with self.assertRaisesRegex(ValueError, "prohibits generated or AI-edited"):
            promotion.save_draft(
                self.db,
                candidate["id"],
                {
                    "reply": "Generated answer",
                    "why": "direct",
                    "confidence": "high",
                    "include_link": False,
                },
            )

    def test_legacy_hacker_news_drafted_state_without_active_draft_is_reconciled(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="hackernews",
            source_url="https://news.ycombinator.com/item?id=76543",
            author="asker",
            body="Ask HN: How should I keep a local model deployment reproducible?",
        )
        self.db.execute(
            "UPDATE candidates SET status='drafted' WHERE id=?",
            (candidate["id"],),
        )
        self.db.commit()
        self.db.close()

        self.db = promotion.open_db(Path(self.tmp.name) / "test.sqlite3")
        status = self.db.execute(
            "SELECT status, triage_reason FROM candidates WHERE id=?",
            (candidate["id"],),
        ).fetchone()
        self.assertEqual(status["status"], "rejected")
        self.assertIn("discovery-only", status["triage_reason"])
        events = self.db.execute(
            "SELECT COUNT(*) FROM events WHERE candidate_id=? AND kind='blocked_platform_draft_reconciled'",
            (candidate["id"],),
        ).fetchone()[0]
        self.assertEqual(events, 1)

    def test_courtesy_draft_needs_no_project_and_cannot_promote(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/thanks/reply/",
            author="kind-reader",
            body="Thank you, those notes have really helped me.",
        )
        draft = promotion.save_courtesy_draft(
            self.db,
            candidate["id"],
            "That genuinely means a lot—thank you.",
            why="A direct acknowledgement requested by the account owner.",
        )
        self.assertEqual(draft["project_id"], "")
        self.assertEqual(draft["model"], "human-directed")
        self.assertEqual(draft["include_link"], 0)
        self.db.close()
        self.db = promotion.open_db(Path(self.tmp.name) / "test.sqlite3")
        reopened = self.db.execute(
            "SELECT project_id FROM drafts WHERE id=?", (draft["id"],)
        ).fetchone()
        self.assertEqual(reopened[0], "")
        with self.assertRaisesRegex(ValueError, "cannot include a promotional link"):
            promotion.save_draft(
                self.db,
                candidate["id"],
                {
                    "reply": "Thanks—visit https://example.test",
                    "why": "not actually a courtesy reply",
                    "confidence": "high",
                    "include_link": True,
                },
                manual=True,
            )

    def test_live_review_can_reject_an_unsent_draft_and_invalidate_approval(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/current/help/",
            author="learner",
            body="Can someone recommend a path for learning embedded systems?",
        )
        promotion.save_triage(
            self.db,
            candidate["id"],
            {
                "eligible": True,
                "project_id": "github-stm32dev",
                "confidence": "medium",
                "reason": "The project may provide a relevant example.",
                "risk_flags": ["live comments not yet reviewed"],
            },
        )
        draft = promotion.save_draft(
            self.db,
            candidate["id"],
            {
                "reply": "Start with GPIO, UART, timers, and a debugger.",
                "why": "A compact learning sequence.",
                "confidence": "medium",
                "include_link": False,
            },
        )
        approval = promotion.approve_draft(self.db, draft["id"], 30)
        result = promotion.reject_draft_after_review(
            self.db,
            draft["id"],
            reason="Existing replies already give the same progression.",
            evidence="https://www.reddit.com/r/example/comments/current/help/",
        )
        self.assertEqual(result["draft_status"], "superseded")
        self.assertEqual(result["candidate_status"], "rejected")
        self.assertFalse(result["public_write"])
        with self.assertRaisesRegex(ValueError, "status is superseded"):
            promotion.validate_approval(
                self.db, draft["id"], approval["approval_token"]
            )

    def test_instagram_comment_draft_includes_exact_target_mention(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="instagram",
            source_url="https://www.instagram.com/p/post123/c/comment456/",
            author="questioner",
            body="Can someone recommend a reliable way to add subtitles automatically?",
        )
        promotion.save_triage(
            self.db,
            candidate["id"],
            {
                "eligible": True,
                "project_id": "lazyedit",
                "confidence": "high",
                "reason": "Direct subtitle need",
                "risk_flags": [],
            },
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
