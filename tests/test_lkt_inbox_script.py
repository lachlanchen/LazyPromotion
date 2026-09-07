import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lkt-inbox.sh"


class LktInboxScriptTests(unittest.TestCase):
    def test_wrapper_has_one_project_owned_session_and_safe_interval(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('SESSION="lazypromotion-lkt-inbox"', text)
        self.assertIn('LKT_INBOX_INTERVAL_MINUTES:-15', text)
        self.assertIn('(( INTERVAL_MINUTES < 5 ))', text)
        self.assertIn('python lkt_inbox.py loop --interval-minutes', text)
        self.assertIn('umask 077', text)
        self.assertNotIn('scripts/desktop.sh', text)

    def test_invalid_interval_fails_before_starting_tmux(self):
        env = dict(os.environ)
        env["LKT_INBOX_INTERVAL_MINUTES"] = "4"
        result = subprocess.run(
            ["bash", str(SCRIPT), "start"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("at least 5", result.stderr)


if __name__ == "__main__":
    unittest.main()
