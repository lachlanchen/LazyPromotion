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
        "gmail": {"state": "not_configured"},
        "alerts": [], "policy": dict(mail.POLICY),
    }


class ObservationTests(unittest.TestCase):
    def test_stage_annotation_preserves_exception_and_inner_operation(self):
        for error in (mail.BrowserTimeout("private locator"), mail.MailSessionUnavailable("private account")):
            with self.subTest(error_type=type(error)), self.assertRaises(type(error)) as raised:
                with mail.observation_stage("application_count_read"):
                    with mail.observation_stage("mail_connection"):
                        raise error
            self.assertIs(raised.exception, error)
            self.assertEqual(mail.failure_stage(error), "mail_connection")
        with self.assertRaises(ValueError):
            with mail.observation_stage("private folder name"):
                self.fail("invalid stage must not run")

    def test_untrusted_stage_values_never_become_output(self):
        error = RuntimeError("private browser text")
        for value in (None, "private browser URL", ["private"], {"subject": "private"}):
            with self.subTest(value=value):
                error._mail_observation_stage = value
                self.assertEqual(mail.failure_stage(error), "unclassified")

    def test_child_failure_emits_only_fixed_diagnostics(self):
        error = mail.BrowserTimeout("private subject, account and URL")
        error._mail_observation_stage = "application_folder_selection"
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(mail.sys, "argv", ["mail", "_collect", "--run-id", "test-run"]))
            stack.enter_context(patch.object(mail.os, "umask"))
            stack.enter_context(patch.object(mail.signal, "signal"))
            stack.enter_context(patch.object(mail, "collect_once", side_effect=error))
            save = stack.enter_context(patch.object(mail, "private_json"))
            with self.assertRaises(SystemExit) as raised:
                mail.main()
        self.assertEqual(raised.exception.code, 1)
        save.assert_called_once()
        result = save.call_args.args[1]
        self.assertFalse(result["ok"])
        self.assertFalse(result["needs_mail_review"])
        self.assertEqual(result["failure_reason"], "browser_timeout")
        self.assertEqual(result["failure_stage"], "application_folder_selection")
        self.assertNotIn("private", json.dumps(result))

    def test_failure_reasons_never_echo_private_browser_errors(self):
        self.assertEqual(mail.failure_reason(RuntimeError("subject: private example")), "unavailable_or_incomplete")
        self.assertEqual(mail.failure_reason(mail.BrowserTimeout("private URL")), "browser_timeout")
        self.assertEqual(mail.failure_reason(RuntimeError("iCloud exposed incomplete application inbox coverage")), "application_coverage_incomplete")

    def test_pending_gmail_activity_requires_one_aggregate_alert(self):
        good = observation()
        good["gmail"] = {"state": "checked", "campaign_count": 2,
                         "matching_thread_count": 1, "unread_matching_thread_count": 0,
                         "review_required": True}
        alert = {"kind": "gmail_application_activity_pending"}
        good["alerts"] = [alert]
        mail.validated_observation(good, "test-run")
        for alerts in ([], [alert, alert], [{**alert, "subject": "private"}]):
            with self.subTest(alerts=alerts), self.assertRaises(ValueError):
                mail.validated_observation({**good, "alerts": alerts}, "test-run")
        with self.assertRaises(ValueError):
            mail.validated_observation({**observation(), "alerts": [alert]}, "test-run")

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
            {"gmail": {"state": "checked", "subject": "private"}},
            {"gmail": {"state": "session_unavailable", "matching_thread_count": 0}},
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

    def test_child_failure_stage_is_whitelisted_without_changing_lifecycle(self):
        self.lifecycle.return_value["state"] = "check_failed"
        for stage in ("application_folder_selection", "private URL", ["private"], None):
            with self.subTest(stage=stage):
                mail.private_json(self.observation, {
                    "run_id": "test-run", "ok": False, "needs_mail_review": False,
                    "failure_stage": stage, "error": "private mailbox content",
                })
                result = self.run_check()
                self.assertFalse(result["ok"])
                self.assertEqual(result["state"], "check_failed")
                self.assertNotIn("applications", result)
                self.assertNotIn("private", self.status.read_text())
                if stage == "application_folder_selection":
                    self.assertEqual(result["failure_stage"], stage)
                else:
                    self.assertNotIn("failure_stage", result)

    def test_legacy_child_review_signal_is_preserved(self):
        self.lifecycle.return_value["state"] = "check_failed"
        mail.private_json(self.observation, {
            "run_id": "test-run", "needs_mail_review": True,
            "failure_stage": "mail_tab_selection",
        })
        result = self.run_check()
        self.assertTrue(result["needs_mail_review"])
        self.assertFalse(result["ok"])
        self.assertNotIn("failure_stage", result)

    def test_cleanup_failure_cannot_be_overwritten_by_successful_collection(self):
        mail.private_json(self.observation, observation())
        self.lifecycle.return_value.update(state="desktop_cleanup_failed", desktop_stopped=False)
        result = self.run_check()
        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "desktop_cleanup_failed")
        self.assertIsNone(result["last_successful_checked_at"])


class CollectionTests(unittest.TestCase):
    def test_failure_stage_identifies_existing_operation_without_retries(self):
        for stage in sorted(mail.FAILURE_STAGES):
            with self.subTest(stage=stage), contextlib.ExitStack() as stack:
                error = mail.BrowserTimeout("private browser diagnostic")
                frame = SimpleNamespace(url="https://mail.example/applications/mail2/en-us/")
                page = MagicMock(url="https://www.icloud.com/mail/")
                page.frames = [frame]
                pw = MagicMock()
                connect = pw.chromium.connect_over_cdp
                connect.return_value = SimpleNamespace(contexts=[SimpleNamespace(pages=[page])])
                stack.enter_context(patch.object(mail, "sync_playwright", return_value=contextlib.nullcontext(pw)))
                stack.enter_context(patch.object(mail.browser, "browser_operation_lock", return_value=contextlib.nullcontext()))
                select = stack.enter_context(patch.object(mail, "select_folder"))
                apps = stack.enter_context(patch.object(mail.applications, "_read_application_counts_locked", return_value=[{}]))
                fits = stack.enter_context(patch.object(mail.intake, "_read_folder_counts_locked", return_value=(2, 0)))
                evidence = stack.enter_context(patch.object(mail, "folder_evidence"))
                expected = error
                if stage == "mail_connection":
                    connect.side_effect = error
                elif stage == "mail_tab_selection":
                    page.bring_to_front.side_effect = error
                elif stage == "mail_frame_readiness":
                    page.frames = []
                    stack.enter_context(patch.object(mail.time, "monotonic", side_effect=[0, 16]))
                    expected = None
                elif stage == "application_folder_selection":
                    select.side_effect = error
                elif stage == "application_count_read":
                    apps.side_effect = error
                elif stage == "fit_folder_selection":
                    select.side_effect = [None, error, None]
                elif stage == "fit_count_read":
                    fits.side_effect = error
                elif stage == "application_folder_restore":
                    select.side_effect = [None, None, error]
                elif stage == "evidence_capture":
                    evidence.side_effect = error
                with self.assertRaises(Exception) as raised:
                    mail.collect_counts({"folder_name": "Inbox"}, capture_evidence=True)
                self.assertEqual(mail.failure_stage(raised.exception), stage)
                if expected is not None:
                    self.assertIs(raised.exception, expected)
                else:
                    self.assertIsInstance(raised.exception, mail.MailSessionUnavailable)
                connect.assert_called_once()
                self.assertLessEqual(apps.call_count, 1)
                self.assertLessEqual(fits.call_count, 1)
                self.assertLessEqual(select.call_count, 3)

    def test_gmail_pending_activity_is_visible_to_root_alert_consumers(self):
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(mail.applications, "load_config", return_value={}))
            stack.enter_context(patch.object(mail, "collect_counts", return_value=([], (2, 0))))
            stack.enter_context(patch.object(mail.applications, "record_observation", return_value={"summary": observation()["applications"], "alerts": []}))
            stack.enter_context(patch.object(mail.intake, "record_observation", return_value={"alerts": []}))
            stack.enter_context(patch.object(mail.gmail, "check_optional", return_value={
                "state": "checked", "campaign_count": 2, "matching_thread_count": 1,
                "unread_matching_thread_count": 0, "review_required": True}))
            result = mail.collect_once("test-run")
        self.assertEqual(result["alerts"], [{"kind": "gmail_application_activity_pending"}])
        mail.validated_observation(result, "test-run")

    def test_gmail_failure_preserves_icloud_observation_without_zero_claim(self):
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(mail.applications, "load_config", return_value={}))
            stack.enter_context(patch.object(mail, "collect_counts", return_value=([], (2, 0))))
            stack.enter_context(patch.object(mail.applications, "record_observation", return_value={"summary": observation()["applications"], "alerts": []}))
            stack.enter_context(patch.object(mail.intake, "record_observation", return_value={"alerts": []}))
            stack.enter_context(patch.object(mail.gmail, "check_optional", side_effect=RuntimeError("private error")))
            result = mail.collect_once("test-run")
        self.assertTrue(result["ok"])
        self.assertEqual(result["fit_folder"], {"message_count": 2, "unread_count": 0})
        self.assertEqual(result["gmail"], {"state": "observation_failed"})
        self.assertNotIn("private error", json.dumps(result))
        mail.validated_observation(result, "test-run")

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
