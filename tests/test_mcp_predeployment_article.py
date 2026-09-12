import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "articles" / "review-mcp-server-before-deployment" / "post.md"


class McpPredeploymentArticleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = ARTICLE.read_text(encoding="utf-8")

    def test_article_has_ten_concrete_checks_and_current_protocol_context(self):
        numbered = re.findall(r"^## ([1-9]|10)\. ", self.text, re.MULTILINE)
        self.assertEqual(len(numbered), 10)
        self.assertIn("2026-07-28", self.text)
        self.assertIn("server/discover", self.text)
        self.assertIn("annotations are hints, not enforcement", self.text)

    def test_article_uses_executed_proof_without_inflating_it(self):
        self.assertIn("two tools and one resource", self.text)
        self.assertIn("Fourteen focused tests passed", self.text)
        self.assertIn("local GO and a remote NO-GO", self.text)
        self.assertIn("not to certify a whole product", self.text)

    def test_article_has_one_bounded_conversion_path(self):
        self.assertEqual(self.text.count("utm_campaign=mcp_boundary_review"), 2)
        self.assertIn("fixed USD 500 review", self.text)
        self.assertIn("one server, one base revision, and ten agreed checks", self.text)
        self.assertIn("no source upload or payment is needed", self.text)

    def test_article_links_only_to_primary_technical_sources(self):
        required = [
            "https://blog.modelcontextprotocol.io/posts/2026-07-28/",
            "https://ts.sdk.modelcontextprotocol.io/v2/protocol-versions",
            "https://ts.sdk.modelcontextprotocol.io/v2/migration/support-2026-07-28",
            "https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/",
            "https://modelcontextprotocol.io/specification/2025-06-18/basic/transports",
            "https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization",
        ]
        for url in required:
            self.assertIn(url, self.text)


if __name__ == "__main__":
    unittest.main()

