from __future__ import annotations

import hashlib
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

    def test_owned_offer_is_live_bounded_and_separate_from_marketplace(self):
        offer = self.campaign["owned_offer"]
        self.assertEqual(self.campaign["version"], 3)
        self.assertEqual(offer["state"], "live_verified")
        self.assertEqual(offer["price_usd"], 400)
        self.assertEqual(
            offer["url"],
            "https://lazying.art/kicad-plugin-evaluation/",
        )
        self.assertEqual(
            offer["fit_check_url"],
            "https://lazying.art/kicad-plugin-evaluation/fit-check/",
        )
        self.assertEqual(offer["live_verification"]["offer_http_status"], 200)
        self.assertEqual(offer["live_verification"]["fit_check_http_status"], 200)
        self.assertIn("Customer boards or confidential design files", offer["exclusions"])
        self.assertIn("stays on Freelancer", offer["policy"])
        self.assertIn("not evidence", offer["policy"])

    def test_linkedin_distribution_is_reviewed_and_not_a_sale(self):
        linkedin = self.campaign["channels"]["linkedin"]
        self.assertEqual(linkedin["state"], "postiz_queue")
        self.assertEqual(linkedin["publish_at"], "2026-09-29T02:00:00Z")
        self.assertEqual(linkedin["account_role"], "Current personal technical profile")
        self.assertFalse(linkedin["shortlink"])
        self.assertIn("USD 400 evaluation", linkedin["content"])
        self.assertIn("No customer board", linkedin["content"])
        self.assertEqual(
            hashlib.sha256(linkedin["content"].encode("utf-8")).hexdigest(),
            linkedin["content_sha256"],
        )
        self.assertTrue(linkedin["verification"]["visible_editor_reviewed"])
        self.assertTrue(linkedin["verification"]["original_url_preserved"])
        self.assertEqual(linkedin["verification"]["verified_state"], "QUEUE")
        self.assertFalse(linkedin["verification"]["release_present"])
        self.assertNotIn("post_id", linkedin)
        self.assertIn("not leads or revenue", linkedin["policy"])

    def test_application_is_not_revenue(self):
        funnel = self.campaign["funnel"]
        self.assertTrue(funnel["application_submitted"])
        self.assertFalse(funnel["buyer_reply_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
