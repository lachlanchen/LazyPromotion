import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LectureArchiveCampaignTests(unittest.TestCase):
    def test_study_post_is_one_reviewed_queue_item(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "lecture-archive-provenance.json").read_text(
                encoding="utf-8"
            )
        )
        study = campaign["channels"]["x"]["study_post"]
        verification = study["verification"]

        self.assertEqual(study["state"], "postiz_queue")
        self.assertFalse(study["visible_review_pending"])
        self.assertTrue(verification["visible_calendar_reviewed"])
        self.assertEqual(verification["matching_posts"], 1)
        self.assertEqual(verification["verified_state"], "QUEUE")
        self.assertFalse(verification["release_present"])
        self.assertLessEqual(len(study["content"]), verification["provider_max_length"])
        self.assertEqual(
            hashlib.sha256(study["content"].encode("utf-8")).hexdigest(),
            study["content_sha256"],
        )
        self.assertFalse(campaign["channels"]["github"]["lead_or_sale_observed"])


if __name__ == "__main__":
    unittest.main()
