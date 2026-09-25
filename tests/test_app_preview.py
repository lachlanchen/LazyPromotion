import io
import json
import unittest
from unittest.mock import patch

import app_preview as preview
import app_workspace


def request(path="/", method="GET", **overrides):
    env = {"REQUEST_METHOD": method, "PATH_INFO": path, "HTTP_HOST": "127.0.0.1:18936",
           "QUERY_STRING": "", "CONTENT_LENGTH": "", "wsgi.input": io.BytesIO(), **overrides}
    result = {}
    def respond(status, headers):
        result.update(status=int(status.split()[0]), headers=dict(headers))
    result["body"] = b"".join(preview.application(env, respond))
    return result


class AppPreviewTests(unittest.TestCase):
    def test_fixed_assets_and_head(self):
        for path, (_, content_type) in preview.ASSETS.items():
            with self.subTest(path=path):
                get, head = request(path), request(path, "HEAD")
                self.assertEqual(get["status"], 200)
                self.assertEqual(get["headers"]["Content-Type"], content_type)
                self.assertEqual(int(get["headers"]["Content-Length"]), len(get["body"]))
                self.assertEqual(head["headers"], get["headers"])
                self.assertEqual(head["body"], b"")
                self.assertEqual(get["headers"]["X-Robots-Tag"], "noindex, nofollow")
                self.assertIn("frame-ancestors 'none'", get["headers"]["Content-Security-Policy"])

    def test_existing_api_contract_is_unchanged(self):
        self.assertEqual(json.loads(request("/api/v1/workspace")["body"]), app_workspace.workspace())
        self.assertEqual(request("/api/v1/projects/bunko")["status"], 200)

    def test_assets_share_the_read_only_request_boundary(self):
        for path in ("/", "/app.mjs", "/sw.js"):
            for method in ("POST", "DELETE", "OPTIONS"):
                self.assertEqual(request(path, method)["status"], 405)
            self.assertEqual(request(path, HTTP_HOST="evil.example")["status"], 400)
            self.assertEqual(request(path, QUERY_STRING="secret=yes")["status"], 400)
            self.assertEqual(request(path, HTTP_ORIGIN="https://example.com")["status"], 403)
            self.assertEqual(request(path, HTTP_SEC_FETCH_SITE="cross-site")["status"], 403)
            self.assertEqual(request(path, CONTENT_LENGTH="50")["status"], 400)

    def test_not_a_repository_file_server(self):
        for path in ("/README.md", "/apps/web/index.html", "/../.local", "/.local/lazypromotion.sqlite3",
                     "/tests", "/api/v1/publish", "/api/v1/drafts", "/app.mjs/", "/favicon.ico"):
            self.assertEqual(request(path)["status"], 404)

    def test_missing_and_symlinked_assets_fail_without_source_details(self):
        for target in ("read_bytes", "is_symlink"):
            options = {"side_effect": OSError("private path")} if target == "read_bytes" else {"return_value": True}
            with patch.object(preview.Path, target, **options):
                result = request()
            self.assertEqual(result["status"], 503)
            self.assertEqual(int(result["headers"]["Content-Length"]), len(result["body"]))
            self.assertNotIn(b"private", result["body"])

    def test_manifest_and_worker_only_cache_app_shell(self):
        manifest = json.loads(request("/manifest.webmanifest")["body"])
        self.assertEqual(manifest["start_url"], "/")
        self.assertEqual(manifest["display"], "standalone")
        worker = request("/sw.js")["body"].decode()
        self.assertNotIn("/api/", worker)
        self.assertNotIn("'sync'", worker)
        self.assertNotIn("'push'", worker)


if __name__ == "__main__":
    unittest.main()
