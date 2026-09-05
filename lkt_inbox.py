#!/usr/bin/env python3
"""Receive encrypted LKT fit checks without persisting them on the web server."""

from __future__ import annotations

import argparse
import base64
import binascii
import fcntl
import hashlib
import json
import os
import re
import shlex
import sqlite3
import stat
import subprocess
import time
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, Protocol

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


ROOT = Path(__file__).resolve().parent
BLOG_ENV_PATH = ROOT.parent / "BLOG" / ".env"
PRIVATE_KEY_PATH = ROOT / ".local" / "intake" / "lkt-fit-check-private.pem"
INBOX_DIR = ROOT / ".local" / "inbound" / "lkt"
DB_PATH = ROOT / ".local" / "inbound" / "lkt-inbox.sqlite3"
STATUS_PATH = ROOT / ".local" / "inbound" / "lkt-inbox-status.json"
LOG_PATH = ROOT / ".local" / "inbound" / "lkt-inbox.jsonl"
LOCK_PATH = ROOT / ".local" / "inbound" / "lkt-inbox.lock"

REMOTE_SPOOL = "/var/lib/lazyingart/lkt-fit-check-inbox"
EXPECTED_FINGERPRINT = (
    "8d9b82057dbae85fd2956b18eff95f775ba18671e2c5bf48d1bd6da39d50498f"
)
ENVELOPE_VERSION = "lkt-fit-check-envelope/v1"
LEGACY_RECORD_VERSION = "lkt-fit-check-record/v1"
RECORD_VERSION = "fit-check-record/v2"
ALGORITHM = "RSA-OAEP-SHA1+AES-256-GCM"
AAD = b"lazyingart:lkt-fit-check:envelope:v1"
LEGACY_SOURCE = {
    "origin": "https://lazying.art",
    "route": "/lazyingart/v1/lkt-fit-check",
    "schema": "lkt-fit-check/v1",
}
SOURCE = {
    "origin": "https://lazying.art",
    "route": "/lazyingart/v1/lkt-fit-check",
    "schema": "fit-check/v2",
}

FILENAME_RE = re.compile(r"\Alkt-([a-f0-9]{32})\.json\Z")
RECEIPT_RE = re.compile(r"\A[a-f0-9]{32}\Z")
FINGERPRINT_RE = re.compile(r"\A[a-f0-9]{64}\Z")
UTC_SECONDS_RE = re.compile(
    r"\A(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"
    r"T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\dZ\Z"
)
BASE64_RE = re.compile(
    r"\A(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?\Z"
)
EMAIL_LOCAL_RE = re.compile(r"\A[a-z0-9!#$%&'*+/=?^_`{|}~.\-]+\Z", re.IGNORECASE)
EMAIL_DOMAIN_RE = re.compile(r"\A[a-z0-9-]+\Z", re.IGNORECASE)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

MAX_ENVELOPE_BYTES = 65_536
MAX_CIPHERTEXT_BYTES = 16_384
MAX_REMOTE_FILES = 200

ENVELOPE_KEYS = {
    "version",
    "algorithm",
    "key_id",
    "receipt",
    "created_at",
    "wrapped_key",
    "iv",
    "tag",
    "ciphertext",
}
RECORD_KEYS = {"version", "received_at", "source", "payload"}
LEGACY_PAYLOAD_KEYS = {
    "contact_email",
    "collection",
    "language_goal",
    "readers",
    "hardware",
    "sample",
    "constraints",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "rights_confirmed",
    "scope_confirmed",
    "client_elapsed_ms",
}
COMMON_PAYLOAD_KEYS = {
    "offer",
    "contact_email",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "rights_confirmed",
    "scope_confirmed",
    "client_elapsed_ms",
}
OFFER_FIELD_RULES = {
    "lkt": {
        "collection": (1200, True, True),
        "language_goal": (300, True, False),
        "readers": (300, True, False),
        "hardware": (300, True, False),
        "sample": (300, True, False),
        "constraints": (800, False, True),
    },
    "manuscript": {
        "role": (700, True, True),
        "shape": (400, True, False),
        "venue": (700, True, True),
        "problem": (1000, True, True),
        "outputs": (700, False, True),
        "handling": (800, True, True),
        "constraints": (800, False, True),
    },
    "lecture": {
        "source": (1000, True, True),
        "format": (400, True, False),
        "language": (300, True, False),
        "terms": (800, False, True),
        "excerpt": (300, False, False),
        "intended_use": (800, True, True),
        "constraints": (800, False, True),
    },
    "story_clip": {
        "source": (600, True, True),
        "language": (300, True, False),
        "rights_scope": (1000, True, True),
        "audience_platform": (600, True, True),
        "goal": (800, True, True),
        "constraints": (800, False, True),
    },
}


class InboxError(RuntimeError):
    """A fail-closed intake error whose details must not enter public logs."""


class LockBusy(InboxError):
    """Another receiver owns the private inbox lock."""


class SpoolClient(Protocol):
    def list_filenames(self) -> list[str]: ...

    def fetch(self, filename: str) -> bytes: ...

    def delete_if_unchanged(self, filename: str, sha256: str) -> bool: ...


@dataclass(frozen=True)
class SshConfig:
    target: str
    port: int
    key_path: Path
    strict_host_key: str


@dataclass(frozen=True)
class ReceiverConfig:
    blog_env_path: Path = BLOG_ENV_PATH
    private_key_path: Path = PRIVATE_KEY_PATH
    inbox_dir: Path = INBOX_DIR
    db_path: Path = DB_PATH
    status_path: Path = STATUS_PATH
    log_path: Path = LOG_PATH
    lock_path: Path = LOCK_PATH
    expected_fingerprint: str = EXPECTED_FINGERPRINT


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _dotenv_value(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value[0] in {"'", '"'}:
        quote = value[0]
        if len(value) < 2 or value[-1] != quote:
            raise InboxError("invalid private SSH configuration")
        value = value[1:-1]
        if quote == '"':
            value = value.replace(r"\$", "$").replace(r"\"", '"').replace(r"\\", "\\")
    else:
        comment = re.search(r"\s+#", value)
        if comment:
            value = value[: comment.start()].rstrip()
    if "\x00" in value or "\n" in value or "\r" in value:
        raise InboxError("invalid private SSH configuration")
    return value


def load_blog_ssh_config(path: Path = BLOG_ENV_PATH) -> SshConfig:
    """Read only the three SSH settings needed by the receiver; never source .env."""
    wanted = {
        "BLOG_SSH_TARGET",
        "BLOG_SSH_PORT",
        "BLOG_SSH_KEY",
        "BLOG_SSH_STRICT_HOSTKEY",
    }
    values: dict[str, str] = {}
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                match = re.match(
                    r"\A\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)\Z",
                    line.rstrip("\n"),
                )
                if match and match.group(1) in wanted:
                    if match.group(1) in values:
                        raise InboxError("duplicate private SSH configuration")
                    values[match.group(1)] = _dotenv_value(match.group(2))
    except (OSError, UnicodeError) as exc:
        raise InboxError("private SSH configuration is unavailable") from exc

    target = values.get("BLOG_SSH_TARGET", "")
    if not re.fullmatch(
        r"(?:[A-Za-z_][A-Za-z0-9._-]*@)?(?:[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?)",
        target,
    ):
        raise InboxError("invalid private SSH configuration")

    raw_port = values.get("BLOG_SSH_PORT", "22")
    if not raw_port.isdigit() or not 1 <= int(raw_port) <= 65535:
        raise InboxError("invalid private SSH configuration")

    raw_key = values.get("BLOG_SSH_KEY", "")
    raw_key = raw_key.replace("${HOME}", str(Path.home())).replace(
        "$HOME", str(Path.home())
    )
    key_path = Path(raw_key).expanduser()
    if not key_path.is_absolute() or not key_path.is_file():
        raise InboxError("private SSH configuration is unavailable")

    strict = values.get("BLOG_SSH_STRICT_HOSTKEY", "accept-new")
    if strict not in {"yes", "accept-new"}:
        raise InboxError("invalid private SSH configuration")

    return SshConfig(target, int(raw_port), key_path, strict)


class SshSpoolClient:
    """Minimal SSH boundary with static remote paths and validated filenames."""

    def __init__(
        self,
        config: SshConfig,
        *,
        runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
    ) -> None:
        self.config = config
        self.runner = runner

    def _command(self, remote_command: str, *, timeout: int = 20) -> bytes:
        command = [
            "ssh",
            "-T",
            "-p",
            str(self.config.port),
            "-i",
            str(self.config.key_path),
            "-o",
            "BatchMode=yes",
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "ConnectTimeout=10",
            "-o",
            "LogLevel=ERROR",
            "-o",
            f"StrictHostKeyChecking={self.config.strict_host_key}",
            "--",
            self.config.target,
            remote_command,
        ]
        try:
            completed = self.runner(
                command,
                check=False,
                capture_output=True,
                timeout=timeout,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise InboxError("encrypted inbox transport failed") from exc
        if completed.returncode != 0:
            raise InboxError("encrypted inbox transport failed")
        if not isinstance(completed.stdout, bytes):
            raise InboxError("encrypted inbox transport failed")
        return completed.stdout

    def list_filenames(self) -> list[str]:
        command = (
            f"find {shlex.quote(REMOTE_SPOOL)} -maxdepth 1 -type f "
            "-name 'lkt-*.json' -printf '%f\\0'"
        )
        output = self._command(command)
        if len(output) > MAX_REMOTE_FILES * 128 or (
            output and not output.endswith(b"\x00")
        ):
            raise InboxError("encrypted inbox listing is invalid")

        names: list[str] = []
        for raw_name in output.split(b"\x00"):
            if not raw_name:
                continue
            try:
                name = raw_name.decode("ascii")
            except UnicodeDecodeError:
                continue
            if FILENAME_RE.fullmatch(name):
                names.append(name)
        if len(names) > MAX_REMOTE_FILES or len(names) != len(set(names)):
            raise InboxError("encrypted inbox listing is invalid")
        return sorted(names)

    @staticmethod
    def _safe_filename(filename: str) -> str:
        if not FILENAME_RE.fullmatch(filename):
            raise InboxError("invalid encrypted inbox filename")
        return filename

    def fetch(self, filename: str) -> bytes:
        filename = self._safe_filename(filename)
        path = f"{REMOTE_SPOOL}/{filename}"
        output = self._command(
            f"head -c {MAX_ENVELOPE_BYTES + 1} -- {shlex.quote(path)}"
        )
        if not output or len(output) > MAX_ENVELOPE_BYTES:
            raise InboxError("encrypted inbox envelope is invalid")
        return output

    def delete_if_unchanged(self, filename: str, sha256: str) -> bool:
        filename = self._safe_filename(filename)
        if not FINGERPRINT_RE.fullmatch(sha256):
            raise InboxError("invalid encrypted inbox digest")
        path = shlex.quote(f"{REMOTE_SPOOL}/{filename}")
        # The filename and digest contain only validated ASCII. Rechecking the
        # digest prevents deleting a file that changed after it was fetched.
        command = (
            "set -eu; actual=$(sha256sum -- "
            + path
            + '); [ "${actual%% *}" = '
            + shlex.quote(sha256)
            + " ] && rm -- "
            + path
        )
        try:
            self._command(command)
        except InboxError:
            return False
        return True


def _pairs_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InboxError("encrypted inbox JSON is invalid")
        result[key] = value
    return result


def strict_json_object(data: bytes, *, maximum: int) -> dict:
    if not data or len(data) > maximum:
        raise InboxError("encrypted inbox JSON is invalid")
    try:
        decoded = data.decode("utf-8")
        value = json.loads(
            decoded,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=lambda _value: (_ for _ in ()).throw(
                InboxError("encrypted inbox JSON is invalid")
            ),
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError, InboxError) as exc:
        raise InboxError("encrypted inbox JSON is invalid") from exc
    if not isinstance(value, dict):
        raise InboxError("encrypted inbox JSON is invalid")
    return value


def validate_utc_seconds(value: object) -> str:
    if not isinstance(value, str) or not UTC_SECONDS_RE.fullmatch(value):
        raise InboxError("encrypted inbox timestamp is invalid")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise InboxError("encrypted inbox timestamp is invalid") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise InboxError("encrypted inbox timestamp is invalid")
    return value


def strict_base64(
    value: object, *, expected: int | None = None, maximum: int | None = None
) -> bytes:
    if not isinstance(value, str) or not value or not BASE64_RE.fullmatch(value):
        raise InboxError("encrypted inbox encoding is invalid")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise InboxError("encrypted inbox encoding is invalid") from exc
    if base64.b64encode(decoded).decode("ascii") != value:
        raise InboxError("encrypted inbox encoding is invalid")
    if expected is not None and len(decoded) != expected:
        raise InboxError("encrypted inbox field length is invalid")
    if maximum is not None and len(decoded) > maximum:
        raise InboxError("encrypted inbox field length is invalid")
    return decoded


def private_key_fingerprint(private_key: rsa.RSAPrivateKey) -> str:
    der = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return hashlib.sha256(der).hexdigest()


def load_private_key(path: Path, expected_fingerprint: str) -> rsa.RSAPrivateKey:
    if not FINGERPRINT_RE.fullmatch(expected_fingerprint):
        raise InboxError("private intake key configuration is invalid")
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
            raise InboxError("private intake key permissions are invalid")
        data = path.read_bytes()
    except OSError as exc:
        raise InboxError("private intake key is unavailable") from exc
    if not 1_000 <= len(data) <= 16_384:
        raise InboxError("private intake key is invalid")
    try:
        key = serialization.load_pem_private_key(data, password=None)
    except (TypeError, ValueError) as exc:
        raise InboxError("private intake key is invalid") from exc
    finally:
        del data
    if not isinstance(key, rsa.RSAPrivateKey) or key.key_size < 2048:
        raise InboxError("private intake key is invalid")
    if private_key_fingerprint(key) != expected_fingerprint:
        raise InboxError("private intake key fingerprint does not match")
    return key


def validate_envelope(
    raw: bytes,
    *,
    filename: str,
    private_key: rsa.RSAPrivateKey,
    expected_fingerprint: str,
) -> tuple[dict, dict]:
    match = FILENAME_RE.fullmatch(filename)
    if not match:
        raise InboxError("invalid encrypted inbox filename")
    envelope = strict_json_object(raw, maximum=MAX_ENVELOPE_BYTES)
    if set(envelope) != ENVELOPE_KEYS:
        raise InboxError("encrypted inbox envelope schema is invalid")
    if envelope["version"] != ENVELOPE_VERSION or envelope["algorithm"] != ALGORITHM:
        raise InboxError("encrypted inbox envelope contract is invalid")
    if envelope["key_id"] != f"sha256:{expected_fingerprint}":
        raise InboxError("encrypted inbox key identifier does not match")
    receipt = envelope["receipt"]
    if (
        not isinstance(receipt, str)
        or not RECEIPT_RE.fullmatch(receipt)
        or receipt != match.group(1)
    ):
        raise InboxError("encrypted inbox receipt does not match")
    created_at = validate_utc_seconds(envelope["created_at"])

    wrapped = strict_base64(envelope["wrapped_key"], expected=private_key.key_size // 8)
    iv = strict_base64(envelope["iv"], expected=12)
    tag = strict_base64(envelope["tag"], expected=16)
    ciphertext = strict_base64(envelope["ciphertext"], maximum=MAX_CIPHERTEXT_BYTES)
    if not ciphertext:
        raise InboxError("encrypted inbox ciphertext is invalid")

    try:
        content_key = private_key.decrypt(
            wrapped,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None,
            ),
        )
    except ValueError as exc:
        raise InboxError("encrypted inbox key could not be opened") from exc
    if len(content_key) != 32:
        raise InboxError("encrypted inbox content key is invalid")
    try:
        plaintext = AESGCM(content_key).decrypt(iv, ciphertext + tag, AAD)
    except InvalidTag as exc:
        raise InboxError("encrypted inbox authentication failed") from exc
    finally:
        del content_key

    record = strict_json_object(plaintext, maximum=MAX_CIPHERTEXT_BYTES)
    validate_record(record, created_at=created_at)
    return envelope, record


def _validate_text(
    value: object,
    *,
    maximum: int,
    required: bool,
    allow_lines: bool,
) -> str:
    if not isinstance(value, str):
        raise InboxError("encrypted inbox payload is invalid")
    if (
        value.strip(" \t\n\r\x00\x0b") != value
        or "\r" in value
        or CONTROL_RE.search(value)
    ):
        raise InboxError("encrypted inbox payload is invalid")
    if required and not value:
        raise InboxError("encrypted inbox payload is invalid")
    if not allow_lines and "\n" in value:
        raise InboxError("encrypted inbox payload is invalid")
    if len(value) > maximum:
        raise InboxError("encrypted inbox payload is invalid")
    return value


def _valid_utm(value: str) -> bool:
    return all(
        character in " ._/-" or unicodedata.category(character)[0] in {"L", "N"}
        for character in value
    )


def _valid_wordpress_email(value: str) -> bool:
    """Mirror the unfiltered WordPress is_email checks used by the endpoint."""
    if len(value.encode("utf-8")) < 6 or "@" not in value[1:]:
        return False
    local, domain = value.split("@", 1)
    if not EMAIL_LOCAL_RE.fullmatch(local) or ".." in domain:
        return False
    if domain.strip(" \t\n\r\x00\x0b.") != domain:
        return False
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    return all(
        label.strip(" \t\n\r\x00\x0b-") == label
        and bool(EMAIL_DOMAIN_RE.fullmatch(label))
        for label in labels
    )


def validate_payload(payload: object, *, version: str = RECORD_VERSION) -> dict:
    if not isinstance(payload, dict):
        raise InboxError("encrypted inbox payload schema is invalid")

    if version == LEGACY_RECORD_VERSION:
        if set(payload) != LEGACY_PAYLOAD_KEYS:
            raise InboxError("encrypted inbox payload schema is invalid")
        offer = "lkt"
        field_rules = OFFER_FIELD_RULES[offer]
    elif version == RECORD_VERSION:
        offer = payload.get("offer")
        if not isinstance(offer, str) or offer not in OFFER_FIELD_RULES:
            raise InboxError("encrypted inbox offer is invalid")
        field_rules = OFFER_FIELD_RULES[offer]
        if set(payload) != COMMON_PAYLOAD_KEYS | set(field_rules):
            raise InboxError("encrypted inbox payload schema is invalid")
    else:
        raise InboxError("encrypted inbox payload schema is invalid")

    email = _validate_text(
        payload["contact_email"], maximum=254, required=True, allow_lines=False
    )
    if not _valid_wordpress_email(email):
        raise InboxError("encrypted inbox contact is invalid")

    for key, (maximum, required, allow_lines) in field_rules.items():
        _validate_text(
            payload[key],
            maximum=maximum,
            required=required,
            allow_lines=allow_lines,
        )

    for key in ("utm_source", "utm_medium", "utm_campaign", "utm_content"):
        value = _validate_text(
            payload[key], maximum=80, required=False, allow_lines=False
        )
        if value and not _valid_utm(value):
            raise InboxError("encrypted inbox attribution is invalid")

    if (
        payload["rights_confirmed"] is not True
        or payload["scope_confirmed"] is not True
    ):
        raise InboxError("encrypted inbox confirmations are invalid")
    elapsed = payload["client_elapsed_ms"]
    if (
        isinstance(elapsed, bool)
        or not isinstance(elapsed, int)
        or not 0 <= elapsed <= 86_400_000
    ):
        raise InboxError("encrypted inbox elapsed time is invalid")
    return payload


def validate_record(record: object, *, created_at: str) -> dict:
    if not isinstance(record, dict) or set(record) != RECORD_KEYS:
        raise InboxError("encrypted inbox record schema is invalid")
    version = record["version"]
    if version not in {LEGACY_RECORD_VERSION, RECORD_VERSION} or record["received_at"] != created_at:
        raise InboxError("encrypted inbox record contract is invalid")
    validate_utc_seconds(record["received_at"])
    expected_source = LEGACY_SOURCE if version == LEGACY_RECORD_VERSION else SOURCE
    if record["source"] != expected_source:
        raise InboxError("encrypted inbox record source is invalid")
    validate_payload(record["payload"], version=version)
    return record


def _ensure_private_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True, mode=0o700, exist_ok=True)
        metadata = path.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise InboxError("private intake directory is invalid")
        path.chmod(0o700)
    except OSError as exc:
        raise InboxError("private intake directory is unavailable") from exc


def _verify_private_file(path: Path, expected: bytes) -> None:
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
            raise InboxError("private intake file permissions are invalid")
        actual = path.read_bytes()
    except OSError as exc:
        raise InboxError("private intake file is unavailable") from exc
    if (
        not hashlib.sha256(actual).digest() == hashlib.sha256(expected).digest()
        or actual != expected
    ):
        raise InboxError("private intake file does not match")


def private_atomic_write(path: Path, data: bytes, *, replace: bool = False) -> None:
    _ensure_private_directory(path.parent)
    if path.exists() or path.is_symlink():
        if not replace:
            _verify_private_file(path, data)
            return
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise InboxError("private intake destination is unavailable") from exc
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
            raise InboxError("private intake destination is invalid")

    temporary = path.parent / f".{path.name}.{os.urandom(12).hex()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor: int | None = None
    complete = False
    try:
        descriptor = os.open(temporary, flags, 0o600)
        os.fchmod(descriptor, 0o600)
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise InboxError("private intake write was incomplete")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        if not replace and (path.exists() or path.is_symlink()):
            raise InboxError("private intake destination changed")
        os.replace(temporary, path)
        path.chmod(0o600)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        complete = True
    except OSError as exc:
        raise InboxError("private intake write failed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if not complete:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
    _verify_private_file(path, data)


def canonical_json(value: dict) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def persist_inquiry(
    directory: Path,
    *,
    receipt: str,
    raw_envelope: bytes,
    record: dict,
    private_key: rsa.RSAPrivateKey,
    expected_fingerprint: str,
) -> None:
    envelope_path = directory / f"lkt-{receipt}.envelope.json"
    inquiry_path = directory / f"lkt-{receipt}.inquiry.json"
    inquiry_data = canonical_json(record)
    private_atomic_write(envelope_path, raw_envelope)
    private_atomic_write(inquiry_path, inquiry_data)

    # Re-read and re-validate both durable files before allowing remote deletion.
    persisted_envelope = envelope_path.read_bytes()
    _, persisted_record = validate_envelope(
        persisted_envelope,
        filename=f"lkt-{receipt}.json",
        private_key=private_key,
        expected_fingerprint=expected_fingerprint,
    )
    persisted_inquiry = strict_json_object(
        inquiry_path.read_bytes(), maximum=MAX_CIPHERTEXT_BYTES
    )
    validate_record(persisted_inquiry, created_at=persisted_record["received_at"])
    if (
        canonical_json(persisted_record) != inquiry_data
        or persisted_inquiry != persisted_record
    ):
        raise InboxError("private intake verification failed")


def open_status_db(path: Path) -> sqlite3.Connection:
    _ensure_private_directory(path.parent)
    if path.is_symlink():
        raise InboxError("private intake status database is invalid")
    try:
        db = sqlite3.connect(path)
        path.chmod(0o600)
        db.row_factory = sqlite3.Row
        db.executescript(
            """
            PRAGMA journal_mode=DELETE;
            CREATE TABLE IF NOT EXISTS lkt_inbox_receipts (
              receipt TEXT PRIMARY KEY,
              created_at TEXT NOT NULL,
              processed_at TEXT NOT NULL,
              state TEXT NOT NULL CHECK(state IN ('saved_local', 'remote_deleted'))
            );
            """
        )
        return db
    except (OSError, sqlite3.Error) as exc:
        raise InboxError("private intake status database is unavailable") from exc


def record_state(
    db: sqlite3.Connection,
    *,
    receipt: str,
    created_at: str,
    processed_at: str,
    state: str,
) -> None:
    if state not in {"saved_local", "remote_deleted"}:
        raise InboxError("invalid private intake state")
    try:
        db.execute(
            """
            INSERT INTO lkt_inbox_receipts(receipt, created_at, processed_at, state)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(receipt) DO UPDATE SET
              created_at=excluded.created_at,
              processed_at=excluded.processed_at,
              state=excluded.state
            """,
            (receipt, created_at, processed_at, state),
        )
        db.commit()
    except sqlite3.Error as exc:
        raise InboxError("private intake status could not be recorded") from exc


def append_private_log(path: Path, event: dict) -> None:
    _ensure_private_directory(path.parent)
    line = canonical_json(event)
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            view = memoryview(line)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise InboxError("private intake status log write was incomplete")
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise InboxError("private intake status log is unavailable") from exc


@contextmanager
def receiver_lock(path: Path) -> Iterator[None]:
    _ensure_private_directory(path.parent)
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
        os.fchmod(descriptor, 0o600)
    except OSError as exc:
        raise InboxError("private intake lock is unavailable") from exc
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LockBusy("another encrypted inbox receiver is running") from exc
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _safe_event(receipt: str, processed_at: str, state: str) -> dict[str, str]:
    return {"receipt": receipt, "processed_at": processed_at, "state": state}


def receive_once(
    config: ReceiverConfig = ReceiverConfig(),
    *,
    client: SpoolClient | None = None,
    now: Callable[[], str] = utc_now,
) -> dict:
    with receiver_lock(config.lock_path):
        private_key = load_private_key(
            config.private_key_path, config.expected_fingerprint
        )
        if client is None:
            client = SshSpoolClient(load_blog_ssh_config(config.blog_env_path))
        try:
            filenames = client.list_filenames()
        except Exception as exc:
            checked_at = now()
            status = {"checked_at": checked_at, "state": "unavailable"}
            private_atomic_write(
                config.status_path, canonical_json(status), replace=True
            )
            append_private_log(config.log_path, status)
            raise InboxError("encrypted inbox could not be checked safely") from exc

        db = open_status_db(config.db_path)
        events: list[dict[str, str]] = []
        try:
            for filename in filenames:
                receipt = FILENAME_RE.fullmatch(filename).group(1)  # type: ignore[union-attr]
                processed_at = now()
                try:
                    raw = client.fetch(filename)
                    envelope, record = validate_envelope(
                        raw,
                        filename=filename,
                        private_key=private_key,
                        expected_fingerprint=config.expected_fingerprint,
                    )
                    persist_inquiry(
                        config.inbox_dir,
                        receipt=receipt,
                        raw_envelope=raw,
                        record=record,
                        private_key=private_key,
                        expected_fingerprint=config.expected_fingerprint,
                    )
                    record_state(
                        db,
                        receipt=receipt,
                        created_at=envelope["created_at"],
                        processed_at=processed_at,
                        state="saved_local",
                    )
                    if not client.delete_if_unchanged(
                        filename, hashlib.sha256(raw).hexdigest()
                    ):
                        event = _safe_event(
                            receipt, processed_at, "saved_local_remote_pending"
                        )
                    else:
                        record_state(
                            db,
                            receipt=receipt,
                            created_at=envelope["created_at"],
                            processed_at=processed_at,
                            state="remote_deleted",
                        )
                        event = _safe_event(receipt, processed_at, "remote_deleted")
                except Exception:
                    event = _safe_event(
                        receipt, processed_at, "left_remote_unprocessed"
                    )
                events.append(event)
                append_private_log(config.log_path, event)
        finally:
            db.close()

        checked_at = now()
        if not events:
            state = "no_pending"
        elif all(event["state"] == "remote_deleted" for event in events):
            state = "complete"
        else:
            state = "partial"
        status = {"checked_at": checked_at, "state": state, "receipts": events}
        private_atomic_write(config.status_path, canonical_json(status), replace=True)
        return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("once", "loop"), help="Receive once or poll continuously."
    )
    parser.add_argument("--interval-minutes", type=int, default=15)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "once":
        try:
            report = receive_once()
        except InboxError:
            print(json.dumps({"state": "unavailable"}))
            return 1
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["state"] in {"complete", "no_pending"} else 1

    if args.interval_minutes < 5:
        print(json.dumps({"state": "unavailable"}))
        return 1
    while True:
        try:
            receive_once()
        except InboxError:
            pass
        time.sleep(args.interval_minutes * 60)


if __name__ == "__main__":
    raise SystemExit(main())
