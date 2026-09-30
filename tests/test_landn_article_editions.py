"""Local editorial parity; these checks do not prove release facts or revenue."""
from pathlib import Path
import unittest

import blog_editorial


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "articles/l-and-n-listening-practice"


class LandnArticleEditionsTests(unittest.TestCase):
    def test_reviewed_chinese_edition_preserves_structure_and_destinations(self):
        english = blog_editorial.read_document(ARTICLE / "post.md")
        chinese = blog_editorial.read_document(ARTICLE / "translations/zh.md")
        self.assertEqual(english.metadata["id"], "3849")
        self.assertEqual(chinese.metadata["language"], "zh")
        self.assertEqual(chinese.metadata["source_language"], "en")
        self.assertEqual(
            blog_editorial._structural_signature(english.body, english.path),
            blog_editorial._structural_signature(chinese.body, chinese.path),
        )
        for document in (english, chinese):
            self.assertEqual(document.body.count("\n## "), 4)
            self.assertIn("https://apps.apple.com/us/app/l-n-speech-practice/id6808872450", document.body)
            self.assertIn("https://play.google.com/store/apps/details?id=art.lazying.landn", document.body)
            self.assertIn("https://www.youtube.com/shorts/Nlsx_5U6g6U", document.body)
            self.assertEqual(document.body.count("https://l-and-n.lazying.art/lessons/light-vs-night/"), 1)
            self.assertNotIn("testflight.apple.com", document.body)
            self.assertNotIn("/downloads/", document.body)

    def test_original_build_details_are_explicitly_historical(self):
        english = blog_editorial.read_document(ARTICLE / "post.md").body
        chinese = blog_editorial.read_document(ARTICLE / "translations/zh.md").body
        self.assertIn("first listening build", english)
        self.assertIn("September 20, 2026", english)
        self.assertIn("An empty transcript produced no saved score.", english)
        self.assertIn("最初的听辨版本", chinese)
        self.assertIn("2026 年 9 月 20 日", chinese)
        self.assertIn("那时，识别结果为空", chinese)


if __name__ == "__main__":
    unittest.main()
