from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, Route, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixture"
ARTIFACT_DIR = Path(
    os.environ.get(
        "ARTIFACT_DIR",
        ROOT.parents[1] / ".local" / "proofs" / "stateful-pwa-recovery",
    )
)


@dataclass
class ApiFixture:
    notes: dict[str, dict[str, dict[str, str]]] = field(default_factory=dict)
    attempts: list[dict[str, str]] = field(default_factory=list)
    fail_next_posts: int = 0

    def handle(self, route: Route) -> None:
        request = route.request
        parsed = urlsplit(request.url)
        if request.method == "GET":
            owner = parse_qs(parsed.query).get("owner", [""])[0]
            rows = list(self.notes.get(owner, {}).values())
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"notes": rows}))
            return
        if request.method == "POST":
            payload = request.post_data_json
            row = {key: str(payload.get(key) or "") for key in ("id", "owner", "text")}
            self.attempts.append(row)
            if self.fail_next_posts:
                self.fail_next_posts -= 1
                route.fulfill(status=503, content_type="application/json", body='{"error":"fixture interruption"}')
                return
            owner_notes = self.notes.setdefault(row["owner"], {})
            owner_notes.setdefault(row["id"], {**row, "status": "saved"})
            route.fulfill(status=200, content_type="application/json", body=json.dumps(owner_notes[row["id"]]))
            return
        route.fulfill(status=405, body="method not allowed")


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
    options = {"headless": True}
    if executable:
        options["executable_path"] = executable
    instance = playwright_instance.chromium.launch(**options)
    try:
        yield instance
    finally:
        instance.close()


@pytest.fixture
def recovery_page(browser: Browser, request: pytest.FixtureRequest) -> Iterator[tuple[Page, ApiFixture]]:
    context: BrowserContext = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    api = ApiFixture()
    page.route("**/api/notes**", api.handle)
    yield page, api
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        failure_dir = ARTIFACT_DIR / "failures"
        failure_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(failure_dir / f"{request.node.name}.png"), full_page=True)
        context.tracing.stop(path=str(failure_dir / f"{request.node.name}.zip"))
    else:
        context.tracing.stop()
    context.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

