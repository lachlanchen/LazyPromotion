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

On 2026-09-01, the reviewed LKT X and Instagram items were moved to the Postiz
queue for 2026-09-08T01:00:00Z and 2026-09-08T11:31:00Z. The operator fetched
both live provider contracts first, kept the uploaded wide and 4:5 visuals,
confirmed the concept/not-inventory disclosures, changed both destinations to
the verified fit-check page, declined URL shortening, and then verified the
persisted `QUEUE` records. The Wenyan and eInk items remained drafts.

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
