---
title: "Fix GitHub MCP ‘Requires Authentication’ in Docker Sandboxes"
slug: "github-mcp-requires-authentication-docker-sandboxes"
status: "publish"
source_language: "en"
author: "Lachlan Chen"
categories:
  - "Computer & Internet"
  - "Artificial Intelligence"
tags:
  - "Docker Sandboxes"
  - "GitHub Copilot"
  - "MCP"
  - "Authentication"
  - "Developer Tools"
excerpt: "Separate the Docker sandbox secret, Copilot CLI's built-in GitHub MCP server, and workspace overrides when GitHub MCP still says it requires authentication."
---

When Copilot CLI reports `MCP server 'github-mcp-server' requires authentication` inside Docker Sandboxes, adding another token to another JSON file is rarely the best first move.

Three pieces are easy to confuse:

1. Docker Sandboxes supplies a GitHub credential through its host-side secret system.
2. Copilot CLI includes its own GitHub MCP server.
3. A repository can replace that built-in server with a project-level MCP definition.

Check them in that order.

## Give the existing sandbox its own GitHub secret

Docker's global service secrets apply when a sandbox is created. If the sandbox already existed when the GitHub secret was added or changed, bind the secret directly to that sandbox:

```bash
sbx secret set github --sandbox <sandbox-name> --command 'gh auth token'
```

The command runs on the host. Docker stores the resolver rather than requiring the token to be pasted into a repository or shell command.

For a new sandbox, set the global secret before creation:

```bash
sbx secret set github --command 'gh auth token'
```

The selected GitHub account must have Copilot access. A global secret added after a sandbox starts will not repair that existing sandbox; either use the sandbox-scoped form or recreate it.

## Test the built-in server before adding another one

Copilot CLI already ships with `github-mcp-server`. From an active Copilot session, inspect it with:

```text
/mcp show github-mcp-server
```

Now check the project root for `.mcp.json` and `.github/mcp.json`. Copilot CLI loads those files inside the sandbox, and a project-level definition named `github-mcp-server` takes precedence over the built-in definition.

That override may be intentional, but it changes the authentication path. Rename or temporarily remove the override for the first test. Do not expect the host's `~/.copilot/mcp-config.json` to appear inside the sandbox: Docker Sandboxes exposes project-level configuration from the mounted workspace, not the host's user-level Copilot configuration.

## Enable write tools without replacing the server

The built-in GitHub MCP server starts with a read-only tool selection. To expose its broader tool set for one Copilot run, add GitHub's supported flag after the Docker Sandboxes argument separator:

```bash
sbx run docker.io/sbx/copilot-kit:latest <project> -- --enable-all-github-mcp-tools
```

Docker Sandboxes v0.42 requires the full kit image name shown above. Releases with the `copilot` shorthand can use the same trailing flag with their usual `sbx run copilot ...` command.

Enabling tools does not grant permissions that the GitHub credential lacks. Prefer a fine-grained token with only the repositories and operations the agent actually needs.

## Use one small diagnostic split

If authentication still fails, open a shell in the running sandbox and check the GitHub CLI without printing its token:

```bash
sbx exec -it <sandbox-name> bash
gh auth status
```

The result narrows the problem:

| Observation | Likely boundary to inspect |
| --- | --- |
| `gh auth status` also fails | Docker sandbox secret scope or the host resolver account |
| `gh` works but the built-in MCP server fails | Copilot kit or MCP credential wiring |
| A differently named MCP server works | A same-name project override is shadowing the built-in server |
| Read operations work but writes fail | Enabled tool selection or GitHub token permissions |

Avoid printing environment variables, dumping configuration files that may contain headers, or committing a bearer token to `.mcp.json`. The useful evidence is which boundary succeeds, not the credential value.

For a different remote MCP server, the same habit applies: identify the client, transport, credential source, and exact authority before widening access. This [executed MCP boundary sample](https://lazying.art/mcp-boundary-review/sample-report/?utm_source=lazyblog&utm_medium=article&utm_campaign=mcp_boundary_review&utm_content=docker_sbx_auth_guide) shows the resulting evidence packet. A [metadata-only fit check](https://lazying.art/mcp-boundary-review/fit-check/?utm_source=lazyblog&utm_medium=article&utm_campaign=mcp_boundary_review&utm_content=docker_sbx_auth_guide_fit) comes before repository access or payment.

## Primary references

- [Docker Sandboxes: Copilot](https://docs.docker.com/ai/sandboxes/agents/copilot/)
- [Docker Sandboxes: manage credentials](https://docs.docker.com/ai/sandboxes/configuration/credentials/)
- [Docker Sandboxes: run commands inside a sandbox](https://docs.docker.com/ai/sandboxes/usage/)
- [GitHub Copilot CLI: add MCP servers](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers)
- [GitHub MCP Server: Copilot CLI installation](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-copilot-cli.md)
