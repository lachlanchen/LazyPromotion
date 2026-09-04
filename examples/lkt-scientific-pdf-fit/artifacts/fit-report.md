# Synthetic scientific-PDF collection-fit report

> **Evidence boundary:** Project-owned synthetic evidence; not a benchmark, customer result, scientific result, or paid delivery.

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

- Input records: **4**.
- Canonical PDFs searched: **3**.
- Exact duplicate groups: **1**.
- Multilingual input present: **yes** (English, Simplified Chinese, Japanese).
- Network, model, embedding, graph, and customer-data use: **none**.

## 2. Extraction and retrieval evidence

- Fixed questions: **20**.
- Expected hits: **17**; observed hits: **16**.
- Recorded lexical misses: **1**.
- Expected no-match checks: **3**.
- Unexpected matches: **0**.
- Accepted citation records checked: **16**.
- Missing provenance fields: **0**.

The saved miss for “instrument warm-up procedure” is intentional: the source
says “thermal stabilization,” showing a vocabulary mismatch that exact lexical
search does not solve. It is evidence for reviewing a semantic layer, not proof
that a semantic method would improve a real collection.

## 3. Explicit extraction weaknesses

- an exact duplicate must be retained in the source ledger but excluded from retrieval.
- character extraction does not prove translation correctness.
- plain text loses typography, ruby, layout, and some relationship cues.
- plain-text extraction cannot prove table cell reading order.
- plain-text extraction linearizes mathematical notation.
- version-family detection is declared metadata rather than semantic proof.

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
