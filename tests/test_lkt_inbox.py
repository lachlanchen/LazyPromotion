import base64
import hashlib
import json
import os
import sqlite3
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import lkt_inbox


CREATED_AT = "2026-09-04T13:00:00Z"
PROCESSED_AT = "2026-09-04T13:01:00Z"


def sample_payload():
    return {
        "contact_email": "reader@example.com",
        "collection": "A private set of multilingual history books.",
        "language_goal": "Classical Chinese with English notes",
        "readers": "One teacher and a small class",
        "hardware": "Existing Linux workstation",
        "sample": "Ten representative pages",
        "constraints": "Keep the collection local.\nPreserve page citations.",
        "utm_source": "lazying.art",
        "utm_medium": "owned_site",
        "utm_campaign": "lkt_fit_check",
        "utm_content": "sample_report",
        "rights_confirmed": True,
        "scope_confirmed": True,
        "client_elapsed_ms": 5000,
    }


def sample_record(payload=None, *, created_at=CREATED_AT):
    return {
        "version": lkt_inbox.RECORD_VERSION,
        "received_at": created_at,
        "source": dict(lkt_inbox.SOURCE),
        "payload": payload or sample_payload(),
    }


def fingerprint(key):
    return lkt_inbox.private_key_fingerprint(key)


def encrypted_envelope(key, receipt, *, record=None, created_at=CREATED_AT):
    record = record or sample_record(created_at=created_at)
    plaintext = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    content_key = os.urandom(32)
    iv = os.urandom(12)
    encrypted = AESGCM(content_key).encrypt(iv, plaintext, lkt_inbox.AAD)
    ciphertext, tag = encrypted[:-16], encrypted[-16:]
    wrapped = key.public_key().encrypt(
        content_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None,
        ),
    )
    envelope = {
        "version": lkt_inbox.ENVELOPE_VERSION,
        "algorithm": lkt_inbox.ALGORITHM,
        "key_id": f"sha256:{fingerprint(key)}",
        "receipt": receipt,
        "created_at": created_at,
        "wrapped_key": base64.b64encode(wrapped).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "tag": base64.b64encode(tag).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }
    return envelope, (json.dumps(envelope, separators=(",", ":")) + "\n").encode()


class FakeClient:
    def __init__(self, files=None, *, delete=True, list_error=None):
        self.files = dict(files or {})
        self.delete = delete
        self.list_error = list_error
        self.fetches = []
        self.delete_calls = []

    def list_filenames(self):
        if self.list_error:
            raise self.list_error
        return sorted(self.files)

    def fetch(self, filename):
        self.fetches.append(filename)
        value = self.files[filename]
        if isinstance(value, Exception):
            raise value
        return value

    def delete_if_unchanged(self, filename, sha256):
        self.delete_calls.append((filename, sha256))
        if self.delete:
            self.files.pop(filename, None)
            return True
        return False


class ReceiverFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.key_fingerprint = fingerprint(cls.key)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.private_key = self.root / "private.pem"
        self.private_key.write_bytes(
            self.key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        self.private_key.chmod(0o600)
        self.config = lkt_inbox.ReceiverConfig(
            blog_env_path=self.root / "blog.env",
            private_key_path=self.private_key,
            inbox_dir=self.root / "runtime" / "lkt",
            db_path=self.root / "runtime" / "status.sqlite3",
            status_path=self.root / "runtime" / "status.json",
            log_path=self.root / "runtime" / "status.jsonl",
            lock_path=self.root / "runtime" / "receiver.lock",
            expected_fingerprint=self.key_fingerprint,
        )
        self.receipt = "ab" * 16
        self.filename = f"lkt-{self.receipt}.json"
        self.envelope, self.raw = encrypted_envelope(self.key, self.receipt)

    def tearDown(self):
        self.temporary.cleanup()

    def receive(self, client):
        return lkt_inbox.receive_once(
            self.config, client=client, now=lambda: PROCESSED_AT
        )


class EnvelopeTests(ReceiverFixture):
    def validate(self, raw=None, filename=None):
        return lkt_inbox.validate_envelope(
            raw or self.raw,
            filename=filename or self.filename,
            private_key=self.key,
            expected_fingerprint=self.key_fingerprint,
        )

    def test_decrypts_oaep_sha1_and_aes_gcm_record(self):
        envelope, record = self.validate()
        self.assertEqual(envelope["receipt"], self.receipt)
        self.assertEqual(record, sample_record())

    def test_rejects_filename_receipt_mismatch(self):
        with self.assertRaises(lkt_inbox.InboxError):
            self.validate(filename=f"lkt-{'cd' * 16}.json")

    def test_rejects_extra_missing_or_changed_envelope_fields(self):
        cases = []
        extra = dict(self.envelope, unexpected="value")
        cases.append(extra)
        missing = dict(self.envelope)
        missing.pop("tag")
        cases.append(missing)
        cases.append(dict(self.envelope, version="lkt-fit-check-envelope/v2"))
        cases.append(dict(self.envelope, algorithm="RSA-OAEP-SHA256+AES-256-GCM"))
        cases.append(dict(self.envelope, key_id="sha256:" + "0" * 64))
        cases.append(dict(self.envelope, created_at="2026-02-30T13:00:00Z"))
        cases.append(dict(self.envelope, iv=base64.b64encode(b"short").decode()))
        cases.append(dict(self.envelope, tag="not base64"))
        cases.append(dict(self.envelope, ciphertext=""))
        for envelope in cases:
            with self.subTest(keys=set(envelope), version=envelope.get("version")):
                raw = json.dumps(envelope, separators=(",", ":")).encode()
                with self.assertRaises(lkt_inbox.InboxError):
                    self.validate(raw=raw)

    def test_rejects_noncanonical_or_duplicate_json(self):
        malformed = self.raw.replace(
            b'"version":"lkt-fit-check-envelope/v1",',
            b'"version":"lkt-fit-check-envelope/v1","version":"lkt-fit-check-envelope/v1",',
            1,
        )
        with self.assertRaises(lkt_inbox.InboxError):
            self.validate(raw=malformed)
        envelope = dict(self.envelope)
        envelope["iv"] = envelope["iv"][:-1]
        with self.assertRaises(lkt_inbox.InboxError):
            self.validate(raw=json.dumps(envelope).encode())

    def test_rejects_authentication_failure(self):
        envelope = dict(self.envelope)
        tag = bytearray(base64.b64decode(envelope["tag"]))
        tag[0] ^= 1
        envelope["tag"] = base64.b64encode(tag).decode()
        with self.assertRaises(lkt_inbox.InboxError):
            self.validate(raw=json.dumps(envelope).encode())

    def test_rejects_wrong_wrapped_content_key_length(self):
        envelope = dict(self.envelope)
        envelope["wrapped_key"] = base64.b64encode(b"x" * 255).decode()
        with self.assertRaises(lkt_inbox.InboxError):
            self.validate(raw=json.dumps(envelope).encode())

    def test_rejects_invalid_plaintext_contract_and_payload(self):
        payload_cases = []
        extra = sample_payload()
        extra["website"] = ""
        payload_cases.append(extra)
        missing = sample_payload()
        missing.pop("constraints")
        payload_cases.append(missing)
        rights = sample_payload()
        rights["rights_confirmed"] = 1
        payload_cases.append(rights)
        elapsed = sample_payload()
        elapsed["client_elapsed_ms"] = True
        payload_cases.append(elapsed)
        bad_utm = sample_payload()
        bad_utm["utm_source"] = "source?query=secret"
        payload_cases.append(bad_utm)
        untrimmed = sample_payload()
        untrimmed["collection"] = " leading"
        payload_cases.append(untrimmed)
        multiline = sample_payload()
        multiline["hardware"] = "one\ntwo"
        payload_cases.append(multiline)
        for payload in payload_cases:
            with self.subTest(payload=payload):
                _, raw = encrypted_envelope(
                    self.key, self.receipt, record=sample_record(payload)
                )
                with self.assertRaises(lkt_inbox.InboxError):
                    self.validate(raw=raw)

    def test_rejects_record_source_and_timestamp_mismatch(self):
        wrong_source = sample_record()
        wrong_source["source"] = dict(lkt_inbox.SOURCE, route="/wrong")
        wrong_time = sample_record()
        wrong_time["received_at"] = "2026-09-04T13:00:01Z"
        extra = sample_record()
        extra["receipt"] = self.receipt
        for record in (wrong_source, wrong_time, extra):
            _, raw = encrypted_envelope(self.key, self.receipt, record=record)
            with self.assertRaises(lkt_inbox.InboxError):
                self.validate(raw=raw)

    def test_email_validation_matches_wordpress_endpoint_contract(self):
        accepted = sample_payload()
        accepted["contact_email"] = ".reader..name@example.com"
        _, raw = encrypted_envelope(
            self.key, self.receipt, record=sample_record(accepted)
        )
        _, record = self.validate(raw=raw)
        self.assertEqual(record["payload"]["contact_email"], accepted["contact_email"])

        for rejected in ("a@b", "reader@-example.com", "reader@example..com"):
            payload = sample_payload()
            payload["contact_email"] = rejected
            _, raw = encrypted_envelope(
                self.key, self.receipt, record=sample_record(payload)
            )
            with self.subTest(email=rejected), self.assertRaises(lkt_inbox.InboxError):
                self.validate(raw=raw)

    def test_elapsed_time_matches_zero_minimum_backend_contract(self):
        accepted = sample_payload()
        accepted["client_elapsed_ms"] = 0
        _, raw = encrypted_envelope(
            self.key, self.receipt, record=sample_record(accepted)
        )
        self.validate(raw=raw)

        rejected = sample_payload()
        rejected["client_elapsed_ms"] = -1
        _, raw = encrypted_envelope(
            self.key, self.receipt, record=sample_record(rejected)
        )
        with self.assertRaises(lkt_inbox.InboxError):
            self.validate(raw=raw)


class KeyAndConfigTests(ReceiverFixture):
    def test_loads_private_key_only_with_exact_fingerprint_and_private_mode(self):
        loaded = lkt_inbox.load_private_key(self.private_key, self.key_fingerprint)
        self.assertEqual(fingerprint(loaded), self.key_fingerprint)
        with self.assertRaises(lkt_inbox.InboxError):
            lkt_inbox.load_private_key(self.private_key, "0" * 64)
        self.private_key.chmod(0o640)
        with self.assertRaises(lkt_inbox.InboxError):
            lkt_inbox.load_private_key(self.private_key, self.key_fingerprint)

    def test_loads_only_validated_blog_ssh_settings_without_shell_evaluation(self):
        ssh_key = self.root / "ssh key"
        ssh_key.write_text("test", encoding="utf-8")
        env = self.root / ".env"
        env.write_text(
            "IGNORED_SECRET=$(touch /tmp/must-not-run)\n"
            "BLOG_SSH_TARGET=operator@example.test\n"
            "BLOG_SSH_PORT=2222\n"
            f'BLOG_SSH_KEY="{ssh_key}"\n'
            "BLOG_SSH_STRICT_HOSTKEY=yes\n",
            encoding="utf-8",
        )
        loaded = lkt_inbox.load_blog_ssh_config(env)
        self.assertEqual(loaded.target, "operator@example.test")
        self.assertEqual(loaded.port, 2222)
        self.assertEqual(loaded.key_path, ssh_key)
        self.assertEqual(loaded.strict_host_key, "yes")
        self.assertFalse(Path("/tmp/must-not-run").exists())

    def test_rejects_unsafe_ssh_values(self):
        ssh_key = self.root / "key"
        ssh_key.write_text("test", encoding="utf-8")
        defaults = {
            "BLOG_SSH_TARGET": "operator@example.test",
            "BLOG_SSH_PORT": "22",
            "BLOG_SSH_KEY": str(ssh_key),
            "BLOG_SSH_STRICT_HOSTKEY": "yes",
        }
        for key, value in (
            ("BLOG_SSH_TARGET", "-oProxyCommand=bad"),
            ("BLOG_SSH_PORT", "99999"),
            ("BLOG_SSH_KEY", "relative-key"),
            ("BLOG_SSH_STRICT_HOSTKEY", "no"),
            ("BLOG_SSH_STRICT_HOSTKEY", "surprise"),
        ):
            env = self.root / "bad.env"
            values = dict(defaults)
            values[key] = value
            env.write_text(
                "".join(f"{name}={setting}\n" for name, setting in values.items()),
                encoding="utf-8",
            )
            with self.subTest(key=key, value=value), self.assertRaises(
                lkt_inbox.InboxError
            ):
                lkt_inbox.load_blog_ssh_config(env)

    def test_rejects_duplicate_ssh_settings(self):
        env = self.root / "duplicate.env"
        env.write_text(
            "BLOG_SSH_TARGET=first@example.test\n"
            "BLOG_SSH_TARGET=second@example.test\n",
            encoding="utf-8",
        )
        with self.assertRaises(lkt_inbox.InboxError):
            lkt_inbox.load_blog_ssh_config(env)


class SshClientTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.key_path = Path("/tmp/fake-safe-key")
        self.config = lkt_inbox.SshConfig(
            "operator@example.test", 2222, self.key_path, "yes"
        )

    def runner(self, command, **kwargs):
        self.calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, self.stdout, b"")

    def test_lists_only_exact_final_filenames(self):
        good = "lkt-" + "ab" * 16 + ".json"
        self.stdout = (
            good.encode()
            + b"\0.lkt-temp.tmp\0lkt-not-a-receipt.json\0"
            + b"lkt-"
            + b"cd" * 16
            + b".json/extra\0"
        )
        client = lkt_inbox.SshSpoolClient(self.config, runner=self.runner)
        self.assertEqual(client.list_filenames(), [good])
        command = self.calls[0][0]
        self.assertIn("BatchMode=yes", command)
        self.assertIn("StrictHostKeyChecking=yes", command)
        self.assertNotIn("cat", command[-1])

    def test_fetch_is_bounded_and_rejects_unsafe_filename(self):
        self.stdout = b"{}"
        client = lkt_inbox.SshSpoolClient(self.config, runner=self.runner)
        filename = "lkt-" + "ab" * 16 + ".json"
        self.assertEqual(client.fetch(filename), b"{}")
        self.assertIn(
            f"head -c {lkt_inbox.MAX_ENVELOPE_BYTES + 1}", self.calls[0][0][-1]
        )
        with self.assertRaises(lkt_inbox.InboxError):
            client.fetch("../../private.pem")
        self.assertEqual(len(self.calls), 1)

    def test_delete_rechecks_digest_and_exact_path(self):
        self.stdout = b""
        client = lkt_inbox.SshSpoolClient(self.config, runner=self.runner)
        filename = "lkt-" + "ab" * 16 + ".json"
        digest = "f" * 64
        self.assertTrue(client.delete_if_unchanged(filename, digest))
        remote = self.calls[0][0][-1]
        self.assertIn("sha256sum", remote)
        self.assertIn(digest, remote)
        self.assertIn(f"{lkt_inbox.REMOTE_SPOOL}/{filename}", remote)
        with self.assertRaises(lkt_inbox.InboxError):
            client.delete_if_unchanged(filename, "not-a-digest")

    def test_transport_failure_never_echoes_stderr(self):
        secret = "private-message-body"

        def failed(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, b"", secret.encode())

        client = lkt_inbox.SshSpoolClient(self.config, runner=failed)
        with self.assertRaisesRegex(lkt_inbox.InboxError, "transport failed") as raised:
            client.list_filenames()
        self.assertNotIn(secret, str(raised.exception))


class ReceiveTests(ReceiverFixture):
    def test_receives_verifies_saves_and_only_then_deletes(self):
        client = FakeClient({self.filename: self.raw})
        report = self.receive(client)
        self.assertEqual(report["state"], "complete")
        self.assertEqual(report["receipts"][0]["state"], "remote_deleted")
        self.assertEqual(client.files, {})
        self.assertEqual(
            client.delete_calls,
            [(self.filename, hashlib.sha256(self.raw).hexdigest())],
        )

        envelope_path = self.config.inbox_dir / f"lkt-{self.receipt}.envelope.json"
        inquiry_path = self.config.inbox_dir / f"lkt-{self.receipt}.inquiry.json"
        self.assertEqual(envelope_path.read_bytes(), self.raw)
        inquiry = json.loads(inquiry_path.read_text(encoding="utf-8"))
        self.assertEqual(inquiry, sample_record())
        for path in (
            envelope_path,
            inquiry_path,
            self.config.db_path,
            self.config.status_path,
            self.config.log_path,
            self.config.lock_path,
        ):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

        status_data = self.config.status_path.read_text(encoding="utf-8")
        log_data = self.config.log_path.read_text(encoding="utf-8")
        with sqlite3.connect(self.config.db_path) as db:
            rows = db.execute(
                "SELECT receipt, created_at, processed_at, state FROM lkt_inbox_receipts"
            ).fetchall()
            schema = db.execute(
                "SELECT sql FROM sqlite_master WHERE type='table'"
            ).fetchall()
        self.assertEqual(
            rows,
            [(self.receipt, CREATED_AT, PROCESSED_AT, "remote_deleted")],
        )
        sanitized = status_data + log_data + json.dumps(schema)
        self.assertNotIn("reader@example.com", sanitized)
        self.assertNotIn("multilingual history", sanitized)
        self.assertNotIn("contact_email", sanitized)

    def test_invalid_envelope_leaves_remote_and_no_plaintext(self):
        broken = bytearray(self.raw)
        broken[-5] ^= 1
        client = FakeClient({self.filename: bytes(broken)})
        report = self.receive(client)
        self.assertEqual(report["state"], "partial")
        self.assertEqual(report["receipts"][0]["state"], "left_remote_unprocessed")
        self.assertIn(self.filename, client.files)
        self.assertEqual(client.delete_calls, [])
        self.assertFalse(
            (self.config.inbox_dir / f"lkt-{self.receipt}.inquiry.json").exists()
        )

    def test_fetch_failure_leaves_remote_and_uses_sanitized_state(self):
        client = FakeClient({self.filename: lkt_inbox.InboxError("contact secret")})
        report = self.receive(client)
        self.assertEqual(report["receipts"][0]["state"], "left_remote_unprocessed")
        serialized = (
            self.config.status_path.read_text() + self.config.log_path.read_text()
        )
        self.assertNotIn("contact secret", serialized)
        self.assertEqual(client.delete_calls, [])

    def test_delete_failure_keeps_verified_local_copy_and_retry_is_idempotent(self):
        client = FakeClient({self.filename: self.raw}, delete=False)
        first = self.receive(client)
        self.assertEqual(first["receipts"][0]["state"], "saved_local_remote_pending")
        self.assertIn(self.filename, client.files)
        self.assertTrue(
            (self.config.inbox_dir / f"lkt-{self.receipt}.inquiry.json").is_file()
        )
        client.delete = True
        second = self.receive(client)
        self.assertEqual(second["receipts"][0]["state"], "remote_deleted")
        self.assertNotIn(self.filename, client.files)
        with sqlite3.connect(self.config.db_path) as db:
            self.assertEqual(
                db.execute(
                    "SELECT state FROM lkt_inbox_receipts WHERE receipt=?",
                    (self.receipt,),
                ).fetchone()[0],
                "remote_deleted",
            )

    def test_existing_mismatched_local_file_fails_closed(self):
        self.config.inbox_dir.mkdir(parents=True)
        path = self.config.inbox_dir / f"lkt-{self.receipt}.envelope.json"
        path.write_bytes(b"different")
        path.chmod(0o600)
        client = FakeClient({self.filename: self.raw})
        report = self.receive(client)
        self.assertEqual(report["receipts"][0]["state"], "left_remote_unprocessed")
        self.assertIn(self.filename, client.files)
        self.assertEqual(client.delete_calls, [])

    def test_no_pending_writes_only_sanitized_status(self):
        report = self.receive(FakeClient())
        self.assertEqual(
            report,
            {
                "checked_at": PROCESSED_AT,
                "state": "no_pending",
                "receipts": [],
            },
        )
        self.assertEqual(json.loads(self.config.status_path.read_text()), report)

    def test_listing_failure_records_generic_status_and_raises(self):
        client = FakeClient(list_error=RuntimeError("ssh target and key path"))
        with self.assertRaisesRegex(
            lkt_inbox.InboxError, "could not be checked safely"
        ):
            self.receive(client)
        self.assertEqual(
            json.loads(self.config.status_path.read_text()),
            {"checked_at": PROCESSED_AT, "state": "unavailable"},
        )
        self.assertNotIn("ssh target", self.config.log_path.read_text())

    def test_lock_prevents_concurrent_receiver(self):
        with lkt_inbox.receiver_lock(self.config.lock_path):
            with self.assertRaises(lkt_inbox.LockBusy):
                self.receive(FakeClient())

    def test_never_loads_ssh_configuration_when_client_is_injected(self):
        with mock.patch.object(
            lkt_inbox, "load_blog_ssh_config", side_effect=AssertionError
        ):
            report = self.receive(FakeClient())
        self.assertEqual(report["state"], "no_pending")


if __name__ == "__main__":
    unittest.main()
