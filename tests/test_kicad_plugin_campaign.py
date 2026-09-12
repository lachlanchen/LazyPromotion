from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class KiCadPluginCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(
            (ROOT / "campaigns" / "kicad-plugin-testing-freelancer.json").read_text(
                encoding="utf-8"
            )
        )

    def test_need_is_current_and_bounded(self):
        need = self.campaign["source_need"]
        self.assertEqual(need["state"], "active_open")
        self.assertEqual(need["project_id"], 40700587)
        self.assertEqual(need["published_budget"], "USD 250–750 fixed")
        self.assertIn("authorized plugin package", need["scope_unknowns"][0])

    def test_fixture_is_project_owned_and_drc_clean(self):
        proof = self.campaign["fit"]["executed_fixture"]
        self.assertEqual(proof["cases"], 7)
        self.assertEqual(proof["track_segments"], 34)
        self.assertEqual(proof["drc_violations"], 0)
        self.assertEqual(proof["unconnected_items"], 0)
        self.assertIn("buyer", proof["boundary"])
        self.assertIn(
            "installation or behavior of Rounder for Tracks v3.2",
            self.campaign["fit"]["not_proven"],
        )

    def test_application_used_one_free_bid_without_upgrade(self):
        application = self.campaign["application"]
        self.assertEqual(application["proposed_bid_usd"], 400)
        self.assertEqual(application["proposed_delivery_days"], 2)
        self.assertEqual(application["platform_fee_usd"], 40)
        self.assertEqual(application["proposed_net_before_tax_usd"], 360)
        self.assertTrue(application["free_bid_required"])
        self.assertFalse(application["paid_upgrade_selected"])
        self.assertTrue(application["bid_submitted"])
        self.assertEqual(application["free_bids_remaining_after_submission"], 3)

    def test_application_is_not_revenue(self):
        funnel = self.campaign["funnel"]
        self.assertTrue(funnel["application_submitted"])
        self.assertFalse(funnel["buyer_reply_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
