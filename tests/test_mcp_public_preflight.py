import base64
import json
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import mcp_public_preflight as preflight


COMMIT_SHA = "a" * 40
TREE_SHA = "b" * 40
README_SHA = "c" * 40
SERVER_SHA = "d" * 40
PACKAGE_SHA = "e" * 40


def blob(text):
    raw = text.encode("utf-8")
    return {
        "encoding": "base64",
        "size": len(raw),
        "content": base64.b64encode(raw).decode("ascii"),
    }


class FakeFetcher:
    def __init__(self, *, private=False, truncated=False):
        self.endpoints = []
        self.payloads = {
            "repos/example/server": {
                "private": private,
                "full_name": "example/server",
                "default_branch": "main",
                "archived": False,
                "fork": False,
            },
            "repos/example/server/commits/main": {
                "sha": COMMIT_SHA,
                "commit": {"tree": {"sha": TREE_SHA}},
            },
            f"repos/example/server/git/trees/{TREE_SHA}?recursive=1": {
                "truncated": truncated,
                "tree": [
                    {
                        "path": "README.md",
                        "type": "blob",
                        "size": 80,
                        "sha": README_SHA,
                    },
                    {
                        "path": "src/mcp_server.py",
                        "type": "blob",
                        "size": 400,
                        "sha": SERVER_SHA,
                    },
                    {
                        "path": "package.json",
                        "type": "blob",
                        "size": 100,
                        "sha": PACKAGE_SHA,
                    },
                    {
                        "path": "assets/demo.png",
                        "type": "blob",
                        "size": 100,
                        "sha": "f" * 40,
                    },
                ],
            },
            f"repos/example/server/git/blobs/{README_SHA}": blob(
                "MCP server over stdio with an optional Streamable HTTP transport."
            ),
            f"repos/example/server/git/blobs/{SERVER_SHA}": blob(
                """
import os
API_KEY = os.environ["DOCS_API_KEY"]
UPSTREAM = "https://api.example.test/v1"

@mcp.tool(name="search_docs")
def search(query: str):
    return query

@mcp.tool()
def publish_note(text: str):
    return text

@mcp.resource("docs://{document_id}")
def document(document_id: str):
    return document_id

@mcp.prompt()
def summarize():
    return "summary"
"""
            ),
            f"repos/example/server/git/blobs/{PACKAGE_SHA}": blob(
                json.dumps({"name": "example-mcp-server", "type": "module"})
            ),
        }

    def get(self, endpoint):
        self.endpoints.append(endpoint)
        return self.payloads[endpoint]


class McpPublicPreflightTests(unittest.TestCase):
    def test_public_docs_route_to_one_live_generated_output_sample(self):
        root = Path(__file__).resolve().parents[1]
        expected = (
            "https://lazying.art/mcp-boundary-review/preflight-sample/"
            "?utm_source=github&utm_medium=repository"
            "&utm_campaign=mcp_boundary_review&utm_content=preflight_tool_docs"
        )
        readme = (root / "README.md").read_text(encoding="utf-8")
        guide = (root / "docs" / "mcp-public-preflight.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(readme.count(expected), 1)
        self.assertEqual(guide.count(expected), 1)
        self.assertIn("exact generated Markdown", guide)
        self.assertIn("separate executed report", guide)

    def test_repository_url_accepts_only_clean_github_root(self):
        self.assertEqual(
            preflight.parse_repository_url("https://github.com/Example/Server.git/"),
            ("Example", "Server", "https://github.com/Example/Server"),
        )
        for value in (
            "http://github.com/example/server",
            "https://gitlab.com/example/server",
            "https://github.com/example/server/issues/1",
            "https://github.com/example/server?tab=readme",
            "https://github.com/example/%73erver",
            "https://github.com:invalid/example/server",
            "https://[github.com/example/server",
            " https://github.com/example/server",
        ):
            with self.subTest(value=value):
                with self.assertRaises(preflight.PreflightError):
                    preflight.parse_repository_url(value)

    def test_build_preflight_pins_revision_and_detects_static_surface(self):
        fetcher = FakeFetcher()
        report = preflight.build_preflight(
            "https://github.com/example/server",
            fetcher=fetcher,
            generated_at="2026-09-13T01:02:03Z",
        )

        self.assertEqual(report["repository"]["revision"], COMMIT_SHA)
        self.assertEqual(report["repository"]["tree_sha"], TREE_SHA)
        self.assertTrue(report["method"]["static_only"])
        self.assertFalse(report["method"]["repository_code_executed"])
        self.assertTrue(report["method"]["tree_complete"])
        self.assertEqual(report["method"]["readable_files"], 3)
        capabilities = report["surface"]["capabilities"]
        self.assertEqual(
            [item["name"] for item in capabilities["tool"]],
            ["publish_note", "search_docs"],
        )
        self.assertEqual(capabilities["resource"][0]["name"], "docs://{document_id}")
        self.assertEqual(capabilities["prompt"][0]["name"], "summarize")
        self.assertEqual(
            [item["name"] for item in report["surface"]["transports"]],
            ["Streamable HTTP", "stdio"],
        )
        self.assertEqual(
            report["surface"]["environment_variables"][0]["name"],
            "DOCS_API_KEY",
        )
        self.assertEqual(
            report["surface"]["external_host_candidates"][0]["name"],
            "api.example.test",
        )
        self.assertEqual(report["surface"]["mutating_name_candidates"], ["publish_note"])
        self.assertEqual(len(report["proposed_checks"]), 10)
        self.assertEqual(report["commercial_boundary"]["review_fee_usd"], 500)
        self.assertTrue(all("git/blobs" in item or item.startswith("repos/example/server") for item in fetcher.endpoints))

    def test_private_repository_is_refused_before_commit_or_tree_reads(self):
        fetcher = FakeFetcher(private=True)
        with self.assertRaisesRegex(preflight.PreflightError, "must be public"):
            preflight.build_preflight(
                "https://github.com/example/server", fetcher=fetcher
            )
        self.assertEqual(fetcher.endpoints, ["repos/example/server"])

    def test_truncated_tree_is_reported_without_claiming_complete_inventory(self):
        report = preflight.build_preflight(
            "https://github.com/example/server",
            fetcher=FakeFetcher(truncated=True),
        )
        self.assertFalse(report["method"]["tree_complete"])
        body = preflight.render_markdown(report)
        self.assertIn("Recursive tree complete: `no`", body)

    def test_candidate_selection_ignores_binary_and_respects_limit(self):
        tree = [
            {"path": "README.md", "type": "blob", "size": 20, "sha": "1" * 40},
            {"path": "src/mcp.py", "type": "blob", "size": 20, "sha": "2" * 40},
            {"path": "assets/server.png", "type": "blob", "size": 20, "sha": "3" * 40},
        ]
        selected = preflight.select_text_blobs(tree, maximum=1)
        self.assertEqual([item["path"] for item in selected], ["src/mcp.py"])
        with self.assertRaises(preflight.PreflightError):
            preflight.select_text_blobs(tree, maximum=0)

    def test_decode_blob_accepts_github_line_wrapped_base64(self):
        payload = blob("hello public repository")
        encoded = payload["content"]
        payload["content"] = encoded[:8] + "\n" + encoded[8:] + "\n"
        self.assertEqual(preflight.decode_blob(payload), "hello public repository")

    def test_render_is_review_ready_and_does_not_overclaim(self):
        report = preflight.build_preflight(
            "https://github.com/example/server", fetcher=FakeFetcher()
        )
        body = preflight.render_markdown(report)
        self.assertIn("No repository code was cloned or executed", body)
        self.assertIn("## Proposed ten-check review", body)
        self.assertIn("## Missing decisions before scope", body)
        self.assertIn("## Review-ready reply draft", body)
        self.assertIn("fixed USD 500", body)
        self.assertIn("not a penetration test", body)
        self.assertNotIn("secure for production", body)

    def test_private_output_stays_ignored_and_owner_only(self):
        report = preflight.build_preflight(
            "https://github.com/example/server", fetcher=FakeFetcher()
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output_dir = root / ".local" / "mcp-preflight"

            def ignored_runner(command, **kwargs):
                self.assertEqual(command[0], "git")
                self.assertEqual(kwargs["timeout"], 30)
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            destination = preflight.write_preflight(
                report,
                output_dir=output_dir,
                root=root,
                runner=ignored_runner,
            )
            body = destination.read_text(encoding="utf-8")
            self.assertIn(COMMIT_SHA, body)
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(output_dir.stat().st_mode), 0o700)

    def test_gh_fetcher_uses_get_and_hides_cli_diagnostics(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(
                returncode=1,
                stdout="",
                stderr="private-token=must-not-leak",
            )

        with self.assertRaises(preflight.PreflightError) as raised:
            preflight.GhFetcher(runner).get("repos/example/server")
        command, kwargs = calls[0]
        self.assertEqual(command[command.index("--method") + 1], "GET")
        self.assertEqual(kwargs["timeout"], 60)
        self.assertNotIn("private-token", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
