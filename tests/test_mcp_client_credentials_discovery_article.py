import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = (
    ROOT
    / "articles"
    / "mcp-client-credentials-oauth-discovery-missing"
    / "post.md"
)


class McpClientCredentialsDiscoveryArticleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = ARTICLE.read_text(encoding="utf-8")

    def test_article_is_publishable_and_routes_to_one_bounded_offer(self):
        self.assertIn('status: "publish"', self.text)
        self.assertIn(
            'slug: "mcp-client-credentials-oauth-discovery-missing"',
            self.text,
        )
        self.assertEqual(self.text.count("fixed USD 500 pre-deployment review"), 1)
        self.assertEqual(self.text.count("utm_campaign=mcp_boundary_review"), 2)
        self.assertIn("comes before source upload or payment", self.text)

    def test_article_separates_resource_issuer_endpoint_and_auth_method(self):
        required = (
            "MCP resource",
            "Authorization-server issuer",
            "Token endpoint",
            "token_endpoint_auth_method",
            "does not tell the client where that endpoint is",
        )
        for phrase in required:
            self.assertIn(phrase, self.text)

    def test_article_preserves_discovery_and_compatibility_boundaries(self):
        required = (
            "OAuth Protected Resource Metadata",
            "RFC 8414",
            "does not make the server conform",
            "work only with the non-interactive `client_credentials` grant",
            "keep cached tokens separate",
            "That pull request is still under review",
        )
        for phrase in required:
            self.assertIn(phrase, self.text)

    def test_article_checks_reacquisition_negative_cases_and_log_safety(self):
        required = (
            "obtain a second token without opening a browser",
            "without looping",
            "earlier cached token is not reused",
            "embedded credentials",
            "bearer tokens",
        )
        for phrase in required:
            self.assertIn(phrase, self.text)

    def test_article_uses_primary_sources_and_no_secret_literal(self):
        urls = re.findall(r"https://[^)\s]+", self.text)
        self.assertGreaterEqual(len(urls), 10)
        self.assertIn("https://modelcontextprotocol.io/", self.text)
        self.assertIn("https://www.rfc-editor.org/", self.text)
        self.assertIn("https://github.com/punkpeye/mcp-remote", self.text)
        lowered = self.text.casefold()
        self.assertNotIn("your-token-here", lowered)
        self.assertNotIn("client_secret=", lowered)
        self.assertNotIn("authorization: basic ", lowered)


if __name__ == "__main__":
    unittest.main()
