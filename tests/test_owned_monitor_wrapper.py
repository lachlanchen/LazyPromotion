import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "owned-monitor.sh"


class OwnedMonitorWrapperTests(unittest.TestCase):
    def test_shell_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrapper_is_browser_independent_and_single_session(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('SESSION="lazypromotion-owned-monitor"', text)
        self.assertIn("python owned_monitor.py loop", text)
        self.assertIn("python owned_monitor.py status", text)
        self.assertIn("tmux has-session", text)
        self.assertNotIn("desktop.sh", text)
        self.assertNotIn("firefox", text.casefold())

    def test_private_log_and_minimum_interval_are_explicit(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("OWNED_MONITOR_INTERVAL_MINUTES", text)
        self.assertIn("INTERVAL_MINUTES < 5", text)
        self.assertIn("umask 077", text)
        self.assertIn(".local/owned-monitor-stdout.log", text)


if __name__ == "__main__":
    unittest.main()
