# Postiz operator integration

LazyPromotion uses Postiz for reviewed campaign drafts and scheduling across X,
Instagram, LinkedIn, and Reddit. YouTube is connected for reviewed first-party
videos. Hacker News remains a direct-browser channel because it is not a Postiz
integration.

## Components

- The official `postiz` CLI is the primary automation surface. It uses OAuth
  device authorization and stores credentials at `~/.postiz/credentials.json`
  with user-only permissions.
- The official remote MCP server is configured at `https://api.postiz.com/mcp`.
  It is disabled by default and limited to integration discovery, schema
  discovery, platform helpers, draft creation, post listing, and unpublished
  post settings. AI image/video tools are not enabled, so Postiz generation
  quota is not spent accidentally.
- The locally installed official `gitroomhq/postiz-agent` skill documents
  current platform settings and draft-first campaign patterns.
- `.local/private/` is ignored by Git and may hold local operator notes or
  non-secret integration metadata. Do not duplicate the OAuth token there.

## Safe operator use

Verify the official CLI connection without exposing a token:

```bash
postiz auth:status
postiz integrations:list
```

Start an operator Codex process with Postiz MCP enabled:

```bash
scripts/postiz-codex.sh
```

The wrapper reads the OAuth token from the official CLI store into the child
process environment. It never writes or prints the token. Ordinary worker model
subprocesses explicitly disable both the browser and Postiz MCP servers.

Use `type=draft` first. Review channel-specific copy and settings in the visible
Postiz calendar before scheduling or publishing. Public replies to discovered
individual needs continue through LazyPromotion's exact-content review queue.

Media stays in draft until a current full-playback review checks the opening,
middle, ending, transitions, readable text, audio, framing, and overall finish.
An old archive asset does not pass because it is project-owned or technically
valid. Only reviewed current media may represent LazyingArt or a paid offer.

Before changing any draft to scheduled state, fetch the live provider contract
with `postiz integrations:settings INTEGRATION_ID` and honor its `rules` plus
each field description. Provider-inapplicable settings can be silently ignored,
so a successful API response is not proof that the intended behavior survived.
Every media value must be the `.path` returned by `postiz upload`; never pass a
raw local path or unrelated external URL to a Postiz post.

The live 2026-08-31 MCP handshake returns 13 tools. Its current creation tool
is named `integrationSchedulePostTool`, despite the public MCP page still using
the older `schedulePostTool` name. The project allowlist follows the live schema
and should be rechecked after Postiz upgrades.

Postiz preserved the destination text in the X and Instagram drafts created by
the CLI during the 2026-08-31 validation. Recheck the visible editor after every
creation because provider transformations can change, and do not infer that a
URL will be clickable until the platform preview or final composer proves it.

On 2026-09-02, Postiz stripped both a bare GitHub URL and its protocol-less
variant from an unpublished X item. The reviewed replacement used the owned
`blog.lazying.art/?p=3167&...` route, which remained intact and resolved to the
canonical article with campaign attribution. The two broken unpublished drafts
were deleted only after the replacement was visibly queued; no published post
was removed. Prefer a verified owned route when a provider removes a direct
repository destination, and always compare the stored content with the source
campaign before leaving an item in the queue.

On 2026-09-01, the reviewed LKT X and Instagram items were moved to the Postiz
queue for 2026-09-08T01:00:00Z and 2026-09-08T11:31:00Z. The operator fetched
both live provider contracts first, kept the uploaded wide and 4:5 visuals,
confirmed the concept/not-inventory disclosures, and then updated both product
posts to lead with the first-party sample report instead of asking readers to
start with the fit check. The Instagram caption includes the measured
project-owned example and its explicit non-customer-result boundary; the
operator retained the original lazying.art URL rather than accepting a
shortlink. A fresh record and visible-calendar review confirmed the exact copy,
uploaded media, provider settings, unchanged times, and persisted `QUEUE`
state. At that review point, the Wenyan and eInk items remained drafts.

On 2026-09-05, the unpublished Instagram item was corrected after the current
LKT parser excluded index-only morphology rows. The visible editor retained the
same image, account, 2026-09-08T11:31:00Z schedule, original tracked URL, and
customer-result and hardware boundaries while changing only the measured
reference count to 16,800 current-code records. A fresh provider read confirmed
the exact correction and `QUEUE` state; no provider ID is stored in Git.

Also on 2026-09-05, a CLI-created LinkedIn video draft replaced a pinned GitHub
proof URL with a Postiz shortlink even though the item was still a draft. The
video, account, copy, and 2026-09-19T02:00:00Z time were visibly reviewed before
the item was scheduled once. A single visible edit then restored the pinned URL
and selected original URLs; a fresh provider read confirmed `QUEUE`, the exact
time and canonical copy, and no remaining shortlink. Treat draft creation as a
provider transformation boundary: inspect the stored URL before and after every
status change.

On 2026-09-02, a publication preflight caught a format mismatch after the two
Wenyan items had subsequently entered the queue. The X copy said the
`資治通鑑` edition was available in both color and black-and-white, while the
live canonical shelf exposed six black-and-white parts and no color link. The
Instagram copy could also be read as promising both formats for every named
history, although availability varies by title. The operator moved only those
two unpublished items from `QUEUE` back to `DRAFT`; no release existed and no
post was deleted. The tracked campaign source now states the exact current
inventory and uses a direct, campaign-tagged shelf URL. Any future scheduling
still requires a fresh visible preview and destination check.

On 2026-09-04, one real capture of the live passage-provenance viewer was
reviewed in Postiz for three distinct posts. The X draft exposed another
provider transformation: Postiz removed a final protocol URL, while retaining
the same owned route without the protocol. The operator corrected it in the
visible editor and verified the 245-character preview before scheduling. The
Instagram caption kept its full campaign URL and the LinkedIn version connected
the evidence-chain problem to the fixed USD 250 existing-machine sprint. All
three previews showed the project-owned image and exact bounded proof; the
provider records then independently reported `QUEUE` for
2026-09-16T02:00:00Z, 2026-09-17T12:00:00Z, and 2026-09-18T02:00:00Z. No
provider IDs are stored in Git. The newly connected YouTube channel was not used
for a static-image post. Instead, a 26-second first-party walkthrough was
rendered and inspected through the established LazyEdit video workflow, then
published and publicly verified at
<https://www.youtube.com/watch?v=UuVa-DaSAvI>. Its title, thumbnail, public
visibility, playback, and both LKT links were checked after release. Postiz
remains the reviewed scheduler for future channel posts; it did not submit this
video.

On 2026-09-05, a LinkedIn post for the Bilingual Lecture Pack was visibly
reviewed and queued for 2026-09-15T02:00:00Z. It leads with the practical
timestamp-first workflow, links to project-owned proof, keeps the original
campaign URL, and states the fixed USD 250 rights-cleared scope. The read-only
monitor confirmed the exact text, time, provider, and `QUEUE` state.

The LKT offer also gained one early LinkedIn slot at 2026-09-09T01:00:00Z. Its
complete preview showed the intended account, uploaded service cover, exact
USD 250 existing-machine scope, exclusions, and first-party sample-report URL.
The final visible confirmation kept that original URL instead of a Postiz
shortlink, and a provider read confirmed `QUEUE`. This is owned distribution,
not a lead or sale.

On 2026-09-07, the two lexical-ingestion drafts were replaced after the owned
proof page went live. Postiz stripped the protocol URL from the first X
replacement, so it was discarded and a second draft used the visibly reviewed
`lazying.art/lkt/lexical-ingest/` route. LinkedIn retained the complete tracked
owned URL. Provider reads matched both committed content hashes and returned
`DRAFT` with no release ID or release URL; the superseded drafts were removed
only after their replacements passed that check. After a final visible review,
the X and LinkedIn items entered the queue for 2026-09-17T01:00:00Z and
2026-09-17T02:00:00Z. Fresh provider reads and the visible Scheduled view
confirmed the exact copy, provider settings, and times. Neither item is yet
published, and queue state is not a lead or sale.

Later that day, the complete source-first lecture guide was published on
LazyBlog and one separate LinkedIn note was visibly reviewed for
2026-09-24T02:00:00Z, after the existing campaign calendar. The note teaches
why transcripts, translations, subtitles, and study books should derive from
stable timed segments, then links to the full English/Traditional
Chinese/Japanese article. The original tracked URL was retained without a
shortlink. A provider read confirmed `QUEUE`, the exact time, and the exact
text after normalizing Postiz's paragraph HTML. No provider ID is stored in
Git, and the queued note is not a lead or sale.

The Bilingual Lecture Pack video became the first verified YouTube release
scheduled through Postiz. The exact reviewed title, text, content hash, public
playback, and both first-party description links were checked at
<https://www.youtube.com/watch?v=G9NKncZgRis>. Postiz was the only publication
route; do not send the same LazyEdit package through AutoPublish after release.

On 2026-09-07, the queued LinkedIn AI Clip Assembly note was corrected after
the exact six-source proof went live. The visible editor replaced its stale
four-piece wording with one plain account of the 42-second master and 28-second
web cut. The original tracked LazyingArt URL, account, and
2026-09-28T02:00:00Z time were retained without a shortlink. A fresh provider
read returned the exact copy and `QUEUE` state with no release. This is a future
owned post, not publication, a lead, or revenue.

On 2026-09-12, that AI Clip Assembly note was moved back to `DRAFT` before
release. The older Desert Oasis clip had already been removed from the public
featured portfolio because it did not meet the current visual-quality bar; as
a precaution, the remaining AI-generated assembly proof must receive a fresh
human quality review before it can represent a paid service in social media.
The provider read confirmed one matching draft and no release URL.

Also on 2026-09-07, one LinkedIn note for the Book Specimen Sprint was reviewed
and queued. On 2026-09-11, after the encrypted fit-check path and Stripe
readiness were verified, the same reviewed note was moved forward from
2026-09-30T02:00:00Z to the open 2026-09-12T02:00:00Z slot. It explains why a
representative chapter should be tested as both a fixed print page and a
reflowable EPUB, then links to the live project-owned packet and the bounded
USD 250 fit-check route. The visible editor showed the first-party page capture,
correct account, revised time, scope, and original tracked URL. A provider read
returned one matching `QUEUE` record with no shortlink and no release. At
2026-09-12T02:00:00Z Postiz published the item at
<https://www.linkedin.com/feed/update/urn:li:share:7504358454258630656/>. A
fresh public-page review confirmed the exact copy, image, author profile, and
global visibility. The early visible state was two impressions with no reaction
or comment, while Postiz analytics still returned no rows. Publication and
impressions are attention, not a lead, sale, or revenue.

On 2026-09-11, one LinkedIn release note for LKT's read-only MCP bridge was
visibly reviewed and queued for 2026-10-02T02:00:00Z, after the existing
September calendar. Postiz initially substituted shortlinks while the item was
still a draft. The visible editor restored the public MCP documentation and
owned campaign URL, and the operator selected original URLs at the save and
schedule confirmations. A fresh provider read returned the expected LinkedIn
account, time, normalized content hash, original URLs, `QUEUE` state, and no
release URL. It is one bounded first-party release note, not publication, a fit
inquiry, a sale, or revenue.

Also on 2026-09-11, one tutor-facing L & N note was visibly reviewed and queued
for LinkedIn at 2026-09-25T02:00:00Z. It starts with the finished free
`light/night` lesson, then offers one fixed USD 250 bilingual pronunciation
mini-lesson after a fit check and written scope. The preview showed the correct
account, project-owned lesson image, exact copy, and local 10:00 AM time. The
original tracked L & N URL was selected instead of a Postiz shortlink. A fresh
provider read returned one exact normalized content match in `QUEUE`, with no
release URL. This is scheduled owned distribution, not a buyer inquiry or
revenue.

On 2026-09-12, a timed-frame review found that the shared L & N demonstration
used cross-fades that made headings, bilingual copy, and app screens overlap
during transitions. The Instagram, YouTube, and LinkedIn items were moved back
to `DRAFT` before publication. The separate text-only X item remains queued.
The media-backed items must not be rescheduled until a clean-cut replacement
passes the same timed-frame review.

Also on 2026-09-12, one LinkedIn note for the USD 400 KiCad plugin evaluation
was visibly reviewed and queued for 2026-09-29T02:00:00Z. It teaches a bounded
fixture method before mentioning the offer, uses the project-owned 3D fixture
render, and preserves the original tracked LazyingArt URL. A provider read
confirmed the current personal technical profile, exact normalized copy, one
attachment, future time, and `QUEUE` state with no release. The same post must
not be duplicated from a second LinkedIn or Reddit identity, and queueing is
not a lead or revenue.

The `v5` replacement uses hard cuts, contains the complete L/N teaching-model
regions instead of side-cropping them, and keeps both model words on the
listening slide. Boundary frames and audio timing passed review. The old
attachment was then replaced once in each visible Instagram, YouTube, and
LinkedIn editor. Each editor showed one uploaded replacement and the original
copy, and each save retained the original URL. A provider read returned all
three items as `DRAFT`; none was scheduled or published during the review.

A separate September 12 scheduling review rechecked the exact `v5` hash and a
fresh one-frame-per-second contact sheet, the earlier cut-boundary and audio
checks, all three current provider rule schemas, stored copy and settings, and
the live first-party destinations. YouTube is queued for September 13 at 02:30
UTC, Instagram for September 13 at 12:00 UTC, and LinkedIn for September 20 at
02:00 UTC. A fresh provider read returned each item in `QUEUE` with no release
URL. The rejected cross-faded source remains excluded; queue state is not
publication, feedback, a lead, a sale, or revenue.

The older project-made science scene published on Instagram was removed after
the creator rejected its visual quality. Its public reel route now reports
unavailable, and the matching Postiz record was deleted after the provider
removal. Do not recreate or reuse that scene. The complete project-owned
lecture-pack delivery packet is the current proof instead.

The reviewed Wenyan/Chinese-history shelf note published on Instagram at
<https://www.instagram.com/p/DdL78xymx_R/> on September 12. A fresh provider
read returned the exact caption, the intended account, `PUBLISHED` state, and
the public release route; that route returned HTTP 200. Initial Postiz metrics
were all zero. This is verified owned distribution, not a lead, sale, or
revenue result.

## Owned-post observation

The read-only owned-post monitor uses the official CLI to notice publication
failures and increases in post-level comments or replies:

```bash
python owned_monitor.py once
scripts/owned-monitor.sh start
scripts/owned-monitor.sh status
scripts/owned-monitor.sh stop
```

It matches campaign routes from normalized public copy, persists only a hashed
post identity, and never writes raw Postiz or integration IDs. Account-level
analytics remain reach evidence only. A post-level increase creates an operator
alert to inspect the public response in the visible browser; it is not a lead
and the monitor cannot reply. Missing release IDs and overdue queue states also
require visible review before any connecting or retry action. An unchanged
failure or already-overdue queue does not emit the same alert on every polling
cycle; a new state transition can alert again.

The wrapper keeps exactly one `lazypromotion-owned-monitor` tmux session and a
private sanitized log. It does not start Chrome, noVNC, or Firefox.

Threads is not connected to the current Postiz account. When the dedicated
project browser is already open, `python threads_inbound_monitor.py once`
checks the visible Replies activity page and aggregate reply counts on owned
profile cards without opening any notification. The profile fallback catches
replies that Threads omits from its Replies filter. It stores only opaque
fingerprints and aggregate counts. A new item or an unknown page layout creates
a visible-review alert; it cannot like, follow, message, or reply. The output of
`python owned_monitor.py status` includes this last sanitized Threads state
beside the Postiz schedule, aggregate application-inbox, and due-review
summaries.

The same review pattern was used for a value-first LKT guide post to the
connected Reddit account's own profile. The live provider contract and profile
restrictions confirmed normal text and link posts were allowed without flair.
The exact destination, title, standalone technical steps, maintainer
disclosure, and 2026-09-01T02:00:00Z time were reviewed before scheduling.
Postiz later reported the item as `PUBLISHED` with the exact public Reddit URL.
The provider page showed one matching post by the correct account. Reddit had
rendered the scheduled protocol-less destination as plain text, so the visible
editor was used to add only the `https://` prefix. The repaired anchor was then
clicked through the canonical LazyBlog article to the LKT fit-check page, with
the Reddit campaign fields intact and no form submission. The original Postiz
copy remains a route-matching alias for read-only monitoring. This is a
first-party profile resource, not an automated community submission.

## Quota and trust policy

- Draft text locally with the signed-in account's recommended Codex model at
  low reasoning effort. Set `LAZYPROMOTION_CODEX_MODEL` only when an explicit
  model is known to be available to that account.
- Reuse one grounded source package, then adapt the hook and call to action per
  channel instead of posting identical copy everywhere.
- Batch reviewed schedules in one API call when practical.
- Treat empty analytics series as no attributable evidence, not zero reach and
  not a successful campaign.
- Prefer the public reading shelf for readers and the GitHub pipeline for
  builders; never claim beginner grading, sales, users, or traction without
  evidence.
- Use campaign-specific UTM parameters and inspect Postiz analytics before
  repeating a theme.
