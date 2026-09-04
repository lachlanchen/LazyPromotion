# Reproducible scientific-PDF fit-sprint sample

This project-owned synthetic collection executes the smallest evidence path
behind the USD 250 Local Knowledge Terminal collection-fit sprint:

1. retain source identity, one exact duplicate, and a v1/v2 family;
2. extract born-digital English, Chinese, and Japanese pages locally;
3. run a fixed 20-question SQLite FTS5 baseline;
4. attach every accepted result to a document, version, page, extraction
   method, snippet, and source hash;
5. render one static browser citation card and an evidence-backed go/no-go
   report.

Every source and artifact is synthetic and project-owned. This is not a
benchmark, customer result, scientific result, paid delivery, or claim about a
300- or 17,000-PDF collection.

## Build

The build uses only local `pdflatex`, `pdftotext`, `pdfinfo`, Python, and
SQLite. It performs no network request, model call, embedding, graph build, OCR,
or browser automation. Missing tools and changed acceptance counts fail before
the checked artifact set is replaced.

```bash
python examples/lkt-scientific-pdf-fit/build.py
```

Build twice into separate temporary directories and compare hashes when the
toolchain changes. The manifest records tool versions plus every source and
artifact hash, while deliberately excluding its own hash to avoid a cycle.

## Evidence

- [`fit-report.md`](artifacts/fit-report.md) gives the three sprint-shaped
  deliverables and explicit GO/NO-GO boundaries.
- [`source-ledger.json`](artifacts/source-ledger.json) records the exact
  duplicate, version families, languages, rights boundary, and PDF hashes.
- [`extraction-ledger.json`](artifacts/extraction-ledger.json) records per-page
  text hashes and known weaknesses.
- [`retrieval-ledger.json`](artifacts/retrieval-ledger.json) records all 20
  fixed queries, hits, misses, and checkable result payloads.
- [`citation-check.json`](artifacts/citation-check.json) validates the required
  provenance fields.
- [`browser-card.html`](artifacts/browser-card.html) is the static browser
  proof and contains no generated answer or external resource.
- [`manifest.json`](artifacts/manifest.json) makes the checked build auditable.

## Boundary

The sample supports a bounded born-digital extraction and lexical-search fit
decision only. It does not support claims about scanned PDFs, OCR, semantic
retrieval, graph quality, whole-collection performance, production deployment,
or customer outcomes.
