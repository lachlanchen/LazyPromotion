import unittest

import sync_github_catalog


class GitHubCatalogTests(unittest.TestCase):
    def test_normalize_preserves_activity_timestamps(self):
        repositories = [
            {
                "name": "Example",
                "url": "https://github.com/lachlanchen/Example",
                "description": "  Example project  ",
                "homepageUrl": "https://example.test",
                "isArchived": False,
                "primaryLanguage": {"name": "Python"},
                "pushedAt": "2026-09-05T05:17:14Z",
                "updatedAt": "2026-09-05T05:17:18Z",
                "repositoryTopics": [{"name": "example"}],
            }
        ]

        normalized = sync_github_catalog.normalize(repositories)

        self.assertEqual(normalized[0]["pushed_at"], "2026-09-05T05:17:14Z")
        self.assertEqual(normalized[0]["updated_at"], "2026-09-05T05:17:18Z")
        self.assertEqual(normalized[0]["description"], "Example project")


if __name__ == "__main__":
    unittest.main()
