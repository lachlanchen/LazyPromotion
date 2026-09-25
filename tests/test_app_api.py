import io
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

import app_api
import app_workspace


def request(path="/api/v1/workspace", method="GET", **overrides):
    env = {
        "REQUEST_METHOD": method, "PATH_INFO": path,
        "HTTP_HOST": "127.0.0.1:18936", "QUERY_STRING": "",
        "CONTENT_LENGTH": "", "wsgi.input": io.BytesIO(),
        **overrides,
    }
    result = {}

    def start_response(status, headers):
        result.update(status=int(status.split()[0]), headers=dict(headers))

    result["body"] = b"".join(app_api.application(env, start_response))
    return result


class AppApiTests(unittest.TestCase):
    def test_workspace_is_exact_existing_contract(self):
        result = request()
        self.assertEqual(result["status"], 200)
        self.assertEqual(json.loads(result["body"]), app_workspace.workspace())
        self.assertEqual(int(result["headers"]["Content-Length"]), len(result["body"]))

    def test_project_scope_retains_same_envelope(self):
        for project in app_workspace.SOURCES:
            with self.subTest(project=project):
                result = request(f"/api/v1/projects/{project}")
                self.assertEqual(result["status"], 200)
                self.assertEqual(json.loads(result["body"]), app_workspace.workspace([project]))

    def test_health_does_not_claim_catalog_or_provider_health(self):
        with patch.object(app_workspace, "workspace", side_effect=RuntimeError):
            self.assertEqual(json.loads(request("/healthz")["body"]), {"status": "ok"})
            self.assertEqual(request()["status"], 503)

    def test_head_has_get_headers_but_no_body(self):
        for path in ("/api/v1/workspace", "/healthz", "/missing"):
            with self.subTest(path=path):
                get, head = request(path), request(path, "HEAD")
                self.assertEqual(head["status"], get["status"])
                self.assertEqual(head["headers"], get["headers"])
                self.assertEqual(head["body"], b"")

    def test_mutations_and_preflights_never_load_workspace(self):
        with patch.object(app_workspace, "workspace") as load:
            for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"):
                with self.subTest(method=method):
                    result = request(method=method)
                    self.assertEqual(result["status"], 405)
                    self.assertEqual(result["headers"]["Allow"], "GET, HEAD")
            load.assert_not_called()

    def test_arbitrary_files_and_action_routes_never_resolve(self):
        with patch.object(app_workspace, "workspace") as load:
            for path in ("/", "/api/v1/workspace/", "/api/v1/projects/unknown",
                         "/api/v1/projects/bunko/", "/.local/lazypromotion.sqlite3",
                         "/../README.md", "/%2e%2e/.local", "/docs", "/api/v1/approve",
                         "/api/v1/publish", "/api/v1/drafts", "/openapi.json"):
                with self.subTest(path=path):
                    self.assertEqual(request(path)["status"], 404)
            load.assert_not_called()

    def test_queries_and_bodies_are_rejected_without_reading(self):
        class Unreadable:
            def read(self, *args):
                raise AssertionError("Request body must not be read")

        for options in ({"QUERY_STRING": "project=bunko"}, {"CONTENT_LENGTH": "999999"},
                        {"CONTENT_LENGTH": "-1"}, {"CONTENT_LENGTH": "nonsense"},
                        {"HTTP_TRANSFER_ENCODING": "chunked"}):
            with self.subTest(options=options):
                self.assertEqual(request(**{**options, "wsgi.input": Unreadable()})["status"], 400)

    def test_hosts_do_not_trust_forwarded_values(self):
        for host in ("evil.example", "localhost.evil.example", "", "localhost:0", "localhost:65536",
                     "user:pass@localhost", "localhost/", "localhost?x", "localhost#x",
                     "127.0.0.1:bad", "127.0.0.1:", "127.0.0.1:018936", " localhost"):
            with self.subTest(host=host):
                self.assertEqual(request(HTTP_HOST=host, HTTP_X_FORWARDED_HOST="localhost")["status"], 400)
        for host in ("localhost", "localhost:18936", "127.0.0.1", "127.0.0.1:18936"):
            with self.subTest(host=host):
                self.assertEqual(request(HTTP_HOST=host, HTTP_X_FORWARDED_HOST="evil.example")["status"], 200)

    def test_only_same_origin_browser_reads(self):
        for origin in ("https://evil.example", "null", "http://localhost:18936", "http://127.0.0.1:9000"):
            with self.subTest(origin=origin):
                self.assertEqual(request(HTTP_ORIGIN=origin)["status"], 403)
        self.assertEqual(request(HTTP_ORIGIN="http://127.0.0.1:18936")["status"], 200)
        self.assertEqual(request(HTTP_SEC_FETCH_SITE="cross-site")["status"], 403)

    def test_failures_are_generic_and_uncached(self):
        for failure in (ValueError("private source text"), OSError("/home/private/path"), TypeError("secret")):
            with self.subTest(failure=type(failure)), patch.object(app_workspace, "workspace", side_effect=failure):
                result = request()
                self.assertEqual(result["status"], 503)
                self.assertEqual(json.loads(result["body"]), {"error": "workspace_unavailable"})
                self.assertEqual(result["headers"]["Cache-Control"], "no-store")

    def test_response_size_cap_and_security_headers_on_errors(self):
        with patch.object(app_api, "MAX_RESPONSE_BYTES", 32):
            self.assertEqual(request()["status"], 503)
        for result in (request(), request("/missing"), request(method="POST")):
            for key, value in app_api.SECURITY_HEADERS:
                self.assertEqual(result["headers"][key], value)
            self.assertNotIn("Access-Control-Allow-Origin", result["headers"])
            self.assertNotIn("Set-Cookie", result["headers"])

    def test_listener_refuses_non_loopback_bind(self):
        with self.assertRaises(ValueError):
            app_api.LocalServer(("0.0.0.0", 0), app_api.LocalRequestHandler)

    def test_real_http_loopback_and_cleanup(self):
        opener = build_opener(ProxyHandler({}))
        with app_api.make_local_server(0) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with opener.open(base + "/api/v1/projects/bunko", timeout=5) as response:
                    result = json.load(response)
                self.assertEqual(result["projects"][0]["id"], "bunko")
                self.assertIsNone(result["projects"][0]["outcomes"]["receivedGrossUsd"]["value"])
                with self.assertRaises(HTTPError) as error:
                    opener.open(Request(base + "/api/v1/publish", data=b"ignored", method="POST"), timeout=5)
                self.assertEqual(error.exception.code, 405)
                error.exception.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
        self.assertEqual(server.fileno(), -1)

    def test_no_private_operator_imports(self):
        source = Path(app_api.__file__).read_text()
        for dependency in ("import promotion", "import browser", "import sqlite3", "import subprocess"):
            self.assertNotIn(dependency, source)


if __name__ == "__main__":
    unittest.main()
