import hashlib
import json
from pathlib import Path
import unittest

import owned_monitor


ROOT = Path(__file__).resolve().parents[1]


class LandnListeningCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads(
            (ROOT / 'campaigns/l-and-n-listening-round.json').read_text()
        )

    def test_one_spaced_x_post_uses_exact_reviewed_copy(self):
        self.assertEqual(list(self.campaign['channels']), ['x'])
        post = self.campaign['channels']['x']
        self.assertEqual(post['state'], 'queued')
        self.assertEqual(post['publish_at'], '2026-09-22T02:00:00Z')
        self.assertLessEqual(len(post['content']), 280)
        self.assertEqual(hashlib.sha256(post['content'].encode()).hexdigest(), post['content_sha256'])
        self.assertIn('iPhone app US$0.99', post['content'])
        self.assertIn('Free in the browser', post['content'])
        self.assertIn(post['destination'].removeprefix('https://'), post['content'])
        self.assertFalse(post['settings']['paid_partnership'])
        self.assertEqual(post['settings']['post_type'], 'post')

    def test_real_setup_image_is_pinned_not_a_learner_result(self):
        evidence = self.campaign['source_evidence']
        path = ROOT / evidence['capture']
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), evidence['capture_sha256'])
        self.assertIn('not a learner result', evidence['capture_kind'])
        self.assertIn('synthetic', evidence['functional_check'])
        self.assertNotIn('/home/', json.dumps(self.campaign))

    def test_queue_is_verified_without_inventing_publication_or_revenue(self):
        verified = self.campaign['channels']['x']['verification']
        self.assertEqual(verified['verified_state'], 'QUEUE')
        self.assertEqual(verified['matching_posts'], 1)
        self.assertFalse(verified['release_present'])
        self.assertTrue(verified['original_campaign_url_preserved'])
        self.assertTrue(verified['uploaded_image_and_preview_reviewed'])
        self.assertTrue(verified['destination_and_store_continuation_verified'])
        self.assertEqual(self.campaign['funnel']['verified_received_gross_usd'], 0)
        self.assertEqual(self.campaign['funnel']['qualified_leads'], 0)

    def test_original_publication_monitor_can_find_the_new_route(self):
        routes = owned_monitor.route_index()
        post = self.campaign['channels']['x']
        route = owned_monitor.route_for_post('x', post['content'], routes)
        self.assertEqual(route['campaign_id'], self.campaign['id'])

    def test_android_purchase_test_is_not_a_public_release_or_payment(self):
        launch = json.loads((ROOT / 'campaigns/l-and-n-pronunciation-launch.json').read_text())
        internal = launch['source_evidence']['release_state']['android_internal_iap']
        self.assertEqual(internal['state'], 'shipping_reported_internal_only')
        self.assertEqual(internal['version_code'], 10)
        self.assertEqual(internal['usd_base_price'], 0.99)
        self.assertFalse(internal['public_production_verified'])
        self.assertFalse(internal['payment_or_revenue_verified'])
        self.assertNotIn('free on Android', self.campaign['channels']['x']['content'])


if __name__ == '__main__':
    unittest.main()
