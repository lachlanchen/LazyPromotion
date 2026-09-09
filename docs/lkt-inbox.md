# Encrypted service-fit inbox

## Current status

Direct web submission is live for the LKT and lecture routes as of 2026-09-09.
Each deployed frontend, the pinned public-key fingerprint, mode-`0600` private
key, receiver, and remote spool completed an explicitly confirmed synthetic
round trip. Manuscript and Story Clip still review locally and continue through
email or copy. Do not re-enable another route until those same checks succeed
for that route.

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

For one recurring receiver, use:

```bash
scripts/lkt-inbox.sh start
scripts/lkt-inbox.sh status
scripts/lkt-inbox.sh stop
```

The project-owned wrapper keeps one `lazypromotion-lkt-inbox` tmux session and a
private sanitized stdout log. The receiver lock also prevents two checks from
processing an envelope concurrently. A
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

The historically verified four-offer components are myblog commit
`0463dcb2470ad1c908597b7f4d636cf2d33013a1`, LazyingArtWebsite commit
`3ff43e4afc0dfd4512629443af198345696c170e`, and LazyPromotion receiver commit
`f8be630ea3c7a5b4aa90544ddc2b5b212e1a5445`. The earlier
`lazypromotion-lkt-inbox` loop completed the Story Clip probe and
was stopped during recovery; `scripts/lkt-inbox.sh` is now the canonical wrapper
for that single session name. The email-or-copy mitigation was introduced by
LazyingArtWebsite commit `1ba106beadff2de89d71874fa2df6379e6eb35fb` and
remains live in current deployment `e4a1c36b3efa93399b6a5754f3692c1802a211c7`.
This is synthetic operational evidence, not a customer inquiry,
qualified lead, customer outcome, sale, or revenue.

On 2026-09-07 the lecture route was restored by LazyingArtWebsite commit
`135e2827d1210db84f98054ac717db8a3b6df64a`. One labeled request passed the
visible review and confirmation gates, returned HTTP 202, was decrypted and
saved privately, and was deleted remotely only after unchanged verification. A
second check returned `no_pending`. Its private synthetic artifacts are retained
outside Git.

On 2026-09-09 the LKT route was restored by LazyingArtWebsite commit
`04d9ec740ef2ec467a7ea25e9e0cd3525a94dd5b`. After deployment, one labeled
request passed the visible review and confirmation gates, returned HTTP 202,
matched the routed LKT schema after decryption, persisted with mode `0600`, and
was deleted remotely only after unchanged verification. A second receiver check
returned `no_pending`. Its private synthetic artifacts and browser snapshot are
retained outside Git. Manuscript and Story Clip remain disabled for direct
submit. This test is not a lead, customer result, payment, delivery, or revenue.
