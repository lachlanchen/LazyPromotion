#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="lazypromotion-owned-monitor"
LOG="$ROOT/.local/owned-monitor-stdout.log"
INTERVAL_MINUTES="${OWNED_MONITOR_INTERVAL_MINUTES:-15}"

case "${1:-status}" in
  start)
    if ! [[ "$INTERVAL_MINUTES" =~ ^[0-9]+$ ]] || (( INTERVAL_MINUTES < 5 )); then
      echo "OWNED_MONITOR_INTERVAL_MINUTES must be an integer of at least 5" >&2
      exit 2
    fi
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "Owned Postiz monitor is already running in tmux session $SESSION"
      exit 0
    fi
    mkdir -p "$ROOT/.local"
    umask 077
    : >"$LOG"
    command=(python owned_monitor.py loop --interval-minutes "$INTERVAL_MINUTES")
    printf -v command_line '%q ' "${command[@]}"
    tmux new-session -d -s "$SESSION" -c "$ROOT" "$command_line >> .local/owned-monitor-stdout.log 2>&1"
    echo "Started owned Postiz monitor in tmux session $SESSION"
    ;;
  status)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "Owned Postiz monitor is running in tmux session $SESSION"
      python owned_monitor.py status
    else
      echo "Owned Postiz monitor is stopped"
      exit 1
    fi
    ;;
  stop)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      tmux kill-session -t "$SESSION"
      echo "Stopped owned Postiz monitor; private observation state was retained"
    else
      echo "Owned Postiz monitor is already stopped"
    fi
    ;;
  *)
    echo "Usage: scripts/owned-monitor.sh {start|status|stop}" >&2
    exit 2
    ;;
esac
