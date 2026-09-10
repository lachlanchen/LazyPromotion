import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import affiliate


ROOT = Path(__file__).resolve().parents[1]


class AffiliatePortfolioTests(unittest.TestCase):
    def setUp(self):
        self.registry = affiliate.load_registry()
        self.by_id = {program["id"]: program for program in self.registry["programs"]}

    def test_portfolio_has_contextual_programs_and_safe_states(self):
        self.assertGreaterEqual(len(self.by_id), 18)
        self.assertEqual(self.by_id["lingq"]["priority"], 1)
        self.assertEqual(self.by_id["bookshop"]["priority"], 2)
        self.assertEqual(self.by_id["postiz"]["priority"], 3)
        self.assertEqual(self.by_id["datacamp"]["priority"], 4)
        self.assertEqual(self.by_id["lingq"]["state"], "manual_registration_only")
        self.assertEqual(
            self.by_id["bookshop"]["state"], "security_verification_required"
        )
        self.assertEqual(
            self.by_id["datacamp"]["state"], "defer_until_relevant_traffic"
        )
        self.assertEqual(self.by_id["waveshare"]["state"], "migration_first")
        self.assertEqual(self.by_id["tradingview"]["state"], "hold")
        self.assertEqual(self.by_id["amazon-us"]["state"], "delay")
        self.assertEqual(self.by_id["distrokid"]["state"], "conditional")
        self.assertEqual(self.by_id["digitalocean"]["state"], "rebuild_first")
        self.assertEqual(self.by_id["roboforex"]["state"], "account_review_required")

    def test_public_registry_contains_no_private_link_or_identifier_fields(self):
        body = (ROOT / "affiliate-programs.json").read_text(encoding="utf-8").casefold()
        for forbidden in ('"issued_url"', '"referral_code"', '"affiliate_id"', '"tracking_id"'):
            self.assertNotIn(forbidden, body)
        self.assertNotIn("23819860", body)
        for program in self.registry["programs"]:
            self.assertTrue(program["disclosure"])
            self.assertTrue(program["direct_url"].startswith("https://"))
            self.assertTrue(program["matches"])
            self.assertTrue(program["activation_gates"])

    def test_only_received_commission_is_revenue(self):
        self.assertEqual(self.registry["revenue_event"], "affiliate_commission_received")
        self.assertIn("not revenue", self.registry["policy"].casefold())

    def test_datacamp_requires_accepted_offer_and_exact_course_match(self):
        program = self.by_id["datacamp"]
        self.assertIn("impact_offer_reviewed", program["activation_gates"])
        self.assertIn("relevant_owned_traffic_observed", program["activation_gates"])
        self.assertIn("BLOG post 2180", program["matches"][0]["asset"])
        self.assertIn("non-affiliate", program["disclosure"])
        self.assertIn("self-referral", program["forbidden_actions"])
        self.assertIn("15% of monthly", program["public_economics"])
        self.assertIn("7.5% of yearly", program["public_economics"])
        self.assertIn("7-day attribution", program["public_economics"])

    def test_registration_gates_reject_automation_and_security_bypass(self):
        lingq = self.by_id["lingq"]
        self.assertIn("automated account registration", lingq["forbidden_actions"])
        self.assertIn("registered by bots", lingq["unknowns"][0])
        self.assertIn("human_account_registration_compliant", lingq["activation_gates"])
        self.assertIn("HTTP 403", self.by_id["bookshop"]["unknowns"][0])

    def test_postiz_application_packet_records_accepted_state_without_private_link(self):
        program = self.by_id["postiz"]
        packet = program["application_form_packet"]
        self.assertEqual(packet["website_or_social_channel"], "https://lazying.art/")
        self.assertEqual(packet["promotion_plan"], program["application_pitch"])
        self.assertIn("ordinary, untracked Postiz links", packet["additional_comments"])
        self.assertEqual(packet["submit_state"], "submitted_and_accepted_2026-09-10")
        self.assertEqual(packet["operator_only_fields"], [])
        self.assertEqual(program["state"], "approved_payout_pending")
        checkpoint = program["verified_checkpoint"]
        self.assertEqual(checkpoint["application"], "accepted")
        self.assertEqual(checkpoint["link"], "issued_and_destination_tested_once")
        self.assertEqual(checkpoint["test_clicks"], 1)
        self.assertEqual(checkpoint["leads"], 0)
        self.assertEqual(checkpoint["sales"], 0)
        self.assertEqual(checkpoint["earnings_minor"], 0)
        self.assertEqual(checkpoint["payout"], "incomplete")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            affiliate.print_packet(program)
        rendered = output.getvalue()
        self.assertIn("Prepared non-sensitive application fields:", rendered)
        self.assertIn("Website / social channel: https://lazying.art/", rendered)
        self.assertIn("Submission state: submitted_and_accepted_2026-09-10", rendered)

    def test_lingq_packet_preserves_public_cash_out_boundary(self):
        program = self.by_id["lingq"]
        self.assertIn("PayPal", program["public_economics"])
        self.assertIn("10,000-point (USD 100)", program["public_economics"])
        self.assertIn("account review", program["unknowns"][0])

    def test_private_read_is_explicit_and_missing_record_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(affiliate.RegistryError, "private read"):
                affiliate.check_ready(self.by_id["lingq"], False, Path(tmp))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = affiliate.check_ready(self.by_id["lingq"], True, Path(tmp))
            self.assertEqual(code, 1)
            self.assertIn("NOT READY", output.getvalue())

    def test_private_readiness_never_displays_issued_link(self):
        program = self.by_id["postiz"]
        private = {
            "accepted": True,
            "terms_reviewed_at": "2026-09-02",
            "issued_url": "https://postiz.pro/?ref=private-value",
            "destination_tested": True,
            "payout_ready": True,
            "placement_reviewed": True,
            "confirmed_gates": program["activation_gates"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            private_root = Path(tmp)
            (private_root / "postiz.json").write_text(json.dumps(private), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = affiliate.check_ready(program, True, private_root)
            rendered = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("READY", rendered)
            self.assertNotIn("private-value", rendered)
            self.assertNotIn("https://", rendered)

    def test_hold_and_blocked_states_cannot_become_ready(self):
        for program_id in (
            "lingq",
            "bookshop",
            "datacamp",
            "tradingview",
            "amazon-us",
            "distrokid",
            "digitalocean",
            "wise",
            "skrill",
            "waveshare",
            "roboforex",
        ):
            program = self.by_id[program_id]
            private = {
                "accepted": True,
                "terms_reviewed_at": "2026-09-02",
                "issued_url": f"https://{program['permitted_link_hosts'][0]}/private",
                "destination_tested": True,
                "payout_ready": True,
                "placement_reviewed": True,
                "confirmed_gates": program["activation_gates"],
            }
            with self.subTest(program=program_id):
                failures = affiliate.readiness(program, private)
                self.assertIn(f"public state is {program['state']}", failures)

    def test_roboforex_stays_gated_around_existing_microquant_placement(self):
        program = self.by_id["roboforex"]
        self.assertEqual(program["reviewed_at"], "2026-09-05")
        self.assertIn("MicroQuant", program["matches"][0]["asset"])
        self.assertIn("Existing disclosed README", program["matches"][0]["placement"])
        self.assertIn("publisher_eligibility_confirmed", program["activation_gates"])
        self.assertIn("audience_geography_confirmed", program["activation_gates"])
        self.assertTrue(
            any("restricted jurisdictions" in action for action in program["forbidden_actions"])
        )
        self.assertIn("not expected income", program["public_economics"])

    def test_skrill_packet_preserves_clarification_gate(self):
        program = self.by_id["skrill"]
        self.assertEqual(program["state"], "terms_conflict_review")
        self.assertEqual(
            program["official_urls"]["terms"],
            "https://affiliates.skrill.com/terms_and_conditions.asp",
        )
        self.assertIn("up to 30 days", program["public_economics"])
        self.assertIn("neutral, source-cited", program["clarification_request"])
        self.assertIn(
            "neutral_review_permission_confirmed_in_writing",
            program["activation_gates"],
        )
        self.assertNotIn("paysafeaffiliates.com", program["permitted_link_hosts"])
        self.assertIn(
            "social-media promotion of Paysafe or Skrill",
            program["forbidden_actions"],
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            affiliate.print_packet(program)
        rendered = output.getvalue()
        self.assertIn("Written clarification request:", rendered)
        self.assertIn("global or USA programme", rendered)
        self.assertIn("Official contact: https://affiliates.skrill.com/contact.asp", rendered)
        self.assertIn("Exact media submitted for approval:", rendered)
        self.assertIn("Channels: owned blog only", rendered)

    def test_wrong_or_plain_destination_fails(self):
        program = self.by_id["postiz"]
        base = {
            "accepted": True,
            "terms_reviewed_at": "2026-09-02",
            "destination_tested": True,
            "payout_ready": True,
            "placement_reviewed": True,
            "confirmed_gates": program["activation_gates"],
        }
        for url, expected in (
            ("https://evil.example/ref", "allowlist"),
            (program["direct_url"], "plain official"),
            ("http://postiz.com/ref", "credential-free HTTPS"),
        ):
            with self.subTest(url=url):
                failures = affiliate.readiness(program, {**base, "issued_url": url})
                self.assertTrue(any(expected in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
