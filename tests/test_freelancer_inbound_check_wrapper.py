import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "freelancer-inbound-check.sh"


class FreelancerInboundCheckWrapperTests(unittest.TestCase):
    def test_shell_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrapper_owns_only_a_fully_stopped_project_stack(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('DESKTOP="$ROOT/scripts/desktop.sh"', text)
        self.assertIn('stack_status="$("$DESKTOP" status || true)"', text)
        self.assertIn("stopped_count == COMPONENT_COUNT", text)
        self.assertIn("running_count != COMPONENT_COUNT", text)
        self.assertIn('"$DESKTOP" start', text)
        self.assertIn('"$DESKTOP" stop', text)
        self.assertIn("started_here", text)
        self.assertNotIn("firefox", text.casefold())

    def test_wrapper_is_one_shot_private_and_serialized(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("umask 077", text)
        self.assertIn("flock -n 9", text)
        self.assertIn("freelancer_inbound_monitor.py once", text)
        self.assertNotIn("freelancer_inbound_monitor.py loop", text)
        self.assertIn(".local/private/freelancer_login.py", text)
        self.assertIn("session is not authenticated", text)
        self.assertIn('[[ -L "$LOGIN_HELPER" ]]', text)
        self.assertNotIn("CREDENTIALS.md", text)
        self.assertNotIn("credential_vault", text)
        self.assertNotIn("message", text.casefold().replace("inbound", ""))


if __name__ == "__main__":
    unittest.main()
