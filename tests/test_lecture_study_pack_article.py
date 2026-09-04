import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "articles" / "lecture-to-bilingual-study-pack"


class LectureStudyPackArticleTests(unittest.TestCase):
    def test_three_reviewed_editions_share_structure_and_evidence(self):
        files = [
            ARTICLE / "post.md",
            ARTICLE / "translations" / "zh-hant.md",
            ARTICLE / "translations" / "ja.md",
        ]
        editions = [path.read_text(encoding="utf-8") for path in files]

        for text in editions:
            self.assertEqual(len(re.findall(r"^## ", text, re.MULTILINE)), 7)
            self.assertEqual(text.count("https://"), 8)
            self.assertEqual(text.count("```"), 4)
            self.assertIn("https://github.com/lachlanchen/Video2Book", text)
            self.assertIn("https://github.com/lachlanchen/LazyEdit", text)
            self.assertIn("https://github.com/lachlanchen/PocketPolyglot", text)
            self.assertIn("https://github.com/lachlanchen/LocalKnowledgeTerminal", text)
            self.assertIn("https://lazying.art/lecture-pack/", text)

    def test_source_scope_matches_the_live_offer(self):
        source = (ARTICLE / "post.md").read_text(encoding="utf-8")
        self.assertIn("15 timed source segments", source)
        self.assertIn("up to 20 minutes", source)
        self.assertIn("Traditional Chinese or Japanese for USD 250", source)
        self.assertIn("before any source upload or payment", source)
        self.assertIn(
            "preserve the source, correct the words, align the segments, derive the formats",
            source,
        )


if __name__ == "__main__":
    unittest.main()
