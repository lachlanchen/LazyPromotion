#!/usr/bin/env python3
"""Loopback-only development API for the reviewed public campaign projection.

This is not the operator API or a production server. No provider, database,
browser, file-serving, drafting, approval or sending capability is imported.
"""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from urllib.parse import urlsplit
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import app_workspace


MAX_RESPONSE_BYTES = 512 * 1024
LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}
SECURITY_HEADERS = (
    ("Content-Type", "application/json; charset=utf-8"),
    ("Cache-Control", "no-store"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "no-referrer"),
    ("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"),
    ("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()"),
)


def loopback_authority(value: str) -> bool:
    """Validate the literal Host header without trusting forwarded headers."""
    try:
        url = urlsplit("http://" + value)
        return bool(
            value and not any(c.isspace() for c in value)
            and url.hostname in LOOPBACK_HOSTS
            and url.netloc == value and not url.path and not url.query
            and not url.fragment and url.username is None and url.password is None
            and (url.port is None or 1 <= url.port <= 65535)
            and (value in LOOPBACK_HOSTS or value == f"{url.hostname}:{url.port}")
        )
    except ValueError:
        return False


def request_problem(environ):
    """Shared read-only request boundary; never consume the request body."""
    if not loopback_authority(environ.get("HTTP_HOST", "")):
        return 400, "invalid_host", ()
    if environ.get("REQUEST_METHOD") not in {"GET", "HEAD"}:
        return 405, "read_only", (("Allow", "GET, HEAD"),)
    # No CORS and no cross-origin browser use, even from a loopback page.
    origin = environ.get("HTTP_ORIGIN")
    if origin is not None and origin != "http://" + environ["HTTP_HOST"]:
        return 403, "cross_origin_not_supported", ()
    if environ.get("HTTP_SEC_FETCH_SITE") == "cross-site":
        return 403, "cross_origin_not_supported", ()
    length = environ.get("CONTENT_LENGTH", "")
    if length not in {"", "0"} or environ.get("HTTP_TRANSFER_ENCODING"):
        return 400, "request_body_not_supported", ()
    if environ.get("QUERY_STRING"):
        return 400, "query_not_supported", ()
    return None


def application(environ, start_response):
    """Version-one read-only WSGI application, with no request-body reads."""
    method = environ.get("REQUEST_METHOD", "")

    def respond(status, payload, extra=()):
        data = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
        if len(data) > MAX_RESPONSE_BYTES:
            status, data = 503, b'{"error":"workspace_unavailable"}'
        headers = [*SECURITY_HEADERS, ("Content-Length", str(len(data))), *extra]
        start_response(f"{status} {HTTPStatus(status).phrase}", headers)
        return [] if method == "HEAD" else [data]

    problem = request_problem(environ)
    if problem:
        status, error, extra = problem
        return respond(status, {"error": error}, extra)

    path = environ.get("PATH_INFO", "")
    if path == "/healthz":
        return respond(200, {"status": "ok"})
    if path == "/api/v1/workspace":
        projects = None
    elif path in {f"/api/v1/projects/{key}" for key in app_workspace.SOURCES}:
        projects = [path.rsplit("/", 1)[1]]
    else:
        return respond(404, {"error": "not_found"})
    try:
        return respond(200, app_workspace.workspace(projects))
    except Exception:
        # Curated records can be missing, invalid, or mid-update. No partial
        # success, source paths, campaign contents or traceback reaches a client.
        return respond(503, {"error": "workspace_unavailable"})


class LocalRequestHandler(WSGIRequestHandler):
    server_version = "LazyPromotionPreview"
    sys_version = ""

    def setup(self):
        self.request.settimeout(5)
        super().setup()

    def log_message(self, format, *args):
        # Request paths and headers are not written to the shared terminal.
        pass


class LocalServer(WSGIServer):
    def server_bind(self):
        if self.server_address[0] != "127.0.0.1":
            raise ValueError("The preview API must bind to IPv4 loopback")
        super().server_bind()

    def handle_error(self, request, client_address):
        # The development server does not persist raw requests or tracebacks.
        pass


def make_local_server(port: int = 18936):
    return make_server("127.0.0.1", port, application, LocalServer, LocalRequestHandler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18936)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    try:
        with make_local_server(args.port) as server:
            print(f"Read-only development API: http://127.0.0.1:{args.port}/api/v1/workspace", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    except OSError:
        parser.exit(1, "Cannot bind the preview port; do not stop another project's service.\n")


if __name__ == "__main__":
    main()
