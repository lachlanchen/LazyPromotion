import tempfile
import unittest
from pathlib import Path

import metrics
import network
import promotion


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = promotion.open_db(Path(self.tmp.name) / "metrics.sqlite3")
        self.candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/real/reply/",
            author="reader",
            body="Thank you, this was useful.",
        )

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_report_starts_with_zero_confirmed_revenue(self):
        report = metrics.funnel_report(self.db)
        goal = report["usd_1000_gross_goal"]
        self.assertEqual(goal["confirmed_minor"], 0)
        self.assertEqual(goal["progress_percent"], 0)
        self.assertEqual(goal["additional_250_usd_sprints_needed"], 4)
        self.assertEqual(goal["additional_128_usd_orders_needed"], 8)

    def test_verified_reply_and_sale_are_distinct(self):
        metrics.record_outcome(
            self.db,
            kind="reply_received",
            candidate_id=self.candidate["id"],
        )
        metrics.record_outcome(
            self.db,
            kind="sale_confirmed",
            campaign_id="eink-multilingual-reading",
            project_id="lazyingart-eink",
            amount="128",
            currency="usd",
            reference="private-order-001",
        )
        report = metrics.funnel_report(self.db)
        self.assertEqual(report["outcomes"]["reply_received"], 1)
        self.assertEqual(report["gross_revenue_minor_by_currency"]["USD"], 12_800)
        self.assertEqual(report["usd_1000_gross_goal"]["progress_percent"], 12.8)
        self.assertEqual(
            report["usd_1000_gross_goal"]["additional_250_usd_sprints_needed"], 4
        )
        self.assertEqual(
            report["usd_1000_gross_goal"]["additional_128_usd_orders_needed"], 7
        )

    def test_money_and_non_money_outcomes_are_validated(self):
        with self.assertRaisesRegex(ValueError, "three-letter currency"):
            metrics.record_outcome(
                self.db,
                kind="sale_confirmed",
                project_id="lazyingart-eink",
                amount="128",
            )
        with self.assertRaisesRegex(ValueError, "cannot record"):
            metrics.record_outcome(
                self.db,
                kind="qualified_lead",
                project_id="lazyingart-eink",
                amount="1",
                currency="USD",
            )

    def test_money_reference_is_hashed_and_idempotent(self):
        result = metrics.record_outcome(
            self.db,
            kind="donation_received",
            project_id="leonardsusskind",
            amount="5",
            currency="USD",
            reference="private-receipt-001",
        )
        self.assertNotIn("private-receipt-001", str(result))
        self.assertEqual(len(result["reference_hash"]), 64)
        with self.assertRaisesRegex(ValueError, "already recorded"):
            metrics.record_outcome(
                self.db,
                kind="donation_received",
                project_id="leonardsusskind",
                amount="5",
                currency="USD",
                reference="private-receipt-001",
            )

    def test_affiliate_referral_is_not_revenue_and_requires_private_reference(self):
        with self.assertRaisesRegex(ValueError, "private conversion reference"):
            metrics.record_outcome(
                self.db,
                kind="affiliate_referral_confirmed",
                campaign_id="postiz-affiliate-pilot",
            )
        result = metrics.record_outcome(
            self.db,
            kind="affiliate_referral_confirmed",
            campaign_id="postiz-affiliate-pilot",
            reference="private-dub-conversion-001",
        )
        self.assertNotIn("private-dub-conversion-001", str(result))
        report = metrics.funnel_report(self.db)
        self.assertEqual(report["outcomes"]["affiliate_referral_confirmed"], 1)
        self.assertEqual(report["gross_revenue_minor_by_currency"], {})

    def test_received_affiliate_commission_is_revenue_and_reversal_reduces_net(self):
        metrics.record_outcome(
            self.db,
            kind="affiliate_commission_received",
            campaign_id="postiz-affiliate-pilot",
            amount="30",
            currency="usd",
            reference="private-dub-payout-001",
        )
        metrics.record_outcome(
            self.db,
            kind="affiliate_commission_reversed",
            campaign_id="postiz-affiliate-pilot",
            amount="6",
            currency="USD",
            reference="private-dub-reversal-001",
        )
        report = metrics.funnel_report(self.db)
        self.assertEqual(report["gross_revenue_minor_by_currency"]["USD"], 3_000)
        self.assertEqual(report["reversals_minor_by_currency"]["USD"], 600)
        self.assertEqual(report["refunds_minor_by_currency"], {})
        self.assertEqual(report["net_revenue_minor_by_currency"]["USD"], 2_400)
        self.assertEqual(report["usd_1000_gross_goal"]["progress_percent"], 3.0)

    def test_outcome_stays_private_in_graph_export(self):
        outcome = metrics.record_outcome(
            self.db,
            kind="reply_received",
            candidate_id=self.candidate["id"],
            note="private acknowledgement",
        )
        network.sync_graph(self.db)
        snapshot = network.public_snapshot(self.db)
        serialized = str(snapshot)
        self.assertNotIn(outcome["id"], serialized)
        self.assertNotIn("private acknowledgement", serialized)


if __name__ == "__main__":
    unittest.main()
