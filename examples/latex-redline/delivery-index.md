# Synthetic manuscript delivery packet

This packet shows how the bounded Manuscript Build & Redline Sprint is handed
back. The manuscript is a one-page, project-owned synthetic example. It is not
customer work, a scientific result, a journal submission, or evidence of
publication.

## Deliverable map

| Promised deliverable | Files in this packet |
| --- | --- |
| Clean build | `sources/revision/main.tex`, `pdf/revision.pdf`, `logs/revision-final.log` |
| Template and issue check | `ISSUE_LEDGER.md`, `evidence/build-manifest.json`, `evidence/delivery-manifest.json` |
| Reproducible redline | `sources/baseline/main.tex`, `redline/redline.tex`, `pdf/baseline.pdf`, `pdf/redline.pdf`, `logs/baseline-final.log`, `logs/redline-final.log` |

The clean revision remains the source of truth. The generated redline is a
separate review artifact tied to the exact baseline and revision hashes.

## Inspect it

1. Read `ISSUE_LEDGER.md` for the compact build and review record.
2. Open `pdf/revision.pdf` and `pdf/redline.pdf` side by side.
3. Compare `sources/baseline/main.tex` with `sources/revision/main.tex`.
4. Use `evidence/delivery-manifest.json` to verify every included file.

From the directory containing the downloaded archive and checksum:

```bash
sha256sum -c sample-delivery.zip.sha256
unzip -l sample-delivery.zip
```

The paid sprint has a larger manuscript boundary and buyer-specific written
scope. This sample proves only the small build, ledger, and packaging path shown
here.
