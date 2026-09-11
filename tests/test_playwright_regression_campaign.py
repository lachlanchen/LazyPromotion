from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PlaywrightRegressionCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(
            (ROOT / "campaigns" / "playwright-regression-contract.json").read_text(
                encoding="utf-8"
            )
        )

    def test_live_need_and_scope_boundary_are_explicit(self):
        need = self.campaign["source_need"]
        self.assertEqual(need["state"], "active_open")
        self.assertEqual(need["project_id"], 40704383)
        self.assertIn("manual checklist and application size", need["scope_unknowns"])
        self.assertIn("funded first milestone", need["policy"])

    def test_executed_proof_does_not_invent_buyer_coverage(self):
        specimen = self.campaign["fit"]["executed_specimen"]
        self.assertEqual(specimen["state"], "three_consecutive_runs_passed")
        self.assertEqual(specimen["tests_per_run"], 2)
        self.assertIn("Project-owned login fixture", specimen["boundary"])
        self.assertIn(
            "three clean runs against the buyer's environment",
            self.campaign["fit"]["not_proven"],
        )

    def test_real_site_proof_is_ci_verified_and_first_party(self):
        proof = self.campaign["fit"]["real_site_regression"]
        self.assertEqual(proof["state"], "clean_ci_three_consecutive_runs_passed")
        self.assertEqual(proof["tests_per_run"], 3)
        self.assertEqual(proof["runs"], 3)
        self.assertIn("all 11 chapters", proof["journeys"][0])
        self.assertIn("not a customer result", proof["boundary"])

    def test_stateful_recovery_is_companion_proof_not_a_new_claim(self):
        proof = self.campaign["fit"]["stateful_recovery_specimen"]
        self.assertEqual(proof["state"], "clean_ci_three_consecutive_runs_passed")
        self.assertEqual(proof["tests_per_run"], 3)
        self.assertEqual(proof["runs"], 3)
        self.assertEqual(len(proof["journeys"]), 3)
        self.assertIn("same id", proof["journeys"][1])
        self.assertIn("no customer data or private AiMemo source", proof["boundary"])
        self.assertIn("not a customer result", proof["boundary"])

        market = self.campaign["stateful_recovery_market_check"]
        self.assertEqual(market["state"], "proof_ready_no_qualified_current_bid")
        self.assertEqual(len(market["rejected_current_routes"]), 3)
        self.assertFalse(market["application_submitted"])
        self.assertFalse(market["social_post_scheduled"])
        self.assertEqual(market["received_revenue_usd"], 0)

    def test_owned_baseline_is_bounded_and_not_a_customer_outcome(self):
        offer = self.campaign["owned_offer"]
        scope = offer["scope"]
        self.assertEqual(offer["state"], "live_encrypted_intake_verified")
        self.assertEqual(offer["price_usd"], 250)
        self.assertEqual(
            offer["website_commit"],
            "aceb4fce038bbd6d0c0f544f6c6a48ad3c853809",
        )
        self.assertIn("34652194605", offer["website_pages_run"])
        self.assertEqual(scope["journeys"], 3)
        self.assertEqual(scope["checkpoints"], 12)
        self.assertEqual(scope["viewports"], ["1440x1000", "390x844"])
        self.assertIn("three consecutive runs", scope["runs"])
        self.assertIn("not a customer result", offer["proof"]["boundary"])
        self.assertIn("must remain on that marketplace", offer["marketplace_boundary"])
        self.assertEqual(self.campaign["funnel"]["received_revenue_usd"], 0)

    def test_linkedin_post_leads_with_proof_and_uses_one_owned_offer(self):
        post = self.campaign["channels"]["linkedin"]
        self.assertEqual(post["state"], "postiz_queue")
        self.assertEqual(post["publish_at"], "2026-09-16T02:00:00Z")
        self.assertNotEqual(post["content"], post["postiz_content"])
        self.assertEqual(post["shortlink"], "https://dub.sh/JcVjOwy")
        self.assertIn(post["shortlink"], post["postiz_content"])
        self.assertIn("survive the second and third run", post["content"])
        self.assertIn("all eleven chapters", post["content"])
        self.assertIn("fixed USD 250 baseline", post["content"])
        self.assertEqual(post["content"].count("https://"), 1)
        self.assertEqual(post["postiz_content"].count("https://"), 1)
        self.assertNotIn("customer result", post["content"])

    def test_bid_has_no_paid_upgrade_or_revenue_claim(self):
        application = self.campaign["application"]
        funnel = self.campaign["funnel"]
        self.assertEqual(application["state"], "submitted_once_proof_updated_once")
        self.assertTrue(application["bid_submitted"])
        self.assertFalse(application["paid_upgrade_selected"])
        self.assertFalse(application["proof_update"]["new_bid_created"])
        self.assertFalse(application["proof_update"]["bid_amount_or_delivery_changed"])
        self.assertTrue(funnel["application_submitted"])
        self.assertEqual(application["milestones_inr"], [11250, 22500, 16875, 5625])
        self.assertEqual(funnel["received_revenue_usd"], 0)

    def test_portfolio_card_stops_at_phone_gate(self):
        item = self.campaign["marketplace_account"]["portfolio_item"]
        self.assertEqual(
            item["state"], "prepared_not_published_phone_verification_required"
        )
        self.assertFalse(item["phone_verification_requested"])
        self.assertRegex(item["image_sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
