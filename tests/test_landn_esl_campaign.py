import hashlib
import json
from pathlib import Path
import unittest

import owned_monitor

ROOT = Path(__file__).resolve().parents[1]


class LandnTeacherCampaignTests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads((ROOT / 'campaigns/l-and-n-esl-teacher-exercise.json').read_text())
        self.post = self.campaign['channels']['reddit']

    def test_exact_reviewed_copy_and_store_links(self):
        copy = self.post['content']
        self.assertEqual(hashlib.sha256(copy.encode()).hexdigest(), self.post['content_sha256'])
        self.assertTrue(copy.startswith('One small exercise for adult learners'))
        self.assertIn('Then swap roles', copy)
        self.assertIn('I built L & N', copy)
        self.assertIn('US$0.99', copy)
        self.assertIn('free download, with in-app purchases', copy)
        self.assertIn('https://apps.apple.com/us/app/l-n-speech-practice/id6808872450', copy)
        self.assertIn('https://play.google.com/store/apps/details?id=art.lazying.landn', copy)
        self.assertNotIn('l-and-n.lazying.art', copy)
        self.assertNotIn('TestFlight', copy)

    def test_one_future_queue_not_a_publication_or_sale(self):
        self.assertEqual(self.post['state'], 'queued_verified')
        self.assertEqual(self.post['publish_at'], '2026-09-27T12:00:00Z')
        self.assertNotIn('release_url', self.post)
        v = self.post['publication_verification']
        self.assertEqual(v['verified_state'], 'QUEUE')
        self.assertEqual(v['schedule_actions'], 1)
        self.assertTrue(v['single_matching_item'])
        self.assertFalse(v['release_present'])
        self.assertIsNone(self.campaign['funnel']['verified_new_users'])
        self.assertIsNone(self.campaign['funnel']['verified_received_gross_usd'])

    def test_specific_teacher_venue_and_optional_flair_evidence(self):
        self.assertEqual(self.post['community'], 'r/ESL_Teachers')
        self.assertEqual(self.post['settings']['type'], 'self')
        self.assertEqual(self.post['settings']['flair'], 'Helpful Materials')
        v = self.post['publication_verification']
        self.assertTrue(v['saved_preview_reviewed'])
        self.assertTrue(v['optional_flair_verified_against_live_provider'])
        self.assertFalse(v['flair_dropdown_populated_in_web_editor'])
        self.assertIn("not something I'd use to grade a student", self.post['content'])

    def test_monitor_can_match_copy_without_provider_ids(self):
        route = owned_monitor.route_for_post('reddit', self.post['content'], owned_monitor.route_index())
        self.assertEqual(route['campaign_id'], self.campaign['id'])
        self.assertEqual(route['known_owned_replies'], 0)
        raw = json.dumps(self.campaign)
        for marker in ('/home/', '.local/', '127.0.0.1', 'integrationId', 'postId', 'cmuhcr'):
            self.assertNotIn(marker, raw)

    def test_no_automatic_repeat_or_followup(self):
        follow_up = self.campaign['follow_up']
        self.assertTrue(follow_up['postiz_managed'])
        for key in ('automatic_replies', 'automatic_reposts', 'unsolicited_private_messages'):
            self.assertFalse(follow_up[key])
        self.assertEqual(follow_up['repeat_not_before'], '2026-10-04')
        self.assertIn('not permission', follow_up['next_action'])


if __name__ == '__main__':
    unittest.main()
