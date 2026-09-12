#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME="$ROOT/.local"
LOCK="$RUNTIME/freelancer-inbound-check.lock"
DESKTOP="$ROOT/scripts/desktop.sh"
LOGIN_HELPER="$ROOT/.local/private/freelancer_login.py"
COMPONENT_COUNT=5
started_here=0

prepare_runtime() {
  if [[ -L "$RUNTIME" ]]; then
    echo "Refusing symbolic-link runtime directory: $RUNTIME" >&2
    exit 2
  fi
  install -d -m 700 "$RUNTIME"
  if [[ -L "$LOCK" ]] || [[ -e "$LOCK" && ! -f "$LOCK" ]]; then
    echo "Refusing unsafe check lock: $LOCK" >&2
    exit 2
  fi
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  if (( started_here )); then
    "$DESKTOP" stop || true
  fi
  exit "$status"
}

prepare_runtime
umask 077
exec 9>"$LOCK"
chmod 600 "$LOCK"
if ! flock -n 9; then
  echo "A Freelancer inbound check is already running" >&2
  exit 2
fi

stack_status="$("$DESKTOP" status || true)"
running_count="$(awk '$2 == "running" { count++ } END { print count + 0 }' <<<"$stack_status")"
stopped_count="$(awk '$2 == "stopped" { count++ } END { print count + 0 }' <<<"$stack_status")"

if (( stopped_count == COMPONENT_COUNT )); then
  "$DESKTOP" start
  started_here=1
elif (( running_count != COMPONENT_COUNT )); then
  echo "Refusing a partial LazyPromotion desktop stack" >&2
  exit 2
fi

trap cleanup EXIT INT TERM
cd "$ROOT"
if monitor_output="$(python freelancer_inbound_monitor.py once 2>&1)"; then
  printf '%s\n' "$monitor_output"
elif [[ "$monitor_output" == *"the dedicated Freelancer session is not authenticated"* ]]; then
  if [[ ! -f "$LOGIN_HELPER" ]] || [[ -L "$LOGIN_HELPER" ]]; then
    echo "Freelancer authentication expired and no safe private restore helper is available" >&2
    exit 1
  fi
  if ! python "$LOGIN_HELPER" >/dev/null; then
    echo "Freelancer authentication restore failed in the isolated profile" >&2
    exit 1
  fi
  python freelancer_inbound_monitor.py once
else
  printf '%s\n' "$monitor_output" >&2
  exit 1
fi
