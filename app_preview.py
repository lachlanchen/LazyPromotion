#!/usr/bin/env python3
"""Local client preview: seven fixed assets and the read-only campaign API."""

import argparse
from pathlib import Path
from wsgiref.simple_server import make_server

import app_api

WEB = Path(__file__).resolve().parent / "apps" / "web"
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.mjs": ("app.mjs", "text/javascript; charset=utf-8"),
    "/model.mjs": ("model.mjs", "text/javascript; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json"),
    "/icon.svg": ("icon.svg", "image/svg+xml"),
    "/sw.js": ("sw.js", "text/javascript; charset=utf-8"),
}
CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
    "connect-src 'self'; worker-src 'self'; manifest-src 'self'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


def application(environ, start_response):
    path = environ.get("PATH_INFO", "")
    if app_api.request_problem(environ) or path not in ASSETS:
        return app_api.application(environ, start_response)
    filename, content_type = ASSETS[path]
    source = WEB / filename
    try:
        if WEB.is_symlink() or WEB.parent.is_symlink() or source.is_symlink():
            raise OSError("unsafe asset")
        data = source.read_bytes()
        if len(data) > 128 * 1024:
            raise OSError("oversized asset")
    except OSError:
        start_response("503 Service Unavailable", [*app_api.SECURITY_HEADERS, ("Content-Length", "31")])
        return [] if environ["REQUEST_METHOD"] == "HEAD" else [b'{"error":"preview_unavailable"}']
    headers = [(key, value) for key, value in app_api.SECURITY_HEADERS
               if key not in {"Content-Type", "Content-Security-Policy"}]
    headers.extend([
        ("Content-Type", content_type), ("Content-Security-Policy", CSP),
        ("Content-Length", str(len(data))), ("X-Robots-Tag", "noindex, nofollow"),
    ])
    start_response("200 OK", headers)
    return [] if environ["REQUEST_METHOD"] == "HEAD" else [data]


def make_local_server(port=18936):
    return make_server("127.0.0.1", port, application, app_api.LocalServer, app_api.LocalRequestHandler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18936)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    try:
        with make_local_server(args.port) as server:
            print(f"Local read-only app preview: http://127.0.0.1:{args.port}/", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    except OSError:
        parser.exit(1, "Preview port unavailable; do not stop another project's service.\n")


if __name__ == "__main__":
    main()
