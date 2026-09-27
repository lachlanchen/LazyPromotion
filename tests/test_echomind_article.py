from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EchoMindArticleTests(unittest.TestCase):
    def setUp(self):
        self.article = (ROOT / 'articles/echomind-language-in-conversation/post.md').read_text()

    def test_existing_article_and_store_routes_are_preserved(self):
        self.assertIn('id: 3867', self.article)
        self.assertIn('slug: "echomind-language-help-in-conversation"', self.article)
        self.assertIn('id6793615455', self.article)
        self.assertIn('id=art.lazying.echomind', self.article)
        self.assertIn('for US$0.99', self.article)
        self.assertIn('free download on [Google Play]', self.article)

    def test_guest_reading_is_not_membership_or_a_purchase_entitlement(self):
        self.assertIn('[public Plaza](https://chat.lazying.art/)', self.article)
        self.assertIn('browse public Plaza posts without signing in', self.article)
        gate = 'downloading the app or creating a general LazyingArt account does not unlock them'
        self.assertIn(gate, self.article)
        self.assertLess(self.article.index(gate), self.article.index('## Begin with a message'))
        self.assertIn('If you already have EchoMind access', self.article)
        self.assertIn('Confirm invitation availability before buying', self.article)

    def test_no_public_agent_or_private_runtime_claim(self):
        self.assertNotIn('EchoMind includes both kinds of conversation', self.article)
        self.assertNotIn('An AI conversation gives you room to rehearse', self.article)
        for marker in ('canary', '40 provider attempts', '/home/', '.private/', 'unlimited', '$20', '$100', '$200'):
            self.assertNotIn(marker, self.article)


if __name__ == '__main__':
    unittest.main()
