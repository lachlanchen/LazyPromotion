import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "articles" / "test-one-chapter-before-typesetting"


class BookSpecimenArticleTests(unittest.TestCase):
    def test_three_reviewed_editions_share_structure_and_sources(self):
        files = [
            ARTICLE / "post.md",
            ARTICLE / "translations" / "zh-hant.md",
            ARTICLE / "translations" / "ja.md",
        ]
        editions = [path.read_text(encoding="utf-8") for path in files]

        for text in editions:
            self.assertEqual(len(re.findall(r"^## ", text, re.MULTILINE)), 7)
            self.assertEqual(text.count("https://"), 8)
            self.assertEqual(text.count("```"), 2)
            self.assertIn("https://www.w3.org/TR/epub-33/", text)
            self.assertIn("https://www.w3.org/TR/epub-rs-33/", text)
            self.assertIn("https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6/", text)
            self.assertIn("https://kdp.amazon.com/en_US/help/topic/G202131170", text)
            self.assertIn("https://github.com/w3c/epubcheck", text)
            self.assertIn("https://github.com/lachlanchen/PocketPolyglot", text)
            self.assertIn("https://lazying.art/book-specimen/", text)

    def test_offer_boundary_matches_live_service(self):
        source = (ARTICLE / "post.md").read_text(encoding="utf-8")
        self.assertIn("final, rights-cleared copy", source)
        self.assertIn("one chapter up to 5,000 words", source)
        self.assertIn("one agreed 6 × 9 print profile", source)
        self.assertIn("fit check before any manuscript upload or payment", source)
        self.assertEqual(source.count("USD 250 Book Specimen Sprint"), 1)

    def test_article_does_not_overclaim_the_public_proof(self):
        source = (ARTICLE / "post.md").read_text(encoding="utf-8")
        self.assertIn("not a customer result", source)
        self.assertIn("or a claim that one layout suits every printer", source)
        self.assertNotIn("guarantee", source.lower())


if __name__ == "__main__":
    unittest.main()
