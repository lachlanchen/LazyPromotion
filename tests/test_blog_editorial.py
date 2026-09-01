import json
import tempfile
import unittest
from pathlib import Path

import blog_editorial


class BlogEditorialTests(unittest.TestCase):
    def test_ledger_requires_sorted_unique_consistent_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.md"
            ledger.write_text(
                "As of the verified commit, **3 posts** have completed:\n\n"
                "`7, 9, 10`\n\nPosts: `7, 10`.\n",
                encoding="utf-8",
            )
            self.assertEqual(
                blog_editorial.validate_ledger(ledger),
                {"verified_posts": 3, "categories": 1},
            )
            ledger.write_text(
                "As of the verified commit, **3 posts** have completed:\n\n"
                "`7, 10, 9`\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                blog_editorial.EditorialValidationError, "not sorted"
            ):
                blog_editorial.validate_ledger(ledger)

    def test_post_validates_identity_language_and_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            post_dir = root / "content" / "posts" / "42"
            translations = post_dir / "translations"
            translations.mkdir(parents=True)
            common = (
                "id: '42'\nslug: 'answer'\ndate: '2026-09-01T00:00:00'\n"
                "status: 'publish'\nlink: 'https://example.test/42'\n"
                "source_language: 'zh'\n"
            )
            (post_dir / "post.md").write_text(
                f"---\n{common}title: '答案'\n---\n\n## 步骤\n\n"
                "- [资料](https://example.test/source)\n\n```bash\nprintf ok\n```\n",
                encoding="utf-8",
            )
            for language, title, heading in (
                ("en", "Answer", "Steps"),
                ("ja", "答え", "手順"),
            ):
                (translations / f"{language}.md").write_text(
                    f"---\n{common}language: '{language}'\ntitle: '{title}'\n---\n\n"
                    f"## {heading}\n\n- [Source](https://example.test/source)\n\n"
                    "```bash\nprintf ok\n```\n",
                    encoding="utf-8",
                )
            (post_dir / "lazyblog.json").write_text(
                json.dumps({"post_id": 42}), encoding="utf-8"
            )
            result = blog_editorial.validate_post(root, 42)
            self.assertEqual(result["translations"], ["en", "ja"])
            self.assertEqual(result["files"], 4)
            self.assertEqual(result["links"], 1)

    def test_post_rejects_structure_drift_and_body_h1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            post_dir = root / "content" / "posts" / "42"
            translations = post_dir / "translations"
            translations.mkdir(parents=True)
            common = (
                "id: '42'\nslug: 'answer'\ndate: '2026-09-01T00:00:00'\n"
                "status: 'publish'\nlink: 'https://example.test/42'\n"
                "source_language: 'zh'\n"
            )
            (post_dir / "post.md").write_text(
                f"---\n{common}title: '答案'\n---\n\n# Too large\n",
                encoding="utf-8",
            )
            for language in ("en", "ja"):
                (translations / f"{language}.md").write_text(
                    f"---\n{common}language: '{language}'\ntitle: 'Answer'\n---\n\n"
                    "# Too large\n",
                    encoding="utf-8",
                )
            (post_dir / "lazyblog.json").write_text(
                json.dumps({"post_id": 42}), encoding="utf-8"
            )
            with self.assertRaisesRegex(
                blog_editorial.EditorialValidationError, "body H1"
            ):
                blog_editorial.validate_post(root, 42)

    def test_post_rejects_list_or_link_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            post_dir = root / "content" / "posts" / "42"
            translations = post_dir / "translations"
            translations.mkdir(parents=True)
            common = (
                "id: '42'\nslug: 'answer'\ndate: '2026-09-01T00:00:00'\n"
                "status: 'publish'\nlink: 'https://example.test/42'\n"
                "source_language: 'zh'\n"
            )
            (post_dir / "post.md").write_text(
                f"---\n{common}title: '答案'\n---\n\n## 步骤\n\n"
                "- [资料](https://example.test/source)\n",
                encoding="utf-8",
            )
            (translations / "en.md").write_text(
                f"---\n{common}language: 'en'\ntitle: 'Answer'\n---\n\n## Steps\n\n"
                "1. [Source](https://example.test/other)\n",
                encoding="utf-8",
            )
            (translations / "ja.md").write_text(
                f"---\n{common}language: 'ja'\ntitle: '答え'\n---\n\n## 手順\n\n"
                "- [資料](https://example.test/source)\n",
                encoding="utf-8",
            )
            (post_dir / "lazyblog.json").write_text(
                json.dumps({"post_id": 42}), encoding="utf-8"
            )
            with self.assertRaisesRegex(
                blog_editorial.EditorialValidationError, "Markdown blocks"
            ):
                blog_editorial.validate_post(root, 42)


if __name__ == "__main__":
    unittest.main()
