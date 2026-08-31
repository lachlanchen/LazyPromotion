import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import promotion
import worker


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = promotion.open_db(Path(self.tmp.name) / "worker.sqlite3")
        self.now = datetime.now(timezone.utc).isoformat()

    def tearDown(self):
        self.db.close()
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


if __name__ == "__main__":
    unittest.main()
