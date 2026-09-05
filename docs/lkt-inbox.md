# Encrypted service-fit inbox

`lkt_inbox.py` is the operator-side receiver for the LKT, manuscript, lecture,
and Story Clip fit checks accepted by the first-party WordPress endpoint. The web
server stores an encrypted envelope, not a readable inquiry. The receiver
downloads a final envelope over SSH, checks the entire cryptographic and
application contract, saves both copies locally, verifies them from disk, and
only then removes that exact unchanged remote file.

Run one check from this repository:

```bash
python lkt_inbox.py once
```

The receiver reads only `BLOG_SSH_TARGET`, `BLOG_SSH_PORT`, `BLOG_SSH_KEY`,
and `BLOG_SSH_STRICT_HOSTKEY` from the ignored sibling `BLOG/.env`. It does not
source that file or print those values. The RSA private key remains at the
ignored `.local/intake/lkt-fit-check-private.pem` path with mode `0600`.

Accepted final spool names have the exact form
`lkt-<32 lowercase hexadecimal characters>.json`. Temporary and unexpected
names are ignored. A valid envelope must use the pinned key fingerprint,
RSA-OAEP with SHA-1 for the 32-byte key wrap, AES-256-GCM with the contract AAD,
and either the legacy LKT v1 record or the routed `fit-check-record/v2` schema.
The v2 payload has a strict `lkt`, `manuscript`, `lecture`, or `story_clip`
offer discriminator and rejects fields from another offer. Authentication, schema, source,
timestamp, receipt, normalization, or persistence failures leave the remote
file in place.

Private inquiries are stored under the ignored `.local/inbound/lkt/` directory
with mode `0600`. The adjacent SQLite status, current status JSON, and JSONL
log contain only receipts, times, and processing states—never contact details
or inquiry content. The receiver does not reply, qualify a lead, or change a
revenue state.

For recurring operation, use:

```bash
python lkt_inbox.py loop --interval-minutes 15
```

The lock prevents two checks from processing an envelope concurrently. A
`remote_deleted` state means the encrypted file was durably received and then
removed from the server; it does not mean the request is qualified or paid.

## Live verification

The original LKT route was verified on 2026-09-04 with an explicitly labeled
synthetic request submitted through the visible fit-check page. On 2026-09-05,
the manuscript, lecture, and Story Clip pages each completed the same visible,
explicitly confirmed round trip using routed v2 records. All records were
authenticated, decrypted, saved in private mode `0600`, verified from disk,
and followed by deletion of only the unchanged remote envelope. The exact
synthetic local payload artifacts were then removed and the remote spool was
empty. Private visual evidence remains outside Git.

The current four-offer components are myblog commit
`0463dcb2470ad1c908597b7f4d636cf2d33013a1`, LazyingArtWebsite commit
`3ff43e4afc0dfd4512629443af198345696c170e`, and LazyPromotion receiver commit
`f8be630ea3c7a5b4aa90544ddc2b5b212e1a5445`. The 15-minute
`lazypromotion-lkt-inbox` loop is healthy and completed the Story Clip probe.
This is synthetic operational evidence, not a customer inquiry,
qualified lead, customer outcome, sale, or revenue.
