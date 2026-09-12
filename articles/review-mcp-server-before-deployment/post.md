---
title: "Ten Checks Before You Deploy an MCP Server"
slug: "review-mcp-server-before-deployment"
status: "publish"
source_language: "en"
author: "Lachlan Chen"
categories:
  - "Computer & Internet"
  - "Artificial Intelligence"
tags:
  - "MCP"
  - "Model Context Protocol"
  - "software testing"
  - "deployment"
excerpt: "A practical pre-deployment review for an MCP server: pin the protocol era and code revision, compare advertised and live capabilities, exercise valid and invalid calls, map real authority, and finish with an evidence-backed go/no-go decision."
---

An MCP server can pass a clean demo and still be unclear at the boundary that matters: what can it actually read, write, disclose, or call when an agent uses it?

The useful review is not a vague security score. It is a short, reproducible answer to a deployment question. Freeze the exact server and client, exercise the live protocol surface, follow each operation into the underlying code, and record what happened. These ten checks are a practical starting point.

## 1. Pin the protocol era, client, transport, and code

Start with a run manifest. Record the repository revision, SDK and runtime versions, client, transport, launch command, operating system, fixtures, and the deployment decision you are trying to make.

This matters more now because MCP has two substantially different protocol eras in active use. The official TypeScript SDK describes the 2025 family as a legacy, initialization-based era and the `2026-07-28` revision as a stateless era with `server/discover` and a metadata envelope on each request. Its migration guide also notes that using the new SDK does not automatically put the new revision on the wire; the modern era is an explicit choice.

Do not write “tested with MCP” when the result actually means “tested revision X, through client Y, over transport Z, at code revision A.”

## 2. Record what the server advertises

Capture the server's declared capabilities and the complete live inventory of tools, resources, prompts, and extensions. Save names, descriptions, schemas, annotations, and pagination or cache metadata where the selected protocol revision supports them.

Then compare that inventory with the repository and its documentation. A tool mentioned in the README but absent at runtime is a compatibility problem. A live tool that is missing from the documentation is more serious: reviewers and users may not know that the authority exists.

Keep the raw protocol response as evidence. A screenshot of a client menu is convenient, but it can hide schema details and client-side filtering.

## 3. Exercise one valid tool call

Choose a representative, non-destructive tool and call it with a small fixture. Save the request, response, exit state, and relevant sanitized logs. Check the result against the source rather than merely accepting valid JSON.

For a search tool, that might mean confirming that returned snippets come from the expected collection, citations resolve to the right source units, limits are honored, and no unrelated records appear. For a calculation or transformation, keep a known-answer fixture.

The goal is not broad functional testing. It is to establish one complete chain from protocol input to underlying operation and back to the client.

## 4. Exercise one valid resource read

Tools and resources are different surfaces, so test both when both exist. Resolve one advertised resource URI and confirm its content, media type, size, provenance, and access boundary.

A resource read should not silently expand into a directory traversal, fetch a neighboring record, or return an entire private object when the client asked for one bounded unit. If the server builds the result from a database, index, filesystem, or network request, record that dependency in the authority map.

Large results need a handoff test of their own. Keep list operations bounded with opaque cursors. For a large tool result, return a short summary plus a resource link or another client-resolvable reference instead of dumping everything into context. Record the media type, byte size, source revision, and expiry or cleanup behavior.

A raw server-local path is not a portable handoff. It is useful only when the intended client shares that filesystem and has permission to read it; otherwise it is dead output that may also disclose host layout. Whatever reference is returned should preserve the same access boundary as the source data.

## 5. Send unknown names and malformed input

Happy-path demos say little about how a server fails. Try an unknown tool or resource, a missing required field, a wrong type, an oversized but still safe value, and one malformed request appropriate to the protocol era.

The server should reject bad input consistently, without executing a partial action or returning a stack trace full of local paths and configuration. Record both the protocol error and the server log. They often reveal different problems.

Do not hard-code one expected error from an older revision without pinning the era. The 2026 release changed parts of the request model and some error behavior, which is precisely why the run manifest belongs at the front of the report.

## 6. Trace actual authority, not names

A tool named `preview`, `lookup`, or `read` is not necessarily read-only. Follow its code and runtime configuration far enough to list:

- files, databases, and indexes it can read;
- files, databases, or queues it can change;
- external services it can contact;
- credentials it can use;
- approvals or confirmations that can stop the operation;
- the plausible effect of failure.

Repeat the same exercise for resource handlers and any server-initiated or extension behavior. The output is a compact authority map, not a guess based on naming.

## 7. Treat annotations as claims to verify

Tool annotations are useful vocabulary. They can describe whether a tool appears read-only, destructive, idempotent, or externally connected. The MCP maintainers are equally clear about their limit: annotations are hints, not enforcement.

Compare each annotation with the implementation and the client behavior. If `readOnlyHint` is present, verify that the operation and its dependencies do not write. If an action can change state, check whether the client actually changes its approval behavior. A correct label is helpful; it does not replace a permission boundary.

## 8. Look for disclosure in outputs and logs

Run the agreed valid and invalid cases, then inspect what reached the client and what was written to logs. Look for tokens, connection strings, private prompts, local paths, neighboring records, raw exception objects, source text beyond the requested limit, and internal URLs.

For remote HTTP servers, authorization needs its own evidence. The MCP authorization specification requires protected servers to bind tokens to the intended resource and forbids putting access tokens in query strings. The transport specification also calls for origin validation, local-only binding when appropriate, and authentication for connections.

A server can perform no writes and still be unsafe to expose remotely because it discloses private context to any caller.

## 9. Force one safe failure or timeout

Choose one failure that can be produced without harming production: an unavailable fixture, a bounded timeout, a refused network dependency, or a deliberately rejected operation. Confirm that the request ends, the client receives a useful error, partial state is not left behind, and a retry does not duplicate work.

If the tool has side effects, perform this check only in a disposable environment with an explicit rollback. “It probably fails safely” is not evidence.

## 10. End with a narrow deployment decision

The report should end with the exact boundary supported by the evidence:

- **GO:** the recorded server revision, client, transport, fixtures, and exposure model;
- **NO-GO:** a specific deployment that the evidence does not support;
- unresolved limits and the smallest next change or test;
- checks that passed, failed, or could not be run;
- hashes or revisions for the evidence packet.

In one public Local Knowledge Terminal sample, the executed surface contained two tools and one resource. Fourteen focused tests passed, and the source database timestamp stayed unchanged. That supported a local read-only use case. It did not support direct remote exposure, because the standalone HTTP bridge had no client authentication. The same server therefore received a local GO and a remote NO-GO without pretending that either decision proved universal security.

That is the point of a pre-deployment review: not to certify a whole product, but to make one real decision from evidence someone else can reproduce.

The [complete sample report and protocol packet](https://lazying.art/mcp-boundary-review/sample-report/?utm_source=lazyblog&utm_medium=article&utm_campaign=mcp_boundary_review&utm_content=pre_deployment_guide) show the format. I also offer the same bounded method as a [fixed USD 500 review](https://lazying.art/mcp-boundary-review/fit-check/?utm_source=lazyblog&utm_medium=article&utm_campaign=mcp_boundary_review&utm_content=pre_deployment_guide_fit) of one server, one base revision, and ten agreed checks, with a limited recheck. The fit check uses repository metadata first; no source upload or payment is needed to establish scope.

## Primary references

- [MCP 2026-07-28 specification release](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
- [MCP TypeScript SDK protocol versions](https://ts.sdk.modelcontextprotocol.io/v2/protocol-versions)
- [MCP TypeScript SDK migration guide for 2026-07-28](https://ts.sdk.modelcontextprotocol.io/v2/migration/support-2026-07-28)
- [MCP tool annotations: what hints can and cannot do](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/)
- [MCP tool results and resource links](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [MCP resources and URI handling](https://modelcontextprotocol.io/specification/2025-11-25/server/resources)
- [MCP opaque-cursor pagination](https://modelcontextprotocol.io/specification/2025-11-25/server/utilities/pagination)
- [MCP transport requirements](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
- [MCP authorization requirements](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
