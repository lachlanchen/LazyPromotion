---
title: "Claude MCP Authentication: Public, Local, or Remote?"
slug: "claude-mcp-authentication-public-local-remote"
status: "publish"
source_language: "en"
author: "Lachlan Chen"
categories:
  - "Computer & Internet"
  - "Artificial Intelligence"
tags:
  - "MCP"
  - "Model Context Protocol"
  - "OAuth"
  - "Claude Code"
  - "FastMCP"
excerpt: "Choose MCP authentication from the deployment boundary: a deliberately public demo, a local developer server, or an OAuth-protected remote service for Claude."
---

The first question in MCP authentication is not “Which Claude client am I using?” It is “Who should be allowed to reach this server, and what changes when they do?”

A public demonstration, a local developer tool, and a remote service holding private data are three different systems. Treating them as one usually produces either needless login friction or an endpoint that is much more open than its owner intended.

| Deployment | Sensible first boundary | What it is good for |
| --- | --- | --- |
| Public demo with intentionally public data | No login, but strict limits | Documentation, evaluation, and small read-only examples |
| Local developer server | Loopback or stdio plus the local process boundary | One developer using Claude Code or MCP Inspector |
| Remote server with private or per-user data | OAuth-protected HTTPS | Claude connecting on behalf of identified users |

## A public demo can be deliberately unauthenticated

Authentication is unnecessary when every result is meant for every visitor. In that case, adding one shared “demo token” often creates the appearance of security without an authorization decision behind it.

The public choice should still be explicit and bounded:

- expose only the tools and resources needed for the demonstration;
- keep calls read-only when that is the promise;
- cap row counts, output size, execution time, and concurrency;
- apply rate limits at the internet-facing MCP boundary;
- make sure errors and logs do not disclose local paths, credentials, or neighboring data;
- keep private and production datasets out of the demo deployment.

This is a good fit for a small, baked dataset or a project-owned fixture. It is not a shortcut for exposing a private service.

## A local demo already has a boundary

For one developer, the shortest route is usually a server bound to loopback or launched as a local stdio process. FastMCP describes stdio authentication as inherited from the local execution environment; there is no MCP OAuth exchange on that transport.

This works well with Claude Code or MCP Inspector because the server does not need to become an internet service. Keep the listener on `127.0.0.1`, not all interfaces, and remember that anyone who can control the local process or configuration may inherit its authority.

Claude Desktop also supports local MCP configuration, but that is separate from its remote connector path. “Desktop” does not automatically mean the request stays on the laptop.

## A private remote server needs real OAuth

Once a remote MCP server returns private data, separates users, or has different permission levels, it should authenticate the client before initialization, discovery, or tool execution.

The current MCP authorization model treats the MCP server as an OAuth protected resource. The important pieces are:

1. serve the MCP endpoint over HTTPS;
2. return `401 Unauthorized` with a `WWW-Authenticate` challenge that points to protected-resource metadata;
3. publish the corresponding well-known metadata and identify the authorization server;
4. request a token for the canonical MCP resource;
5. validate issuer, expiry, scope, and the intended audience or resource at the MCP server;
6. accept bearer tokens in the `Authorization` header, never in the URL;
7. do not pass the MCP access token through to an upstream API.

Start with one narrow scope such as `records:read`. Add another scope only when a real tool needs a different authority. A tool name or `readOnlyHint` is useful description, but it does not replace token validation or authorization.

## What changes between Claude Code and remote connectors

Claude Code supports remote HTTP MCP servers and can complete an OAuth flow from its `/mcp` menu. When a protected server responds with `401` or `403`, Claude Code can discover the authorization path and guide the user through sign-in. It also supports static headers and a `headersHelper` for internal systems with another authentication scheme.

A fixed bearer token can be convenient during a closed developer test. It is a poor public design: it has no user consent, is easily copied, and usually gives every holder the same authority.

Claude's remote custom connectors behave differently from a local process. Anthropic's documentation says those connections originate from its cloud infrastructure, including when the user is in Claude Desktop. The MCP endpoint therefore needs to be reachable from that infrastructure. A laptop-only URL or a firewall rule limited to the developer's own IP will not work for the remote connector path.

For a private remote connector, combine that reachability with OAuth. Public reachability is not the same thing as public access.

## Fit authentication into FastMCP without mixing the APIs

FastMCP accepts an authentication provider when the server is created. A FastAPI-derived MCP server can keep its existing route conversion and pass the provider through:

```python
def build_mcp_app(api_app, *, auth=None):
    mcp = FastMCP.from_fastapi(
        app=api_app,
        name="example",
        route_maps=route_maps,
        auth=auth,
    )
    return mcp.http_app(path="/mcp")
```

Use an external identity provider rather than writing a new authorization server inside the project. FastMCP's `RemoteAuthProvider` is designed for identity providers that support dynamic client registration. Its OAuth proxy and provider integrations cover common providers that require a pre-registered application.

Keep client secrets in the deployment environment, not the repository. Cloud workload identities used for image pulls or deployments are also not automatically identities for MCP users; those are separate trust relationships.

There is one easy boundary to miss when MCP is generated from FastAPI: protecting `/mcp` does not automatically make `/data`, `/openapi.json`, or another ordinary API route private. Decide the policy for each surface and test it directly.

## Tests that make the decision reproducible

For a protected remote server, I would require these cases before enabling it:

- no token fails with `401` and a usable `WWW-Authenticate` challenge before tool discovery;
- expired, wrong-issuer, wrong-scope, and wrong-audience tokens fail;
- a valid least-privilege token can initialize, list the intended surface, and perform one representative call;
- health checks remain available without exposing application data;
- the ordinary API and MCP routes each follow their documented policy;
- logs and client-visible errors contain no bearer token or private context.

For a public demo, test the opposite decision: an anonymous client can use only the intended bounded surface, while oversized, malformed, or unexpected calls fail cleanly.

The right result is not always “add OAuth.” It is a deployment statement that another person can verify: public and bounded, local only, or remote and authenticated.

The [executed MCP boundary sample](https://lazying.art/mcp-boundary-review/sample-report/?utm_source=lazyblog&utm_medium=article&utm_campaign=mcp_boundary_review&utm_content=claude_auth_guide) shows how I record that decision with a pinned revision and sanitized protocol evidence. I use the same method for a [fixed USD 500 pre-deployment review](https://lazying.art/mcp-boundary-review/fit-check/?utm_source=lazyblog&utm_medium=article&utm_campaign=mcp_boundary_review&utm_content=claude_auth_guide_fit); the fit check starts with repository metadata, not source upload or payment.

## Primary references

- [MCP authorization specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
- [Claude Code: connect to tools with MCP](https://code.claude.com/docs/en/mcp)
- [Claude remote custom connectors](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)
- [FastMCP authentication](https://gofastmcp.com/servers/auth/authentication)
- [FastMCP authorization](https://gofastmcp.com/servers/authorization)
