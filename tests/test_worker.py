import tempfile
import unittest
import json
from datetime import datetime, timezone
from pathlib import Path

import promotion
import worker
from unittest.mock import MagicMock, call, patch


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.queue_path_patch = patch.object(
            worker,
            "QUEUE_PATH",
            Path(self.tmp.name) / "review-queue.json",
        )
        self.queue_path_patch.start()
        self.db = promotion.open_db(Path(self.tmp.name) / "worker.sqlite3")
        self.now = datetime.now(timezone.utc).isoformat()

    def tearDown(self):
        self.db.close()
        self.queue_path_patch.stop()
        self.tmp.cleanup()

    def test_pending_queue_prefers_current_fresh_requests_and_drains_backlog(self):
        backlog = promotion.ingest_candidate(
            self.db,
            platform="hackernews",
            source_url="https://news.ycombinator.com/item?id=1",
            author="reader-one",
            body="Ask HN: How should I build a private local knowledge base",
            published_at=self.now,
        )
        promotion.mark_triage_requested(self.db, [backlog["id"]])
        current = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/2/help/",
            author="reader-two",
            body="Can someone recommend a bilingual Japanese reader?",
            published_at=self.now,
        )
        promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/3/unknown-date/",
            author="reader-three",
            body="Can someone recommend a Japanese reader?",
        )
        selected = worker.pending_candidate_ids(self.db, [current["id"]], 2)
        self.assertEqual(selected, [current["id"], backlog["id"]])

    def test_filtered_discovery_does_not_enter_model_backlog(self):
        filtered = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/filtered/help/",
            author="reader",
            body="Can someone recommend private local search for my PDF collection?",
            published_at=self.now,
        )
        self.assertEqual(filtered["triage_requested_at"], "")
        self.assertEqual(worker.pending_candidate_ids(self.db, [], 1), [])

    def test_model_failure_remains_retryable_only_after_route_admission(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/retry/help/",
            author="reader",
            body="Can someone recommend private local search for my PDF collection?",
            published_at=self.now,
        )
        promotion.mark_triage_requested(self.db, [candidate["id"]])
        with patch("promotion.open_db", return_value=self.db), patch(
            "promotion.run_codex_triage", side_effect=RuntimeError("temporary model failure")
        ):
            result = worker.run_models([candidate["id"]], max_triage=1, max_drafts=0)
        self.assertEqual(result["errors"][0]["stage"], "triage")
        self.assertEqual(worker.pending_candidate_ids(self.db, [], 1), [candidate["id"]])

    def test_review_queue_only_contains_latest_unsent_draft(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/review/help/",
            body="Looking for a bilingual Japanese reader",
        )
        promotion.save_draft(
            self.db,
            candidate["id"],
            {"reply": "First answer", "why": "first", "confidence": "high", "include_link": False},
        )
        latest = promotion.save_draft(
            self.db,
            candidate["id"],
            {"reply": "Improved answer", "why": "second", "confidence": "high", "include_link": False},
        )
        queued = worker.review_queue(self.db)
        self.assertEqual([item["draft_id"] for item in queued], [latest["id"]])
        self.assertEqual(queued[0]["draft_project_id"], latest["project_id"])
        self.assertEqual(queued[0]["project"]["id"], latest["project_id"])

    def test_review_queue_supports_non_promotional_courtesy_reply(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/thanks/child/",
            author="reader",
            body="Thank you, this helped me.",
        )
        draft = promotion.save_courtesy_draft(
            self.db,
            candidate["id"],
            "That means a lot—thank you.",
            why="Direct acknowledgement.",
        )
        queued = worker.review_queue(self.db)
        self.assertEqual(queued[0]["draft_id"], draft["id"])
        self.assertIsNone(queued[0]["project"])

    def test_hacker_news_need_is_research_only(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="hackernews",
            source_url="https://news.ycombinator.com/item?id=777",
            author="reader",
            body="Ask HN: How should I run a private local LLM with GGUF?",
            published_at=self.now,
        )
        accepted = {
            "eligible": True,
            "project_id": "github-localllm",
            "confidence": "high",
            "reason": "Direct local LLM need",
            "risk_flags": [],
        }
        with patch("promotion.open_db", return_value=self.db), patch(
            "promotion.run_codex_triage", return_value=accepted
        ), patch("promotion.run_codex_draft") as draft_model:
            result = worker.run_models([candidate["id"]], max_triage=1, max_drafts=1)
        draft_model.assert_not_called()
        self.assertEqual(result["drafted"], [])
        self.assertEqual(result["draft_skipped"][0]["candidate_id"], candidate["id"])
        self.assertEqual(
            json.loads(worker.QUEUE_PATH.read_text(encoding="utf-8"))["count"],
            0,
        )

    def test_continuous_reddit_draft_is_value_only_by_default(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/value/help/",
            author="reader",
            body="Can someone recommend a private local RAG workflow for my PDF collection?",
            published_at=self.now,
        )
        accepted = {
            "eligible": True,
            "project_id": "localknowledgeterminal",
            "confidence": "high",
            "reason": "Exact bounded private collection need",
            "risk_flags": [],
        }
        value_only_reply = {
            "reply": "Start with full-text search and measure misses before adding embeddings.",
            "why": "Useful independent answer.",
            "confidence": "high",
            "include_link": False,
        }
        with patch("promotion.open_db", return_value=self.db), patch(
            "promotion.run_codex_triage", return_value=accepted
        ), patch(
            "promotion.run_codex_draft", return_value=value_only_reply
        ) as draft_model:
            result = worker.run_models([candidate["id"]], max_triage=1, max_drafts=1)
        draft_model.assert_called_once()
        self.assertTrue(draft_model.call_args.kwargs["value_only"])
        self.assertTrue(result["drafted"][0]["value_only"])
        self.assertFalse(worker.review_queue(self.db)[0]["include_link"])
        self.assertEqual(
            json.loads(worker.QUEUE_PATH.read_text(encoding="utf-8"))["count"],
            1,
        )

    def test_failed_discovery_route_is_retried(self):
        self.assertEqual(worker.next_route_cursor(5, {"ok": False, "next_query": 6}), 5)
        self.assertEqual(worker.next_route_cursor(5, {"ok": True, "next_query": 6}), 6)

    def test_cdp_attach_retries_one_transient_handshake_failure(self):
        connected = object()
        playwright = MagicMock()
        playwright.chromium.connect_over_cdp.side_effect = [
            RuntimeError("transient attach failure"),
            connected,
        ]
        with patch("worker.time.sleep") as sleep:
            result = worker.connect_browser(playwright, "http://127.0.0.1:9436")
        self.assertIs(result, connected)
        self.assertEqual(
            playwright.chromium.connect_over_cdp.call_args_list,
            [
                call(
                    "http://127.0.0.1:9436",
                    timeout=worker.CDP_ATTACH_TIMEOUT_MS,
                ),
                call(
                    "http://127.0.0.1:9436",
                    timeout=worker.CDP_ATTACH_TIMEOUT_MS,
                ),
            ],
        )
        sleep.assert_called_once_with(worker.CDP_ATTACH_RETRY_SECONDS)

    def test_legacy_state_gains_independent_core_cursors(self):
        path = Path(self.tmp.name) / "legacy-state.json"
        path.write_text(
            json.dumps({"version": 1, "cycles": 4, "cursors": {"reddit": 7}}),
            encoding="utf-8",
        )
        state = worker.load_state(path)
        self.assertEqual(state["cursors"]["reddit"], 7)
        self.assertEqual(state["core_cursors"]["reddit"], 0)
        self.assertEqual(set(state["core_cursors"]), set(worker.DEFAULT_PLATFORMS))


if __name__ == "__main__":
    unittest.main()
