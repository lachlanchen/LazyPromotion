from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPECIMEN = ROOT / "examples" / "stateful-pwa-recovery"


class StatefulPwaRecoveryExampleTests(unittest.TestCase):
    def test_public_specimen_is_synthetic_and_bounded(self):
        readme = (SPECIMEN / "README.md").read_text(encoding="utf-8")
        self.assertIn("project-owned fixture", readme)
        self.assertIn("contains no AiMemo source", readme)
        self.assertIn("up to three agreed recovery journeys / twelve checkpoints", readme)
        self.assertIn("customer-controlled staging PWA", readme)

    def test_fixture_namespaces_state_and_queues_before_write(self):
        fixture = (SPECIMEN / "fixture" / "index.html").read_text(encoding="utf-8")
        self.assertIn("recovery-fixture:draft:${owner}", fixture)
        self.assertIn("indexedDB.open", fixture)
        save_handler = fixture.split('document.querySelector("#save")', 1)[1]
        self.assertLess(save_handler.index("await queue("), save_handler.index("await flush()"))
        self.assertIn('localStorage.removeItem(sessionKey)', fixture)

    def test_three_journeys_cover_reload_retry_and_account_switch(self):
        tests = (SPECIMEN / "tests" / "test_recovery.py").read_text(encoding="utf-8")
        self.assertIn("test_reload_restores_scoped_draft_without_writing", tests)
        self.assertIn("test_interrupted_write_retries_same_id_once", tests)
        self.assertIn("test_account_switch_hides_cached_state", tests)
        self.assertIn('[first_id, first_id]', tests)

    def test_runner_keeps_junit_and_failure_evidence(self):
        runner = (SPECIMEN / "run_suite.sh").read_text(encoding="utf-8")
        conftest = (SPECIMEN / "tests" / "conftest.py").read_text(encoding="utf-8")
        repeat = (SPECIMEN / "verify_three_runs.sh").read_text(encoding="utf-8")
        self.assertIn("--junitxml", runner)
        self.assertIn("context.tracing.start", conftest)
        self.assertIn("page.screenshot", conftest)
        self.assertIn("for run in 1 2 3", repeat)


if __name__ == "__main__":
    unittest.main()
