from __future__ import annotations

from collections.abc import Iterator
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import threading

import pytest
from playwright.sync_api import Browser, Page, Playwright, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixture"
ARTIFACT_DIR = Path(
    os.environ.get(
        "ARTIFACT_DIR",
        ROOT.parents[1] / ".local" / "proofs" / "playwright-regression",
    )
)


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(  # noqa: E731
        *args, directory=str(FIXTURE), **kwargs
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@pytest.fixture(scope="session")
def playwright_instance() -> Iterator[Playwright]:
    with sync_playwright() as instance:
        yield instance


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Iterator[Browser]:
    executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if executable is None and Path("/usr/bin/google-chrome").is_file():
        executable = "/usr/bin/google-chrome"
    launch_options = {"headless": True}
    if executable:
        launch_options["executable_path"] = executable
    instance = playwright_instance.chromium.launch(**launch_options)
    try:
        yield instance
    finally:
        instance.close()


@pytest.fixture
def page(browser: Browser, request: pytest.FixtureRequest) -> Iterator[Page]:
    context = browser.new_context()
    current = context.new_page()
    yield current
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        screenshot_dir = ARTIFACT_DIR / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        current.screenshot(path=str(screenshot_dir / f"{request.node.name}.png"))
    context.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
