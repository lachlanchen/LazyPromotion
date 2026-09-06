# Source-aware book specimen

This is project-owned process evidence for a candidate LazyingArt book
production specimen. It turns six reviewed English–Traditional Chinese source
units into four large-font 6 × 9 PDF variants and one reflowable EPUB while
keeping stable paragraph IDs, source locations, readings, grammar roles,
review state, rights, and output hashes.

## Inspect the packet

- `source/book.json` — durable bilingual source with six stable paragraph IDs
- `source/cover.png` — generated textless cover art used by PDF and EPUB
- `artifacts/book-specimen-en-main-color.pdf`
- `artifacts/book-specimen-en-main-blackwhite.pdf`
- `artifacts/book-specimen-zh-main-color.pdf`
- `artifacts/book-specimen-zh-main-blackwhite.pdf`
- `artifacts/book-specimen.epub` — reflowable bilingual EPUB
- `artifacts/style-sheet.md` — the layout and language rules
- `artifacts/source-ledger.json` — source hash and exact output locators
- `artifacts/validation-report.md` — checks and honest boundaries
- `artifacts/manifest.json` and `artifacts/SHA256SUMS` — artifact inventory
- `artifacts/source-aware-book-specimen.zip` and `.sha256` — deterministic
  review packet

## Rebuild

Run:

```bash
python3 build.py
```

The build uses Python's standard library plus XeLaTeX, Noto Serif/Noto Sans,
`qpdf`, and `pdftotext`. It validates source coverage and token reconstruction,
compiles both language directions in colour and black-and-white, checks every
PDF, validates the EPUB package and links, writes hashes, and assembles the ZIP.

## Boundary

This is a short project-owned specimen, not customer work, a translation
benchmark, a KDP/IngramSpark approval, or proof of an urgent 230,000-word
delivery. A future paid specimen may accept one rights-cleared chapter only
after its input, correction, cancellation, refund, retention, and support terms
are live and reviewed. Translation, substantive editing, cover commissions,
ISBNs, platform uploads, printing, and complete-book production remain separate
scopes.
