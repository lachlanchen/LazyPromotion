import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaigns" / "cross-source-card-dedup.json"


class CrossSourceCardDedupCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    def test_live_article_has_one_bounded_offer_path(self):
        lazyblog = self.campaign["channels"]["lazyblog"]
        conversion = lazyblog["conversion_path"]

        self.assertEqual(self.campaign["version"], 5)
        self.assertIn("48adb6a", lazyblog["blog_commits"])
        self.assertIn("USD 250", conversion["offer"])
        self.assertIn("12 source units", conversion["offer"])
        self.assertIn("20 test questions", conversion["offer"])
        self.assertEqual(
            conversion["fit_check"],
            "https://lazying.art/lkt/fit-check/?utm_source=lazyblog&utm_medium=article&utm_campaign=card_dedup&utm_content=fit_check",
        )
        self.assertFalse(conversion["automatic_form_submission"])
        self.assertIn("HTTP 200", conversion["live_review"])

    def test_reddit_profile_queue_is_concise_and_visibly_verified(self):
        reddit = self.campaign["channels"]["reddit"]
        review = reddit["visible_review"]

        self.assertEqual(reddit["state"], "postiz_queue")
        self.assertEqual(reddit["scope"], "own_profile")
        self.assertEqual(reddit["settings"]["subreddit"], "/r/u_Ok-Perception1122")
        self.assertIn("I maintain the guide.", reddit["content"])
        self.assertNotIn("Disclosure:", reddit["content"])
        self.assertIn(
            "https://blog.lazying.art/?p=3782&utm_source=reddit&utm_medium=profile&utm_campaign=card_dedup",
            reddit["content"],
        )
        self.assertEqual(review["stored_state"], "QUEUE")
        self.assertTrue(review["stored_text_exact"])
        self.assertTrue(review["stored_title_exact"])
        self.assertTrue(review["stored_time_exact"])
        self.assertTrue(review["original_url_preserved"])
        self.assertEqual(review["update_attempts"], 1)

    def test_x_retry_is_single_and_duplicate_checked(self):
        channel = self.campaign["channels"]["x"]
        review = channel["delivery_review"]

        self.assertEqual(channel["state"], "published")
        self.assertEqual(channel["original_publish_at"], "2026-09-07T02:00:00Z")
        self.assertEqual(channel["publish_at"], review["retry_publish_at"])
        self.assertEqual(review["first_attempt_state"], "ERROR")
        self.assertEqual(review["retry_attempts"], 1)
        self.assertFalse(review["visible_profile_match_found"])
        self.assertFalse(review["exact_x_search_match_found"])
        self.assertFalse(review["postiz_provider_match_found"])
        self.assertEqual(review["retry_state"], "PUBLISHED")
        self.assertTrue(review["visible_copy_exact"])
        self.assertTrue(review["tracked_destination_verified"])
        self.assertEqual(
            channel["release_url"],
            "https://x.com/lazyingart/status/2096791913928278225",
        )
        self.assertIn("Do not retry again", channel["policy"])

    def test_publication_and_attention_do_not_inflate_revenue(self):
        funnel = self.campaign["funnel"]
        self.assertEqual(funnel["state"], "attention")
        self.assertFalse(funnel["fit_inquiry_observed"])
        self.assertFalse(funnel["payment_confirmed"])
        self.assertEqual(funnel["received_revenue_usd"], 0)


if __name__ == "__main__":
    unittest.main()
