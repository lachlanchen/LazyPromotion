# Synthetic lexical-ingest proof

This project-owned sample demonstrates a small, deterministic data-carpentry
pipeline. It ingests one synthetic Toolbox-style text file and one synthetic
CSV lexicon into a canonical SQLite database while retaining source record IDs,
field-level locators, exact raw values, source SHA-256 hashes, and explicit
transformation notes.

English-gloss normalization is stored separately from the source value. IPA is
copied exactly as supplied; the builder does not infer, convert, or validate
pronunciation. Two deliberately incomplete synthetic records exercise stable
reject handling.

## Build and verify

The builder uses only the Python standard library:

```bash
python examples/lexical-ingest-proof/build.py
python examples/lexical-ingest-proof/build.py --check
python -m unittest tests.test_lexical_ingest_proof
```

The build performs a dry run, creates the database in one transaction, reruns
the same upsert without changing its bytes, and injects a failure into a
disposable database to verify rollback. The manifest hashes every input and
artifact except itself, avoiding a self-hash cycle.

SQLite stores the patch version of the last library that wrote a database in
four informational header bytes. The builder clears that non-semantic stamp
after each close so a compatible SQLite patch update does not create a false
artifact mismatch; schema version 1 and the logical fingerprint remain explicit.

## Boundaries

This is workflow evidence, not domain evidence. It uses no OUTOFPAPUA schema,
no real Toolbox corpus, no client data, and no OCR. It is not a linguistic
accuracy benchmark or a customer result. The source forms, glosses, language
codes, and IPA are synthetic and make no claim about a real language.
