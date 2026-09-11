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

    def test_reader_index_routes_every_book_without_claiming_a_sale(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "lecture-archive-provenance.json").read_text(
                encoding="utf-8"
            )
        )
        github = campaign["channels"]["github"]
        index = github["reader_index"]

        self.assertEqual(index["state"], "published")
        self.assertEqual(index["books"], 19)
        self.assertEqual(
            index["url"],
            "https://github.com/lachlanchen/leonardsusskind/tree/main/all_notes",
        )
        self.assertFalse(github["lead_or_sale_observed"])

    def test_rights_cleared_service_path_keeps_the_archive_free(self):
        campaign = json.loads(
            (ROOT / "campaigns" / "lecture-archive-provenance.json").read_text(
                encoding="utf-8"
            )
        )
        route = campaign["channels"]["github"]["rights_cleared_service_path"]

        self.assertEqual(campaign["version"], 3)
        self.assertEqual(route["state"], "published")
        self.assertEqual(route["readme_languages"], 11)
        self.assertEqual(len(route["repository_commit"]), 40)
        self.assertIn("utm_campaign=leonard_susskind_archive", route["url"])
        self.assertIn("archive free", route["policy"])
        self.assertFalse(campaign["channels"]["github"]["lead_or_sale_observed"])


if __name__ == "__main__":
    unittest.main()
