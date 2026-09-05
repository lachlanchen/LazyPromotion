import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LandnPortfolioShortTests(unittest.TestCase):
    def test_renderer_is_first_party_traditional_chinese_web_demo(self):
        source = (ROOT / "scripts" / "render_landn_bilingual_short.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("L 和 N，總是聽起來很像嗎？", source)
        self.assertIn("先聽，再錄。", source)
        self.assertIn("舌位相近，氣流不同。", source)
        self.assertIn("不只給分數，也說明依據。", source)
        self.assertIn("l-and-n.lazying.art", source)
        self.assertIn("first-party app and audio", source)
        self.assertIn('"en-light.mp3"', source)
        self.assertIn('"en-night.mp3"', source)
        self.assertIn("pan=stereo", source)
        self.assertNotIn("App Store", source)
        self.assertNotIn("Google Play", source)
        self.assertNotIn("accuracy", source.casefold())


if __name__ == "__main__":
    unittest.main()
