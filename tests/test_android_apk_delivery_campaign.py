from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AndroidApkDeliveryCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(
            (ROOT / "campaigns" / "android-apk-delivery-freelancer.json").read_text(
                encoding="utf-8"
            )
        )

    def test_live_need_is_exact_and_bounded(self):
        need = self.campaign["source_need"]
        self.assertEqual(need["state"], "active_open")
        self.assertEqual(need["project_id"], 40705956)
        self.assertEqual(need["published_budget"], "USD 30–250 fixed")
        self.assertIn("branch or tag", need["scope_unknowns"])
        self.assertIn("signing material", need["scope_unknowns"][-1])

    def test_project_owned_proof_does_not_claim_buyer_delivery(self):
        proof = self.campaign["fit"]["executed_proof"]
        self.assertEqual(proof["state"], "project_owned_android_release_verified")
        self.assertRegex(proof["apk_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("not a successful build", proof["boundary"])
        self.assertIn(
            "successful installation of the buyer APK",
            self.campaign["fit"]["not_proven"],
        )

    def test_application_used_one_free_bid_and_no_upgrade(self):
        application = self.campaign["application"]
        self.assertEqual(application["proposed_bid_usd"], 100)
        self.assertEqual(application["proposed_delivery_days"], 1)
        self.assertEqual(application["milestone_request_usd"], 100)
        self.assertTrue(application["free_bid_required"])
        self.assertFalse(application["paid_upgrade_selected"])
        self.assertTrue(application["bid_submitted"])
        self.assertEqual(application["free_bids_remaining_after_submission"], 4)
        self.assertEqual(application["visible_confirmation"], "You've successfully placed a bid")
        self.assertIn("Do not begin work", application["policy"])

    def test_submitted_application_is_not_revenue(self):
        funnel = self.campaign["funnel"]
        self.assertTrue(funnel["application_submitted"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
