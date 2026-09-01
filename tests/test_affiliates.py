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
        self.assertGreaterEqual(len(self.by_id), 17)
        self.assertEqual(self.by_id["lingq"]["priority"], 1)
        self.assertEqual(self.by_id["bookshop"]["priority"], 2)
        self.assertEqual(self.by_id["postiz"]["priority"], 3)
        self.assertEqual(self.by_id["waveshare"]["state"], "migration_first")
        self.assertEqual(self.by_id["tradingview"]["state"], "hold")
        self.assertEqual(self.by_id["amazon-us"]["state"], "delay")
        self.assertEqual(self.by_id["distrokid"]["state"], "conditional")
        self.assertEqual(self.by_id["digitalocean"]["state"], "rebuild_first")

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
        program = self.by_id["lingq"]
        private = {
            "accepted": True,
            "terms_reviewed_at": "2026-09-02",
            "issued_url": "https://www.lingq.com/settings/referrals?referral=private-value",
            "destination_tested": True,
            "payout_ready": True,
            "placement_reviewed": True,
            "confirmed_gates": program["activation_gates"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            private_root = Path(tmp)
            (private_root / "lingq.json").write_text(json.dumps(private), encoding="utf-8")
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
            "tradingview",
            "amazon-us",
            "distrokid",
            "digitalocean",
            "wise",
            "skrill",
            "waveshare",
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
