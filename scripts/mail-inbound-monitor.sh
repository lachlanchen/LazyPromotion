#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="lazypromotion-mail-inbound-monitor"
LOG="$ROOT/.local/mail-inbound-monitor-stdout.log"
INTERVAL_MINUTES="${MAIL_INBOUND_INTERVAL_MINUTES:-60}"

case "${1:-status}" in
  start)
    if ! [[ "$INTERVAL_MINUTES" =~ ^[0-9]+$ ]] || (( INTERVAL_MINUTES < 60 )); then
      printf 'MAIL_INBOUND_INTERVAL_MINUTES must be an integer of at least 60.\n' >&2
      exit 2
    fi
    if tmux has-session -t "=$SESSION" 2>/dev/null; then
      printf 'Mail monitor already has a session; no second worker was started.\n'
      exit 0
    fi
    [[ ! -L "$ROOT/.local" && ! -L "$LOG" ]] || exit 2
    mkdir -p "$ROOT/.local"
    touch "$LOG"
    chmod 600 "$LOG"
    command=(python "$ROOT/mail_inbound_check.py" loop --interval-minutes "$INTERVAL_MINUTES")
    printf -v command_line '%q ' "${command[@]}"
    printf -v log_path '%q' "$LOG"
    tmux new-session -d -s "$SESSION" -c "$ROOT" "exec $command_line >> $log_path 2>&1"
    printf 'Started hourly metadata-only mail monitoring; startup respects the previous check time.\n'
    ;;
  status)
    if tmux has-session -t "=$SESSION" 2>/dev/null; then
      printf 'Mail monitor is running in %s.\n' "$SESSION"
    else
      printf 'Mail monitor is stopped.\n'
    fi
    python "$ROOT/mail_inbound_check.py" status
    ;;
  stop)
    if ! tmux has-session -t "=$SESSION" 2>/dev/null; then
      printf 'Mail monitor is already stopped.\n'
      exit 0
    fi
    pid="$(tmux list-panes -t "=$SESSION" -F '#{pane_pid}')"
    [[ "$pid" =~ ^[0-9]+$ && -r "/proc/$pid/cmdline" ]] || exit 2
    [[ "$(readlink "/proc/$pid/cwd")" == "$ROOT" ]] || exit 2
    command_line="$(tr '\0' ' ' <"/proc/$pid/cmdline")"
    [[ "$command_line" == "python $ROOT/mail_inbound_check.py loop --interval-minutes "* ]] || exit 2
    # One graceful signal lets a finite check finish its exact-owner cleanup.
    # Do not kill the tmux session or any unrelated browser process.
    kill -TERM "$pid"
    for (( attempt=0; attempt<60; attempt++ )); do
      if ! tmux has-session -t "=$SESSION" 2>/dev/null; then
        printf 'Mail monitor stopped; aggregate evidence was retained.\n'
        exit 0
      fi
      sleep 1
    done
    printf 'Monitor is still cleaning up; inspect private status before taking further action.\n' >&2
    exit 1
    ;;
  *)
    printf 'Usage: scripts/mail-inbound-monitor.sh {start|status|stop}\n' >&2
    exit 2
    ;;
esac
