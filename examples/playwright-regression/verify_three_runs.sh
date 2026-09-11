#!/usr/bin/env bash
set -euo pipefail

specimen_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for run in 1 2 3; do
  ARTIFACT_DIR="${ARTIFACT_DIR:-${specimen_dir}/../../.local/proofs/playwright-regression}/run-${run}" \
    "${specimen_dir}/run_suite.sh"
done
