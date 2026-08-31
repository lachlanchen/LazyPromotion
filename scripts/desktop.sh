#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$PROJECT_ROOT/.local/runtime"
PROFILE_DIR="$PROJECT_ROOT/.local/browser/profile"
DISPLAY_ID=116
DISPLAY_NAME=":$DISPLAY_ID"
VNC_PORT=5936
NOVNC_PORT=6136
CDP_PORT=9436
START_URL="${LAZYPROMOTION_START_URL:-https://www.reddit.com/}"
NOVNC_URL="http://127.0.0.1:$NOVNC_PORT/vnc.html?host=127.0.0.1&port=$NOVNC_PORT&autoconnect=1&resize=scale&view_only=0&shared=0&reconnect=0"
TMUX_SESSION="lazypromotion-browser"

pid_alive() {
  local file="$1"
  local marker="$2"
  local pid
  [[ -f "$file" ]] || return 1
  pid="$(<"$file")"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  [[ -r "/proc/$pid/cmdline" ]] || return 1
  tr '\0' ' ' <"/proc/$pid/cmdline" | grep -Fq -- "$marker"
}

wait_http() {
  local url="$1"
  local tries=0
  until curl --fail --silent --show-error "$url" >/dev/null 2>&1; do
    tries=$((tries + 1))
    if (( tries >= 80 )); then
      return 1
    fi
    sleep 0.25
  done
}

clean_owned_stale_display() {
  local lock="/tmp/.X${DISPLAY_ID}-lock"
  local socket="/tmp/.X11-unix/X${DISPLAY_ID}"
  local recorded=""
  local locked=""
  [[ -f "$RUNTIME_DIR/xvfb.pid" ]] && recorded="$(<"$RUNTIME_DIR/xvfb.pid")"
  [[ -f "$lock" ]] && locked="$(tr -d '[:space:]' <"$lock")"
  if [[ "$recorded" =~ ^[0-9]+$ ]] && ! kill -0 "$recorded" 2>/dev/null; then
    if [[ -z "$locked" || "$locked" == "$recorded" ]]; then
      rm -f -- "$lock" "$socket"
    fi
  fi
}

fit_window_loop() {
  local chrome_pid="$1"
  local display_name="$2"
  export DISPLAY="$display_name"
  while kill -0 "$chrome_pid" 2>/dev/null; do
    read -r width height < <(xdotool getdisplaygeometry)
    local normal_index=0
    while read -r window_id; do
      [[ -n "$window_id" ]] || continue
      if ! xprop -id "$window_id" _NET_WM_WINDOW_TYPE 2>/dev/null | grep -q '_NET_WM_WINDOW_TYPE_NORMAL'; then
        continue
      fi
      if (( normal_index == 0 )); then
        xdotool windowmove --sync "$window_id" 0 0 >/dev/null 2>&1 || true
        xdotool windowsize --sync "$window_id" "$width" "$height" >/dev/null 2>&1 || true
      else
        local dialog_width=720
        local dialog_height=820
        local dialog_x=$(( (width - dialog_width) / 2 ))
        local dialog_y=$(( (height - dialog_height) / 2 ))
        xdotool windowmove --sync "$window_id" "$dialog_x" "$dialog_y" >/dev/null 2>&1 || true
        xdotool windowsize --sync "$window_id" "$dialog_width" "$dialog_height" >/dev/null 2>&1 || true
      fi
      normal_index=$((normal_index + 1))
    done < <(xdotool search --onlyvisible --pid "$chrome_pid" 2>/dev/null || true)
    sleep 2
  done
}

write_handoff() {
  {
    printf 'noVNC URL: %s\n' "$NOVNC_URL"
    printf 'X display: %s\n' "$DISPLAY_NAME"
    printf 'VNC: 127.0.0.1:%s\n' "$VNC_PORT"
    printf 'CDP: http://127.0.0.1:%s\n' "$CDP_PORT"
    printf 'Profile: %s\n' "$PROFILE_DIR"
    printf 'tmux session: %s\n' "$TMUX_SESSION"
    printf 'Owned PID files: %s/*.pid\n' "$RUNTIME_DIR"
  } >"$RUNTIME_DIR/handoff.txt"
}

status() {
  local ok=0
  for spec in "xvfb.pid|Xvfb $DISPLAY_NAME" "x11vnc.pid|rfbport $VNC_PORT" "novnc.pid|$NOVNC_PORT" "chrome.pid|$PROFILE_DIR"; do
    IFS='|' read -r file marker <<<"$spec"
    if pid_alive "$RUNTIME_DIR/$file" "$marker"; then
      printf '%s running pid=%s\n' "${file%.pid}" "$(<"$RUNTIME_DIR/$file")"
    else
      printf '%s stopped\n' "${file%.pid}"
      ok=1
    fi
  done
  printf 'noVNC %s\n' "$NOVNC_URL"
  printf 'CDP http://127.0.0.1:%s\n' "$CDP_PORT"
  return "$ok"
}

start_stack() {
  mkdir -p "$RUNTIME_DIR" "$PROFILE_DIR"
  if status >/dev/null 2>&1; then
    status
    return 0
  fi
  stop_stack >/dev/null 2>&1 || true
  clean_owned_stale_display
  if ss -ltn | grep -Eq ":($VNC_PORT|$NOVNC_PORT|$CDP_PORT)\\b"; then
    printf 'One or more LazyPromotion ports are already occupied; refusing to reuse unknown listeners.\n' >&2
    exit 1
  fi
  if [[ -e "/tmp/.X${DISPLAY_ID}-lock" || -S "/tmp/.X11-unix/X${DISPLAY_ID}" ]]; then
    printf 'Display %s is occupied; refusing to reuse it.\n' "$DISPLAY_NAME" >&2
    exit 1
  fi

  nohup Xvfb "$DISPLAY_NAME" -screen 0 1440x1000x24 -nolisten tcp -ac -noreset \
    >"$RUNTIME_DIR/xvfb.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/xvfb.pid"

  local tries=0
  until [[ -S "/tmp/.X11-unix/X${DISPLAY_ID}" ]]; do
    tries=$((tries + 1))
    if (( tries >= 80 )); then
      printf 'Xvfb did not create its display socket.\n' >&2
      exit 1
    fi
    sleep 0.25
  done

  nohup x11vnc -display "$DISPLAY_NAME" -localhost -nopw -forever -nevershared \
    -rfbport "$VNC_PORT" -o "$RUNTIME_DIR/x11vnc.log" \
    >"$RUNTIME_DIR/x11vnc.stdout.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/x11vnc.pid"

  nohup websockify --web=/usr/share/novnc "127.0.0.1:$NOVNC_PORT" "127.0.0.1:$VNC_PORT" \
    >"$RUNTIME_DIR/novnc.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/novnc.pid"

  DISPLAY="$DISPLAY_NAME" nohup /opt/google/chrome/chrome \
    --user-data-dir="$PROFILE_DIR" \
    --remote-debugging-address=127.0.0.1 \
    --remote-debugging-port="$CDP_PORT" \
    --remote-allow-origins="http://127.0.0.1:$CDP_PORT" \
    --window-position=0,0 \
    --window-size=1440,1000 \
    --no-first-run \
    --no-default-browser-check \
    --disable-dev-shm-usage \
    --password-store=basic \
    --new-window "$START_URL" \
    >"$RUNTIME_DIR/chrome.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/chrome.pid"

  nohup bash -c "$(declare -f fit_window_loop); fit_window_loop '$!' '$DISPLAY_NAME'" \
    >"$RUNTIME_DIR/fit.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/fit.pid"

  wait_http "http://127.0.0.1:$CDP_PORT/json/version"
  wait_http "http://127.0.0.1:$NOVNC_PORT/vnc.html"
  write_handoff
  status
}

stop_one() {
  local file="$1"
  local marker="$2"
  if ! pid_alive "$RUNTIME_DIR/$file" "$marker"; then
    return 0
  fi
  local pid
  pid="$(<"$RUNTIME_DIR/$file")"
  kill "$pid"
  local tries=0
  while kill -0 "$pid" 2>/dev/null; do
    tries=$((tries + 1))
    if (( tries >= 40 )); then
      kill -KILL "$pid"
      break
    fi
    sleep 0.25
  done
}

stop_stack() {
  stop_one "fit.pid" "fit_window_loop" || true
  stop_one "chrome.pid" "$PROFILE_DIR" || true
  stop_one "novnc.pid" "$NOVNC_PORT" || true
  stop_one "x11vnc.pid" "rfbport $VNC_PORT" || true
  stop_one "xvfb.pid" "Xvfb $DISPLAY_NAME" || true
}

serve() {
  trap 'stop_stack' EXIT HUP INT TERM
  start_stack
  while pid_alive "$RUNTIME_DIR/chrome.pid" "$PROFILE_DIR"; do
    sleep 2
  done
}

start() {
  if status >/dev/null 2>&1; then
    status
    return 0
  fi
  if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    printf 'Owned tmux session %s exists but the stack is unhealthy; run stop before relaunch.\n' "$TMUX_SESSION" >&2
    exit 1
  fi
  tmux new-session -d -s "$TMUX_SESSION" "exec '$PROJECT_ROOT/scripts/desktop.sh' _serve"
  local tries=0
  until status >/dev/null 2>&1; do
    tries=$((tries + 1))
    if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
      printf 'Owned tmux supervisor exited during startup.\n' >&2
      tail -n 80 "$RUNTIME_DIR/supervisor.log" 2>/dev/null || true
      exit 1
    fi
    if (( tries >= 100 )); then
      printf 'Timed out waiting for the LazyPromotion browser stack.\n' >&2
      exit 1
    fi
    sleep 0.25
  done
  status
}

stop() {
  stop_stack
  if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    tmux kill-session -t "$TMUX_SESSION"
  fi
  status || true
}

case "${1:-status}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  _serve) serve ;;
  *) printf 'Usage: %s {start|stop|restart|status}\n' "$0" >&2; exit 2 ;;
esac
