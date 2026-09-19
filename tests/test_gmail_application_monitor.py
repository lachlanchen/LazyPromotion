import copy
import json
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from unittest.mock import MagicMock

from playwright.sync_api import sync_playwright

import gmail_application_monitor as gmail


STAMP = "2026-09-20T00:00:00+00:00"
RULE = {"campaign_id": "sample-pitch", "subject": "A bounded sample article pitch",
        "sender_domain": "example.org", "after": "2026-09-08"}
CONFIG = {"account_email": "operator@example.net", "campaigns": [RULE]}


def snapshot(*, unread=False, last="abcdef123456"):
    return {"empty": False, "complete": True, "rows": [{
        "thread_id": "#thread-f:test123", "last_message_id": last,
        "subject": "Re: " + RULE["subject"], "unread": unread,
    }]}


def summary(**kwargs):
    return gmail.validate_snapshot(snapshot(**kwargs), RULE)


class ConfigTests(unittest.TestCase):
    def test_query_is_bounded_by_incoming_domain_subject_and_date(self):
        config = gmail.validate_config(CONFIG)
        self.assertEqual(gmail.search_query(config["campaigns"][0]),
                         'in:anywhere after:2026/09/08 from:example.org subject:"A bounded sample article pitch"')
        self.assertIsNot(config["campaigns"], CONFIG["campaigns"])

    def test_rejects_query_injection_duplicate_and_unbounded_rules(self):
        invalid = [
            {**CONFIG, "account_email": "operator@example.net subject:private"},
            {**CONFIG, "campaigns": []}, {**CONFIG, "campaigns": [RULE] * 2},
            {**CONFIG, "extra": "private"},
        ]
        for field, value in (("subject", 'pitch" OR in:anywhere'), ("subject", "x\nprivate"),
                             ("sender_domain", "example.org OR gmail.com"), ("after", "2026/01/01"),
                             ("campaign_id", "../private")):
            invalid.append({**CONFIG, "campaigns": [{**RULE, field: value}]})
        for value in invalid:
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                gmail.validate_config(value)

    def test_config_requires_private_regular_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(CONFIG))
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                gmail.load_config(path)
            path.chmod(0o600)
            self.assertEqual(gmail.load_config(path), CONFIG)
            link = Path(directory) / "link.json"
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                gmail.load_config(link)


class SnapshotTests(unittest.TestCase):
    def test_only_aggregate_counts_and_digest_leave_snapshot(self):
        row = summary(unread=True)
        self.assertEqual(row["matching_thread_count"], 1)
        self.assertEqual(row["unread_matching_thread_count"], 1)
        serialized = json.dumps(row)
        for private in (RULE["subject"], "test123", "abcdef123456", "@"):
            self.assertNotIn(private, serialized)
        self.assertEqual(len(row["snapshot_digest"]), 64)

    def test_unverified_empty_incomplete_wrong_subject_and_duplicate_fail(self):
        bad = [None, {}, {"empty": True, "complete": False, "rows": []},
               {**snapshot(), "empty": True}, {**snapshot(), "complete": False}]
        for field, value in (("subject", "Unrelated mail"), ("unread", 1),
                             ("thread_id", ""), ("last_message_id", None)):
            item = snapshot()
            item["rows"][0][field] = value
            bad.append(item)
        duplicate = snapshot()
        duplicate["rows"] *= 2
        bad.append(duplicate)
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                gmail.validate_snapshot(value, RULE)

    def test_verified_empty_has_zero_counts_without_raw_fields(self):
        row = gmail.validate_snapshot({"empty": True, "complete": True, "rows": []}, RULE)
        self.assertEqual(row["matching_thread_count"], 0)
        self.assertEqual(row["unread_matching_thread_count"], 0)


class StateTests(unittest.TestCase):
    def test_startup_wait_observes_sign_in_without_interaction(self):
        page = MagicMock(url="https://accounts.google.com/")
        with patch.object(gmail.time, "monotonic", side_effect=[0, 1]), patch.object(gmail, "account_matches", side_effect=[False, True]):
            gmail.wait_for_account(page, CONFIG["account_email"], deadline=10)
        page.wait_for_timeout.assert_called_once_with(250)
        page.click.assert_not_called()
        page.fill.assert_not_called()
        with patch.object(gmail.time, "monotonic", return_value=11), self.assertRaises(gmail.GmailSessionUnavailable):
            gmail.wait_for_account(page, CONFIG["account_email"], deadline=10)

    def test_initial_incoming_and_same_count_new_message_signal_review(self):
        first = gmail.record_observation(CONFIG, [summary()], {}, STAMP)
        self.assertEqual(len(first["alerts"]), 1)
        acknowledged = {**first, "alerts": []}
        unchanged = gmail.record_observation(CONFIG, [summary()], acknowledged, STAMP)
        self.assertEqual(unchanged["alerts"], [])
        changed = gmail.record_observation(CONFIG, [summary(last="abcdef987654")], acknowledged, STAMP)
        self.assertEqual(len(changed["alerts"]), 1)
        pending = gmail.record_observation(CONFIG, [summary(last="abcdef987654")], changed, STAMP)
        self.assertEqual(pending["alerts"], changed["alerts"])

    def test_failure_recovery_null_baseline_and_config_change_are_supported(self):
        empty = gmail.validate_snapshot({"empty": True, "complete": True, "rows": []}, RULE)
        first = gmail.record_observation(CONFIG, [empty], {"last_success": None}, STAMP)
        self.assertEqual(first["alerts"], [])
        changed_config = {**CONFIG, "account_email": "another@example.net"}
        changed = gmail.record_observation(changed_config, [summary()], first, STAMP)
        self.assertEqual(len(changed["alerts"]), 1)

    def test_unexpected_private_fields_are_not_retained_as_last_success(self):
        before = gmail.record_observation(CONFIG, [summary()], {}, STAMP)
        self.assertIsNotNone(gmail.validated_success(before["last_success"]))
        bad = copy.deepcopy(before["last_success"])
        bad["campaigns"][0]["subject"] = "private"
        self.assertIsNone(gmail.validated_success(bad))
        with self.assertRaises(ValueError):
            gmail.record_observation(CONFIG, bad["campaigns"], {}, STAMP)

    def test_status_is_private_and_unavailable_is_not_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            config, status_path = Path(directory) / "config.json", Path(directory) / "status.json"
            config.write_text(json.dumps(CONFIG))
            config.chmod(0o600)
            with patch.object(gmail, "collect_counts", return_value=[summary()]):
                result = gmail.check_optional(config, status_path)
            self.assertTrue(result["review_required"])
            self.assertEqual(stat.S_IMODE(status_path.stat().st_mode), 0o600)
            success = json.loads(status_path.read_text())["last_success"]
            with patch.object(gmail, "collect_counts", side_effect=gmail.GmailSessionUnavailable("private secret")):
                result = gmail.check_optional(config, status_path)
            self.assertEqual(result, {"state": "session_unavailable"})
            saved = json.loads(status_path.read_text())
            self.assertEqual(saved["last_success"], success)
            self.assertEqual(len(saved["alerts"]), 1)
            self.assertNotIn("private secret", status_path.read_text())

    def test_absent_configuration_does_not_open_browser(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(gmail, "collect_counts") as collect:
            result = gmail.check_optional(Path(directory) / "absent", Path(directory) / "status")
        self.assertEqual(result, {"state": "not_configured"})
        collect.assert_not_called()

    def test_summary_rejects_contacts_and_zero_claim_on_failure(self):
        for value in ({"state": "session_unavailable", "matching_thread_count": 0},
                      {"state": "not_configured", "email": "private"},
                      {"state": "checked", "campaign_count": 1, "matching_thread_count": 0,
                       "unread_matching_thread_count": 1, "review_required": False}):
            with self.assertRaises(ValueError):
                gmail.validated_summary(value)


CHROME = shutil.which("google-chrome") or shutil.which("chromium")


@unittest.skipUnless(CHROME, "Chrome is required for the synthetic DOM contract")
class BrowserContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(executable_path=CHROME, headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page()
        self.addCleanup(self.page.close)

    def fixture(self, *, pager="1–1 of 1", unread=False):
        state = "zE" if unread else "yO"
        subject = RULE["subject"]
        self.page.set_content(f'''<div class="Dj">{pager}</div><main role="main"><table><tr class="zA {state}">
          <td><span data-thread-id="#thread-f:test123" data-legacy-last-non-draft-message-id="abcdef123456">{subject}</span></td>
          <td class="y2">PRIVATE PREVIEW NEVER READ</td></tr></table></main>''')
        self.page.evaluate('''() => {window.clicked = 0; const row = document.querySelector('tr');
          row.onclick = () => window.clicked++; for (const key of ['textContent','innerText'])
          Object.defineProperty(row, key, {get: () => {throw Error('row preview read')}});}''')

    def test_real_collector_reads_metadata_without_row_text_or_click(self):
        self.fixture(unread=True)
        result = gmail.validate_snapshot(self.page.evaluate(gmail.SNAPSHOT_JS), RULE)
        self.assertEqual(result["unread_matching_thread_count"], 1)
        self.assertEqual(self.page.evaluate("window.clicked"), 0)
        self.assertNotIn("PRIVATE", json.dumps(result))

    def test_incomplete_pagination_and_open_message_are_rejected(self):
        self.fixture(pager="1–1 of 5")
        with self.assertRaises(ValueError):
            gmail.validate_snapshot(self.page.evaluate(gmail.SNAPSHOT_JS), RULE)
        self.fixture()
        self.page.locator('main').evaluate("e => e.insertAdjacentHTML('beforeend', '<div class=a3s>BODY</div>')")
        self.assertIsNone(self.page.evaluate(gmail.SNAPSHOT_JS))

    def test_empty_needs_both_exact_visible_markers(self):
        self.page.set_content('<main role="main"><div class="LeCudf"><b>No matches</b><br>Try a different search</div></main>')
        result = gmail.validate_snapshot(self.page.evaluate(gmail.SNAPSHOT_JS), RULE)
        self.assertEqual(result["matching_thread_count"], 0)
        self.page.set_content('<main role="main">Loading…</main>')
        self.assertIsNone(self.page.evaluate(gmail.SNAPSHOT_JS))
        self.page.set_content('<main role="main"><div class="LeCudf" style="display:none"><b>No matches</b><br>Try a different search</div></main>')
        self.assertIsNone(self.page.evaluate(gmail.SNAPSHOT_JS))

    def test_duplicate_subject_links_cannot_disagree(self):
        self.fixture()
        self.page.locator('tr td').first.evaluate("e => e.appendChild(e.firstChild.cloneNode(true))")
        self.page.locator('[data-thread-id]').last.evaluate("e => e.textContent = 'unrelated'")
        with self.assertRaises(ValueError):
            gmail.validate_snapshot(self.page.evaluate(gmail.SNAPSHOT_JS), RULE)

    def test_account_requires_matching_origin_title_and_visible_marker(self):
        html = ('<title>Search results - operator@example.net - Gmail</title>'
                '<a aria-label="Google Account: Operator (operator@example.net)">Account</a>')
        self.page.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=html))
        self.page.goto("https://mail.google.com/mail/u/0/")
        self.assertTrue(gmail.account_matches(self.page, CONFIG["account_email"]))
        self.page.evaluate("document.title = 'Search results - wrong@example.net - Gmail'")
        self.assertFalse(gmail.account_matches(self.page, CONFIG["account_email"]))
        self.page.reload()
        self.page.locator('a').evaluate("e => e.setAttribute('aria-label', 'Google Account: Other (wrong@example.net)')")
        self.assertFalse(gmail.account_matches(self.page, CONFIG["account_email"]))
        self.page.goto("https://accounts.google.com/")
        self.assertFalse(gmail.account_matches(self.page, CONFIG["account_email"]))


if __name__ == "__main__":
    unittest.main()
