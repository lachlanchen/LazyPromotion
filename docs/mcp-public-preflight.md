# MCP public-repository preflight

`mcp_public_preflight.py` turns one clean public GitHub repository URL into a
private, review-ready scope report for the fixed USD 500 MCP Server
Pre-Deployment Review.

```bash
python mcp_public_preflight.py https://github.com/owner/repository
```

Before running it, inspect the project-owned
[browser sample](https://lazying.art/mcp-boundary-review/preflight-sample/?utm_source=github&utm_medium=repository&utm_campaign=mcp_boundary_review&utm_content=preflight_tool_docs)
or download its exact generated Markdown. The sample is the static first step;
the separate executed report shows what the paid review adds.

The preflight pins the default-branch commit and tree, reads a bounded set of
public text blobs through explicit GitHub API GET requests, and records likely
tools, resources, prompts, transports, configuration names, external hosts,
and side-effect names. It proposes the ten review checks and lists the client,
transport, authority, and decision questions still needed before a paid scope
can be accepted.

It does not clone the repository, execute repository code, read private
repositories, submit a fit check, create a payment, or claim a security finding.
Output is written with owner-only permissions under the Git-ignored
`.local/mcp-preflight/` directory. Review the generated Markdown before using
any part of it in a buyer conversation.

Only a clean repository-root URL is accepted. Paths to branches, files, issues,
query strings, fragments, credentials, alternate hosts, and non-HTTPS URLs are
rejected.
