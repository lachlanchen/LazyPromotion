# Validation report

Status: **PASS**

- Source schema: `source-aware-book-specimen/v1`
- Coverage: 3 chapters, 6 reviewed paragraphs, 0 missing, 0 stale, 0 duplicate IDs
- Token reconstruction: English spaces preserved; Traditional Chinese token/readings preserved; normalized grammar roles only
- Cover: nonempty textless PNG used by all PDF variants and the EPUB
- PDF: 4 large-font 6 × 9 variants; `qpdf --check` and `pdftotext` survival checks passed
- EPUB: mimetype order/compression, ZIP integrity, container, package XML, navigation links, cover, three chapters, and all six paragraph anchors passed
- Variants: English-main and Chinese-main, each in colour and black-and-white
- Rebuild: deterministic artifact and packet hashes are recorded in `SHA256SUMS`

## Honest boundary

This is a short project-owned workflow specimen. It is not customer work, an independent translation review, a linguistic benchmark, a KDP/IngramSpark approval, a printer proof, or evidence of a 230,000-word rush delivery. Translation, substantive editing, commissioned cover design, ISBNs, marketplace upload, printing, and complete-book production require a separate reviewed scope.
