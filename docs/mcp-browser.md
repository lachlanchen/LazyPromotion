# Browser MCP attachment

LazyPromotion includes an optional, project-scoped Codex configuration for
[Microsoft Playwright MCP](https://github.com/microsoft/playwright-mcp). It is
an additive control surface over the same visible Chrome instance—not a second
browser, profile, login, or source of truth.

## Why this server

- Apache-2.0 open source with an official `--cdp-endpoint` attachment mode.
- Uses the same Playwright model as `browser.py`, which keeps selectors and
  debugging concepts consistent.
- Attaches to the existing loopback-only CDP endpoint at
  `http://127.0.0.1:9436`.
- The package is pinned to `@playwright/mcp@0.0.79`; updates are deliberate
  repository changes instead of silent runtime changes.
- `browser_close` and `browser_install` are disabled so an MCP call cannot stop
  the shared review browser or download a redundant browser.

The MCP is optional (`required = false`). The direct `browser.py` controller
remains the fallback and the only supported public-send path because it checks
the destination, exact draft hash, short-lived approval, visible composer, and
post-send evidence as one transaction.

## Use it with Codex

Start the project-owned desktop first:

```bash
scripts/desktop.sh start
curl --fail --silent http://127.0.0.1:9436/json/version
```

Trust this repository when Codex asks. Codex then loads
`.codex/config.toml`, starts the pinned stdio server on demand, and attaches it
to the already-running Chrome. Confirm the project-scoped entry from the
repository root:

```bash
codex mcp list
codex mcp get lazypromotion_browser
```

Good MCP tasks include listing tabs, inspecting accessibility snapshots,
checking selectors, reading console errors, and taking screenshots. MCP tools
that mutate browser state use Codex's `writes` approval mode.

## Trust boundary

CDP grants complete control of the attached browser profile. The launcher binds
CDP, VNC, and noVNC only to `127.0.0.1`, and `.local/` is ignored by Git. Do not
expose port `9436`, commit the profile, or browse unrelated sensitive accounts
while an untrusted MCP client is attached.

MCP convenience never bypasses the review contract:

1. Search narrowly and inspect the full destination plus community rules.
2. Draft one relevant response with an honest affiliation disclosure.
3. Prepare the exact text visibly.
4. Obtain an explicit human approval for that exact destination and content.
5. Use `promotion.py approve` and `browser.py send`; never ask a generic MCP
   click/type tool to perform the public send.

Search syntax is not treated as evidence that a result matches. Reviewed
high-intent routes may define `required_body_groups`; after the full body is
hydrated, each group must contribute a distinct signal such as ownership,
document-search intent, and local/privacy need. `excluded_body_any` prevents a
self-announced tool from consuming model quota on a buyer-intent route. The
general help detector makes the same distinction, while still allowing a
builder who states a direct unresolved request.
Only candidates that pass these gates receive the durable model-triage
admission marker. Failed model calls can retry from that admitted backlog;
unqualified search results remain available as private research evidence but
cannot consume later model capacity.

## Verification and fallback

Check the package and advertised CDP option without launching another browser:

```bash
npx --yes @playwright/mcp@0.0.79 --version
npx --yes @playwright/mcp@0.0.79 --help | grep -- '--cdp-endpoint'
```

If the MCP server cannot attach, verify `scripts/desktop.sh status` and the CDP
JSON endpoint, then continue with `python browser.py status`. Restart the single
project-owned stack only when its authoritative status is unhealthy; do not
launch a replacement browser from the MCP server.
