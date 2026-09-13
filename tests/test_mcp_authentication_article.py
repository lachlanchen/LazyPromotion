import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = (
    ROOT
    / "articles"
    / "claude-mcp-authentication-public-local-remote"
    / "post.md"
)


class McpAuthenticationArticleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = ARTICLE.read_text(encoding="utf-8")

    def test_article_has_publishable_metadata_and_bounded_offer_route(self):
        self.assertIn("\nid: 3832\n", self.text)
        self.assertIn('status: "publish"', self.text)
        self.assertIn(
            'slug: "claude-mcp-authentication-public-local-remote"',
            self.text,
        )
        self.assertIn("fixed USD 500 pre-deployment review", self.text)
        self.assertIn("utm_source=lazyblog", self.text)
        self.assertIn("not source upload or payment", self.text)

    def test_article_separates_public_local_and_private_remote_boundaries(self):
        self.assertIn("Public demo with intentionally public data", self.text)
        self.assertIn("Loopback or stdio", self.text)
        self.assertIn("OAuth-protected HTTPS", self.text)
        self.assertIn("Public reachability is not the same thing as public access", self.text)

    def test_article_includes_current_interoperability_requirements(self):
        required = (
            "WWW-Authenticate",
            "protected-resource metadata",
            "canonical MCP resource",
            "issuer, expiry, scope",
            "intended audience or resource",
            "Authorization` header",
        )
        for phrase in required:
            self.assertIn(phrase, self.text)
        self.assertIn("protecting `/mcp` does not automatically", self.text)

    def test_article_traces_cloud_only_connector_failures_before_oauth_changes(self):
        self.assertIn("If Claude Code works but claude.ai does not", self.text)
        self.assertIn("160.79.104.0/21", self.text)
        self.assertIn("Check the CDN or WAF log", self.text)
        self.assertIn("leave OAuth alone for the moment", self.text)
        self.assertIn("canonical scheme, host, port, and path", self.text)
        self.assertIn("request ID, UTC time, source range", self.text)
        self.assertNotIn("smartchart.vn", self.text)

    def test_article_uses_primary_sources_and_no_secret_examples(self):
        urls = re.findall(r"https://[^)\s]+", self.text)
        self.assertGreaterEqual(len(urls), 7)
        self.assertIn("https://modelcontextprotocol.io/", self.text)
        self.assertIn("https://code.claude.com/", self.text)
        self.assertIn("https://support.claude.com/", self.text)
        self.assertIn("https://platform.claude.com/", self.text)
        self.assertIn("https://gofastmcp.com/", self.text)
        lowered = self.text.casefold()
        self.assertNotIn("your-token-here", lowered)
        self.assertNotIn("client_secret=", lowered)

    def test_initialize_response_diagnostic_separates_wire_evidence_from_logs(self):
        section = self.text.split("## If initialize returns 200 but the connector stops\n", 1)[1].split("\n## ", 1)[0]
        for phrase in (
            "response after the proxy or CDN",
            "`Content-Type`",
            "`application/json`",
            "`text/event-stream`",
            "terminating blank line",
            "remaining buffered",
            "does not show a version mismatch",
            "`notifications/initialized`",
            "not which side is at fault",
            "session identifiers out of public reports",
        ):
            self.assertIn(phrase, section)
        self.assertIn("/basic/transports#sending-messages-to-the-server", section)
        self.assertIn("/basic/lifecycle#initialization", section)
        self.assertIn("html.spec.whatwg.org/", section)
        for private_marker in ("smartchart.vn", "ofid_", "cf-ray", "hoandc88"):
            self.assertNotIn(private_marker, section)


if __name__ == "__main__":
    unittest.main()
