# Reproducible LaTeX redline sample

This project-owned synthetic pair demonstrates the three builds behind an editor-readable revision package:

1. a frozen baseline;
2. a clean revision;
3. a redline generated from those exact sources.

It contains no customer manuscript and no scientific result. The source change is intentionally small enough to inspect in the clean and redline PDFs.

## Build

The checked sample uses the official `latexdiff` `1.4.0` tag at commit `57d0ec532c41eb73645804d7f67667336da8bd01`.

```bash
LATEXDIFF_BIN=/path/to/latexdiff-1.4.0 ./build.sh
```

The script builds both sources independently, generates the redline, compiles it with the same local TeX environment, rejects LaTeX errors and undefined references, checks representative PDF text, and records source, tool, and PDF hashes.

Current evidence lives under `artifacts/`:

- `baseline.pdf`
- `revision.pdf`
- `redline.pdf`
- `redline.tex`
- three final-pass LaTeX logs
- `manifest.json`
- `delivery-manifest.json`
- `sample-delivery.zip` and its SHA-256 checksum

The downloadable packet also includes a concise synthetic issue ledger and a
delivery index mapping each promised output to its source, PDF, log, and
manifest. Rebuild it from the checked artifacts with:

```bash
python3 package_sample.py
sha256sum -c artifacts/sample-delivery.zip.sha256
```

Read [Both LaTeX Versions Compile, but the Latexdiff File Does Not](https://blog.lazying.art/html/computer_internet/3784/latex-latexdiff-redline-compiles-overleaf.html) for the reasoning behind the workflow. The maintained [paper revision skill](https://github.com/lachlanchen/paper-revision-skill) covers larger manuscripts, response locations, and plan-gated edits.

## Boundary

This sample proves a small build path only. It does not prove scientific correctness, journal compliance, confidential intake, customer delivery, or acceptance by an editor.
