import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "articles" / "multilingual-ocr-before-rag"


class MultilingualOcrArticleTests(unittest.TestCase):
    def test_three_reviewed_editions_keep_the_same_structure_and_routes(self):
        files = [
            ARTICLE / "post.md",
            ARTICLE / "translations" / "zh.md",
            ARTICLE / "translations" / "ja.md",
        ]
        editions = [path.read_text(encoding="utf-8") for path in files]

        for text in editions:
            self.assertEqual(len(re.findall(r"^## ", text, re.MULTILINE)), 7)
            self.assertEqual(text.count("https://"), 10)
            self.assertEqual(text.count("```"), 6)
            self.assertIn("https://www.w3.org/TR/charmod-norm/", text)
            self.assertIn("https://ocr-d.de/en/spec/ocrd_eval.html", text)
            self.assertIn("https://lazying.art/lkt/sample-report/", text)
            self.assertIn("https://lazying.art/lkt/fit-check/", text)

    def test_source_scope_does_not_sell_full_archive_ocr(self):
        source = (ARTICLE / "post.md").read_text(encoding="utf-8")
        self.assertIn("custom OCR", source)
        self.assertIn("not custom OCR or a full-library conversion", source)
        self.assertIn("The useful order is simple: sample, transcribe, measure, route, preserve, then index.", source)


if __name__ == "__main__":
    unittest.main()
