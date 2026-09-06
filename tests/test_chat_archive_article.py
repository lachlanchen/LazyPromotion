import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "articles" / "chat-archive-current-state"


class ChatArchiveArticleTests(unittest.TestCase):
    def test_three_editions_keep_the_same_practical_structure(self):
        files = [
            ARTICLE / "post.md",
            ARTICLE / "translations" / "zh-hant.md",
            ARTICLE / "translations" / "ja.md",
        ]
        editions = [path.read_text(encoding="utf-8") for path in files]

        for text in editions:
            self.assertEqual(len(re.findall(r"^## ", text, re.MULTILINE)), 7)
            self.assertEqual(text.count("```"), 8)
            self.assertIn("https://learn.chatgpt.com/docs/use-chatgpt", text)
            self.assertIn("/3802/meeting-transcripts-decisions-action-items-audit-trail.html", text)
            self.assertIn("https://github.com/lachlanchen/LocalKnowledgeTerminal", text)
            self.assertIn("https://lazying.art/lkt/fit-check/", text)
            self.assertIn("utm_content=chat_archive_current_state", text)

    def test_current_state_never_overwrites_source_evidence(self):
        source = (ARTICLE / "post.md").read_text(encoding="utf-8")
        self.assertIn("Keep the original export immutable", source)
        self.assertIn("Separate evidence from current state", source)
        self.assertIn('"supersedes": "state-project-orchid-status-v1"', source)
        self.assertIn("proposed", source)
        self.assertIn("confirmed", source)
        self.assertIn("rejected", source)
        self.assertIn("superseded", source)
        self.assertIn("uncertain", source)

    def test_offer_is_bounded_and_not_presented_as_a_finished_importer(self):
        source = (ARTICLE / "post.md").read_text(encoding="utf-8")
        self.assertIn("not a finished ChatGPT importer", source)
        self.assertIn("up to 12 representative source units and 20 real questions", source)
        self.assertIn("free fit check", source)
        self.assertIn("no archive upload or payment", source)
        self.assertEqual(source.count("USD 250 Local Knowledge Terminal"), 1)
        self.assertNotIn("guarantee", source.casefold())


if __name__ == "__main__":
    unittest.main()
