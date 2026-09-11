#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="lazypromotion-bounty-marketplace-monitor"
RUNTIME="$ROOT/.local"
LOG="$RUNTIME/bounty-marketplace-monitor-stdout.log"
INTERVAL_MINUTES="${BOUNTY_MARKETPLACE_MONITOR_INTERVAL_MINUTES:-5}"

prepare_runtime() {
  if [[ -L "$RUNTIME" ]]; then
    echo "Refusing symbolic-link runtime directory: $RUNTIME" >&2
    exit 2
  fi
  install -d -m 700 "$RUNTIME"
  if [[ -L "$LOG" ]] || [[ -e "$LOG" && ! -f "$LOG" ]]; then
    echo "Refusing unsafe monitor log path: $LOG" >&2
    exit 2
  fi
  touch "$LOG"
  chmod 600 "$LOG"
}

case "${1:-status}" in
  start)
    if ! [[ "$INTERVAL_MINUTES" =~ ^[0-9]+$ ]] || (( INTERVAL_MINUTES < 5 )); then
      echo "BOUNTY_MARKETPLACE_MONITOR_INTERVAL_MINUTES must be an integer of at least 5" >&2
      exit 2
    fi
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "Bounty marketplace monitor is already running in tmux session $SESSION"
      exit 0
    fi
    prepare_runtime
    umask 077
    command=(python bounty_marketplace_monitor.py loop --interval-minutes "$INTERVAL_MINUTES")
    printf -v command_line '%q ' "${command[@]}"
    tmux new-session -d -s "$SESSION" -c "$ROOT" "$command_line >> .local/bounty-marketplace-monitor-stdout.log 2>&1"
    echo "Started Bounty marketplace monitor in tmux session $SESSION"
    ;;
  status)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "Bounty marketplace monitor is running in tmux session $SESSION"
      tail -n 1 "$LOG" 2>/dev/null || true
    else
      echo "Bounty marketplace monitor is stopped"
      exit 1
    fi
    ;;
  stop)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      tmux kill-session -t "$SESSION"
      echo "Stopped Bounty marketplace monitor; private seen state was retained"
    else
      echo "Bounty marketplace monitor is already stopped"
    fi
    ;;
  *)
    echo "Usage: scripts/bounty-marketplace-monitor.sh {start|status|stop}" >&2
    exit 2
    ;;
esac
