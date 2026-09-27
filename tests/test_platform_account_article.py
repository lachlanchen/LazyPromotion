from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PlatformAccountArticleTests(unittest.TestCase):
    def setUp(self):
        self.article = (ROOT / 'articles/lazyingart-platform-shared-account/post.md').read_text()

    def test_updates_existing_article_and_keeps_browsing_account_free(self):
        self.assertIn('id: 3873', self.article)
        self.assertIn('slug: "lazyingart-platform-tools-shared-account"', self.article)
        self.assertIn('There is no account wall around the catalogue.', self.article)
        self.assertIn('you do not need to register just to find L & N, Bunko or EchoMind', self.article)

    def test_only_qualified_shared_password_flow_is_live(self):
        self.assertIn('[Platform sign-in](https://platform.lazying.art/account)', self.article)
        self.assertIn('register without an invitation and sign in with a password', self.article)
        self.assertIn('Google, Apple and GitHub sign-in are still being connected', self.article)
        self.assertIn('they are not available in this shared flow yet', self.article)
        self.assertNotIn('Shared sign-in is not live on the platform yet', self.article)
        self.assertNotIn('production shared-login routes remain disabled', self.article)

    def test_coin_read_is_separate_and_never_a_balance_or_reward_promise(self):
        self.assertIn('Coin access is a separate choice', self.article)
        self.assertIn('not as having a zero balance', self.article)
        self.assertIn('Account linking is not available yet', self.article)
        self.assertIn('withdraw that permission without signing out', self.article)
        self.assertIn('does not connect a wallet or distribute coins', self.article)
        self.assertIn('does not grant paid features', self.article)
        for marker in ('/home/', '.private/', 'client.secret', 'X-Lac-Read-Token'):
            self.assertNotIn(marker, self.article)


if __name__ == '__main__':
    unittest.main()
