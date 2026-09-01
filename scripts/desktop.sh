#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$PROJECT_ROOT/.local/runtime"
PROFILE_DIR="$PROJECT_ROOT/.local/browser/profile"
DISPLAY_ID=116
DISPLAY_NAME=":$DISPLAY_ID"
DISPLAY_WIDTH=3840
DISPLAY_HEIGHT=1080
LANE_WIDTH=1920
VNC_PORT=5936
NOVNC_PORT=6136
AFFILIATE_VNC_PORT=5937
AFFILIATE_NOVNC_PORT=6137
CAMPAIGN_VNC_PORT=5938
CAMPAIGN_NOVNC_PORT=6138
CDP_PORT=9436
START_URL="${LAZYPROMOTION_START_URL:-https://www.reddit.com/}"
CAMPAIGN_HOME_URL="${LAZYPROMOTION_CAMPAIGN_HOME_URL:-https://platform.postiz.com/launches}"
INBOX_URL="${LAZYPROMOTION_INBOX_URL:-https://www.icloud.com/mail/}"
LINGQ_AFFILIATE_URL="https://www.lingq.com/settings/referrals"
BOOKSHOP_AFFILIATE_URL="https://bookshop.org/affiliates/profile/introduction"
POSTIZ_AFFILIATE_URL="https://partners.dub.co/postiz/apply"
NOVNC_URL="http://127.0.0.1:$NOVNC_PORT/vnc.html?host=127.0.0.1&port=$NOVNC_PORT&autoconnect=1&resize=scale&view_only=0&shared=0&reconnect=1"
AFFILIATE_NOVNC_URL="http://127.0.0.1:$AFFILIATE_NOVNC_PORT/vnc.html?host=127.0.0.1&port=$AFFILIATE_NOVNC_PORT&autoconnect=1&resize=scale&view_only=0&shared=0&reconnect=1"
CAMPAIGN_NOVNC_URL="http://127.0.0.1:$CAMPAIGN_NOVNC_PORT/vnc.html?host=127.0.0.1&port=$CAMPAIGN_NOVNC_PORT&autoconnect=1&resize=scale&view_only=0&shared=0&reconnect=1"
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

normal_window_ids() {
  local chrome_pid="$1"
  local window_id
  while read -r window_id; do
    [[ -n "$window_id" ]] || continue
    if DISPLAY="$DISPLAY_NAME" xprop -id "$window_id" _NET_WM_WINDOW_TYPE 2>/dev/null | grep -q '_NET_WM_WINDOW_TYPE_NORMAL'; then
      printf '%s\n' "$window_id"
    fi
  done < <(DISPLAY="$DISPLAY_NAME" xdotool search --onlyvisible --pid "$chrome_pid" 2>/dev/null || true)
}

window_title() {
  DISPLAY="$DISPLAY_NAME" xdotool getwindowname "$1" 2>/dev/null || true
}

cdp_has_url() {
  local needle="$1"
  curl --fail --silent "http://127.0.0.1:$CDP_PORT/json/list" \
    | jq -e --arg needle "$needle" 'any(.[]; (.url // "") | contains($needle))' >/dev/null
}

open_urls_in_window() {
  local window_id="$1"
  shift
  (( $# > 0 )) || return 0
  DISPLAY="$DISPLAY_NAME" xdotool windowfocus --sync "$window_id" >/dev/null 2>&1 || true
  DISPLAY="$DISPLAY_NAME" /opt/google/chrome/chrome \
    --user-data-dir="$PROFILE_DIR" \
    "$@" >>"$RUNTIME_DIR/workspace.log" 2>&1
}

restore_browser_workspace() {
  local chrome_pid="$1"
  local tries=0
  local window_id title
  local campaign_window=""
  local affiliate_window=""
  local -a windows=()
  local -a campaign_urls=()
  local -a affiliate_urls=()

  until mapfile -t windows < <(normal_window_ids "$chrome_pid") && (( ${#windows[@]} > 0 )); do
    tries=$((tries + 1))
    (( tries < 80 )) || return 1
    sleep 0.25
  done

  # Reuse restored windows where possible. The active title gives us a stable
  # campaign/affiliate classification without reading page content.
  for window_id in "${windows[@]}"; do
    title="$(window_title "$window_id")"
    if [[ -z "$campaign_window" && "$title" =~ (iCloud|Postiz|Reddit|Instagram|Search|GitHub|Insights) ]]; then
      campaign_window="$window_id"
    fi
    if [[ -z "$affiliate_window" && "$title" =~ (Affiliate|Referral|Partner) ]]; then
      affiliate_window="$window_id"
    fi
  done
  [[ -n "$campaign_window" ]] || campaign_window="${windows[0]}"
  if [[ "$affiliate_window" == "$campaign_window" ]]; then
    affiliate_window=""
  fi
  if [[ -z "$affiliate_window" ]]; then
    for window_id in "${windows[@]}"; do
      if [[ "$window_id" != "$campaign_window" ]]; then
        affiliate_window="$window_id"
        break
      fi
    done
  fi

  cdp_has_url 'www.icloud.com/mail' || campaign_urls+=("$INBOX_URL")
  cdp_has_url 'platform.postiz.com/launches' || campaign_urls+=("$CAMPAIGN_HOME_URL")
  open_urls_in_window "$campaign_window" "${campaign_urls[@]}" || return 1

  cdp_has_url 'lingq.com/settings/referrals' || affiliate_urls+=("$LINGQ_AFFILIATE_URL")
  cdp_has_url 'bookshop.org/affiliates/profile' || affiliate_urls+=("$BOOKSHOP_AFFILIATE_URL")
  cdp_has_url 'partners.dub.co/postiz' || affiliate_urls+=("$POSTIZ_AFFILIATE_URL")
  if [[ -z "$affiliate_window" ]]; then
    DISPLAY="$DISPLAY_NAME" /opt/google/chrome/chrome \
      --user-data-dir="$PROFILE_DIR" --new-window \
      "${affiliate_urls[@]:-$LINGQ_AFFILIATE_URL}" \
      >>"$RUNTIME_DIR/workspace.log" 2>&1 || return 1
    tries=0
    until (( ${#windows[@]} >= 2 )); do
      mapfile -t windows < <(normal_window_ids "$chrome_pid")
      tries=$((tries + 1))
      (( tries < 80 )) || return 1
      sleep 0.25
    done
    for window_id in "${windows[@]}"; do
      if [[ "$window_id" != "$campaign_window" ]]; then
        affiliate_window="$window_id"
        break
      fi
    done
  else
    open_urls_in_window "$affiliate_window" "${affiliate_urls[@]}" || return 1
  fi

  [[ -n "$campaign_window" && -n "$affiliate_window" ]] || return 1
  printf '%s\n' "$campaign_window" >"$RUNTIME_DIR/campaign.window"
  printf '%s\n' "$affiliate_window" >"$RUNTIME_DIR/affiliate.window"
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
  local campaign_window="$3"
  local affiliate_window="$4"
  export DISPLAY="$display_name"
  while kill -0 "$chrome_pid" 2>/dev/null; do
    read -r width height < <(xdotool getdisplaygeometry)
    local lane_width=$(( width / 2 ))
    # Pin each exported browser window to its named lane. Re-enumerating by
    # stacking order swaps the views whenever focus changes and can expose an
    # obscured window as black blocks through x11vnc.
    xdotool windowmove --sync "$campaign_window" 0 0 >/dev/null 2>&1 || true
    xdotool windowsize --sync "$campaign_window" "$lane_width" "$height" >/dev/null 2>&1 || true
    xdotool windowmove --sync "$affiliate_window" "$lane_width" 0 >/dev/null 2>&1 || true
    xdotool windowsize --sync "$affiliate_window" "$lane_width" "$height" >/dev/null 2>&1 || true
    sleep 2
  done
}

write_handoff() {
  {
    printf 'Current noVNC URL: %s\n' "$CAMPAIGN_NOVNC_URL"
    printf 'Affiliate noVNC URL: %s\n' "$AFFILIATE_NOVNC_URL"
    printf 'Overview noVNC URL: %s\n' "$NOVNC_URL"
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
  for spec in \
    "xvfb.pid|Xvfb $DISPLAY_NAME" \
    "x11vnc.pid|rfbport $VNC_PORT" \
    "novnc.pid|$NOVNC_PORT" \
    "affiliate-x11vnc.pid|rfbport $AFFILIATE_VNC_PORT" \
    "affiliate-novnc.pid|$AFFILIATE_NOVNC_PORT" \
    "campaign-x11vnc.pid|rfbport $CAMPAIGN_VNC_PORT" \
    "campaign-novnc.pid|$CAMPAIGN_NOVNC_PORT" \
    "chrome.pid|$PROFILE_DIR" \
    "fit.pid|fit_window_loop"; do
    IFS='|' read -r file marker <<<"$spec"
    if pid_alive "$RUNTIME_DIR/$file" "$marker"; then
      printf '%s running pid=%s\n' "${file%.pid}" "$(<"$RUNTIME_DIR/$file")"
    else
      printf '%s stopped\n' "${file%.pid}"
      ok=1
    fi
  done
  printf 'noVNC %s\n' "$NOVNC_URL"
  printf 'affiliate noVNC %s\n' "$AFFILIATE_NOVNC_URL"
  printf 'campaign noVNC %s\n' "$CAMPAIGN_NOVNC_URL"
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
  if ss -ltn | grep -Eq ":($VNC_PORT|$NOVNC_PORT|$AFFILIATE_VNC_PORT|$AFFILIATE_NOVNC_PORT|$CAMPAIGN_VNC_PORT|$CAMPAIGN_NOVNC_PORT|$CDP_PORT)\\b"; then
    printf 'One or more LazyPromotion ports are already occupied; refusing to reuse unknown listeners.\n' >&2
    exit 1
  fi
  if [[ -e "/tmp/.X${DISPLAY_ID}-lock" || -S "/tmp/.X11-unix/X${DISPLAY_ID}" ]]; then
    printf 'Display %s is occupied; refusing to reuse it.\n' "$DISPLAY_NAME" >&2
    exit 1
  fi

  nohup Xvfb "$DISPLAY_NAME" -screen 0 "${DISPLAY_WIDTH}x${DISPLAY_HEIGHT}x24" -nolisten tcp -ac -noreset \
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

  nohup x11vnc -display "$DISPLAY_NAME" -localhost -nopw -forever -nevershared -noxdamage \
    -rfbport "$VNC_PORT" -o "$RUNTIME_DIR/x11vnc.log" \
    >"$RUNTIME_DIR/x11vnc.stdout.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/x11vnc.pid"

  nohup websockify --web=/usr/share/novnc "127.0.0.1:$NOVNC_PORT" "127.0.0.1:$VNC_PORT" \
    >"$RUNTIME_DIR/novnc.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/novnc.pid"

  nohup x11vnc -display "$DISPLAY_NAME" -clip "${LANE_WIDTH}x${DISPLAY_HEIGHT}+${LANE_WIDTH}+0" \
    -localhost -nopw -forever -nevershared -noxdamage \
    -rfbport "$AFFILIATE_VNC_PORT" -o "$RUNTIME_DIR/affiliate-x11vnc.log" \
    >"$RUNTIME_DIR/affiliate-x11vnc.stdout.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/affiliate-x11vnc.pid"

  nohup websockify --web=/usr/share/novnc "127.0.0.1:$AFFILIATE_NOVNC_PORT" "127.0.0.1:$AFFILIATE_VNC_PORT" \
    >"$RUNTIME_DIR/affiliate-novnc.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/affiliate-novnc.pid"

  nohup x11vnc -display "$DISPLAY_NAME" -clip "${LANE_WIDTH}x${DISPLAY_HEIGHT}+0+0" \
    -localhost -nopw -forever -nevershared -noxdamage \
    -rfbport "$CAMPAIGN_VNC_PORT" -o "$RUNTIME_DIR/campaign-x11vnc.log" \
    >"$RUNTIME_DIR/campaign-x11vnc.stdout.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/campaign-x11vnc.pid"

  nohup websockify --web=/usr/share/novnc "127.0.0.1:$CAMPAIGN_NOVNC_PORT" "127.0.0.1:$CAMPAIGN_VNC_PORT" \
    >"$RUNTIME_DIR/campaign-novnc.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/campaign-novnc.pid"

  DISPLAY="$DISPLAY_NAME" nohup /opt/google/chrome/chrome \
    --user-data-dir="$PROFILE_DIR" \
    --remote-debugging-address=127.0.0.1 \
    --remote-debugging-port="$CDP_PORT" \
    --remote-allow-origins="http://127.0.0.1:$CDP_PORT" \
    --window-position=0,0 \
    --window-size="$LANE_WIDTH,$DISPLAY_HEIGHT" \
    --no-first-run \
    --no-default-browser-check \
    --disable-dev-shm-usage \
    --password-store=basic \
    --new-window "$START_URL" \
    >"$RUNTIME_DIR/chrome.log" 2>&1 &
  local chrome_pid="$!"
  printf '%s\n' "$chrome_pid" >"$RUNTIME_DIR/chrome.pid"

  wait_http "http://127.0.0.1:$CDP_PORT/json/version"
  if ! restore_browser_workspace "$chrome_pid"; then
    printf 'Browser started, but one or more review workspace tabs could not be restored.\n' >&2
    return 1
  fi
  local campaign_window affiliate_window
  campaign_window="$(<"$RUNTIME_DIR/campaign.window")"
  affiliate_window="$(<"$RUNTIME_DIR/affiliate.window")"
  nohup bash -c "$(declare -f fit_window_loop); fit_window_loop '$chrome_pid' '$DISPLAY_NAME' '$campaign_window' '$affiliate_window'" \
    >"$RUNTIME_DIR/fit.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/fit.pid"
  wait_http "http://127.0.0.1:$NOVNC_PORT/vnc.html"
  wait_http "http://127.0.0.1:$AFFILIATE_NOVNC_PORT/vnc.html"
  wait_http "http://127.0.0.1:$CAMPAIGN_NOVNC_PORT/vnc.html"
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
  stop_one "campaign-novnc.pid" "$CAMPAIGN_NOVNC_PORT" || true
  stop_one "campaign-x11vnc.pid" "rfbport $CAMPAIGN_VNC_PORT" || true
  stop_one "affiliate-novnc.pid" "$AFFILIATE_NOVNC_PORT" || true
  stop_one "affiliate-x11vnc.pid" "rfbport $AFFILIATE_VNC_PORT" || true
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
