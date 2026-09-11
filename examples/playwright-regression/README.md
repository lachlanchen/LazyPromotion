# Playwright regression-suite specimen

This small, executed specimen shows the structure proposed for a browser
regression project:

- page objects keep selectors and user actions in one place;
- pytest fixtures own the browser and an isolated local test server;
- tests describe user-visible paths rather than DOM implementation details;
- failed tests retain a screenshot;
- one stable command emits JUnit XML for CI or an MCP runner.

The target is a deterministic project-owned login fixture, not a customer
application or a claim that an unknown manual checklist is already covered.

## Run

```bash
python -m pip install -r examples/playwright-regression/requirements.txt
playwright install chromium
examples/playwright-regression/run_suite.sh
```

Artifacts default to `.local/proofs/playwright-regression/` and stay outside
Git. Override the location when a pipeline manages its own workspace:

```bash
ARTIFACT_DIR="$PWD/test-results" examples/playwright-regression/run_suite.sh
```

The command exits non-zero on a test failure and writes
`junit-playwright.xml`. An MCP or merge pipeline can call the same command and
return the exit code plus artifact path without giving a model browser, file,
or credential privileges.

## Layout

```text
pages/login_page.py       selectors and login actions
tests/conftest.py         server, browser, context, and failure screenshots
tests/test_login.py       successful and rejected login paths
fixture/index.html        deterministic test target
run_suite.sh              stable CI/MCP entry point
verify_three_runs.sh      repeatability check
```

For a real application, the first funded milestone would replace the fixture
with the agreed staging URL, roles, test-data reset contract, and capped manual
checklist. Credentials belong in runtime secrets, never in the suite.
