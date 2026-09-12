---
title: "Why MCP Client Credentials Fail When OAuth Discovery Is Missing"
slug: "mcp-client-credentials-oauth-discovery-missing"
status: "publish"
source_language: "en"
author: "Lachlan Chen"
categories:
  - "Computer & Internet"
  - "Artificial Intelligence"
tags:
  - "MCP"
  - "OAuth"
  - "Client Credentials"
  - "Authentication"
  - "Developer Tools"
excerpt: "Separate the MCP resource, authorization-server issuer, and token endpoint when a machine client has valid credentials but discovery never reaches the token request."
---

A machine client can have the right client ID, secret, scope, and token endpoint and still fail before it sends a token request. The usual reason is not `client_secret_basic`. It is that the client cannot discover where the authorization server is or which URL is its token endpoint.

That distinction matters because this setting:

```json
{
  "token_endpoint_auth_method": "client_secret_basic"
}
```

chooses how the client authenticates at a token endpoint. It does not tell the client where that endpoint is.

## Keep the three addresses separate

For an HTTP MCP connection, write down three different values before changing credentials:

| Value | Example | What it identifies |
| --- | --- | --- |
| MCP resource | `https://mcp.example.com/mcp` | The protected server the token will be used with |
| Authorization-server issuer | `https://auth.example.com` | The authority that issues and validates the token relationship |
| Token endpoint | `https://auth.example.com/oauth/token` | The URL that receives the client-credentials request |

The normal MCP path discovers them in order. The protected MCP server publishes OAuth Protected Resource Metadata, including its authorization server. The authorization server then publishes RFC 8414 or OpenID Connect metadata containing `issuer`, `token_endpoint`, and supported authentication methods.

The current MCP authorization specification requires that discovery path for conforming HTTP servers and clients. The optional OAuth Client Credentials extension inherits the baseline authorization requirements; it changes the grant from an interactive user flow to a pre-registered machine identity, not the discovery model.

## Find the missing hop without exposing a secret

Start with requests that contain no credential. For a root-level example:

```bash
curl --silent --show-error --include https://mcp.example.com/mcp

curl --fail --silent --show-error \
  https://mcp.example.com/.well-known/oauth-protected-resource/mcp \
  | jq '{resource, authorization_servers, scopes_supported}'

curl --fail --silent --show-error \
  https://auth.example.com/.well-known/oauth-authorization-server \
  | jq '{issuer, token_endpoint, token_endpoint_auth_methods_supported}'
```

Issuer URLs with a path use a different well-known URL order, so follow the MCP discovery rules rather than guessing the path.

The result usually falls into one of four cases:

| Observation | Meaning |
| --- | --- |
| The first response supplies `resource_metadata` | Follow and validate that exact metadata URL |
| No challenge URL, but the protected-resource well-known document works | The client should use its standards fallback |
| Resource metadata names an issuer, but its metadata returns HTML or redirects elsewhere | Authorization-server discovery is the broken hop |
| A token endpoint works only when entered manually | Credentials may be valid, but the deployment is missing discoverable metadata |

Do not diagnose this by printing environment variables, command-line arguments, token-cache files, or full debug headers. Status codes, content types, requested origins, and sanitized metadata fields are enough.

## If you control the server, publish metadata

The durable repair is to make the deployment discoverable:

1. Return a valid `WWW-Authenticate` challenge or host OAuth Protected Resource Metadata at the required well-known path.
2. List the authorization-server issuer that is actually allowed to mint tokens for this MCP resource.
3. Publish authorization-server metadata with an exact matching `issuer`, the HTTPS `token_endpoint`, and the supported token-endpoint authentication methods.
4. Validate token issuer, intended audience or resource, expiry, and scope at the MCP server.

This is more than convenience. Discovery binds the resource, issuer, and endpoints so a client does not invent that relationship from a redirect or an HTML error page.

## If you control only the client, keep the fallback narrow

Some internal or legacy services have a known token endpoint but cannot add discovery immediately. An explicit endpoint can be a useful compatibility option, but it does not make the server conform to the MCP authorization specification.

A safe client-side fallback should:

- work only with the non-interactive `client_credentials` grant;
- require HTTPS, apart from an explicit loopback development exception;
- reject endpoint URLs containing embedded credentials or fragments;
- avoid discovery requests once the operator has supplied the exact endpoint;
- keep cached tokens separate when the MCP resource or token endpoint changes;
- keep the client secret outside source files and process arguments; and
- continue sending the canonical MCP resource in the token request when the authorization server supports the MCP flow.

As of 13 September 2026, the npm release of `mcp-remote` is 0.13.5 and does not document an explicit token-endpoint option. [Issue 361](https://github.com/punkpeye/mcp-remote/issues/361) records the no-discovery case, while [pull request 362](https://github.com/punkpeye/mcp-remote/pull/362) proposes a guarded `--token-endpoint` option. That pull request is still under review, so check the installed command's `--help` output and the release notes instead of copying an unreleased flag into production.

## Test the second token, not only the first

A one-time `tools/list` success is not enough. The client-credentials grant normally obtains a new access token by repeating the authenticated token request; RFC 6749 says a refresh token should not normally be included.

Cover at least these cases:

1. Obtain the first token, initialize MCP, and list the expected tools.
2. Expire or invalidate that token in a controlled test, then obtain a second token without opening a browser.
3. Return one authentication failure from the MCP resource and confirm that retry follows the same endpoint and scope boundary without looping.
4. Change the configured token endpoint and prove that the earlier cached token is not reused.
5. Reject HTTP remote endpoints, malformed URLs, embedded credentials, fragments, and use outside `client_credentials`.
6. Inspect logs and failure artifacts for client secrets, bearer tokens, and unredacted headers.

This separates a working token exchange from a working MCP authentication lifecycle.

If you are reviewing an unfamiliar server before exposing it to an agent, this [executed MCP boundary sample](https://lazying.art/mcp-boundary-review/sample-report/?utm_source=lazyblog&utm_medium=article&utm_campaign=mcp_boundary_review&utm_content=client_credentials_discovery_guide) shows the evidence packet I use. The fixed USD 500 pre-deployment review covers one pinned server revision and ten agreed checks; the [metadata-only fit check](https://lazying.art/mcp-boundary-review/fit-check/?utm_source=lazyblog&utm_medium=article&utm_campaign=mcp_boundary_review&utm_content=client_credentials_discovery_guide_fit) comes before source upload or payment.

## Primary references

- [MCP 2026-07-28 authorization specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- [MCP authorization-server discovery](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/authorization-server-discovery)
- [MCP OAuth Client Credentials extension](https://modelcontextprotocol.io/extensions/auth/oauth-client-credentials)
- [OAuth 2.0 client credentials grant, RFC 6749 section 4.4](https://www.rfc-editor.org/rfc/rfc6749.html#section-4.4)
- [OAuth Authorization Server Metadata, RFC 8414](https://www.rfc-editor.org/rfc/rfc8414.html)
- [OAuth Protected Resource Metadata, RFC 9728](https://www.rfc-editor.org/rfc/rfc9728.html)
- [`mcp-remote` issue 361](https://github.com/punkpeye/mcp-remote/issues/361)
- [`mcp-remote` pull request 362](https://github.com/punkpeye/mcp-remote/pull/362)
