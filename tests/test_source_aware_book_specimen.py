import hashlib
import json
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "source-aware-book-specimen"
SOURCE = SAMPLE / "source"
ARTIFACTS = SAMPLE / "artifacts"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourceAwareBookSpecimenTests(unittest.TestCase):
    def test_source_is_complete_reviewed_and_reconstructable(self):
        book = json.loads((SOURCE / "book.json").read_text(encoding="utf-8"))
        self.assertEqual(book["schema"], "source-aware-book-specimen/v1")
        self.assertEqual(book["languages"], ["en", "zh-Hant"])
        self.assertFalse(book["rights"]["third_party_content"])
        self.assertEqual(len(book["chapters"]), 3)

        paragraphs = [
            paragraph
            for chapter in book["chapters"]
            for paragraph in chapter["paragraphs"]
        ]
        self.assertEqual([item["id"] for item in paragraphs], [f"p-{n:03d}" for n in range(1, 7)])

        roles = {
            "subject",
            "predicate",
            "object",
            "attributive",
            "adverbial",
            "complement",
            "topic",
            "function",
        }
        for chapter_index, chapter in enumerate(book["chapters"]):
            for paragraph_index, paragraph in enumerate(chapter["paragraphs"]):
                expected_source = (
                    f"source/book.json#/chapters/{chapter_index}/paragraphs/{paragraph_index}"
                )
                self.assertEqual(paragraph["source_location"], expected_source)
                self.assertEqual(paragraph["status"], "reviewed")
                self.assertTrue(paragraph["reviewer_notes"])
                self.assertEqual(
                    " ".join(token["text"] for token in paragraph["main"]["tokens"]),
                    paragraph["main"]["text"],
                )
                self.assertEqual(
                    "".join(token["text"] for token in paragraph["comment"]["tokens"]),
                    paragraph["comment"]["text"],
                )
                for token in paragraph["main"]["tokens"] + paragraph["comment"]["tokens"]:
                    self.assertIn(token["role"], roles)
                self.assertTrue(
                    all("reading" in token for token in paragraph["comment"]["tokens"])
                )

    def test_manifest_outputs_and_checksums_are_current(self):
        manifest = json.loads((ARTIFACTS / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "source-aware-book-specimen-manifest/v1")
        self.assertEqual(manifest["status"], "project_owned_process_evidence")
        self.assertEqual(manifest["source"]["chapters"], 3)
        self.assertEqual(manifest["source"]["reviewed_paragraphs"], 6)
        self.assertEqual(manifest["source"]["languages"], ["en", "zh-Hant"])
        self.assertFalse(manifest["source"]["third_party_content"])
        self.assertTrue(manifest["cover"]["textless"])
        self.assertEqual(manifest["validation"]["directions"], ["en-main", "zh-main"])
        self.assertEqual(manifest["validation"]["variants"], ["color", "blackwhite"])

        for output in manifest["outputs"]:
            path = SAMPLE / output["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(digest(path), output["sha256"], path)

        checksum_lines = (ARTIFACTS / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(checksum_lines), 11)
        for line in checksum_lines:
            expected, relative = line.split("  ", 1)
            self.assertEqual(digest(SAMPLE / relative), expected, relative)

    def test_pdf_epub_and_delivery_packet_have_expected_structure(self):
        pdf_names = {
            "book-specimen-en-main-color.pdf",
            "book-specimen-en-main-blackwhite.pdf",
            "book-specimen-zh-main-color.pdf",
            "book-specimen-zh-main-blackwhite.pdf",
        }
        for name in pdf_names:
            self.assertTrue((ARTIFACTS / name).read_bytes().startswith(b"%PDF-"), name)

        epub = ARTIFACTS / "book-specimen.epub"
        with zipfile.ZipFile(epub) as archive:
            self.assertIsNone(archive.testzip())
            infos = archive.infolist()
            self.assertEqual(infos[0].filename, "mimetype")
            self.assertEqual(infos[0].compress_type, zipfile.ZIP_STORED)
            self.assertEqual(archive.read("mimetype"), b"application/epub+zip")
            for name in (
                "META-INF/container.xml",
                "OEBPS/content.opf",
                "OEBPS/nav.xhtml",
                "OEBPS/cover.xhtml",
                "OEBPS/chapter-1.xhtml",
                "OEBPS/chapter-2.xhtml",
                "OEBPS/chapter-3.xhtml",
            ):
                ET.fromstring(archive.read(name))
            combined = b"".join(
                archive.read(f"OEBPS/chapter-{index}.xhtml") for index in range(1, 4)
            ).decode("utf-8")
            for paragraph_id in (f"p-{n:03d}" for n in range(1, 7)):
                self.assertIn(f'id="{paragraph_id}"', combined)

        packet = ARTIFACTS / "source-aware-book-specimen.zip"
        expected = (ARTIFACTS / "source-aware-book-specimen.zip.sha256").read_text().split()[0]
        self.assertEqual(digest(packet), expected)
        with zipfile.ZipFile(packet) as archive:
            self.assertIsNone(archive.testzip())
            names = set(archive.namelist())
        self.assertTrue(
            {
                "README.md",
                "LICENSE-SAMPLE.md",
                "build.py",
                "source/book.json",
                "source/cover.png",
                "artifacts/manifest.json",
                "artifacts/source-ledger.json",
                "artifacts/validation-report.md",
                "artifacts/SHA256SUMS",
                "artifacts/book-specimen.epub",
                *{f"artifacts/{name}" for name in pdf_names},
            }.issubset(names)
        )

    def test_public_copy_preserves_the_commercial_boundary(self):
        readme = (SAMPLE / "README.md").read_text(encoding="utf-8").casefold()
        report = (ARTIFACTS / "validation-report.md").read_text(encoding="utf-8").casefold()
        combined = " ".join((readme + "\n" + report).split())
        for phrase in (
            "project-owned",
            "not customer work",
            "translation benchmark",
            "kdp/ingramspark approval",
            "printer proof",
            "complete-book production",
            "rights-cleared chapter",
        ):
            self.assertIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
