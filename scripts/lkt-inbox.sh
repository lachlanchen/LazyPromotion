#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="lazypromotion-lkt-inbox"
LOG="$ROOT/.local/lkt-inbox-stdout.log"
INTERVAL_MINUTES="${LKT_INBOX_INTERVAL_MINUTES:-15}"

case "${1:-status}" in
  start)
    if ! [[ "$INTERVAL_MINUTES" =~ ^[0-9]+$ ]] || (( INTERVAL_MINUTES < 5 )); then
      echo "LKT_INBOX_INTERVAL_MINUTES must be an integer of at least 5" >&2
      exit 2
    fi
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "Encrypted fit-check receiver is already running in tmux session $SESSION"
      exit 0
    fi
    mkdir -p "$ROOT/.local"
    umask 077
    : >"$LOG"
    command=(python lkt_inbox.py loop --interval-minutes "$INTERVAL_MINUTES")
    printf -v command_line '%q ' "${command[@]}"
    tmux new-session -d -s "$SESSION" -c "$ROOT" "$command_line >> .local/lkt-inbox-stdout.log 2>&1"
    echo "Started encrypted fit-check receiver in tmux session $SESSION"
    ;;
  status)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "Encrypted fit-check receiver is running in tmux session $SESSION"
      tail -n 5 "$LOG" 2>/dev/null || true
    else
      echo "Encrypted fit-check receiver is stopped"
      exit 1
    fi
    ;;
  stop)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      tmux kill-session -t "$SESSION"
      echo "Stopped encrypted fit-check receiver; private inbox state was retained"
    else
      echo "Encrypted fit-check receiver is already stopped"
    fi
    ;;
  *)
    echo "Usage: scripts/lkt-inbox.sh {start|status|stop}" >&2
    exit 2
    ;;
esac
