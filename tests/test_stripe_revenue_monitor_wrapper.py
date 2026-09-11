import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "stripe-revenue-monitor.sh"


class StripeRevenueMonitorWrapperTests(unittest.TestCase):
    def test_shell_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrapper_has_one_private_browser_independent_session(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('SESSION="lazypromotion-stripe-revenue-monitor"', text)
        self.assertIn("--confirm-private-financial-read", text)
        self.assertIn("tmux has-session", text)
        self.assertIn("chmod 600", text)
        self.assertNotIn("desktop.sh", text)
        self.assertNotIn("firefox", text.casefold())

    def test_minimum_interval_is_explicit(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("STRIPE_REVENUE_MONITOR_INTERVAL_MINUTES", text)
        self.assertIn("INTERVAL_MINUTES < 15", text)
        self.assertIn("umask 077", text)


if __name__ == "__main__":
    unittest.main()
