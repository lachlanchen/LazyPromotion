import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import network
import promotion


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = promotion.open_db(Path(self.tmp.name) / "network.sqlite3")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_graph_connects_private_need_to_public_project(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/ChineseLanguage/comments/example/reader/",
            author="reader",
            body="Can anyone recommend a multilingual Classical Chinese reader?",
        )
        report = network.sync_graph(self.db)
        self.assertGreater(report["entities"], 100)
        match = self.db.execute(
            """
            SELECT 1 FROM relationships
            WHERE source_id=? AND relation='matches' AND target_id=?
            """,
            (f"need:{candidate['id']}", f"project:{candidate['suggested_tool']}"),
        ).fetchone()
        self.assertIsNotNone(match)

    def test_nested_campaign_evidence_urls_are_discovered(self):
        evidence = {
            "offer": "https://lazying.art/lecture-pack/",
            "executed_sample": {
                "url": "https://example.test/proof",
                "outputs": ["not a URL", "https://example.test/export.vtt"],
            },
        }
        self.assertEqual(
            [
                ("offer", "https://lazying.art/lecture-pack/"),
                ("executed sample url", "https://example.test/proof"),
                ("executed sample outputs 2", "https://example.test/export.vtt"),
            ],
            list(network.source_evidence_urls(evidence)),
        )

    def test_live_encrypted_intake_sources_enter_public_graph(self):
        network.sync_graph(self.db)
        snapshot = json.dumps(network.public_snapshot(self.db), ensure_ascii=False)
        self.assertIn(
            "https://blog.lazying.art/wp-json/lazyingart/v1/lkt-fit-check",
            snapshot,
        )
        self.assertIn("0463dcb2470ad1c908597b7f4d636cf2d33013a1", snapshot)
        self.assertIn("3ff43e4afc0dfd4512629443af198345696c170e", snapshot)
        self.assertIn("f8be630ea3c7a5b4aa90544ddc2b5b212e1a5445", snapshot)

    def test_public_snapshot_excludes_people_drafts_and_local_paths(self):
        candidate = promotion.ingest_candidate(
            self.db,
            platform="reddit",
            source_url="https://www.reddit.com/r/example/comments/private/thanks/",
            author="private-person",
            body="Thank you, this helped me.",
        )
        promotion.save_courtesy_draft(
            self.db,
            candidate["id"],
            "That means a lot—thank you.",
            why="Direct acknowledgement.",
        )
        network.sync_graph(self.db)
        snapshot = network.public_snapshot(self.db)
        serialized = json.dumps(snapshot, ensure_ascii=False)
        self.assertNotIn("private-person", serialized)
        self.assertNotIn("That means a lot", serialized)
        self.assertNotIn("r/example", serialized)
        self.assertNotIn("workspace_checkout", serialized)
        self.assertIn("LazyingArt eInk", serialized)

    def test_github_repository_has_one_canonical_entity(self):
        network.sync_graph(self.db)
        count = self.db.execute(
            "SELECT COUNT(*) FROM entities WHERE id='repository:lachlanchen/LazyEdit'"
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_public_projects_exactly_follow_current_catalog(self):
        network.upsert_entity(
            self.db,
            "project:obsolete-generated-alias",
            kind="project",
            label="Obsolete alias",
            url="https://github.com/lachlanchen/Video2Book",
            visibility="public",
        )
        network.sync_graph(self.db)

        expected = {
            f"project:{project['id']}"
            for project in promotion.load_catalog()["projects"]
        }
        snapshot = network.public_snapshot(self.db)
        actual = {
            entity["id"]
            for entity in snapshot["entities"]
            if entity["kind"] == "project"
        }

        self.assertEqual(actual, expected)
        self.assertIn("project:video2book", actual)
        self.assertIn("project:paperagent", actual)
        self.assertNotIn("project:obsolete-generated-alias", actual)
        visibility = self.db.execute(
            "SELECT visibility FROM entities WHERE id='project:obsolete-generated-alias'"
        ).fetchone()[0]
        self.assertEqual(visibility, "private")

    def test_public_opportunity_combines_multiple_public_projects(self):
        network.sync_graph(self.db)
        opportunity_id = "opportunity:creator-media-library"
        entity = self.db.execute(
            "SELECT visibility FROM entities WHERE id=?", (opportunity_id,)
        ).fetchone()
        self.assertEqual(entity[0], "public")
        targets = self.db.execute(
            """
            SELECT target_id FROM relationships
            WHERE source_id=? AND relation='combines'
            ORDER BY target_id
            """,
            (opportunity_id,),
        ).fetchall()
        self.assertEqual(len(targets), 4)
        self.assertTrue(all(row[0].startswith("project:") for row in targets))

        snapshot = json.dumps(network.public_snapshot(self.db), ensure_ascii=False)
        self.assertIn("Creator media library website", snapshot)
        self.assertIn("LalaMedias", snapshot)

    def test_workspace_scan_skips_unreadable_entries(self):
        parent = Path(self.tmp.name) / "projects"
        parent.mkdir()
        (parent / "plain-directory").mkdir()
        count = network.sync_workspace(self.db, parent)
        self.assertEqual(count, 0)

    def test_unverified_workspace_remote_stays_private(self):
        parent = Path(self.tmp.name) / "projects"
        repo = parent / "private-work"
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(
            [
                "git", "-C", str(repo), "remote", "add", "origin",
                "git@github.com:lachlanchen/not-in-public-index.git",
            ],
            check=True,
        )
        network.sync_graph(self.db)
        network.sync_workspace(self.db, parent)
        visibility = self.db.execute(
            """
            SELECT visibility FROM entities
            WHERE id='repository:lachlanchen/not-in-public-index'
            """
        ).fetchone()[0]
        self.assertEqual(visibility, "private")

    def test_sync_demotes_replaced_repository_and_evidence_url(self):
        stale_url = "https://github.com/lachlanchen/LazyingArtLanding"
        stale_repo = network.repository_entity(
            self.db,
            stale_url,
            label="Old eInk checkout name",
        )
        stale_resource = network.url_entity(
            self.db,
            stale_url,
            label="old hero asset repository",
        )
        network.upsert_relationship(
            self.db,
            "project:lazyingart-eink",
            "backed_by",
            stale_repo,
            evidence_url=stale_url,
        )
        network.upsert_relationship(
            self.db,
            "campaign:eink-multilingual-reading",
            "uses_evidence",
            stale_resource,
            evidence_url=stale_url,
        )

        network.sync_graph(self.db)
        snapshot = json.dumps(network.public_snapshot(self.db), ensure_ascii=False)

        self.assertNotIn("LazyingArtLanding", snapshot)
        self.assertEqual(
            self.db.execute(
                "SELECT visibility FROM entities WHERE id=?",
                (stale_repo,),
            ).fetchone()[0],
            "private",
        )
        self.assertEqual(
            self.db.execute(
                "SELECT visibility FROM entities WHERE id=?",
                (stale_resource,),
            ).fetchone()[0],
            "private",
        )


if __name__ == "__main__":
    unittest.main()
