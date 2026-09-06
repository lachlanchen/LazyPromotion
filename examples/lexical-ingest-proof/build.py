#!/usr/bin/env python3
"""Build a deterministic SQLite proof from two project-owned lexical sources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sqlite3
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs"
DEFAULT_OUTPUT = ROOT / "artifacts"
TOOLBOX_SOURCE = INPUTS / "synthetic-toolbox.txt"
CSV_SOURCE = INPUTS / "synthetic-lexicon.csv"
BOUNDARY = (
    "Project-owned synthetic workflow proof: no OUTOFPAPUA schema, no real "
    "Toolbox corpus, no client data, no OCR, no linguistic accuracy benchmark, "
    "and no customer result."
)
SOURCE_FILES = (
    "README.md",
    "build.py",
    "inputs/synthetic-toolbox.txt",
    "inputs/synthetic-lexicon.csv",
)
ARTIFACT_FILES = (
    "canonical-lexicon.sqlite",
    "dry-run.json",
    "idempotency.json",
    "report.md",
    "rollback-safety.json",
    "validation.json",
)
SQLITE_LAST_WRITER_VERSION_OFFSET = 96
SQLITE_CANONICAL_LAST_WRITER_VERSION = b"\x00\x00\x00\x00"
CSV_FIELDS = (
    "record_id",
    "lemma",
    "language",
    "part_of_speech",
    "ipa",
    "gloss_en",
    "note",
)
TOOLBOX_MAP = {
    "lx": "lemma",
    "lg": "language",
    "ps": "part_of_speech",
    "ph": "ipa",
    "ge": "gloss_en",
    "nt": "note",
}


class BuildError(RuntimeError):
    """Raised when an input or generated artifact violates the proof contract."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonicalize_sqlite_last_writer_version(path: Path) -> None:
    """Remove the non-semantic SQLite library patch stamp from a closed database."""

    with path.open("r+b") as handle:
        header = handle.read(100)
        if len(header) != 100 or not header.startswith(b"SQLite format 3\x00"):
            raise BuildError("generated database has an invalid SQLite header")
        handle.seek(SQLITE_LAST_WRITER_VERSION_OFFSET)
        handle.write(SQLITE_CANONICAL_LAST_WRITER_VERSION)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(json_bytes(value))


def source_descriptor(source_id: str, path: Path, source_format: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "filename": path.name,
        "format": source_format,
        "sha256": sha256(path),
        "synthetic": True,
        "transformation_notes": (
            "Raw field values are retained exactly. Structural parsing only maps source fields "
            "to canonical column names."
        ),
    }


def parse_toolbox(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = source_descriptor("synthetic-toolbox", path, "toolbox-style-text")
    lines = path.read_text(encoding="utf-8").splitlines()
    groups: list[list[tuple[int, str, str]]] = []
    current: list[tuple[int, str, str]] = []
    header_seen = False
    pattern = re.compile(r"^\\([A-Za-z0-9_]+)(?: (.*))?$")
    for line_number, line in enumerate(lines, 1):
        if not line:
            if current:
                groups.append(current)
                current = []
            continue
        match = pattern.match(line)
        if not match:
            raise BuildError(f"unparseable Toolbox line {line_number}")
        if match.group(1) == "_sh":
            if line_number != 1 or header_seen or current:
                raise BuildError("the Toolbox _sh header must appear exactly once at line 1")
            header_seen = True
            continue
        current.append((line_number, match.group(1), match.group(2) or ""))
    if current:
        groups.append(current)

    # The Toolbox header is source metadata, not a lexical record.
    if not header_seen:
        raise BuildError("the synthetic Toolbox source must begin with a _sh header")
    records: list[dict[str, Any]] = []
    for ordinal, group in enumerate(groups, 1):
        fields = []
        for field_order, (line_number, name, raw_value) in enumerate(group, 1):
            fields.append(
                {
                    "field_order": field_order,
                    "source_name": name,
                    "canonical_name": "record_id" if name == "id" else TOOLBOX_MAP.get(name, name),
                    "locator": f"{path.name}:L{line_number}",
                    "raw_value": raw_value,
                }
            )
        id_fields = [item for item in fields if item["source_name"] == "id"]
        record_id = id_fields[0]["raw_value"].strip() if len(id_fields) == 1 else ""
        records.append(
            {
                "source_id": source["source_id"],
                "source_sha256": source["sha256"],
                "source_record_id": record_id,
                "ordinal": ordinal,
                "record_locator": f"{path.name}:L{group[0][0]}-L{group[-1][0]}",
                "fields": fields,
            }
        )
    return source, records


def parse_csv_source(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = source_descriptor("synthetic-csv", path, "csv")
    text = path.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != CSV_FIELDS:
        raise BuildError("the synthetic CSV header does not match the frozen schema")
    records: list[dict[str, Any]] = []
    for ordinal, row in enumerate(reader, 1):
        line_number = ordinal + 1
        fields = [
            {
                "field_order": index,
                "source_name": name,
                "canonical_name": name,
                "locator": f"{path.name}:R{line_number}:C{name}",
                "raw_value": row[name],
            }
            for index, name in enumerate(CSV_FIELDS, 1)
        ]
        records.append(
            {
                "source_id": source["source_id"],
                "source_sha256": source["sha256"],
                "source_record_id": row["record_id"].strip(),
                "ordinal": ordinal,
                "record_locator": f"{path.name}:R{line_number}",
                "fields": fields,
            }
        )
    return source, records


def field_map(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for field in record["fields"]:
        name = field["canonical_name"]
        if name in mapped:
            raise BuildError(f"duplicate field {name} in {record['record_locator']}")
        mapped[name] = field
    return mapped


def normalize_english_gloss(raw_value: str) -> str:
    """Apply a visible display normalization without modifying source storage."""
    normalized = unicodedata.normalize("NFC", raw_value)
    return re.sub(r"\s+", " ", normalized.strip()).casefold()


def prepare_dataset() -> dict[str, Any]:
    toolbox_source, toolbox_records = parse_toolbox(TOOLBOX_SOURCE)
    csv_source, csv_records = parse_csv_source(CSV_SOURCE)
    sources = [toolbox_source, csv_source]
    records = toolbox_records + csv_records
    seen: set[tuple[str, str]] = set()
    rejects: list[dict[str, Any]] = []
    accepted = 0
    for record in records:
        fields = field_map(record)
        reasons = []
        record_id = record["source_record_id"]
        identity = (record["source_id"], record_id)
        if not record_id:
            reasons.append(("missing_record_id", "A non-empty source record ID is required."))
        elif identity in seen:
            reasons.append(("duplicate_record_id", "The source record ID repeats within this source."))
        seen.add(identity)
        lemma = fields.get("lemma", {}).get("raw_value", "")
        if not lemma.strip():
            reasons.append(("missing_lemma", "A non-empty source lemma is required."))
        required = ("language", "part_of_speech", "ipa", "gloss_en")
        missing = [name for name in required if name not in fields]
        if missing:
            reasons.append(("missing_required_field", f"Missing fields: {', '.join(missing)}."))

        if reasons:
            code, detail = reasons[0]
            record["status"] = "rejected"
            record["rejection_code"] = code
            record["rejection_detail"] = detail
            rejects.append(
                {
                    "code": code,
                    "detail": detail,
                    "record_locator": record["record_locator"],
                    "source_id": record["source_id"],
                    "source_record_id": record_id,
                }
            )
        else:
            record["status"] = "accepted"
            record["rejection_code"] = None
            record["rejection_detail"] = None
            accepted += 1

        stable_id = record_id or f"missing-id-{record['ordinal']:04d}"
        record["record_key"] = f"{record['source_id']}:{stable_id}"
        for field in record["fields"]:
            field["field_key"] = f"{record['record_key']}:{field['field_order']:03d}"

    if len({record["record_key"] for record in records}) != len(records):
        raise BuildError("record keys are not unique after validation")

    stats = {
        "accepted_records": accepted,
        "field_values": sum(len(record["fields"]) for record in records),
        "gloss_normalizations_planned": accepted,
        "records_by_format": {
            source["format"]: sum(record["source_id"] == source["source_id"] for record in records)
            for source in sources
        },
        "reject_codes": dict(sorted(Counter(item["code"] for item in rejects).items())),
        "rejected_records": len(rejects),
        "source_records": len(records),
        "sources": len(sources),
    }
    return {"sources": sources, "records": records, "rejects": rejects, "stats": stats}


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE sources (
  source_id TEXT PRIMARY KEY,
  filename TEXT NOT NULL UNIQUE,
  source_format TEXT NOT NULL,
  source_sha256 TEXT NOT NULL CHECK(length(source_sha256) = 64),
  synthetic INTEGER NOT NULL CHECK(synthetic = 1),
  transformation_notes TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE source_records (
  record_key TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  source_record_id TEXT NOT NULL,
  source_ordinal INTEGER NOT NULL,
  record_locator TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('accepted', 'rejected')),
  rejection_code TEXT,
  rejection_detail TEXT,
  UNIQUE(source_id, source_record_id)
) WITHOUT ROWID;
CREATE TABLE source_fields (
  field_key TEXT PRIMARY KEY,
  record_key TEXT NOT NULL REFERENCES source_records(record_key) ON DELETE CASCADE,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  source_record_id TEXT NOT NULL,
  field_order INTEGER NOT NULL,
  source_name TEXT NOT NULL,
  canonical_name TEXT NOT NULL,
  locator TEXT NOT NULL,
  raw_value TEXT NOT NULL,
  source_sha256 TEXT NOT NULL CHECK(length(source_sha256) = 64),
  UNIQUE(record_key, field_order),
  UNIQUE(record_key, locator)
) WITHOUT ROWID;
CREATE TABLE lexemes (
  lexeme_id TEXT PRIMARY KEY,
  record_key TEXT NOT NULL UNIQUE REFERENCES source_records(record_key) ON DELETE CASCADE,
  lemma_source_raw TEXT NOT NULL,
  language_source_raw TEXT NOT NULL,
  part_of_speech_source_raw TEXT NOT NULL,
  ipa_supplied_raw TEXT NOT NULL,
  english_gloss_source_raw TEXT NOT NULL,
  note_source_raw TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE gloss_normalizations (
  lexeme_id TEXT PRIMARY KEY REFERENCES lexemes(lexeme_id) ON DELETE CASCADE,
  source_field_locator TEXT NOT NULL,
  normalized_english_gloss TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  transformation_note TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE transformation_log (
  transformation_id TEXT PRIMARY KEY,
  record_key TEXT NOT NULL REFERENCES source_records(record_key) ON DELETE CASCADE,
  target_field TEXT NOT NULL,
  source_field_locator TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  note TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX source_fields_record_idx ON source_fields(record_key, field_order);
CREATE INDEX source_records_status_idx ON source_records(status, source_id, source_ordinal);
"""


TABLE_KEYS = {
    "sources": ("source_id",),
    "source_records": ("record_key",),
    "source_fields": ("field_key",),
    "lexemes": ("lexeme_id",),
    "gloss_normalizations": ("lexeme_id",),
    "transformation_log": ("transformation_id",),
}


def initialize_database(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA page_size = 4096")
    connection.execute("PRAGMA encoding = 'UTF-8'")
    connection.execute("PRAGMA journal_mode = DELETE")
    connection.execute("PRAGMA application_id = 1280001100")
    connection.execute("PRAGMA user_version = 1")
    connection.executescript(SCHEMA)
    connection.executemany(
        "INSERT INTO metadata(key, value) VALUES (?, ?)",
        (
            ("boundary", BOUNDARY),
            ("builder", "lexical-ingest-proof-v1"),
            ("schema_version", "1"),
        ),
    )
    connection.commit()
    return connection


def row_state(connection: sqlite3.Connection, table: str, keys: tuple[str, ...], values: dict[str, Any]) -> dict[str, Any] | None:
    where = " AND ".join(f"{key} = ?" for key in keys)
    row = connection.execute(
        f"SELECT * FROM {table} WHERE {where}",
        tuple(values[key] for key in keys),
    ).fetchone()
    return dict(row) if row else None


def upsert_row(
    connection: sqlite3.Connection,
    table: str,
    values: dict[str, Any],
    changes: Counter[str],
) -> bool:
    keys = TABLE_KEYS[table]
    previous = row_state(connection, table, keys, values)
    if previous == values:
        changes[f"{table}.unchanged"] += 1
        return False
    columns = tuple(values)
    placeholders = ", ".join("?" for _ in columns)
    if previous is None:
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(values[column] for column in columns),
        )
        changes[f"{table}.created"] += 1
    else:
        nonkeys = tuple(column for column in columns if column not in keys)
        assignments = ", ".join(f"{column} = ?" for column in nonkeys)
        where = " AND ".join(f"{key} = ?" for key in keys)
        connection.execute(
            f"UPDATE {table} SET {assignments} WHERE {where}",
            tuple(values[column] for column in nonkeys) + tuple(values[key] for key in keys),
        )
        changes[f"{table}.updated"] += 1
    return True


def ingest(
    connection: sqlite3.Connection,
    dataset: dict[str, Any],
    *,
    fail_after_writes: int | None = None,
) -> dict[str, Any]:
    changes: Counter[str] = Counter()
    writes = 0

    def write(table: str, values: dict[str, Any]) -> None:
        nonlocal writes
        if upsert_row(connection, table, values, changes):
            writes += 1
            if fail_after_writes is not None and writes >= fail_after_writes:
                raise BuildError("injected transaction failure")

    try:
        connection.execute("BEGIN IMMEDIATE")
        for source in dataset["sources"]:
            write(
                "sources",
                {
                    "source_id": source["source_id"],
                    "filename": source["filename"],
                    "source_format": source["format"],
                    "source_sha256": source["sha256"],
                    "synthetic": 1,
                    "transformation_notes": source["transformation_notes"],
                },
            )
        for record in dataset["records"]:
            write(
                "source_records",
                {
                    "record_key": record["record_key"],
                    "source_id": record["source_id"],
                    "source_record_id": record["source_record_id"],
                    "source_ordinal": record["ordinal"],
                    "record_locator": record["record_locator"],
                    "status": record["status"],
                    "rejection_code": record["rejection_code"],
                    "rejection_detail": record["rejection_detail"],
                },
            )
            for field in record["fields"]:
                write(
                    "source_fields",
                    {
                        "field_key": field["field_key"],
                        "record_key": record["record_key"],
                        "source_id": record["source_id"],
                        "source_record_id": record["source_record_id"],
                        "field_order": field["field_order"],
                        "source_name": field["source_name"],
                        "canonical_name": field["canonical_name"],
                        "locator": field["locator"],
                        "raw_value": field["raw_value"],
                        "source_sha256": record["source_sha256"],
                    },
                )

            if record["status"] == "rejected":
                connection.execute("DELETE FROM lexemes WHERE record_key = ?", (record["record_key"],))
                continue
            fields = field_map(record)
            lexeme_id = record["record_key"]
            canonical_values = {
                "lemma_source_raw": fields["lemma"]["raw_value"],
                "language_source_raw": fields["language"]["raw_value"],
                "part_of_speech_source_raw": fields["part_of_speech"]["raw_value"],
                "ipa_supplied_raw": fields["ipa"]["raw_value"],
                "english_gloss_source_raw": fields["gloss_en"]["raw_value"],
                "note_source_raw": fields.get("note", {}).get("raw_value", ""),
            }
            write(
                "lexemes",
                {"lexeme_id": lexeme_id, "record_key": record["record_key"], **canonical_values},
            )
            write(
                "gloss_normalizations",
                {
                    "lexeme_id": lexeme_id,
                    "source_field_locator": fields["gloss_en"]["locator"],
                    "normalized_english_gloss": normalize_english_gloss(
                        fields["gloss_en"]["raw_value"]
                    ),
                    "rule_id": "english-display-v1",
                    "transformation_note": (
                        "Unicode NFC, trim outer whitespace, collapse whitespace, then Unicode casefold; "
                        "the source raw value remains unchanged in source_fields and lexemes."
                    ),
                },
            )
            write(
                "transformation_log",
                {
                    "transformation_id": f"{lexeme_id}:gloss-en-v1",
                    "record_key": record["record_key"],
                    "target_field": "normalized_english_gloss",
                    "source_field_locator": fields["gloss_en"]["locator"],
                    "rule_id": "english-display-v1",
                    "note": (
                        "English display normalization is separate from source storage. No lemma, "
                        "language, sense, or IPA inference is performed."
                    ),
                },
            )
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_keys:
            raise BuildError("foreign-key validation failed")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return {"writes": writes, "changes": dict(sorted(changes.items()))}


def table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in TABLE_KEYS
    }


def logical_fingerprint(connection: sqlite3.Connection) -> str:
    state: dict[str, Any] = {}
    for table, keys in TABLE_KEYS.items():
        order = ", ".join(keys)
        state[table] = [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY {order}")]
    return hashlib.sha256(json.dumps(state, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def schema_contract(connection: sqlite3.Connection) -> dict[str, list[str]]:
    return {
        table: [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
        for table in ("sources", "source_records", "source_fields", "lexemes", "gloss_normalizations", "transformation_log")
    }


def verify_rollback(dataset: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "rollback.sqlite"
        connection = initialize_database(path)
        injected_error = None
        try:
            ingest(connection, dataset, fail_after_writes=3)
        except BuildError as exc:
            injected_error = str(exc)
        counts = table_counts(connection)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        connection.close()
    passed = injected_error == "injected transaction failure" and not any(counts.values()) and integrity == "ok"
    if not passed:
        raise BuildError("injected failure did not roll back all ingestion writes")
    return {
        "all_ingest_tables_empty_after_failure": True,
        "boundary": BOUNDARY,
        "failure_injected_after_writes": 3,
        "integrity_check": integrity,
        "passed": True,
        "post_rollback_counts": counts,
        "transaction_scope": "all sources, records, fields, canonical rows, and normalization rows",
    }


def render_report(
    dataset: dict[str, Any],
    counts: dict[str, int],
    database_sha256: str,
    first_run: dict[str, Any],
    second_run: dict[str, Any],
) -> str:
    reject_lines = [
        f"- `{item['source_id']} / {item['source_record_id']}` at `{item['record_locator']}`: "
        f"`{item['code']}` — {item['detail']}"
        for item in dataset["rejects"]
    ]
    return "\n".join(
        [
            "# Synthetic lexical-ingest proof report",
            "",
            f"> {BOUNDARY}",
            "",
            "## Result",
            "",
            f"Two project-owned inputs supplied {dataset['stats']['source_records']} records and "
            f"{dataset['stats']['field_values']} field values. The deterministic validation accepted "
            f"{dataset['stats']['accepted_records']} records and rejected {dataset['stats']['rejected_records']}. "
            f"The canonical database contains {counts['lexemes']} lexemes and "
            f"{counts['gloss_normalizations']} separately stored English-gloss normalizations.",
            "",
            f"Database SHA-256: `{database_sha256}`",
            "",
            "## Provenance retained",
            "",
            "Every source field keeps its source record ID, stable field locator, exact raw value, source "
            "SHA-256, and canonical field name. Transformation notes point back to the gloss locator. "
            "The English display normalization never overwrites the source gloss.",
            "",
            "IPA values are copied exactly into `ipa_supplied_raw`. The pipeline performs no IPA conversion, "
            "pronunciation inference, or linguistic correctness check.",
            "",
            "## Dry run and validation",
            "",
            "The dry run parses and validates both sources before opening the output database. Rejected records "
            "remain in `source_records` and retain all of their source fields, but they do not become lexemes.",
            "",
            *reject_lines,
            "",
            "## Idempotency and transaction safety",
            "",
            f"The first upsert made {first_run['writes']} content writes. Replaying the same prepared dataset "
            f"made {second_run['writes']} writes, and the database hash remained unchanged. A separate deliberate "
            "failure after three writes left every ingestion table empty, confirming transaction rollback.",
            "",
            "## What this does not show",
            "",
            "This proof does not use or infer an OUTOFPAPUA schema, ingest a real Toolbox corpus, process OCR, "
            "measure linguistic accuracy, or report a customer outcome. Real work would require a reviewed field "
            "map, rights and privacy checks, corpus-specific validation, and domain-expert acceptance criteria.",
            "",
        ]
    )


def build(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    dataset = prepare_dataset()
    output_dir.mkdir(parents=True, exist_ok=True)
    database = output_dir / "canonical-lexicon.sqlite"

    dry_run = {
        "boundary": BOUNDARY,
        "database_written": False,
        "mode": "dry-run",
        "network_used": False,
        "planned": dataset["stats"],
        "source_sha256": {source["filename"]: source["sha256"] for source in dataset["sources"]},
    }
    write_json(output_dir / "dry-run.json", dry_run)

    connection = initialize_database(database)
    first_run = ingest(connection, dataset)
    connection.execute("VACUUM")
    first_counts = table_counts(connection)
    first_fingerprint = logical_fingerprint(connection)
    schema = schema_contract(connection)
    connection.close()
    canonicalize_sqlite_last_writer_version(database)
    first_database_sha256 = sha256(database)

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    second_run = ingest(connection, dataset)
    second_counts = table_counts(connection)
    second_fingerprint = logical_fingerprint(connection)
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_key_violations = len(connection.execute("PRAGMA foreign_key_check").fetchall())
    connection.close()
    canonicalize_sqlite_last_writer_version(database)
    second_database_sha256 = sha256(database)
    if first_counts != second_counts or first_fingerprint != second_fingerprint:
        raise BuildError("idempotent replay changed the logical database state")
    if first_database_sha256 != second_database_sha256 or second_run["writes"] != 0:
        raise BuildError("idempotent replay changed the database bytes")
    if integrity != "ok" or foreign_key_violations:
        raise BuildError("canonical database validation failed")

    idempotency = {
        "boundary": BOUNDARY,
        "database_sha256_after_first_run": first_database_sha256,
        "database_sha256_after_second_run": second_database_sha256,
        "database_bytes_unchanged": True,
        "first_run": first_run,
        "logical_fingerprint_after_first_run": first_fingerprint,
        "logical_fingerprint_after_second_run": second_fingerprint,
        "logical_state_unchanged": True,
        "second_run": second_run,
    }
    write_json(output_dir / "idempotency.json", idempotency)
    write_json(output_dir / "rollback-safety.json", verify_rollback(dataset))
    validation = {
        "boundary": BOUNDARY,
        "counts": second_counts,
        "foreign_key_violations": foreign_key_violations,
        "integrity_check": integrity,
        "rejects": dataset["rejects"],
        "schema": schema,
        "stats": dataset["stats"],
    }
    write_json(output_dir / "validation.json", validation)
    (output_dir / "report.md").write_text(
        render_report(
            dataset,
            second_counts,
            second_database_sha256,
            first_run,
            second_run,
        ),
        encoding="utf-8",
    )

    manifest = {
        "artifact_sha256": {name: sha256(output_dir / name) for name in ARTIFACT_FILES},
        "boundary": BOUNDARY,
        "builder": "lexical-ingest-proof-v1",
        "inputs": {
            "client_data_used": False,
            "network_used": False,
            "ocr_used": False,
            "outofpapua_schema_used": False,
            "real_toolbox_corpus_used": False,
            "synthetic_project_owned_sources": 2,
        },
        "manifest_self_hashed": False,
        "schema_version": 1,
        "source_sha256": {name: sha256(ROOT / name) for name in SOURCE_FILES},
        "verification": {
            "counts": second_counts,
            "database_bytes_unchanged_on_replay": True,
            "foreign_key_violations": foreign_key_violations,
            "integrity_check": integrity,
            "rollback_passed": True,
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def check_committed() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        candidate = Path(temporary)
        build(candidate)
        problems = []
        for name in (*ARTIFACT_FILES, "manifest.json"):
            expected = DEFAULT_OUTPUT / name
            actual = candidate / name
            if not expected.is_file():
                problems.append(f"missing committed artifact: {name}")
            elif expected.read_bytes() != actual.read_bytes():
                problems.append(f"stale committed artifact: {name}")
        if problems:
            raise BuildError("; ".join(problems))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare a clean rebuild to committed artifacts")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if args.check:
        if args.output != DEFAULT_OUTPUT:
            parser.error("--check cannot be combined with --output")
        check_committed()
        print("lexical-ingest proof artifacts are current")
    else:
        manifest = build(args.output)
        print(json.dumps(manifest["verification"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
