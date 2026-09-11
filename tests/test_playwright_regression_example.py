from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPECIMEN = ROOT / "examples" / "playwright-regression"


class PlaywrightRegressionExampleTests(unittest.TestCase):
    def test_specimen_has_a_bounded_mcp_ci_entry_point(self):
        readme = (SPECIMEN / "README.md").read_text(encoding="utf-8")
        runner = (SPECIMEN / "run_suite.sh").read_text(encoding="utf-8")
        self.assertIn("project-owned login fixture", readme)
        self.assertIn("capped manual\nchecklist", readme)
        self.assertIn("--junitxml", runner)
        self.assertIn("ARTIFACT_DIR", runner)

    def test_specimen_keeps_selectors_in_a_page_object(self):
        page_object = (SPECIMEN / "pages" / "login_page.py").read_text(
            encoding="utf-8"
        )
        tests = (SPECIMEN / "tests" / "test_login.py").read_text(encoding="utf-8")
        self.assertIn("class LoginPage", page_object)
        self.assertIn("get_by_label", page_object)
        self.assertIn("get_by_role", page_object)
        self.assertIn("LoginPage(page, base_url)", tests)
        self.assertNotIn("locator(", tests)

    def test_repeatability_wrapper_runs_exactly_three_times(self):
        wrapper = (SPECIMEN / "verify_three_runs.sh").read_text(encoding="utf-8")
        self.assertIn("for run in 1 2 3", wrapper)
        self.assertIn("run_suite.sh", wrapper)


if __name__ == "__main__":
    unittest.main()
