#!/usr/bin/env python3
"""Build a deterministic project-owned PDF/EPUB book-production specimen."""

from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import zlib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
ARTIFACTS = ROOT / "artifacts"
BOOK_PATH = SOURCE / "book.json"
COVER_PATH = SOURCE / "cover.png"
FIXED_ZIP_TIME = (2026, 9, 7, 0, 0, 0)
SOURCE_DATE_EPOCH = "1788739200"
ROLES = {
    "subject",
    "predicate",
    "object",
    "attributive",
    "adverbial",
    "complement",
    "topic",
    "function",
}
PDF_VARIANTS = (
    ("en", "color"),
    ("en", "blackwhite"),
    ("zh-Hant", "color"),
    ("zh-Hant", "blackwhite"),
)


class BuildError(RuntimeError):
    """Raised when source or generated evidence violates the specimen contract."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(json_bytes(value))


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise BuildError(f"command failed ({' '.join(command)}):\n{result.stdout[-4000:]}")
    return result.stdout


def load_and_validate() -> dict[str, Any]:
    book = json.loads(BOOK_PATH.read_text(encoding="utf-8"))
    if book.get("schema") != "source-aware-book-specimen/v1":
        raise BuildError("unexpected source schema")
    if book.get("languages") != ["en", "zh-Hant"]:
        raise BuildError("the specimen must preserve the reviewed English/Traditional Chinese pair")
    if book.get("rights", {}).get("third_party_content") is not False:
        raise BuildError("the public specimen must remain project-owned")

    seen_chapters: set[str] = set()
    seen_paragraphs: set[str] = set()
    paragraphs = 0
    for chapter_index, chapter in enumerate(book.get("chapters", [])):
        chapter_id = chapter.get("id", "")
        if not chapter_id or chapter_id in seen_chapters:
            raise BuildError("chapter ids must be nonempty and unique")
        seen_chapters.add(chapter_id)
        for paragraph_index, paragraph in enumerate(chapter.get("paragraphs", [])):
            paragraph_id = paragraph.get("id", "")
            if not paragraph_id or paragraph_id in seen_paragraphs:
                raise BuildError("paragraph ids must be nonempty and unique")
            seen_paragraphs.add(paragraph_id)
            expected = f"source/book.json#/chapters/{chapter_index}/paragraphs/{paragraph_index}"
            if paragraph.get("source_location") != expected:
                raise BuildError(f"{paragraph_id} has a stale source location")
            if paragraph.get("status") != "reviewed" or not paragraph.get("reviewer_notes"):
                raise BuildError(f"{paragraph_id} lacks reviewed status evidence")
            validate_language_block(paragraph_id, paragraph.get("main"), "en", " ")
            validate_language_block(paragraph_id, paragraph.get("comment"), "zh-Hant", "")
            paragraphs += 1
    if len(seen_chapters) != 3 or paragraphs != 6:
        raise BuildError("the frozen specimen requires three chapters and six reviewed paragraphs")
    return book


def validate_language_block(paragraph_id: str, block: Any, language: str, separator: str) -> None:
    if not isinstance(block, dict) or block.get("language") != language:
        raise BuildError(f"{paragraph_id} is missing its {language} block")
    tokens = block.get("tokens")
    if not isinstance(tokens, list) or not tokens:
        raise BuildError(f"{paragraph_id} has no durable {language} tokens")
    for token in tokens:
        if not token.get("text") or token.get("role") not in ROLES:
            raise BuildError(f"{paragraph_id} has an invalid {language} token")
        if language == "zh-Hant" and "reading" not in token:
            raise BuildError(f"{paragraph_id} has a Chinese token without a reading field")
    reconstructed = separator.join(token["text"] for token in tokens)
    if reconstructed != block.get("text"):
        raise BuildError(f"{paragraph_id} {language} token reconstruction drifted")


def png_chunk(name: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + name + payload + struct.pack(">I", zlib.crc32(name + payload) & 0xFFFFFFFF)


def build_cover(path: Path, width: int = 600, height: int = 900) -> None:
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            r, g, b = 241, 235, 220
            if x < 48:
                r, g, b = 27, 107, 94
            if x > width - 108 + y // 7:
                r, g, b = 210, 101, 76
            distance = (x - 390) ** 2 + (y - 255) ** 2
            if distance < 112**2:
                r, g, b = 232, 184, 91
            if 105 < x < 136 and 120 < y < 780:
                r, g, b = 45, 56, 52
            row.extend((r, g, b))
        rows.append(bytes(row))
    payload = b"".join(rows)
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(header + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(payload, 9)) + png_chunk(b"IEND", b""))


def tex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def render_tex(book: dict[str, Any], main_language: str, variant: str) -> str:
    main_key = "main" if main_language == "en" else "comment"
    comment_key = "comment" if main_language == "en" else "main"
    title_main = tex_escape(book["title"][main_language])
    title_comment = tex_escape(book["title"]["zh-Hant" if main_language == "en" else "en"])
    subtitle = tex_escape(book["subtitle"][main_language])
    accent = "1B6B5E" if variant == "color" else "333333"
    companion = "7D5342" if variant == "color" else "555555"
    chapters = []
    for chapter in book["chapters"]:
        chapter_title = tex_escape(chapter["title"][main_language])
        chapter_comment = tex_escape(chapter["title"]["zh-Hant" if main_language == "en" else "en"])
        blocks = []
        for paragraph in chapter["paragraphs"]:
            main_text = tex_escape(paragraph[main_key]["text"])
            comment_text = tex_escape(paragraph[comment_key]["text"])
            locator = tex_escape(f"{paragraph['id']} · {paragraph['source_location']}")
            blocks.append(
                "\\begin{sourceblock}\n"
                f"\\hypertarget{{{paragraph['id']}}}{{\\MainText{{{main_text}}}}}\n"
                f"\\CommentText{{{comment_text}}}\n"
                f"\\SourceLine{{{locator}}}\n"
                "\\end{sourceblock}\n"
            )
        chapters.append(
            f"\\section{{{chapter_title}}}\n"
            f"\\ChapterCompanion{{{chapter_comment}}}\n" + "\n".join(blocks)
        )

    return rf"""\documentclass[11pt]{{article}}
\usepackage[paperwidth=6in,paperheight=9in,top=0.65in,bottom=0.65in,left=0.68in,right=0.68in]{{geometry}}
\usepackage{{fontspec}}
\usepackage{{xeCJK}}
\usepackage{{graphicx}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage{{titlesec}}
\usepackage{{enumitem}}
\setmainfont{{Noto Serif}}
\setsansfont{{Noto Sans}}
\setCJKmainfont{{Noto Serif CJK TC}}
\setCJKsansfont{{Noto Sans CJK TC}}
\XeTeXgenerateactualtext=1
\definecolor{{accent}}{{HTML}}{{{accent}}}
\definecolor{{companion}}{{HTML}}{{{companion}}}
\definecolor{{paper}}{{HTML}}{{F4EFE3}}
\hypersetup{{hidelinks,pdftitle={{{title_main}}},pdfauthor={{LazyingArt}}}}
\pagestyle{{fancy}}
\fancyhf{{}}
\fancyhead[L]{{\sffamily\footnotesize\color{{accent}} {title_main}}}
\fancyfoot[C]{{\sffamily\footnotesize\thepage}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{5pt}}
\titleformat{{\section}}{{\sffamily\bfseries\LARGE\color{{accent}}}}{{\thesection}}{{0.55em}}{{}}
\newenvironment{{sourceblock}}{{\par\vspace{{5pt}}\noindent\color{{accent}}\rule{{\linewidth}}{{0.35pt}}\vspace{{5pt}}}}{{\vspace{{7pt}}}}
\newcommand{{\MainText}}[1]{{{{\fontsize{{13}}{{18}}\selectfont #1\par}}}}
\newcommand{{\CommentText}}[1]{{{{\fontsize{{10.5}}{{15}}\selectfont\color{{companion}} #1\par}}}}
\newcommand{{\SourceLine}}[1]{{{{\sffamily\fontsize{{6.8}}{{8.2}}\selectfont\color{{gray}} #1\par}}}}
\newcommand{{\ChapterCompanion}}[1]{{{{\sffamily\large\color{{companion}} #1\par\vspace{{8pt}}}}}}
\begin{{document}}
\begin{{titlepage}}
\centering
\includegraphics[width=2.55in,height=3.82in]{{cover.png}}\\[0.28in]
{{\sffamily\bfseries\fontsize{{23}}{{28}}\selectfont\color{{accent}} {title_main}\par}}
\vspace{{0.12in}}
{{\sffamily\fontsize{{13}}{{17}}\selectfont\color{{companion}} {title_comment}\par}}
\vspace{{0.18in}}
{{\small {subtitle}\par}}
\vfill
{{\sffamily\small Project-owned source-aware specimen · {variant}\par}}
\end{{titlepage}}
\tableofcontents
\clearpage
{''.join(chapters)}
\clearpage
\section*{{Specimen boundary}}
This packet demonstrates a short, project-owned source-to-PDF/EPUB workflow. It is not customer work, a translation benchmark, a marketplace approval, or proof of complete-book delivery. Translation, substantive editing, cover commissions, ISBNs, platform uploads, printing, and a complete manuscript require a separate scope.

\vspace{{1em}}
\textbf{{Rights.}} Sample text, companion text, cover geometry, and artifacts: CC BY 4.0. Build code: MIT.

\textbf{{Source.}} Every rendered paragraph carries the stable ID and JSON location used to rebuild it.
\end{{document}}
"""


def build_pdf(book: dict[str, Any], main_language: str, variant: str) -> Path:
    stem_language = "en-main" if main_language == "en" else "zh-main"
    target = ARTIFACTS / f"book-specimen-{stem_language}-{variant}.pdf"
    with tempfile.TemporaryDirectory(prefix="book-specimen-pdf-") as raw:
        work = Path(raw)
        (work / "book.tex").write_text(render_tex(book, main_language, variant), encoding="utf-8")
        shutil.copyfile(COVER_PATH, work / "cover.png")
        env = os.environ.copy()
        env.update({"SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH, "TZ": "UTC"})
        for _ in range(2):
            run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "book.tex"], cwd=work, env=env)
        shutil.copyfile(work / "book.pdf", target)
    run(["qpdf", "--check", str(target)])
    with tempfile.TemporaryDirectory(prefix="book-specimen-text-") as raw:
        extracted = Path(raw) / "book.txt"
        run(["pdftotext", str(target), str(extracted)])
        text = extracted.read_text(encoding="utf-8")
        if "usable book" not in text or "separate scope" not in text:
            raise BuildError(f"{target.name} failed text-survival checks")
    return target


def xhtml_document(title: str, body: str, language: str = "en") -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{language}" xml:lang="{language}">
<head><title>{html.escape(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>{body}</body>
</html>
"""


def epub_entries(book: dict[str, Any]) -> dict[str, bytes]:
    title = html.escape(book["title"]["en"])
    title_zh = html.escape(book["title"]["zh-Hant"])
    nav_items = []
    manifest_items = []
    spine_items = []
    entries: dict[str, bytes] = {
        "META-INF/container.xml": b'''<?xml version="1.0" encoding="UTF-8"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>\n''',
        "OEBPS/style.css": b'''body{font-family:serif;line-height:1.55;margin:5%;color:#202824}h1,h2{font-family:sans-serif;color:#1b6b5e}.companion{color:#7d5342}.source{font-family:monospace;font-size:.68em;color:#666}.block{border-top:1px solid #1b6b5e;margin:1.4em 0;padding-top:.7em}.cover{text-align:center}.cover img{max-width:72%;height:auto}.rights{font-size:.85em;color:#555}\n''',
        "OEBPS/cover.png": COVER_PATH.read_bytes(),
    }
    cover_body = (
        f'<main class="cover"><img src="cover.png" alt="Abstract textless specimen cover"/>'
        f"<h1>{title}</h1><p class=\"companion\" lang=\"zh-Hant\">{title_zh}</p>"
        "<p>Project-owned source-aware specimen</p></main>"
    )
    entries["OEBPS/cover.xhtml"] = xhtml_document(book["title"]["en"], cover_body).encode("utf-8")
    manifest_items.append('<item id="cover-page" href="cover.xhtml" media-type="application/xhtml+xml"/>')
    spine_items.append('<itemref idref="cover-page"/>')

    for index, chapter in enumerate(book["chapters"], 1):
        filename = f"chapter-{index}.xhtml"
        item_id = f"chapter-{index}"
        nav_items.append(f'<li><a href="{filename}">{html.escape(chapter["title"]["en"])}</a></li>')
        manifest_items.append(f'<item id="{item_id}" href="{filename}" media-type="application/xhtml+xml"/>')
        spine_items.append(f'<itemref idref="{item_id}"/>')
        blocks = []
        for paragraph in chapter["paragraphs"]:
            blocks.append(
                f'<section class="block" id="{paragraph["id"]}">'
                f'<p lang="en">{html.escape(paragraph["main"]["text"])}</p>'
                f'<p class="companion" lang="zh-Hant">{html.escape(paragraph["comment"]["text"])}</p>'
                f'<p class="source">{html.escape(paragraph["id"] + " · " + paragraph["source_location"])}</p>'
                "</section>"
            )
        body = (
            f'<main><h1>{html.escape(chapter["title"]["en"])}</h1>'
            f'<h2 class="companion" lang="zh-Hant">{html.escape(chapter["title"]["zh-Hant"])}</h2>'
            + "".join(blocks)
            + "</main>"
        )
        entries[f"OEBPS/{filename}"] = xhtml_document(chapter["title"]["en"], body).encode("utf-8")

    nav_body = f'<nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops"><h1>Contents</h1><ol>{"".join(nav_items)}</ol></nav>'
    entries["OEBPS/nav.xhtml"] = xhtml_document("Contents", nav_body).encode("utf-8")
    package = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="book-id" version="3.0" xml:lang="en">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="book-id">urn:lazyingart:source-aware-book-specimen:v1</dc:identifier><dc:title>{title}</dc:title><dc:creator>LazyingArt</dc:creator><dc:language>en</dc:language><dc:language>zh-Hant</dc:language><dc:rights>CC BY 4.0</dc:rights><meta property="dcterms:modified">2026-09-07T00:00:00Z</meta></metadata>
<manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="style" href="style.css" media-type="text/css"/><item id="cover-image" href="cover.png" media-type="image/png" properties="cover-image"/>{''.join(manifest_items)}</manifest>
<spine>{''.join(spine_items)}</spine>
</package>
'''
    entries["OEBPS/content.opf"] = package.encode("utf-8")
    return entries


def add_zip_bytes(archive: zipfile.ZipFile, name: str, payload: bytes, *, stored: bool = False) -> None:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
    archive.writestr(info, payload)


def build_epub(book: dict[str, Any]) -> Path:
    target = ARTIFACTS / "book-specimen.epub"
    entries = epub_entries(book)
    with zipfile.ZipFile(target, "w") as archive:
        add_zip_bytes(archive, "mimetype", b"application/epub+zip", stored=True)
        for name in sorted(entries):
            add_zip_bytes(archive, name, entries[name])
    validate_epub(target)
    return target


def validate_epub(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise BuildError("EPUB ZIP integrity failed")
        infos = archive.infolist()
        if not infos or infos[0].filename != "mimetype" or infos[0].compress_type != zipfile.ZIP_STORED:
            raise BuildError("EPUB mimetype must be first and uncompressed")
        names = {info.filename for info in infos}
        required = {
            "META-INF/container.xml",
            "OEBPS/content.opf",
            "OEBPS/nav.xhtml",
            "OEBPS/cover.xhtml",
            "OEBPS/cover.png",
            "OEBPS/chapter-1.xhtml",
            "OEBPS/chapter-2.xhtml",
            "OEBPS/chapter-3.xhtml",
        }
        if not required.issubset(names):
            raise BuildError("EPUB package is incomplete")
        for name in sorted(required - {"OEBPS/cover.png"}):
            ET.fromstring(archive.read(name))
        nav = archive.read("OEBPS/nav.xhtml").decode("utf-8")
        for index in range(1, 4):
            if f'href="chapter-{index}.xhtml"' not in nav:
                raise BuildError("EPUB navigation has a missing chapter link")
        combined = "".join(archive.read(f"OEBPS/chapter-{index}.xhtml").decode("utf-8") for index in range(1, 4))
        for paragraph_id in (f"p-{index:03d}" for index in range(1, 7)):
            if f'id="{paragraph_id}"' not in combined:
                raise BuildError(f"EPUB is missing {paragraph_id}")


def write_supporting_artifacts(book: dict[str, Any], pdfs: list[Path], epub: Path) -> None:
    style_sheet = """# Specimen style sheet

- Trim: 6 × 9 inches; large-font profile.
- Directions: English main / Traditional Chinese companion and the reverse.
- Variants: colour and black-and-white.
- Main paragraphs: 13 pt with 18 pt leading.
- Companion paragraphs: 10.5 pt with 15 pt leading.
- Each rendered paragraph shows its stable paragraph ID and JSON location.
- Reflowable EPUB uses stacked language blocks rather than shrinking two fixed columns.
- Noto Serif and Noto Sans are selected for readable cross-script coverage.
- Colour is supplementary; hierarchy and labels remain legible in black-and-white.
- Project-owned text and artifacts: CC BY 4.0. Build code: MIT.
"""
    (ARTIFACTS / "style-sheet.md").write_text(style_sheet, encoding="utf-8")

    source_hash = sha256(BOOK_PATH)
    chunks = []
    for chapter in book["chapters"]:
        for paragraph in chapter["paragraphs"]:
            chunks.append(
                {
                    "id": paragraph["id"],
                    "chapter_id": chapter["id"],
                    "source": paragraph["source_location"],
                    "source_sha256": source_hash,
                    "languages": [paragraph["main"]["language"], paragraph["comment"]["language"]],
                    "status": paragraph["status"],
                    "pdf_locator": "visible stable ID beneath the rendered language pair",
                    "epub_locator": f"#{paragraph['id']}",
                }
            )
    write_json(
        ARTIFACTS / "source-ledger.json",
        {
            "schema": "source-aware-book-ledger/v1",
            "source": "source/book.json",
            "source_sha256": source_hash,
            "rights": book["rights"],
            "chunks": chunks,
        },
    )

    report = f"""# Validation report

Status: **PASS**

- Source schema: `source-aware-book-specimen/v1`
- Coverage: {len(book['chapters'])} chapters, {len(chunks)} reviewed paragraphs, 0 missing, 0 stale, 0 duplicate IDs
- Token reconstruction: English spaces preserved; Traditional Chinese token/readings preserved; normalized grammar roles only
- Cover: nonempty textless PNG used by all PDF variants and the EPUB
- PDF: {len(pdfs)} large-font 6 × 9 variants; `qpdf --check` and `pdftotext` survival checks passed
- EPUB: mimetype order/compression, ZIP integrity, container, package XML, navigation links, cover, three chapters, and all six paragraph anchors passed
- Variants: English-main and Chinese-main, each in colour and black-and-white
- Rebuild: deterministic artifact and packet hashes are recorded in `SHA256SUMS`

## Honest boundary

This is a short project-owned workflow specimen. It is not customer work, an independent translation review, a linguistic benchmark, a KDP/IngramSpark approval, a printer proof, or evidence of a 230,000-word rush delivery. Translation, substantive editing, commissioned cover design, ISBNs, marketplace upload, printing, and complete-book production require a separate reviewed scope.
"""
    (ARTIFACTS / "validation-report.md").write_text(report, encoding="utf-8")


def write_manifest_and_packet(book: dict[str, Any]) -> None:
    artifact_names = [
        "book-specimen-en-main-color.pdf",
        "book-specimen-en-main-blackwhite.pdf",
        "book-specimen-zh-main-color.pdf",
        "book-specimen-zh-main-blackwhite.pdf",
        "book-specimen.epub",
        "style-sheet.md",
        "source-ledger.json",
        "validation-report.md",
    ]
    manifest = {
        "schema": "source-aware-book-specimen-manifest/v1",
        "status": "project_owned_process_evidence",
        "book_id": book["book_id"],
        "source": {
            "path": "source/book.json",
            "sha256": sha256(BOOK_PATH),
            "chapters": 3,
            "reviewed_paragraphs": 6,
            "languages": book["languages"],
            "third_party_content": False,
        },
        "cover": {
            "path": "source/cover.png",
            "sha256": sha256(COVER_PATH),
            "textless": True,
            "used_by": ["all PDF variants", "EPUB"],
        },
        "outputs": [
            {"path": f"artifacts/{name}", "sha256": sha256(ARTIFACTS / name)}
            for name in artifact_names
        ],
        "validation": {
            "source_coverage": "pass",
            "pdf_qpdf": "pass",
            "pdf_text_survival": "pass",
            "epub_structure_and_links": "pass",
            "directions": ["en-main", "zh-main"],
            "variants": ["color", "blackwhite"],
        },
        "exclusions": [
            "customer result",
            "independent translation review",
            "linguistic benchmark",
            "KDP or IngramSpark approval",
            "printer proof",
            "complete-book or rush-delivery proof",
        ],
    }
    write_json(ARTIFACTS / "manifest.json", manifest)

    checksum_paths = [BOOK_PATH, COVER_PATH] + [ARTIFACTS / name for name in artifact_names] + [ARTIFACTS / "manifest.json"]
    lines = [f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}" for path in checksum_paths]
    (ARTIFACTS / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")

    packet = ARTIFACTS / "source-aware-book-specimen.zip"
    packet_files = [
        ROOT / "README.md",
        ROOT / "LICENSE-SAMPLE.md",
        ROOT / "build.py",
        BOOK_PATH,
        COVER_PATH,
        *[ARTIFACTS / name for name in artifact_names],
        ARTIFACTS / "manifest.json",
        ARTIFACTS / "SHA256SUMS",
    ]
    with zipfile.ZipFile(packet, "w") as archive:
        for path in sorted(packet_files, key=lambda item: item.relative_to(ROOT).as_posix()):
            add_zip_bytes(archive, path.relative_to(ROOT).as_posix(), path.read_bytes())
    digest_file = ARTIFACTS / "source-aware-book-specimen.zip.sha256"
    digest_file.write_text(f"{sha256(packet)}  {packet.name}\n", encoding="utf-8")


def verify_checksums_and_packet() -> None:
    for line in (ARTIFACTS / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        if sha256(ROOT / relative) != digest:
            raise BuildError(f"checksum drift for {relative}")
    packet = ARTIFACTS / "source-aware-book-specimen.zip"
    expected = (ARTIFACTS / "source-aware-book-specimen.zip.sha256").read_text(encoding="utf-8").split()[0]
    if sha256(packet) != expected:
        raise BuildError("delivery packet checksum drift")
    with zipfile.ZipFile(packet) as archive:
        if archive.testzip() is not None:
            raise BuildError("delivery packet ZIP integrity failed")


def main() -> int:
    for command in ("xelatex", "qpdf", "pdftotext"):
        if shutil.which(command) is None:
            raise BuildError(f"required open-source command is unavailable: {command}")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    book = load_and_validate()
    build_cover(COVER_PATH)
    pdfs = [build_pdf(book, language, variant) for language, variant in PDF_VARIANTS]
    epub = build_epub(book)
    write_supporting_artifacts(book, pdfs, epub)
    write_manifest_and_packet(book)
    verify_checksums_and_packet()
    print(
        json.dumps(
            {
                "status": "pass",
                "pdfs": len(pdfs),
                "epub": epub.name,
                "reviewed_paragraphs": 6,
                "packet_sha256": sha256(ARTIFACTS / "source-aware-book-specimen.zip"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
