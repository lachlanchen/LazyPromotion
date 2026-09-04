#!/usr/bin/env python3
"""Build a deterministic, synthetic scientific-PDF fit-sprint evidence set."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "artifacts"
BOUNDARY = (
    "Project-owned synthetic evidence; not a benchmark, customer result, "
    "scientific result, or paid delivery."
)
SOURCE_DATE_EPOCH = "1788480000"
REQUIRED_COMMANDS = ("pdflatex", "pdftotext", "pdfinfo")
PROVENANCE_FIELDS = (
    "document_id",
    "version_id",
    "pdf_page",
    "printed_page",
    "snippet",
    "extraction_method",
    "source_sha256",
)


class BuildError(RuntimeError):
    """Raised when the evidence set cannot be built safely and completely."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:
        name = Path(command[0]).name
        tail = "\n".join((exc.stdout or "").splitlines()[-12:])
        raise BuildError(f"{name} failed while building the synthetic sample\n{tail}") from exc
    return completed.stdout


def toolchain() -> dict[str, str]:
    resolved: dict[str, str] = {}
    for name in REQUIRED_COMMANDS:
        executable = shutil.which(name)
        if not executable:
            raise BuildError(f"required local tool is unavailable: {name}")
        resolved[name] = executable
    return {
        "pdflatex": run([resolved["pdflatex"], "--version"]).splitlines()[0],
        "pdftotext": run([resolved["pdftotext"], "-v"]).splitlines()[0],
        "pdfinfo": run([resolved["pdfinfo"], "-v"]).splitlines()[0],
        "sqlite": sqlite3.sqlite_version,
        "pipeline": "lkt-scientific-pdf-fit-v1",
    }


def compile_pdf(source: Path, build_directory: Path, environment: dict[str, str]) -> Path:
    build_directory.mkdir(parents=True, exist_ok=True)
    run(
        [
            shutil.which("pdflatex") or "pdflatex",
            "-halt-on-error",
            "-interaction=nonstopmode",
            f"-output-directory={build_directory}",
            str(source),
        ],
        cwd=ROOT,
        env=environment,
    )
    result = build_directory / f"{source.stem}.pdf"
    if not result.is_file() or not result.read_bytes().startswith(b"%PDF-"):
        raise BuildError(f"pdflatex did not produce a valid PDF for {source.name}")
    return result


def page_count(pdf: Path) -> int:
    output = run([shutil.which("pdfinfo") or "pdfinfo", str(pdf)])
    match = re.search(r"^Pages:\s+(\d+)\s*$", output, re.MULTILINE)
    if not match:
        raise BuildError(f"pdfinfo did not expose a page count for {pdf.name}")
    return int(match.group(1))


def extract_pages(pdf: Path, count: int, directory: Path) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    pages: list[str] = []
    for number in range(1, count + 1):
        destination = directory / f"{pdf.stem}-page-{number}.txt"
        run(
            [
                shutil.which("pdftotext") or "pdftotext",
                "-f",
                str(number),
                "-l",
                str(number),
                "-layout",
                "-enc",
                "UTF-8",
                str(pdf),
                str(destination),
            ]
        )
        pages.append(destination.read_text(encoding="utf-8"))
    return pages


def fts_expression(terms: list[str]) -> str:
    if not terms or not all(isinstance(term, str) and term.strip() for term in terms):
        raise BuildError("every question must have non-empty lexical terms")
    return " AND ".join(f'"{term.strip().replace(chr(34), chr(34) * 2)}"' for term in terms)


def snippet(text: str, terms: list[str], limit: int = 360) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    lowered = compact.casefold()
    positions = [lowered.find(term.casefold()) for term in terms]
    positions = [position for position in positions if position >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - 90)
    end = min(len(compact), start + limit)
    return ("…" if start else "") + compact[start:end].strip() + ("…" if end < len(compact) else "")


def citation(row: sqlite3.Row, terms: list[str], hashes: dict[str, str]) -> dict[str, Any]:
    return {
        "document_id": row["document_id"],
        "version_id": row["version_id"],
        "pdf_page": row["pdf_page"],
        "printed_page": row["pdf_page"],
        "snippet": snippet(row["page_text"], terms),
        "extraction_method": "pdftotext -layout",
        "source_sha256": hashes[row["input_id"]],
    }


def build_index(records: list[dict[str, Any]], database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE pages (
          row_id INTEGER PRIMARY KEY,
          input_id TEXT NOT NULL,
          document_id TEXT NOT NULL,
          version_id TEXT NOT NULL,
          pdf_page INTEGER NOT NULL,
          page_text TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE pages_fts USING fts5(
          input_id UNINDEXED,
          document_id UNINDEXED,
          version_id UNINDEXED,
          pdf_page UNINDEXED,
          page_text,
          content='pages',
          content_rowid='row_id',
          tokenize='unicode61 remove_diacritics 2'
        );
        """
    )
    for record in records:
        if record["duplicate_of"]:
            continue
        for page_number, page_text in enumerate(record["pages"], 1):
            connection.execute(
                "INSERT INTO pages(input_id, document_id, version_id, pdf_page, page_text) VALUES (?, ?, ?, ?, ?)",
                (
                    record["input_id"],
                    record["document_id"],
                    record["version_id"],
                    page_number,
                    page_text,
                ),
            )
    connection.execute("INSERT INTO pages_fts(pages_fts) VALUES ('rebuild')")
    connection.commit()
    return connection


def evaluate_questions(
    connection: sqlite3.Connection,
    questions: list[dict[str, Any]],
    hashes: dict[str, str],
) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    for question in questions:
        terms = question["terms"]
        rows = connection.execute(
            """
            SELECT pages.*, bm25(pages_fts) AS rank
            FROM pages_fts JOIN pages ON pages.row_id = pages_fts.rowid
            WHERE pages_fts MATCH ?
            ORDER BY rank, pages.row_id
            LIMIT 5
            """,
            (fts_expression(terms),),
        ).fetchall()
        results = [citation(row, terms, hashes) for row in rows]
        expected = question.get("expected")
        accepted = None
        if expected:
            accepted = next(
                (
                    result
                    for result in results
                    if all(result[field] == expected[field] for field in ("document_id", "version_id", "pdf_page"))
                ),
                None,
            )
            status = "hit" if accepted else "miss"
        else:
            status = "expected_no_match" if not results else "unexpected_match"
        observations.append(
            {
                "id": question["id"],
                "query": question["query"],
                "expected": expected,
                "intended_lexical_miss": bool(question.get("intended_lexical_miss")),
                "status": status,
                "accepted_result": accepted,
                "top_results": results,
            }
        )
    summary = {
        "questions": len(observations),
        "expected_hits": sum(item["expected"] is not None for item in observations),
        "hits": sum(item["status"] == "hit" for item in observations),
        "misses": sum(item["status"] == "miss" for item in observations),
        "expected_no_match": sum(item["status"] == "expected_no_match" for item in observations),
        "unexpected_matches": sum(item["status"] == "unexpected_match" for item in observations),
    }
    return {"boundary": BOUNDARY, "summary": summary, "questions": observations}


def render_browser_card(question: dict[str, Any]) -> str:
    result = question["accepted_result"]
    if not result:
        raise BuildError("the selected browser-card question has no accepted result")
    escaped = {key: html.escape(str(value)) for key, value in result.items()}
    query = html.escape(question["query"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Synthetic scientific-PDF citation card</title>
<style>
:root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #07111f; color: #edf5ff; }}
main {{ width: min(820px, calc(100vw - 48px)); border: 1px solid #315477; border-radius: 20px; padding: 30px; background: #0c1b2d; box-shadow: 0 24px 80px #0008; }}
.boundary {{ color: #ffd27a; font-size: .86rem; letter-spacing: .02em; }}
h1 {{ margin: 10px 0 24px; font-size: 1.65rem; }}
.query {{ padding: 14px 16px; border-left: 4px solid #58c7ff; background: #102943; }}
blockquote {{ margin: 24px 0; color: #dcecff; line-height: 1.55; }}
dl {{ display: grid; grid-template-columns: 170px 1fr; gap: 8px 18px; font-size: .92rem; }}
dt {{ color: #87b4d9; }} dd {{ margin: 0; overflow-wrap: anywhere; }}
</style>
</head>
<body>
<main data-proof="synthetic-project-owned">
  <div class="boundary">{html.escape(BOUNDARY)}</div>
  <h1>Local lexical result with checkable citation</h1>
  <div class="query"><strong>Query:</strong> {query}</div>
  <blockquote>{escaped['snippet']}</blockquote>
  <dl>
    <dt>Document</dt><dd>{escaped['document_id']}</dd>
    <dt>Version</dt><dd>{escaped['version_id']}</dd>
    <dt>PDF / printed page</dt><dd>{escaped['pdf_page']} / {escaped['printed_page']}</dd>
    <dt>Extraction</dt><dd>{escaped['extraction_method']}</dd>
    <dt>Source SHA-256</dt><dd>{escaped['source_sha256']}</dd>
    <dt>Generated context</dt><dd>None. This card displays retrieved synthetic source text.</dd>
  </dl>
</main>
</body>
</html>
"""


def render_report(
    source_ledger: dict[str, Any],
    extraction_ledger: dict[str, Any],
    retrieval: dict[str, Any],
    citation_check: dict[str, Any],
) -> str:
    summary = retrieval["summary"]
    weaknesses = sorted(
        {
            weakness
            for item in extraction_ledger["documents"]
            for weakness in item["declared_weaknesses"]
        }
    )
    weakness_text = "\n".join(f"- {item}." for item in weaknesses)
    return f"""# Synthetic scientific-PDF collection-fit report

> **Evidence boundary:** {BOUNDARY}

## Decision summary

**GO for the bounded local lexical and citation proof.** The sample preserves
four input records, recognizes one exact duplicate, retains the two versions in
one version family, extracts three-page born-digital PDFs locally, and resolves
each accepted result to its source version and page.

**NO-GO for OCR, a whole-collection migration, semantic-retrieval claims, a
knowledge graph, or production deployment.** Those decisions require an
authorized representative sample and owner-defined acceptance criteria.

## 1. Data, privacy, and citation map

```text
project-owned synthetic TeX
  -> deterministic local PDF
  -> SHA-256 source ledger and duplicate/version-family map
  -> page-bounded pdftotext extraction
  -> local SQLite FTS5 baseline
  -> retrieved snippet + document/version/page/method/hash
  -> static browser citation card
```

- Input records: **{len(source_ledger['documents'])}**.
- Canonical PDFs searched: **{sum(not item['duplicate_of'] for item in source_ledger['documents'])}**.
- Exact duplicate groups: **{len(source_ledger['exact_duplicate_groups'])}**.
- Multilingual input present: **yes** (English, Simplified Chinese, Japanese).
- Network, model, embedding, graph, and customer-data use: **none**.

## 2. Extraction and retrieval evidence

- Fixed questions: **{summary['questions']}**.
- Expected hits: **{summary['expected_hits']}**; observed hits: **{summary['hits']}**.
- Recorded lexical misses: **{summary['misses']}**.
- Expected no-match checks: **{summary['expected_no_match']}**.
- Unexpected matches: **{summary['unexpected_matches']}**.
- Accepted citation records checked: **{citation_check['accepted_results_checked']}**.
- Missing provenance fields: **{citation_check['missing_provenance_fields']}**.

The saved miss for “instrument warm-up procedure” is intentional: the source
says “thermal stabilization,” showing a vocabulary mismatch that exact lexical
search does not solve. It is evidence for reviewing a semantic layer, not proof
that a semantic method would improve a real collection.

## 3. Explicit extraction weaknesses

{weakness_text}

The page text is sufficient for this fixed demonstration, but character
presence does not prove equation structure, table reading order, translation
quality, or semantic relationships. Open the cited PDF page when those details
matter.

## 4. Representative browser proof

[`browser-card.html`](browser-card.html) displays one accepted result and the
same document ID, version, PDF/printed page, extraction method, and source hash
recorded in the retrieval ledger. It includes no generated answer.

## 5. What this says about the USD 250 sprint

This executed synthetic example shows the shape of the three bounded
deliverables: a data/privacy/citation map, a small browser proof, and a written
go/no-go boundary. It does not show customer work, establish performance on a
300- or 17,000-PDF library, authorize source reuse, or create a lead, sale, or
revenue event.
"""


def install_artifacts(staging: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for source in sorted(staging.iterdir()):
        if not source.is_file():
            continue
        temporary = output / f".{source.name}.tmp"
        shutil.copyfile(source, temporary)
        os.replace(temporary, output / source.name)


def build(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    tools = toolchain()
    collection = json.loads((ROOT / "collection.json").read_text(encoding="utf-8"))
    question_source = json.loads((ROOT / "questions.json").read_text(encoding="utf-8"))
    sources = collection.get("sources")
    questions = question_source.get("questions")
    if not isinstance(sources, list) or not isinstance(questions, list):
        raise BuildError("collection.json and questions.json must contain lists")
    if collection.get("boundary") != BOUNDARY or len(questions) != 20:
        raise BuildError("the synthetic evidence boundary or fixed 20-question set changed")

    environment = os.environ.copy()
    environment.update(
        {
            "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH,
            "FORCE_SOURCE_DATE": "1",
            "TZ": "UTC",
        }
    )
    with tempfile.TemporaryDirectory(prefix="lazypromotion-scientific-pdf-") as raw_temp:
        temporary = Path(raw_temp)
        staging = temporary / "artifacts"
        staging.mkdir()
        built_by_source: dict[str, Path] = {}
        records: list[dict[str, Any]] = []

        for item in sources:
            source = ROOT / item["source"]
            if not source.is_file():
                raise BuildError(f"declared source is unavailable: {item['source']}")
            source_key = item["source"]
            if source_key not in built_by_source:
                built_by_source[source_key] = compile_pdf(
                    source,
                    temporary / "tex" / source.stem,
                    environment,
                )
            destination = staging / item["output"]
            shutil.copyfile(built_by_source[source_key], destination)
            count = page_count(destination)
            pages = extract_pages(destination, count, temporary / "text")
            records.append({**item, "pdf": destination, "page_count": count, "pages": pages})

        hashes = {item["input_id"]: sha256(item["pdf"]) for item in records}
        hash_groups: dict[str, list[str]] = defaultdict(list)
        for item in records:
            hash_groups[hashes[item["input_id"]]].append(item["input_id"])
        duplicate_groups = [sorted(group) for group in hash_groups.values() if len(group) > 1]
        if duplicate_groups != [["prism-v1", "prism-v1-copy"]]:
            raise BuildError("the sample must contain exactly the declared duplicate pair")

        family_versions: dict[str, set[str]] = defaultdict(set)
        for item in records:
            family_versions[item["version_family"]].add(item["version_id"])
        if family_versions["adaptive-prism-calibration"] != {"v1", "v2"}:
            raise BuildError("the adaptive-prism v1/v2 version family is incomplete")
        if not any(len(item["languages"]) > 1 for item in records):
            raise BuildError("the multilingual source is missing")

        source_ledger = {
            "boundary": BOUNDARY,
            "exact_duplicate_groups": duplicate_groups,
            "version_families": {
                family: sorted(versions) for family, versions in sorted(family_versions.items())
            },
            "documents": [
                {
                    "input_id": item["input_id"],
                    "document_id": item["document_id"],
                    "version_id": item["version_id"],
                    "version_family": item["version_family"],
                    "source_file": item["output"],
                    "source_sha256": hashes[item["input_id"]],
                    "source_tex_sha256": sha256(ROOT / item["source"]),
                    "bytes": item["pdf"].stat().st_size,
                    "page_count": item["page_count"],
                    "duplicate_of": item["duplicate_of"],
                    "languages": item["languages"],
                    "rights": "project-owned synthetic source",
                }
                for item in records
            ],
        }
        write_json(staging / "source-ledger.json", source_ledger)

        extraction_ledger = {
            "boundary": BOUNDARY,
            "method": "pdftotext -layout",
            "documents": [
                {
                    "input_id": item["input_id"],
                    "document_id": item["document_id"],
                    "version_id": item["version_id"],
                    "page_count": item["page_count"],
                    "page_character_counts": [len(page) for page in item["pages"]],
                    "page_text_sha256": [hashlib.sha256(page.encode("utf-8")).hexdigest() for page in item["pages"]],
                    "document_classes": item["document_classes"],
                    "declared_weaknesses": item["declared_weaknesses"],
                }
                for item in records
            ],
        }
        write_json(staging / "extraction-ledger.json", extraction_ledger)

        connection = build_index(records, temporary / "pages.sqlite3")
        try:
            retrieval = evaluate_questions(connection, questions, hashes)
        finally:
            connection.close()
        summary = retrieval["summary"]
        if summary != {
            "questions": 20,
            "expected_hits": 17,
            "hits": 16,
            "misses": 1,
            "expected_no_match": 3,
            "unexpected_matches": 0,
        }:
            missed = [item["id"] for item in retrieval["questions"] if item["status"] == "miss"]
            raise BuildError(
                f"the fixed retrieval acceptance counts changed: {summary}; "
                f"missed questions: {', '.join(missed)}"
            )
        write_json(staging / "retrieval-ledger.json", retrieval)

        accepted = [
            item["accepted_result"] for item in retrieval["questions"] if item["accepted_result"]
        ]
        missing = sum(
            not result.get(field)
            for result in accepted
            for field in PROVENANCE_FIELDS
        )
        citation_check = {
            "boundary": BOUNDARY,
            "accepted_results_checked": len(accepted),
            "required_fields": list(PROVENANCE_FIELDS),
            "missing_provenance_fields": missing,
            "all_pages_within_source_bounds": all(
                1 <= result["pdf_page"] <= next(
                    item["page_count"]
                    for item in source_ledger["documents"]
                    if item["document_id"] == result["document_id"]
                    and item["version_id"] == result["version_id"]
                    and not item["duplicate_of"]
                )
                for result in accepted
            ),
            "all_source_hashes_resolve": all(
                result["source_sha256"]
                in {item["source_sha256"] for item in source_ledger["documents"]}
                for result in accepted
            ),
            "passed": False,
        }
        citation_check["passed"] = bool(
            accepted
            and not missing
            and citation_check["all_pages_within_source_bounds"]
            and citation_check["all_source_hashes_resolve"]
        )
        if not citation_check["passed"]:
            raise BuildError("the accepted citation records did not pass provenance checks")
        write_json(staging / "citation-check.json", citation_check)

        card_question = next(item for item in retrieval["questions"] if item["id"] == "q04")
        (staging / "browser-card.html").write_text(
            render_browser_card(card_question), encoding="utf-8"
        )
        (staging / "fit-report.md").write_text(
            render_report(source_ledger, extraction_ledger, retrieval, citation_check),
            encoding="utf-8",
        )

        source_paths = [ROOT / "build.py", ROOT / "collection.json", ROOT / "questions.json"] + sorted(
            (ROOT / "source").glob("*.tex")
        )
        artifact_paths = sorted(path for path in staging.iterdir() if path.name != "manifest.json")
        manifest = {
            "boundary": BOUNDARY,
            "source_sha256": {
                str(path.relative_to(ROOT)): sha256(path) for path in source_paths
            },
            "artifact_sha256": {path.name: sha256(path) for path in artifact_paths},
            "manifest_self_hashed": False,
            "toolchain": tools,
            "verification": {
                "fixed_questions": 20,
                "hits": 16,
                "recorded_misses": 1,
                "expected_no_match": 3,
                "exact_duplicate_groups": 1,
                "adaptive_prism_versions": ["v1", "v2"],
                "multilingual_source": True,
                "citation_check": "passed",
                "network_used": False,
                "customer_data_used": False,
            },
        }
        write_json(staging / "manifest.json", manifest)
        install_artifacts(staging, output)
        return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        manifest = build(args.output_dir.resolve())
    except (BuildError, OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(args.output_dir.resolve()),
                "verification": manifest["verification"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
