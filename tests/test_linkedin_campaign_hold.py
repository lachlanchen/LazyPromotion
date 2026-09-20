"""Current distribution holds must not erase proof or count as conversions."""
import json
from pathlib import Path
import unittest

from owned_monitor import content_hash

ROOT = Path(__file__).resolve().parents[1]


class LinkedInCampaignHoldTests(unittest.TestCase):
    def test_six_exact_routes_are_drafts_with_reviewed_copy_preserved(self):
        targets = {
            'pronunciation-mini-lesson-pilot': None,
            'kicad-plugin-testing-freelancer': None,
            'playwright-regression-contract': None,
            'openhi-reproducibility-sprint': None,
            'local-knowledge-terminal-pilot': 'multilingual_ocr_guide_post',
            'bilingual-lecture-pack-pilot': 'practical_guide',
        }
        for name, nested in targets.items():
            with self.subTest(campaign=name):
                campaign = json.loads((ROOT / 'campaigns' / (name + '.json')).read_text())
                route = campaign['channels']['linkedin']
                if nested:
                    route = route[nested]
                hold = route['publication_hold']
                self.assertEqual(route['state'], 'postiz_draft_account_review')
                self.assertEqual(hold['provider_state'], 'DRAFT')
                self.assertEqual(hold['reason'], 'Channel account review')
                self.assertTrue(hold['listed_nonstate_fields_unchanged'])
                self.assertTrue(hold['status_only_change'])
                self.assertTrue(hold['other_posts_unchanged'])
                self.assertEqual(content_hash(route.get('postiz_content', route['content'])), hold['normalized_content_sha256'])
                self.assertEqual(hold['stored_publish_at'].replace('.000Z', 'Z'), route.get('publish_at', route.get('scheduled_for')))
                self.assertIn('never automatically requeue', hold['resume_requires'])
                self.assertNotIn('post_id', route)
                funnel = campaign['funnel']
                if name == 'bilingual-lecture-pack-pilot':
                    self.assertIn('Count revenue only after confirmed payment', funnel['revenue_policy'])
                else:
                    revenue_key = {
                        'local-knowledge-terminal-pilot': 'verified_received_gross_usd',
                        'pronunciation-mini-lesson-pilot': 'received_gross_usd',
                    }.get(name, 'received_revenue_usd')
                    self.assertEqual(funnel[revenue_key], 0)


if __name__ == '__main__':
    unittest.main()
