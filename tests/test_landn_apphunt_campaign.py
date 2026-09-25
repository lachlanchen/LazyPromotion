import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LandnAppHuntCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads((ROOT / 'campaigns/l-and-n-apphunt-introduction.json').read_text())
        self.post = self.campaign['channels']['reddit']

    def test_exact_delivered_copy_and_title(self):
        self.assertEqual(self.post['state'], 'published')
        for field in ('content', 'title'):
            self.assertEqual(hashlib.sha256(self.post[field].encode()).hexdigest(), self.post[field + '_sha256'])
        self.assertIn('/r/AppHunt/comments/1wq4pd5/', self.post['release_url'])
        self.assertEqual(self.post['publish_at'], '2026-09-25T18:57:53Z')

    def test_android_only_scope_and_honest_pricing(self):
        self.assertEqual(self.post['link_url'], 'https://play.google.com/store/apps/details?id=art.lazying.landn')
        self.assertEqual(self.post['flair'], 'Android APP')
        self.assertTrue(self.post['brand_affiliate_tag'])
        self.assertIn('I mix up L and N myself', self.post['content'])
        self.assertIn('free to download, with in-app purchases', self.post['content'])
        for forbidden in ('apps.apple.com', 'TestFlight', 'Bunko', 'fully offline', 'guaranteed', '$0.99'):
            self.assertNotIn(forbidden, self.post['content'])

    def test_delivery_is_not_automatic_followup_or_verified_conversion(self):
        verification = self.post['publication_verification']
        self.assertTrue(verification['single_submit_click'])
        self.assertTrue(verification['exact_text_verified_after_reload'])
        self.assertFalse(verification['logged_out_visibility_verified'])
        for key in ('automatic_replies', 'automatic_reposts', 'unsolicited_private_messages', 'postiz_managed'):
            self.assertFalse(self.campaign['follow_up'][key])
        self.assertEqual(self.campaign['follow_up']['repost_not_before'], '2026-10-26')
        for key in ('qualified_leads', 'payments_confirmed', 'verified_received_gross_usd'):
            self.assertEqual(self.campaign['funnel'][key], 0)
        for private in ('/home/', '.local/', '127.0.0.1', 'approval_token', 'integrationId'):
            self.assertNotIn(private, json.dumps(self.campaign))


if __name__ == '__main__':
    unittest.main()
