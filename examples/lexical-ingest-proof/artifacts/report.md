# Synthetic lexical-ingest proof report

> Project-owned synthetic workflow proof: no OUTOFPAPUA schema, no real Toolbox corpus, no client data, no OCR, no linguistic accuracy benchmark, and no customer result.

## Result

Two project-owned inputs supplied 6 records and 42 field values. The deterministic validation accepted 4 records and rejected 2. The canonical database contains 4 lexemes and 4 separately stored English-gloss normalizations.

Database SHA-256: `395e520be855a21cf68fee5c6e9a63d6e9b11c34fb094c6b5e171b3894ff4bc3`

## Provenance retained

Every source field keeps its source record ID, stable field locator, exact raw value, source SHA-256, and canonical field name. Transformation notes point back to the gloss locator. The English display normalization never overwrites the source gloss.

IPA values are copied exactly into `ipa_supplied_raw`. The pipeline performs no IPA conversion, pronunciation inference, or linguistic correctness check.

## Dry run and validation

The dry run parses and validates both sources before opening the output database. Rejected records remain in `source_records` and retain all of their source fields, but they do not become lexemes.

- `synthetic-toolbox / TBX-003` at `synthetic-toolbox.txt:L18-L24`: `missing_lemma` — A non-empty source lemma is required.
- `synthetic-csv / CSV-003` at `synthetic-lexicon.csv:R4`: `missing_lemma` — A non-empty source lemma is required.

## Idempotency and transaction safety

The first upsert made 62 content writes. Replaying the same prepared dataset made 0 writes, and the database hash remained unchanged. A separate deliberate failure after three writes left every ingestion table empty, confirming transaction rollback.

## What this does not show

This proof does not use or infer an OUTOFPAPUA schema, ingest a real Toolbox corpus, process OCR, measure linguistic accuracy, or report a customer outcome. Real work would require a reviewed field map, rights and privacy checks, corpus-specific validation, and domain-expert acceptance criteria.
