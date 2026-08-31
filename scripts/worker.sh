#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="lazypromotion-worker"
LOG="$ROOT/.local/worker-stdout.log"

case "${1:-status}" in
  start)
    shift
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "LazyPromoter worker is already running in tmux session $SESSION"
      exit 0
    fi
    "$ROOT/scripts/desktop.sh" status >/dev/null || "$ROOT/scripts/desktop.sh" start
    mkdir -p "$ROOT/.local"
    command=(env)
    for variable in CODEX_HOME CODEX_SQLITE_HOME AGENT_SHELL_CODEX_HOME AGENT_SHELL_CODEX_SQLITE_HOME; do
      if [[ -v "$variable" ]]; then
        command+=("$variable=${!variable}")
      fi
    done
    command+=(python worker.py "$@")
    printf -v command_line '%q ' "${command[@]}"
    tmux new-session -d -s "$SESSION" -c "$ROOT" "$command_line >> .local/worker-stdout.log 2>&1"
    echo "Started LazyPromoter worker in tmux session $SESSION"
    ;;
  status)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "LazyPromoter worker is running in tmux session $SESSION"
      tail -n 5 "$LOG" 2>/dev/null || true
    else
      echo "LazyPromoter worker is stopped"
      exit 1
    fi
    ;;
  stop)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      tmux kill-session -t "$SESSION"
      echo "Stopped LazyPromoter worker session $SESSION; durable state was retained"
    else
      echo "LazyPromoter worker is already stopped"
    fi
    ;;
  *)
    echo "Usage: scripts/worker.sh {start|status|stop} [worker.py options]" >&2
    exit 2
    ;;
esac
