# Postiz operator integration

LazyPromotion uses Postiz for reviewed campaign drafts and scheduling across X,
Instagram, and Reddit. Hacker News remains a direct-browser channel because it
is not a Postiz integration.

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

## Owned-post observation

The read-only owned-post monitor uses the official CLI to notice publication
failures and increases in post-level comments or replies:

```bash
python owned_monitor.py once
python owned_monitor.py loop --interval-minutes 15
```

It matches campaign routes from normalized public copy, persists only a hashed
post identity, and never writes raw Postiz or integration IDs. Account-level
analytics remain reach evidence only. A post-level increase creates an operator
alert to inspect the public response in the visible browser; it is not a lead
and the monitor cannot reply. Missing release IDs and overdue queue states also
require visible review before any connecting or retry action.

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

- Draft text locally with `gpt-5.6-sol` at low reasoning effort.
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
