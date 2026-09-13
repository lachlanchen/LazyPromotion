import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import intake_review
import lkt_inbox
import owned_monitor
from tests.test_lkt_inbox import CREATED_AT, sample_payload


class IntakeReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / "inquiries"
        self.directory.mkdir(mode=0o700)
        self.ledger = self.root / "review.json"
        self.receipt = "a" * 32
        self.path = self.directory / f"lkt-{self.receipt}.inquiry.json"
        self.record = {
            "version": lkt_inbox.RECORD_VERSION,
            "received_at": CREATED_AT,
            "source": lkt_inbox.SOURCE,
            "payload": sample_payload(),
        }
        self.save_record()

    def save_record(self):
        lkt_inbox.private_atomic_write(self.path, lkt_inbox.canonical_json(self.record), replace=True)

    def summary(self):
        return intake_review.status_summary(self.directory, self.ledger)

    def review(self, state="needs_action", digest=None):
        intake_review.record_review(
            self.receipt, digest or hashlib.sha256(self.path.read_bytes()).hexdigest(), state,
            directory=self.directory, ledger_path=self.ledger,
        )

    def test_empty_remote_poll_does_not_clear_received_inquiry(self):
        remote_status = self.root / "receiver-status.json"
        remote_status.write_text(json.dumps({"state": "complete", "receipts": [self.receipt]}))
        self.assertEqual(self.summary()["pending_review"], 1)
        remote_status.write_text(json.dumps({"state": "no_pending", "receipts": []}))
        result = self.summary()
        self.assertEqual(result["pending_review"], 1)
        self.assertTrue(result["review_required"])

    def test_summary_does_not_expose_inquiry_content_or_receipts(self):
        result = self.summary()
        serialized = json.dumps(result)
        for private in (self.receipt, "reader@example.com", "multilingual history", "Classical Chinese", CREATED_AT):
            self.assertNotIn(private, serialized)
        self.assertFalse(result["automatic_reply"])

    def test_read_only_status_creates_no_ledger_or_lock(self):
        self.summary()
        self.assertFalse(self.ledger.exists())
        self.assertFalse(self.ledger.with_suffix(".lock").exists())

    def test_reviewed_but_unfinished_request_stays_visible(self):
        self.review()
        result = self.summary()
        self.assertEqual(result["pending_review"], 0)
        self.assertEqual(result["needs_action"], 1)
        self.assertTrue(result["review_required"])
        self.assertEqual(self.ledger.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.ledger.with_suffix(".lock").stat().st_mode & 0o777, 0o600)

    def test_synthetic_marker_requires_explicit_exact_review(self):
        self.record["payload"]["constraints"] = "Synthetic test is a phrase in a real customer request."
        self.save_record()
        self.assertEqual(self.summary()["pending_review"], 1)
        self.review("synthetic_test")
        result = self.summary()
        self.assertEqual(result["synthetic_test"], 1)
        self.assertFalse(result["review_required"])
        self.assertTrue(self.path.exists())

    def test_closed_request_does_not_imply_revenue(self):
        self.review("closed")
        result = self.summary()
        self.assertEqual(result["closed"], 1)
        self.assertFalse(result["review_required"])
        self.assertNotIn("revenue", result)
        self.assertNotIn("qualified", result)

    def test_changed_inquiry_reopens_review(self):
        self.review("closed")
        self.record["payload"]["constraints"] = "Changed request."
        self.save_record()
        self.assertEqual(self.summary()["pending_review"], 1)
        self.assertTrue(self.summary()["review_required"])

    def test_wrong_hash_cannot_clear_request(self):
        with self.assertRaises(ValueError):
            self.review("closed", "b" * 64)
        self.assertEqual(self.summary()["pending_review"], 1)

    def test_missing_or_unsafe_directory_is_unknown_not_empty(self):
        self.directory.chmod(0o755)
        self.assertFalse(self.summary()["available"])
        self.assertTrue(self.summary()["review_required"])
        missing = intake_review.status_summary(self.root / "absent", self.ledger)
        self.assertFalse(missing["available"])

    def test_unsafe_inquiry_permissions_and_symlinks_fail_closed(self):
        self.path.chmod(0o644)
        self.assertFalse(self.summary()["available"])
        self.path.chmod(0o600)
        original = self.directory / "retained-original.json"
        self.path.rename(original)
        self.path.symlink_to(original)
        self.assertFalse(self.summary()["available"])

    def test_malformed_and_oversized_inquiry_fail_closed(self):
        lkt_inbox.private_atomic_write(self.path, b"not-json", replace=True)
        self.assertFalse(self.summary()["available"])
        lkt_inbox.private_atomic_write(self.path, b"x" * (lkt_inbox.MAX_CIPHERTEXT_BYTES + 1), replace=True)
        self.assertFalse(self.summary()["available"])

    def test_bad_ledger_and_missing_reviewed_record_are_not_silenced(self):
        self.review("synthetic_test")
        original = self.path.read_bytes()
        self.path.unlink()
        self.assertFalse(self.summary()["available"])
        lkt_inbox.private_atomic_write(self.path, original)
        lkt_inbox.private_atomic_write(self.ledger, b'{"version":1,"reviews":[]}', replace=True)
        self.assertFalse(self.summary()["available"])

    def test_symlinked_ledger_or_lock_cannot_be_written(self):
        target = self.root / "other.json"
        lkt_inbox.private_atomic_write(target, b"{}")
        self.ledger.symlink_to(target)
        self.assertFalse(self.summary()["available"])
        self.ledger.unlink()
        self.ledger.with_suffix(".lock").symlink_to(target)
        with self.assertRaises(OSError):
            self.review()
        self.assertEqual(target.read_bytes(), b"{}")

    def test_unknown_state_and_path_traversal_are_rejected(self):
        for receipt, state in (("../elsewhere", "closed"), (self.receipt, "paid")):
            with self.assertRaises(ValueError):
                intake_review.record_review(receipt, "b" * 64, state, directory=self.directory, ledger_path=self.ledger)

    def test_owned_status_surfaces_queue_even_when_postiz_status_is_missing(self):
        result = owned_monitor.status_summary(
            self.root / "missing-owned.json", intake_directory=self.directory, intake_ledger_path=self.ledger,
        )
        self.assertFalse(result["available"])
        self.assertEqual(result["fit_intake"]["pending_review"], 1)
        self.assertTrue(result["fit_intake"]["review_required"])

    def test_directory_symlink_and_unexpected_inquiry_name_are_unknown(self):
        link = self.root / "linked-inquiries"
        link.symlink_to(self.directory, target_is_directory=True)
        self.assertFalse(intake_review.status_summary(link, self.ledger)["available"])
        lkt_inbox.private_atomic_write(self.directory / "unexpected.inquiry.json", b"{}")
        self.assertFalse(self.summary()["available"])

    def test_empty_private_directory_reports_verified_zero(self):
        self.path.unlink()
        result = self.summary()
        self.assertTrue(result["available"])
        self.assertEqual(result["retained_requests"], 0)
        self.assertFalse(result["review_required"])


class ReceiverStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "receiver.json"
        self.now = datetime(2026, 9, 13, 9, 0, tzinfo=timezone.utc)

    def save(self, state="no_pending", **extra):
        payload = {"state": state, "checked_at": "2026-09-13T09:00:00Z", **extra}
        lkt_inbox.private_atomic_write(self.path, lkt_inbox.canonical_json(payload), replace=True)

    def summary(self, now=None):
        return intake_review.receiver_status_summary(self.path, now=now or self.now)

    def test_fresh_collection_states_are_separate_from_queue_counts(self):
        for state, succeeded in (("no_pending", True), ("complete", True), ("partial", False), ("unavailable", False)):
            with self.subTest(state=state):
                self.save(state)
                result = self.summary()
                self.assertTrue(result["status_available"])
                self.assertEqual(result["state"], state)
                self.assertEqual(result["last_check_succeeded"], succeeded)
                self.assertEqual(result["review_required"], not succeeded)
                self.assertFalse(result["stale"])
                self.assertNotIn("pending_review", result)
                self.assertNotIn("retained_requests", result)

    def test_successful_but_stale_check_requires_review(self):
        self.save()
        self.assertFalse(self.summary(self.now + timedelta(seconds=1799))["stale"])
        result = self.summary(self.now + timedelta(seconds=1800))
        self.assertTrue(result["last_check_succeeded"])
        self.assertTrue(result["stale"])
        self.assertTrue(result["review_required"])

    def test_missing_or_malformed_state_is_unknown_not_healthy(self):
        self.assertFalse(self.summary()["status_available"])
        for raw in (b"{", b"[]", b"{}", b"\xff", b'{"state":"no_pending","state":"complete"}'):
            with self.subTest(raw=raw):
                lkt_inbox.private_atomic_write(self.path, raw, replace=True)
                result = self.summary()
                self.assertEqual(result["state"], "unknown")
                self.assertIsNone(result["last_check_succeeded"])
                self.assertTrue(result["review_required"])
        for fields in (
            {"state": "private diagnostic"}, {"state": []},
            {"checked_at": "not a timestamp"}, {"checked_at": "2026-02-30T09:00:00Z"},
            {"checked_at": "2026-09-13T09:00:01Z"}, {"checked_at": None},
        ):
            with self.subTest(fields=fields):
                self.save(**fields)
                self.assertFalse(self.summary()["status_available"])

    def test_permissions_and_symlinks_fail_closed(self):
        self.save()
        self.path.chmod(0o644)
        self.assertFalse(self.summary()["status_available"])
        self.path.chmod(0o600)
        self.root.chmod(0o755)
        self.assertFalse(self.summary()["status_available"])
        self.root.chmod(0o700)
        target = self.root / "original.json"
        self.path.rename(target)
        self.path.symlink_to(target)
        self.assertFalse(self.summary()["status_available"])

    def test_only_allowlisted_metadata_is_returned_without_writes(self):
        self.save("complete", receipts=[{"receipt": "a" * 32}], error="secret diagnostic", email="private@example.com")
        original = self.path.read_bytes()
        result = self.summary()
        self.assertEqual(set(result), {
            "status_available", "state", "checked_at", "stale", "last_check_succeeded", "review_required",
        })
        for private in ("a" * 32, "secret diagnostic", "private@example.com"):
            self.assertNotIn(private, json.dumps(result))
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(list(self.root.iterdir()), [self.path])

    def test_owned_status_refreshes_receiver_even_when_postiz_missing_or_failed(self):
        self.save("unavailable")
        directory = self.root / "inquiries"
        directory.mkdir(mode=0o700)
        status = self.root / "owned.json"
        for saved in (None, {"summary": {"queued": 2}}, {"error": "failed", "summary": {"queued": 2}}):
            with self.subTest(saved=saved):
                if saved is not None:
                    # An old embedded healthy receiver report must not mask the current check.
                    status.write_text(json.dumps({**saved, "fit_receiver": {"state": "no_pending"}}))
                result = owned_monitor.status_summary(
                    status, intake_directory=directory, intake_ledger_path=self.root / "review.json",
                    intake_receiver_path=self.path, now=self.now,
                    threads_path=self.root / "none-threads", application_inbox_path=self.root / "none-applications",
                    reddit_reply_path=self.root / "none-reddit", social_inbox_path=self.root / "none-social",
                )
                self.assertEqual(result["fit_intake"]["retained_requests"], 0)
                self.assertFalse(result["fit_intake"]["review_required"])
                self.assertEqual(result["fit_receiver"]["state"], "unavailable")
                self.assertTrue(result["fit_receiver"]["review_required"])

    def test_malformed_owned_status_does_not_hide_receiver_warning(self):
        self.save("unavailable")
        status = self.root / "owned.json"
        for raw in (b"[]", b"null", b"{", b"\xff"):
            with self.subTest(raw=raw):
                status.write_bytes(raw)
                result = owned_monitor.status_summary(
                    status, intake_receiver_path=self.path, now=self.now,
                    intake_directory=self.root / "missing", intake_ledger_path=self.root / "review.json",
                )
                self.assertFalse(result["available"])
                self.assertEqual(result["fit_receiver"]["state"], "unavailable")
                self.assertTrue(result["fit_receiver"]["review_required"])
