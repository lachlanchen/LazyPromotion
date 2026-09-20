import json
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
        self.assertEqual(story['medium']['state'], 'draft_saved')
        self.assertFalse(story['medium']['published'])
        self.assertTrue(story['medium']['brief_ai_assistance_label_present'])
        self.assertIn('outside the paywall', story['medium']['publication_gate'])

    def test_current_homepage_evidence_keeps_capture_history_separate(self):
        evidence = json.loads((ROOT / 'campaigns/l-and-n-pronunciation-launch.json').read_text())['source_evidence']
        self.assertEqual(len(evidence['deployed_source_commit']), 40)
        self.assertEqual(len(evidence['current_evidence_commit']), 40)
        self.assertEqual(evidence['homepage_discovery']['state'], 'live')
        self.assertEqual(evidence['homepage_discovery']['entry_asset'], '/assets/index-DZiUdOSI.js')
        self.assertEqual(evidence['owned_store_continuation']['entry_asset'], '/assets/index-zHLbJcBO.js')


if __name__ == '__main__':
    unittest.main()
