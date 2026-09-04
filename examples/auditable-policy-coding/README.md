# Auditable policy content-coding sample

This project-owned example shows a small, reviewable content-coding workflow.
It uses three wholly synthetic policy passages, a frozen codebook, and
hand-authored reference decisions. Every decision retains the exact deciding
excerpt and locator, a one-line rationale, and an explicit ambiguity flag.

No client text, copyrighted source text, model call, or network request is used.
The output is a workflow proof only; it is not a customer result, benchmark,
offer, or revenue claim.

## Build and verify

The builder uses only the Python standard library:

```bash
python examples/auditable-policy-coding/build.py
python examples/auditable-policy-coding/build.py --check
```

The first command validates the source records and writes the deterministic
report and manifest. The second rebuilds into a temporary directory and checks
that the committed artifacts are byte-identical.

## Files

- `inputs/codebook.json` is the versioned, frozen decision framework.
- `inputs/passages.json` contains three short synthetic passages split into
  stable sentence locators.
- `inputs/classifications.json` contains the reference coding decisions.
- `artifacts/report.md` is the human-readable evidence report.
- `artifacts/manifest.json` records source and artifact hashes plus validation
  counts. It intentionally does not hash itself, avoiding a hash cycle.

To change a decision rule, issue a new codebook version and recode all passages;
do not silently edit the frozen version.
