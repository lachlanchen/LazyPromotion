import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import stripe_revenue_monitor as monitor


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def charge(
    identifier: str,
    *,
    amount: int = 25_000,
    refunded: int = 0,
    disputed: bool = False,
    metadata: dict | None = None,
) -> dict:
    return {
        "id": identifier,
        "object": "charge",
        "livemode": True,
        "paid": True,
        "status": "succeeded",
        "amount": amount,
        "amount_refunded": refunded,
        "currency": "usd",
        "created": 1_788_739_200,
        "refunded": refunded == amount,
        "disputed": disputed,
        "billing_details": {"email": "private@example.com"},
        "receipt_url": "https://pay.stripe.com/private-receipt",
        "metadata": metadata or {},
    }


class StripeRevenueMonitorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.env = self.root / ".env"
        self.env.write_text("STRIPE_SECRET_KEY=sk_live_private_test_value\n")
        os.chmod(self.env, 0o600)
        self.db = self.root / "monitor.sqlite3"
        self.status = self.root / "status.json"
        self.log = self.root / "monitor.jsonl"

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def opener(rows):
        def open_request(request, timeout=0):
            payload = {"object": "list", "data": rows, "has_more": False}
            return FakeResponse(json.dumps(payload).encode("utf-8"))

        return open_request

    def run_once(self, rows):
        return monitor.build_report(
            env_path=self.env,
            db_path=self.db,
            status_path=self.status,
            log_path=self.log,
            opener=self.opener(rows),
        )

    def test_first_check_establishes_private_sanitized_baseline(self):
        row = charge(
            "ch_private_raw_identifier",
            metadata={
                "product_slug": "local-knowledge-terminal-collection-fit-sprint",
                "site": "private@example.com",
                "private_note": "do not retain",
            },
        )
        report = self.run_once([row])

        self.assertFalse(report["initialized_before_check"])
        self.assertEqual(report["alerts"], [])
        self.assertEqual(report["summary"]["successful_charge_count"], 1)
        usd = report["summary"]["currencies"]["USD"]
        self.assertEqual(usd["gross_minor"], 25_000)
        serialized = self.status.read_text() + self.log.read_text()
        self.assertNotIn("ch_private_raw_identifier", serialized)
        self.assertNotIn("private@example.com", serialized)
        self.assertNotIn("private-receipt", serialized)
        self.assertNotIn("private_note", serialized)
        self.assertNotIn("product_slug", serialized)
        self.assertEqual(self.status.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.log.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.db.stat().st_mode & 0o777, 0o600)

        with sqlite3.connect(self.db) as db:
            database_text = " ".join(
                str(value)
                for row in db.execute("SELECT * FROM stripe_charge_observations")
                for value in row
            )
        self.assertNotIn("ch_private_raw_identifier", database_text)
        self.assertNotIn("private@example.com", database_text)
        self.assertNotIn("private_note", database_text)
        self.assertIn("product_slug", database_text)

    def test_new_charge_then_refund_emit_review_alerts_without_recording_revenue(self):
        old = charge("ch_old")
        self.run_once([old])

        new = charge(
            "ch_new",
            amount=50_000,
            metadata={"product_slug": "ai-clip-assembly-pilot"},
        )
        report = self.run_once([old, new])
        self.assertEqual(len(report["alerts"]), 1)
        alert = report["alerts"][0]
        self.assertEqual(alert["kind"], "new_successful_charge")
        self.assertEqual(alert["amount_minor"], 50_000)
        self.assertTrue(alert["review_required"])
        self.assertFalse(report["policy"]["automatic_revenue_records"])

        refunded = charge(
            "ch_new",
            amount=50_000,
            refunded=50_000,
            metadata={"product_slug": "ai-clip-assembly-pilot"},
        )
        report = self.run_once([old, refunded])
        self.assertEqual(len(report["alerts"]), 1)
        alert = report["alerts"][0]
        self.assertEqual(alert["kind"], "charge_state_changed")
        self.assertEqual(alert["previous_amount_refunded_minor"], 0)
        self.assertTrue(alert["refunded"])
        usd = report["summary"]["currencies"]["USD"]
        self.assertEqual(usd["gross_minor"], 75_000)
        self.assertEqual(usd["refunded_minor"], 50_000)
        self.assertEqual(usd["net_minor_before_fees_and_disputes"], 25_000)

    def test_unsuccessful_test_and_malformed_rows_are_ignored(self):
        failed = charge("ch_failed")
        failed["status"] = "failed"
        test = charge("ch_test")
        test["livemode"] = False
        malformed = charge("ch_bad")
        malformed["amount"] = True
        report = self.run_once([failed, test, malformed, {"object": "customer"}])
        self.assertEqual(report["summary"]["successful_charge_count"], 0)
        self.assertEqual(report["summary"]["currencies"], {})

    def test_fetch_paginates_without_returning_request_credentials(self):
        seen = []

        def opener(request, timeout=0):
            seen.append((request.full_url, request.headers.get("Authorization")))
            query = parse_qs(urlparse(request.full_url).query)
            if "starting_after" not in query:
                payload = {"data": [charge("ch_page_1")], "has_more": True}
            else:
                payload = {"data": [charge("ch_page_2")], "has_more": False}
            return FakeResponse(json.dumps(payload).encode("utf-8"))

        rows = monitor.fetch_charges("sk_live_secret", 1, opener=opener)
        self.assertEqual([row["id"] for row in rows], ["ch_page_1", "ch_page_2"])
        self.assertIn("starting_after=ch_page_1", seen[1][0])
        self.assertEqual(seen[0][1], "Bearer sk_live_secret")

    def test_private_live_key_and_timezone_are_required(self):
        os.chmod(self.env, 0o644)
        with self.assertRaisesRegex(ValueError, "mode 600"):
            monitor.inspect_live_key(self.env)
        os.chmod(self.env, 0o600)
        self.env.write_text("STRIPE_SECRET_KEY=sk_test_value\n")
        with self.assertRaisesRegex(ValueError, "live secret key"):
            monitor.inspect_live_key(self.env)
        with self.assertRaisesRegex(ValueError, "include a timezone"):
            monitor.parse_since("2026-08-31T00:00:00")


if __name__ == "__main__":
    unittest.main()
