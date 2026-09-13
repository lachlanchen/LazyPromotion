import contextlib
import copy
import json
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import mail_inbound_check as mail


STAMP = "2026-09-13T12:00:00+00:00"


def observation():
    return {
        "run_id": "test-run", "checked_at": STAMP, "ok": True,
        "applications": {
            "campaign_count": 2, "campaigns_with_matching_threads": 1,
            "campaigns_with_unread_matching_threads": 0,
            "matching_thread_count": 1, "unread_matching_thread_count": 0,
        },
        "fit_folder": {"message_count": 2, "unread_count": 0},
        "alerts": [], "policy": dict(mail.POLICY),
    }


class ObservationTests(unittest.TestCase):
    def test_only_aggregate_schema_is_accepted(self):
        result = mail.validated_observation(observation(), "test-run")
        self.assertNotIn("run_id", result)
        self.assertFalse(result["policy"]["message_bodies_read"])
        for change in (
            {"message_body": "private"}, {"desktop_stopped": True},
            {"run_id": "older-run"}, {"checked_at": "private text"},
            {"policy": {**mail.POLICY, "message_bodies_read": True}},
            {"fit_folder": {"message_count": 2, "unread_count": 3}},
            {"fit_folder": {"message_count": True, "unread_count": 0}},
            {"alerts": [{"kind": "unknown", "subject": "private"}]},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                mail.validated_observation({**observation(), **change}, "test-run")

    def test_counts_and_alerts_have_no_open_ended_fields(self):
        good = observation()
        good["alerts"] = [
            {"kind": "application_mail_count_changed", "campaign_id": "sample-campaign",
             "matching_thread_count_increased": True, "unread_matching_thread_count_increased": False},
            {"kind": "inbound_count_increased", "message_delta": 1},
        ]
        mail.validated_observation(good, "test-run")
        for field in ("sender", "subject", "body", "email"):
            bad = copy.deepcopy(good)
            bad["alerts"][0][field] = "private"
            with self.assertRaises(ValueError):
                mail.validated_observation(bad, "test-run")

    def test_private_atomic_write_rejects_symlink_and_cleans_failed_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            mail.private_json(path, {"ok": True})
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(TypeError):
                mail.private_json(path, {"bad": object()})
            self.assertEqual(list(Path(directory).iterdir()), [path])
            link = Path(directory) / "link"
            link.symlink_to(path)
            with self.assertRaises(RuntimeError):
                mail.private_json(link, {})
            self.assertEqual(json.loads(path.read_text()), {"ok": True})


class RunOnceTests(unittest.TestCase):
    def setUp(self):
        self.resources = contextlib.ExitStack()
        self.addCleanup(self.resources.close)
        directory = self.resources.enter_context(tempfile.TemporaryDirectory())
        self.status = Path(directory) / "status.json"
        self.observation = Path(directory) / "observation.json"
        self.resources.enter_context(patch.object(mail.secrets, "token_hex", return_value="test-run"))
        self.lifecycle = self.resources.enter_context(patch.object(mail.desktop_lease, "run_owned_check", return_value={
            "state": "checked", "desktop_started": True, "desktop_stopped": True,
        }))

    def run_check(self):
        return mail.run_once(status_path=self.status, observation_path=self.observation)

    def test_success_requires_matching_run_and_completed_cleanup(self):
        mail.private_json(self.observation, observation())
        result = self.run_check()
        self.assertTrue(result["ok"])
        self.assertEqual(result["last_successful_checked_at"], STAMP)
        self.assertEqual(self.lifecycle.call_args.args[0][-3:], ["_collect", "--run-id", "test-run"])

    def test_missing_stale_or_invalid_observation_never_becomes_success(self):
        for payload in (None, [], {**observation(), "run_id": "old"}, {**observation(), "subject": "secret"}):
            with self.subTest(payload=payload):
                self.observation.write_text(json.dumps(payload))
                result = self.run_check()
                self.assertFalse(result["ok"])
                self.assertIn(result["state"], {"observation_missing_or_stale", "observation_invalid"})
                self.assertNotIn("secret", self.status.read_text())

    def test_skip_preserves_last_success_but_does_not_claim_fresh_check(self):
        mail.private_json(self.status, {"last_successful_checked_at": STAMP})
        self.lifecycle.return_value = {"state": "skipped_active_or_partial_desktop", "desktop_started": False, "desktop_stopped": False}
        result = self.run_check()
        self.assertFalse(result["ok"])
        self.assertEqual(result["last_successful_checked_at"], STAMP)

    def test_malformed_prior_status_is_ignored_and_errors_are_sanitized(self):
        self.status.write_text("[]")
        self.lifecycle.side_effect = RuntimeError("private credential")
        result = self.run_check()
        self.assertEqual(result["state"], "desktop_preflight_failed")
        self.assertNotIn("credential", self.status.read_text())

    def test_child_auth_failure_is_review_signal_not_zero_counts(self):
        self.lifecycle.return_value["state"] = "check_failed"
        mail.private_json(self.observation, {"run_id": "test-run", "ok": False, "needs_mail_review": True, "error": "private"})
        result = self.run_check()
        self.assertTrue(result["needs_mail_review"])
        self.assertFalse(result["ok"])
        self.assertNotIn("applications", result)
        self.assertNotIn("private", self.status.read_text())

    def test_cleanup_failure_cannot_be_overwritten_by_successful_collection(self):
        mail.private_json(self.observation, observation())
        self.lifecycle.return_value.update(state="desktop_cleanup_failed", desktop_stopped=False)
        result = self.run_check()
        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "desktop_cleanup_failed")
        self.assertIsNone(result["last_successful_checked_at"])


class CollectionTests(unittest.TestCase):
    def test_single_lock_covers_both_folders_and_restoration_on_failure(self):
        for fail in (False, True):
            with self.subTest(fail=fail), contextlib.ExitStack() as stack:
                frame = SimpleNamespace(url="https://mail.example/applications/mail2/en-us/")
                page = MagicMock(url="https://www.icloud.com/mail/")
                page.frames = [frame]
                connected = SimpleNamespace(contexts=[SimpleNamespace(pages=[page])])
                pw = MagicMock()
                pw.chromium.connect_over_cdp.return_value = connected
                stack.enter_context(patch.object(mail, "sync_playwright", return_value=contextlib.nullcontext(pw)))
                lock = stack.enter_context(patch.object(mail.browser, "browser_operation_lock", return_value=contextlib.nullcontext()))
                select = stack.enter_context(patch.object(mail, "select_folder"))
                apps = stack.enter_context(patch.object(mail.applications, "_read_application_counts_locked", return_value=[{}]))
                fits = stack.enter_context(patch.object(mail.intake, "_read_folder_counts_locked", return_value=(2, 0)))
                if fail:
                    fits.side_effect = RuntimeError("incomplete folder")
                    with self.assertRaises(RuntimeError):
                        mail.collect_counts({"folder_name": "Inbox"})
                else:
                    self.assertEqual(mail.collect_counts({"folder_name": "Inbox"}), ([{}], (2, 0)))
                lock.assert_called_once_with(timeout_seconds=5)
                apps.assert_called_once()
                self.assertEqual([call.args[1] for call in select.call_args_list], ["Inbox", mail.intake.FOLDER_NAME, "Inbox"])
                page.bring_to_front.assert_called_once()

    def test_folder_selection_clicks_only_exact_option_not_mail_row(self):
        frame = MagicMock()
        option = frame.get_by_role.return_value
        option.count.return_value = 1
        option.get_attribute.return_value = "false"
        mail.select_folder(frame, "Inbox")
        frame.get_by_role.assert_called_once_with("option", name="Inbox", exact=True)
        option.click.assert_called_once()
        self.assertEqual(frame.wait_for_function.call_args.kwargs["arg"], "Inbox")


class LoopTests(unittest.TestCase):
    def test_auth_failure_and_third_failure_pause_but_skips_do_not(self):
        skip = {"state": "skipped_active_or_partial_desktop", "ok": False}
        fail = {"state": "check_failed", "ok": False}
        for reports in (
            [{**fail, "needs_mail_review": True}],
            [skip, fail, fail, fail],
            [{"state": "desktop_cleanup_failed", "ok": False}],
            [{"state": "check_interrupted", "ok": False}],
        ):
            with self.subTest(reports=reports), tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(mail.desktop_lease, "lifecycle_lease", return_value=contextlib.nullcontext()))
                stack.enter_context(patch.object(mail, "LOG_PATH", Path(directory) / "log.jsonl"))
                status = Path(directory) / "status.json"
                stack.enter_context(patch.object(mail, "STATUS_PATH", status))
                stack.enter_context(patch.object(mail, "cooldown_seconds", return_value=0))
                check = stack.enter_context(patch.object(mail, "run_once", side_effect=copy.deepcopy(reports)))
                stack.enter_context(patch.object(mail.time, "sleep"))
                stack.enter_context(patch("builtins.print"))
                mail.loop(60)
                self.assertEqual(check.call_count, len(reports))
                self.assertTrue(json.loads(status.read_text())["loop_paused"])

    def test_minimum_interval_and_startup_cooldown(self):
        with self.assertRaises(ValueError):
            mail.loop(59)
        with patch.object(mail, "private_status", return_value={"checked_at": mail.intake.utc_now()}):
            self.assertGreater(mail.cooldown_seconds(60), 3590)
        with patch.object(mail, "private_status", return_value={"checked_at": "invalid"}):
            self.assertEqual(mail.cooldown_seconds(60), 0)


if __name__ == "__main__":
    unittest.main()
