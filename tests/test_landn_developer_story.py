import json
from datetime import datetime
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LandnDeveloperStoryTests(unittest.TestCase):
    def test_owned_story_has_one_app_action_and_real_release_evidence(self):
        campaign = json.loads((ROOT / 'campaigns/l-and-n-pronunciation-launch.json').read_text())
        story = campaign['source_evidence']['owned_developer_story']
        source = (ROOT / story['source']).read_text()
        self.assertEqual(story['state'], 'published')
        self.assertEqual(story['article_id'], 3849)
        self.assertIn('id: 3849', source)
        self.assertEqual(source.count(story['tracked_destination']), 1)
        self.assertIn('same synthetic voice', source)
        self.assertIn('not an accuracy claim for everyone', source)
        self.assertNotIn('for-tutors', source)
        self.assertNotIn('buy.stripe.com', source)
        self.assertNotIn('access_token', source)
        self.assertNotIn('/home/', source)
        self.assertEqual(story['medium']['state'], 'published')
        self.assertTrue(story['medium']['published'])
        self.assertTrue(story['medium']['brief_ai_assistance_label_present'])
        self.assertIn('outside the paywall', story['medium']['publication_gate'])

    def test_medium_schedule_keeps_free_distribution_separate_from_publication(self):
        campaign = json.loads((ROOT / 'campaigns/l-and-n-pronunciation-launch.json').read_text())
        story = campaign['source_evidence']['owned_developer_story']
        medium = story['medium']
        self.assertFalse(medium['paywall_enabled'])
        self.assertTrue(medium['canonical_setting_verified'])
        self.assertEqual(medium['canonical_url'], story['url'])
        self.assertEqual(medium['topics'], ['Language Learning', 'Programming'])
        self.assertEqual(
            datetime.fromisoformat(medium['scheduled_at_utc'].replace('Z', '+00:00')),
            datetime.fromisoformat(medium['scheduled_at_local']),
        )
        self.assertEqual(medium['schedule_timezone'], 'Asia/Hong_Kong')
        self.assertGreater(medium['scheduled_at_local'][:10], medium['verified_on'])
        self.assertTrue(medium['normalized_text_preserved_after_spacing_cleanup'])
        self.assertTrue(medium['published'])
        self.assertIn('anonymous public access', medium['publication_gate'])
        self.assertNotIn('/p/', json.dumps(medium))
        self.assertNotIn('draft_url', medium)
        self.assertNotIn('editor_url', medium)

    def test_medium_publication_does_not_invent_anonymous_visibility_or_users(self):
        campaign = json.loads((ROOT / 'campaigns/l-and-n-pronunciation-launch.json').read_text())
        medium = campaign['source_evidence']['owned_developer_story']['medium']
        result = medium['publication_verification']
        self.assertTrue(result['published_list_verified'])
        self.assertTrue(result['full_article_author_view_verified'])
        self.assertTrue(result['public_canonical_matches_original_blog'])
        self.assertTrue(result['structured_is_accessible_for_free'])
        self.assertEqual(result['section_headings_verified'], 4)
        self.assertEqual(result['anonymous_visibility'], 'unresolved_http_403')
        self.assertFalse(result['new_publication_action'])
        self.assertGreater(
            datetime.fromisoformat(result['provider_published_at'].replace('Z', '+00:00')),
            datetime.fromisoformat(medium['scheduled_at_utc'].replace('Z', '+00:00')),
        )
        self.assertLess(result['imported_source_date'], result['provider_published_at'])
        self.assertRegex(result['captured_article_text_sha256'], r'^[a-f0-9]{64}$')
        self.assertIn('medium.com/i-mix-up-l-and-n-', medium['published_url'])
        self.assertIn('not a new store-focused campaign',
                      campaign['source_evidence']['owned_developer_story']['policy'])

    def test_current_homepage_evidence_keeps_capture_history_separate(self):
        evidence = json.loads((ROOT / 'campaigns/l-and-n-pronunciation-launch.json').read_text())['source_evidence']
        self.assertEqual(len(evidence['deployed_source_commit']), 40)
        self.assertEqual(len(evidence['current_evidence_commit']), 40)
        self.assertEqual(evidence['homepage_discovery']['state'], 'live')
        self.assertEqual(evidence['homepage_discovery']['entry_asset'], '/assets/index-DZiUdOSI.js')
        self.assertEqual(evidence['owned_store_continuation']['entry_asset'], '/assets/index-zHLbJcBO.js')


if __name__ == '__main__':
    unittest.main()
