import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READMES = [
    ROOT / "README.md",
    *(ROOT / "i18n" / name for name in (
        "README.ar.md",
        "README.es.md",
        "README.fr.md",
        "README.ja.md",
        "README.ko.md",
        "README.vi.md",
        "README.zh-Hans.md",
        "README.zh-Hant.md",
        "README.de.md",
        "README.ru.md",
    )),
]


class RepositoryTests(unittest.TestCase):
    def test_all_eleven_readmes_have_shared_public_panels(self):
        self.assertEqual(len(READMES), 11)
        for path in READMES:
            with self.subTest(path=path.name):
                body = path.read_text(encoding="utf-8")
                header = body.splitlines()[0]
                self.assertEqual(header.count("]("), 11)
                self.assertIn("figs/banner.png", body)
                self.assertIn("chat.lazying.art/donate", body)
                self.assertIn("paypal.me/RongzhouChen", body)
                self.assertIn("buy.stripe.com/", body)
                self.assertIn("CITATION.cff", body)
                self.assertIn("@software{chen_lazypromotion_2026", body)

    def test_readme_language_links_resolve(self):
        for path in READMES:
            header = path.read_text(encoding="utf-8").splitlines()[0]
            for target in header.split("](")[1:]:
                relative = target.split(")", 1)[0]
                with self.subTest(source=path.name, target=relative):
                    self.assertTrue((path.parent / relative).resolve().is_file())

    def test_catalog_has_unique_grounded_projects(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        projects = catalog["projects"]
        ids = [project["id"] for project in projects]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("localknowledgeterminal", ids)
        for project in projects:
            with self.subTest(project=project["id"]):
                self.assertTrue(project["url"].startswith("https://github.com/lachlanchen/"))
                self.assertTrue(project["summary"].strip())
                self.assertTrue(project["keywords"])

    def test_private_runtime_paths_are_ignored(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".local/", ignored)
        self.assertIn("handoff/", ignored)


if __name__ == "__main__":
    unittest.main()
