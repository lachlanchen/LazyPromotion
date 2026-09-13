import contextlib
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import desktop_lease as lease


class LifecycleLockTests(unittest.TestCase):
    def test_lock_is_exclusive_private_and_released(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".local" / "runtime" / "desktop-lifecycle.lock"
            with lease.lifecycle_lease(path):
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                with self.assertRaises(lease.DesktopBusy):
                    with lease.lifecycle_lease(path):
                        self.fail("a second owner acquired the lease")
            with lease.lifecycle_lease(path):
                pass

    def test_symlink_lock_is_rejected_without_changing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "unrelated"
            target.write_text("keep")
            path = root / ".local" / "runtime" / "desktop-lifecycle.lock"
            path.parent.mkdir(parents=True)
            path.symlink_to(target)
            with self.assertRaises(OSError):
                with lease.lifecycle_lease(path):
                    pass
            self.assertEqual(target.read_text(), "keep")

    def test_live_birth_identity_is_available(self):
        identity = lease.process_identity(os.getpid())
        self.assertIsNotNone(identity)
        self.assertGreater(identity[0], 0)

    def test_real_child_timeout_reaps_the_owned_process(self):
        created = []
        real_popen = subprocess.Popen

        def remember(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            created.append(process)
            return process

        with patch.object(lease.subprocess, "Popen", side_effect=remember):
            with self.assertRaises(subprocess.TimeoutExpired):
                lease.run_check_command(
                    [sys.executable, "-c", "import time; time.sleep(30)"], timeout=0.05
                )
        self.assertEqual(len(created), 1)
        self.assertIsNotNone(created[0].returncode)
        self.assertIsNone(lease.process_identity(created[0].pid))

    def test_reused_pid_or_missing_owner_record_refuses_cleanup(self):
        expected = {"chrome": (123, 20)}
        for current, identity in (({"chrome": (123, 21)}, (21, "chrome")), ({}, (20, "chrome"))):
            with self.subTest(current=current), patch.object(
                lease, "stack_snapshot", return_value=current
            ), patch.object(lease, "process_identity", return_value=identity):
                self.assertFalse(lease.ownership_unchanged(expected))

    def test_exited_owned_process_is_not_a_replacement(self):
        with patch.object(lease, "stack_snapshot", return_value={}), patch.object(
            lease, "process_identity", return_value=None
        ):
            self.assertTrue(lease.ownership_unchanged({"chrome": (123, 20)}))

    def test_actual_shell_guard_rejects_forged_fd_and_accepts_held_lease(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "scripts"
            scripts.mkdir()
            prefix = lease.SCRIPT.read_text().split("\npid_alive() {", 1)[0]
            script = scripts / "desktop.sh"
            script.write_text(prefix + '\nprintf "guard reached\\n"\n')
            helper = root / "desktop_lease.py"
            helper.write_text(Path(lease.__file__).read_text())
            lock = root / ".local" / "runtime" / "desktop-lifecycle.lock"
            env = dict(os.environ)
            env[lease.LEASE_ENV] = "999"
            forged = subprocess.run(
                ["bash", str(script), "start"], env=env,
                capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(forged.returncode, 2)
            self.assertNotIn("guard reached", forged.stdout)
            with lease.lifecycle_lease(lock) as fd:
                env[lease.LEASE_ENV] = str(fd)
                accepted = subprocess.run(
                    ["bash", str(script), "start"], env=env, pass_fds=(fd,),
                    capture_output=True, text=True, timeout=5,
                )
                self.assertEqual(accepted.returncode, 0, accepted.stderr)
                self.assertIn("guard reached", accepted.stdout)
                env.pop(lease.LEASE_ENV)
                busy = subprocess.run(
                    ["bash", str(script), "start"], env=env,
                    capture_output=True, text=True, timeout=5,
                )
                self.assertEqual(busy.returncode, 75, busy.stderr)
                self.assertNotIn("guard reached", busy.stdout)


class FiniteDesktopTests(unittest.TestCase):
    def setUp(self):
        self.patches = contextlib.ExitStack()
        self.addCleanup(self.patches.close)
        self.patches.enter_context(patch.object(
            lease, "lifecycle_lease", return_value=contextlib.nullcontext(3)
        ))
        self.snapshot = self.patches.enter_context(patch.object(
            lease, "stack_snapshot", side_effect=[{}, {name: (i + 1, 100) for i, name in enumerate(lease.COMPONENTS)}, {}]
        ))
        self.patches.enter_context(patch.object(lease, "ports_closed", return_value=True))
        self.resources = self.patches.enter_context(patch.object(lease, "resources_available", return_value=True))
        self.ownership = self.patches.enter_context(patch.object(lease, "ownership_unchanged", return_value=True))
        status = "\n".join(f"{name} stopped" for name in lease.COMPONENTS)
        self.stack = self.patches.enter_context(patch.object(
            lease, "stack_command", return_value=subprocess.CompletedProcess([], 0, status, "")
        ))
        self.command = self.patches.enter_context(patch.object(lease, "run_check_command", return_value=0))

    def test_success_starts_and_stops_exactly_once(self):
        result = lease.run_owned_check(["python", "check.py"])
        self.assertEqual(result["state"], "checked")
        self.assertTrue(result["desktop_stopped"])
        self.assertEqual([call.args[0] for call in self.stack.call_args_list], ["status", "start", "stop"])

    def test_active_desktop_is_skipped_without_touching_it(self):
        self.snapshot.side_effect = [{"chrome": (1, 2)}]
        self.assertEqual(lease.run_owned_check(["check"])["state"], "skipped_active_or_partial_desktop")
        self.stack.assert_not_called()
        self.command.assert_not_called()

    def test_resource_pressure_does_not_launch(self):
        self.resources.return_value = False
        self.assertEqual(lease.run_owned_check(["check"])["state"], "skipped_resource_pressure")
        self.assertEqual([call.args[0] for call in self.stack.call_args_list], ["status"])
        self.command.assert_not_called()

    def test_failed_check_and_timeout_both_clean_up(self):
        self.command.side_effect = subprocess.TimeoutExpired("private-command", 1)
        result = lease.run_owned_check(["check"])
        self.assertEqual(result["state"], "check_timeout")
        self.assertTrue(result["desktop_stopped"])
        self.assertNotIn("private-command", str(result))

    def test_nonzero_check_still_cleans_up(self):
        self.command.return_value = 1
        result = lease.run_owned_check(["check"])
        self.assertEqual(result["state"], "check_failed")
        self.assertTrue(result["desktop_stopped"])

    def test_partial_start_is_cleaned_without_running_collection(self):
        self.snapshot.side_effect = [{}, {"xvfb": (1, 100)}, {}]
        result = lease.run_owned_check(["check"])
        self.assertEqual(result["state"], "desktop_start_failed")
        self.assertTrue(result["desktop_stopped"])
        self.command.assert_not_called()

    def test_cleanup_failure_is_not_success(self):
        self.snapshot.side_effect = [{}, {name: (i + 1, 100) for i, name in enumerate(lease.COMPONENTS)}, {"xvfb": (1, 100)}]
        result = lease.run_owned_check(["check"])
        self.assertEqual(result["state"], "desktop_cleanup_failed")
        self.assertFalse(result["desktop_stopped"])

    def test_changed_ownership_refuses_stop(self):
        self.ownership.return_value = False
        result = lease.run_owned_check(["check"])
        self.assertEqual(result["state"], "cleanup_refused_ownership_changed")
        self.assertEqual([call.args[0] for call in self.stack.call_args_list], ["status", "start"])

    def test_interrupt_still_cleans_up(self):
        self.command.side_effect = KeyboardInterrupt
        result = lease.run_owned_check(["check"])
        self.assertEqual(result["state"], "check_interrupted")
        self.assertTrue(result["desktop_stopped"])
        self.assertEqual(self.stack.call_args.args[0], "stop")


if __name__ == "__main__":
    unittest.main()
