# Contra MCP operator path

LazyPromotion uses Contra's official Streamable HTTP MCP endpoint at
`https://contra.com/mcp`. It gives a new Codex session a credential-free way to
inspect the existing Contra account and its opportunity feed without opening a
personal browser.

## Configuration

The project-scoped [`.codex/config.toml`](../.codex/config.toml) registers the
server as `contra`. Account-changing tools use the `writes` approval mode;
read-only inspection remains available to a trusted project session.

```bash
codex mcp list
codex mcp get contra
codex mcp login contra
```

OAuth credentials stay in Codex's private credential store for the current OS
user. They are not copied into this repository. Agents can find the private
handoff through `.local/private/CREDENTIALS.md`; the synced encrypted Markdown
vault is under the private LazyingArt area in Nutstore. Neither pointer contains
an access token.

## Write boundary

Contra documents a two-step prepare-and-confirm flow for every account change.
The preview expires after 15 minutes if it is not confirmed. Keep that boundary
for messages, proposals, applications, projects, products, invoices, payment
links, and payments. Do not reinterpret an old blanket instruction as approval
of a newly prepared financial or legal action.

Identity verification, payout onboarding, contracts, tax declarations, and
residence fields must use accurate operator-reviewed facts. Never infer a
person's residence from a company address, workstation timezone, or IP address.

## Verified state on 2026-09-11

- OAuth authentication succeeds and the account role is `Contractor`.
- `list_job_feed` succeeds with `ALL` and `FOR_YOU`.
- Both presets returned the same three visible listings from a reported 241-item
  feed, marked access-limited with no next page.
- The three listings were design, marketing/legal, and presentation work. None
  matched the public LazyingArt proof closely enough to apply.
- No listing, feed view, account connection, application, inquiry, contract, or
  platform balance is a lead or received revenue.

Current server capabilities and the confirmation model are documented by
[Contra](https://contra.com/features/mcp). Codex's supported HTTP/OAuth setup is
documented by [OpenAI](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
