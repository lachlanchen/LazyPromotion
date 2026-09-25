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
        self.assertEqual(post['state'], 'published')
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

    def test_historical_queue_review_is_preserved_without_inventing_revenue(self):
        verified = self.campaign['channels']['x']['verification']
        self.assertEqual(verified['verified_state'], 'QUEUE')
        self.assertEqual(verified['matching_posts'], 1)
        self.assertFalse(verified['release_present'])
        self.assertTrue(verified['original_campaign_url_preserved'])
        self.assertTrue(verified['uploaded_image_and_preview_reviewed'])
        self.assertTrue(verified['destination_and_store_continuation_verified'])
        self.assertEqual(self.campaign['funnel']['verified_received_gross_usd'], 0)
        self.assertEqual(self.campaign['funnel']['qualified_leads'], 0)

    def test_provider_publication_is_distinct_from_live_review_and_sales(self):
        post = self.campaign['channels']['x']
        verified = post['publication_verification']
        self.assertEqual(verified['verified_state'], 'PUBLISHED')
        self.assertEqual(verified['post_id'], 'cmu9jbo6p0e4ds40ycfj6kkgb')
        self.assertEqual(post['release_url'],
                         'https://twitter.com/lazyingart/status/' + verified['release_id'])
        self.assertTrue(verified['stored_copy_matches_reviewed_text'])
        self.assertTrue(verified['original_campaign_url_preserved'])
        self.assertFalse(verified['live_page_reviewed'])
        self.assertEqual(self.campaign['funnel']['payments_confirmed'], 0)

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

    def test_android_submissions_do_not_become_public_purchase_claims(self):
        launch = json.loads((ROOT / 'campaigns/l-and-n-pronunciation-launch.json').read_text())
        releases = launch['source_evidence']['release_state']
        iap = releases['android_production_iap_submission']
        pro = releases['android_pro_submission']
        self.assertEqual(iap['state'], 'shipping_reported_in_review')
        self.assertEqual(iap['version_code'], 10)
        self.assertEqual(iap['replaces_queued_version_code'], 8)
        self.assertFalse(iap['public_production_verified'])
        self.assertFalse(iap['payment_or_revenue_verified'])
        self.assertEqual(pro['state'], 'shipping_reported_in_review')
        self.assertNotEqual(pro['package_id'], iap['package_id'])
        self.assertEqual(pro['public_listing_http_status'], 404)
        self.assertFalse(pro['public_listing_verified'])
        self.assertFalse(pro['payment_or_revenue_verified'])
        self.assertEqual(pro['usd_base_price'], 0.99)
        self.assertIn('Hold Pro-specific posts', pro['policy'])
        self.assertIn('paid-up-front', pro['purchase_model'])
        self.assertNotIn('landn.pro', json.dumps(launch['channels']))
        self.assertNotIn('landn.pro', json.dumps(self.campaign['channels']))
        for item in (iap, pro):
            self.assertEqual(len(item['shipping_evidence_commit']), 40)
            self.assertNotIn('merchant', json.dumps(item))
            self.assertNotIn('paymentsProfile', json.dumps(item))

    def test_catalog_uses_current_store_evidence_without_inventing_purchase_terms(self):
        catalog = json.loads((ROOT / 'catalog.json').read_text())
        context = next(p['reply_context'] for p in catalog['projects'] if p['id'] == 'l-and-n')
        self.assertIn('shows in-app purchases', context)
        self.assertIn('anonymous public metadata reported version 1.0.9', context)
        self.assertIn('infer the current in-app price from an old submission record', context)
        self.assertIn('Do not promote Pro', context)
        self.assertIn('Current promotion is store-first', context)
        self.assertNotIn('mention the free no-signup PWA', context)
        self.assertNotIn('details?id=art.lazying.landn.pro', context)


if __name__ == '__main__':
    unittest.main()
