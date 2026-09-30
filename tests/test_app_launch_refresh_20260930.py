import hashlib
import json
from pathlib import Path
import unittest

import owned_monitor

ROOT = Path(__file__).resolve().parents[1]


class AppLaunchRefreshTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / 'campaigns' / f'{name}.json').read_text())

    def test_public_copy_is_recognized_without_private_identifiers(self):
        providers = {'x': 'x', 'instagram': 'instagram-standalone', 'reddit': 'reddit'}
        for name in ('onlyideas-mac-introduction', 'bunko-watch-reading', 'l-and-n-saved-take-practice'):
            campaign = self.load(name)
            for key, channel in campaign['channels'].items():
                self.assertIn('I built', channel['content'])
                self.assertEqual(hashlib.sha256(channel['content'].encode()).hexdigest(), channel['content_sha256'])
                route = owned_monitor.route_for_post(providers[key], channel['content'], owned_monitor.route_index())
                self.assertEqual(route['campaign_id'], name)
            for marker in ('/home/', '127.0.0.1', '.local/', 'integrationId', 'cmund4'):
                self.assertNotIn(marker, json.dumps(campaign))
            self.assertIsNone(campaign['funnel']['verified_received_gross_usd'])
            self.assertIsNone(campaign['funnel']['verified_new_users'])
            for key in ('automatic_replies', 'automatic_reposts', 'unsolicited_private_messages'):
                self.assertFalse(campaign['follow_up'][key])

    def test_onlyideas_mac_is_not_mobile_or_general_paid_activation(self):
        c = self.load('onlyideas-mac-introduction')
        self.assertEqual(c['source_evidence']['mac_price_usd'], 0)
        self.assertIn('Not generally', c['source_evidence']['paid_plans'])
        self.assertIn('Shared', c['channels']['reddit']['content'])
        for p in c['channels'].values():
            self.assertIn('?platform=mac', p['content'])
            self.assertNotIn('play.google.com', p['content'])
        self.assertEqual(c['channels']['x']['state'], 'published_verified')

    def test_bunko_watch_scope_and_actual_media(self):
        c = self.load('bunko-watch-reading')
        self.assertEqual(c['source_evidence']['ios_public_version'], '1.0.8')
        self.assertTrue(c['source_evidence']['image_reviewed'])
        self.assertIn('Choose an excerpt on your iPhone', c['channels']['instagram']['content'])
        self.assertIn('US$0.99 once', c['channels']['instagram']['content'])
        self.assertNotIn('Google Play', c['channels']['instagram']['content'])

    def test_landn_future_queue_keeps_both_real_store_links(self):
        c = self.load('l-and-n-saved-take-practice')
        x = c['channels']['x']
        self.assertEqual(x['state'], 'queued_verified')
        self.assertEqual(x['publish_at'], '2026-10-01T02:00:00Z')
        self.assertNotIn('release_url', x)
        self.assertIn('free + IAP', x['content'])
        for store in ('apple', 'google'):
            self.assertIn(c['source_evidence'][store], x['content'])

    def test_articles_keep_live_mac_routes_and_correct_import_privacy(self):
        only = (ROOT/'articles/onlyideas-reading-paper/post.md').read_text()
        bunko = (ROOT/'articles/bunko-reading-classics/post.md').read_text()
        self.assertIn('choose **Only me**', only)
        self.assertNotIn('Personal imports and notes begin privately', only)
        self.assertIn('id6816392935?platform=mac', only)
        self.assertIn('id6815137919?platform=mac', bunko)
        self.assertIn('explicit transfer', bunko)


if __name__ == '__main__':
    unittest.main()
