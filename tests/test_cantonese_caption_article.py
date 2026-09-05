import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE_DIR = ROOT / "articles" / "cantonese-caption-delivery"
ARTICLE_FILES = (
    ARTICLE_DIR / "post.md",
    ARTICLE_DIR / "translations" / "zh-hant.md",
    ARTICLE_DIR / "translations" / "ja.md",
)
EXPECTED_URLS = [
    "https://github.com/BYVoid/OpenCC",
    "https://support.google.com/youtube/answer/2734698?hl=en",
    "https://ffmpeg.org/ffmpeg-filters.html#subtitles-1",
    "https://github.com/lachlanchen/LazyEdit",
    "https://github.com/lachlanchen/LazyPromotion/tree/8db8e1722c85c626296f1306e7dca662439a6a6e/examples/cantonese-caption-delivery",
]


class CantoneseCaptionArticleTests(unittest.TestCase):
    def test_editions_have_matching_structure_and_sources(self):
        for path in ARTICLE_FILES:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(7, len(re.findall(r"^## ", text, re.MULTILINE)))
                self.assertEqual(8, text.count("```"))
                self.assertEqual(EXPECTED_URLS, re.findall(r"https?://[^)\s]+", text))

    def test_source_keeps_delivery_and_proof_boundaries(self):
        text = ARTICLE_FILES[0].read_text(encoding="utf-8")
        for phrase in (
            "hk2s.json",
            "plain UTF-8",
            "cannot prove that a subtitle starts within 0.2 seconds",
            "captions-yue-Hant.srt",
            "captions-zh-Hans.srt",
            "contact@lazying.art",
            "rights-cleared",
            "not a customer video",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

        self.assertNotRegex(text, r"(?i)\bAI[- ]?(generated|written|assisted)\b")


if __name__ == "__main__":
    unittest.main()
