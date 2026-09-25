import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import app_workspace as app


class AppWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.records = app.load_campaigns(list(app.SOURCES))

    def test_real_campaign_projection_without_private_runtime(self):
        result = app.workspace(records=self.records)
        self.assertEqual(result["version"], 1)
        self.assertEqual(len(result["projects"]), 2)
        self.assertEqual(sum(len(p["publications"]) for p in result["projects"]), 5)
        for project in result["projects"]:
            for publication in project["publications"]:
                self.assertEqual(hashlib.sha256(publication["body"].encode()).hexdigest(), publication["bodySha256"])
            for metric in project["outcomes"].values():
                self.assertEqual(metric, {"state": "not_connected", "value": None})
        self.assertEqual([k for k, v in result["capabilities"].items() if v], ["readPublishedCampaigns"])
        encoded = json.dumps(result)
        for forbidden in (".local/", "/home/", "127.0.0.1", "integrationId", "approval_token"):
            self.assertNotIn(forbidden, encoded)

    def test_only_requested_product_and_its_official_destinations(self):
        landn = app.workspace(["l-and-n"], records=self.records)["projects"][0]
        self.assertEqual(set(landn["links"]), {"apple", "google", "video", "repository"})
        self.assertNotIn("l-and-n.lazying.art", json.dumps(landn))
        bunko = app.workspace(["bunko"], records=self.records)["projects"][0]
        self.assertNotIn("google", bunko["links"])
        self.assertEqual(bunko["links"]["video"], "https://www.youtube.com/shorts/pSWnOwzyc-4")

    def test_unknown_fields_and_unselected_campaigns_are_not_exported(self):
        records = copy.deepcopy(self.records)
        records["unrelated-private-campaign"] = {"secret": "DO_NOT_EXPORT"}
        for campaign in records.values():
            campaign["operator"] = {"token": "DO_NOT_EXPORT"}
            for post in campaign.get("channels", {}).values():
                post["private_receipt"] = "DO_NOT_EXPORT"
            campaign["funnel"] = {"verified_received_gross_usd": 1000}
        result = json.dumps(app.workspace(records=records))
        self.assertNotIn("DO_NOT_EXPORT", result)
        self.assertNotIn("1000", result)

    def test_drafts_and_schedules_never_become_publications(self):
        for state in ("draft", "prepared", "scheduled", "failed", "uncertain", "PUBLISHED", None):
            with self.subTest(state=state):
                records = copy.deepcopy(self.records)
                records["bunko-japanese-reader-introduction"]["channels"]["reddit"]["state"] = state
                result = app.workspace(["bunko"], records=records)
                self.assertEqual(len(result["projects"][0]["publications"]), 2)

    def test_anonymous_failure_is_not_claimed_public(self):
        publications = app.workspace(["bunko"], records=self.records)["projects"][0]["publications"]
        japanese = next(p for p in publications if p["id"].startswith("bunko-japanese"))
        self.assertEqual(japanese["visibilityEvidence"], "account_verified")
        records = copy.deepcopy(self.records)
        check = records["bunko-japanese-reader-introduction"]["channels"]["reddit"]["publication_verification"]
        check["logged_out_visibility_verified"] = "true"
        self.assertEqual(app.workspace(["bunko"], records=records)["projects"][0]["publications"][-1]["visibilityEvidence"], "account_verified")
        check.clear()
        self.assertEqual(app.workspace(["bunko"], records=records)["projects"][0]["publications"][-1]["visibilityEvidence"], "unverified")

    def test_changed_published_text_fails_closed(self):
        self.records["bunko-japanese-reader-introduction"]["channels"]["reddit"]["content"] += " changed"
        with self.assertRaises(ValueError):
            app.workspace(records=self.records)

    def test_missing_and_mismatched_selected_campaigns_fail(self):
        with self.assertRaises(ValueError):
            app.workspace(records={})
        self.records["bunko-japanese-reader-introduction"]["id"] = "different"
        with self.assertRaises(ValueError):
            app.workspace(records=self.records)

    def test_unknown_and_duplicate_product_ids_fail(self):
        for products in ([], ["l-and-n", "l-and-n"], ["../.local"], ["unknown"]):
            with self.subTest(products=products), self.assertRaises(ValueError):
                app.workspace(products, records=self.records)

    def test_publication_urls_do_not_accept_credentials_or_private_hosts(self):
        for url in (
            "https://user:pass@www.reddit.com/r/x/comments/abc/title/",
            "https://127.0.0.1/r/x/comments/abc/title/",
            "https://www.reddit.com:443/r/x/comments/abc/title/",
            "https://www.reddit.com/r/x/comments/abc/title/?token=private",
            "https://www.reddit.com/r/x/comments/abc/title/#private",
            "https://www.reddit.com/r/x/comments/abc/%2e%2e/",
            "https://www.reddit.com/message/inbox/",
            "http://www.reddit.com/r/x/comments/abc/title/",
            "https://x.com/name/status/123",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                app.publication_url(url, "reddit")

    def test_cli_outputs_json_without_loading_operator_modules(self):
        result = subprocess.run([sys.executable, "app_workspace.py", "--project", "bunko"], cwd=app.ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["projects"][0]["id"], "bunko")
        self.assertEqual(result.stderr, "")
        source = Path(app.__file__).read_text()
        for dependency in ("import promotion", "import browser", "import sqlite3", "import requests"):
            self.assertNotIn(dependency, source)


if __name__ == "__main__":
    unittest.main()
