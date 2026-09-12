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

    def test_article_uses_primary_sources_and_no_secret_examples(self):
        urls = re.findall(r"https://[^)\s]+", self.text)
        self.assertGreaterEqual(len(urls), 7)
        self.assertIn("https://modelcontextprotocol.io/", self.text)
        self.assertIn("https://code.claude.com/", self.text)
        self.assertIn("https://support.claude.com/", self.text)
        self.assertIn("https://gofastmcp.com/", self.text)
        lowered = self.text.casefold()
        self.assertNotIn("your-token-here", lowered)
        self.assertNotIn("client_secret=", lowered)


if __name__ == "__main__":
    unittest.main()
