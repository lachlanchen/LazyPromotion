#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="lazypromotion-stripe-revenue-monitor"
RUNTIME="$ROOT/.local"
LOG="$RUNTIME/stripe-revenue-monitor-stdout.log"
INTERVAL_MINUTES="${STRIPE_REVENUE_MONITOR_INTERVAL_MINUTES:-30}"

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
    if ! [[ "$INTERVAL_MINUTES" =~ ^[0-9]+$ ]] || (( INTERVAL_MINUTES < 15 )); then
      echo "STRIPE_REVENUE_MONITOR_INTERVAL_MINUTES must be an integer of at least 15" >&2
      exit 2
    fi
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "Stripe revenue monitor is already running in tmux session $SESSION"
      exit 0
    fi
    prepare_runtime
    umask 077
    command=(python stripe_revenue_monitor.py loop --confirm-private-financial-read --interval-minutes "$INTERVAL_MINUTES")
    printf -v command_line '%q ' "${command[@]}"
    tmux new-session -d -s "$SESSION" -c "$ROOT" "$command_line >> .local/stripe-revenue-monitor-stdout.log 2>&1"
    echo "Started read-only Stripe revenue monitor in tmux session $SESSION"
    ;;
  status)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "Stripe revenue monitor is running in tmux session $SESSION"
      python stripe_revenue_monitor.py status
    else
      echo "Stripe revenue monitor is stopped"
      exit 1
    fi
    ;;
  stop)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      tmux kill-session -t "$SESSION"
      echo "Stopped Stripe revenue monitor; private aggregate state was retained"
    else
      echo "Stripe revenue monitor is already stopped"
    fi
    ;;
  *)
    echo "Usage: scripts/stripe-revenue-monitor.sh {start|status|stop}" >&2
    exit 2
    ;;
esac
