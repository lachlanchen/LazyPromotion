#!/usr/bin/env bash
set -euo pipefail

specimen_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "${specimen_dir}/../.." && pwd)"
artifact_dir="${ARTIFACT_DIR:-${repo_dir}/.local/proofs/stateful-pwa-recovery}"
mkdir -p "${artifact_dir}"

cd "${specimen_dir}"
python -m pytest tests \
  --strict-config \
  --strict-markers \
  --junitxml="${artifact_dir}/junit-stateful-pwa-recovery.xml"

