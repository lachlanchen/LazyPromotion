#!/usr/bin/env bash
set -euo pipefail

postiz_credentials="${POSTIZ_CREDENTIALS_FILE:-${HOME}/.postiz/credentials.json}"

if [[ ! -r "${postiz_credentials}" ]]; then
  echo "Postiz credentials are unavailable; run: postiz auth:login" >&2
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to load the private Postiz OAuth credential" >&2
  exit 1
fi

POSTIZ_API_KEY="$(jq -er '.accessToken | select(type == "string" and startswith("pos_"))' "${postiz_credentials}")"
export POSTIZ_API_KEY

exec codex -c mcp_servers.postiz.enabled=true "$@"
