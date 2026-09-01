#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$PROJECT_ROOT/.local/runtime"
PROFILE_DIR="$PROJECT_ROOT/.local/browser/profile"
DISPLAY_ID=116
DISPLAY_NAME=":$DISPLAY_ID"
DISPLAY_WIDTH=1920
DISPLAY_HEIGHT=1080
VNC_PORT=5936
NOVNC_PORT=6136
CDP_PORT=9436
START_URL="${LAZYPROMOTION_START_URL:-https://www.reddit.com/}"
CAMPAIGN_HOME_URL="${LAZYPROMOTION_CAMPAIGN_HOME_URL:-https://platform.postiz.com/launches}"
INBOX_URL="${LAZYPROMOTION_INBOX_URL:-https://www.icloud.com/mail/}"
LINGQ_AFFILIATE_URL="https://www.lingq.com/settings/referrals"
BOOKSHOP_AFFILIATE_URL="https://bookshop.org/affiliates/profile/introduction"
POSTIZ_AFFILIATE_URL="https://partners.dub.co/postiz/apply"
VIEWER_DISPLAY="${LAZYPROMOTION_VIEWER_DISPLAY:-:11}"
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

cdp_has_exact_url() {
  local url="$1"
  curl --fail --silent "http://127.0.0.1:$CDP_PORT/json/list" \
    | jq -e --arg url "$url" 'any(.[]; (.url // "") == $url)' >/dev/null
}

wait_cdp_pages_stable() {
  local tries=0
  local stable=0
  local previous=""
  local signature=""
  while (( tries < 40 )); do
    signature="$(curl --fail --silent "http://127.0.0.1:$CDP_PORT/json/list" 2>/dev/null \
      | jq -c '[.[] | select(.type == "page") | {id, url}] | sort_by(.id)' 2>/dev/null || true)"
    if [[ -n "$signature" && "$signature" == "$previous" ]]; then
      stable=$((stable + 1))
      (( stable >= 3 )) && return 0
    else
      stable=0
      previous="$signature"
    fi
    tries=$((tries + 1))
    sleep 0.25
  done
  return 0
}

workspace_url_allowed() {
  [[ ! "$1" =~ [\?\&](token|access_token|auth|authorization|session|key|secret|code)= ]] || return 1
  case "$1" in
    https://www.reddit.com/*|https://old.reddit.com/*|https://x.com/*|https://www.instagram.com/*|\
    https://hn.algolia.com/*|https://search.google.com/*|https://platform.postiz.com/*|\
    https://www.icloud.com/*|https://www.lingq.com/*|https://bookshop.org/*|\
    https://partners.dub.co/*|https://contra.com/*|https://www.datacamp.com/*|\
    https://github.com/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

workspace_url_is_baseline() {
  case "$1" in
    "$START_URL"|https://www.reddit.com/|https://www.icloud.com/mail/*|\
    https://platform.postiz.com/launches*|https://www.lingq.com/*|\
    https://bookshop.org/affiliates/profile/*|https://partners.dub.co/postiz/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

deduplicate_browser_tabs() {
  local target_id
  while IFS= read -r target_id; do
    [[ -n "$target_id" ]] || continue
    curl --fail --silent "http://127.0.0.1:$CDP_PORT/json/close/$target_id" >/dev/null || true
  done < <(
    curl --fail --silent "http://127.0.0.1:$CDP_PORT/json/list" \
      | jq -r '[.[] | select(.type == "page" and (.url // "" | startswith("https://")))]
        | sort_by(.url) | group_by(.url)[] | select(length > 1) | .[1:][] | .id'
  )
}

close_redundant_reddit_home() {
  local target_id
  if ! curl --fail --silent "http://127.0.0.1:$CDP_PORT/json/list" \
    | jq -e 'any(.[]; .type == "page" and (.url // "" | startswith("https://www.reddit.com/")) and .url != "https://www.reddit.com/")' \
      >/dev/null; then
    return 0
  fi
  while IFS= read -r target_id; do
    [[ -n "$target_id" ]] || continue
    curl --fail --silent "http://127.0.0.1:$CDP_PORT/json/close/$target_id" >/dev/null || true
  done < <(
    curl --fail --silent "http://127.0.0.1:$CDP_PORT/json/list" \
      | jq -r '.[] | select(.type == "page" and .url == "https://www.reddit.com/") | .id'
  )
}

save_browser_workspace() {
  local workspace_file="$RUNTIME_DIR/workspace.urls"
  local candidate_file="$RUNTIME_DIR/workspace.urls.candidate"
  local url
  curl --fail --silent "http://127.0.0.1:$CDP_PORT/json/list" \
    | jq -r '[.[] | select(.type == "page") | .url // "" | select(startswith("https://"))] | unique[]' \
    >"$candidate_file" || {
      rm -f -- "$candidate_file"
      return 0
    }
  : >"$workspace_file"
  while IFS= read -r url; do
    workspace_url_allowed "$url" || continue
    workspace_url_is_baseline "$url" || printf '%s\n' "$url" >>"$workspace_file"
  done <"$candidate_file"
  rm -f -- "$candidate_file"
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
  local window_id
  local url
  local -a windows=()
  local -a missing_urls=()

  until mapfile -t windows < <(normal_window_ids "$chrome_pid") && (( ${#windows[@]} > 0 )); do
    tries=$((tries + 1))
    (( tries < 40 )) || return 1
    sleep 0.25
  done
  wait_cdp_pages_stable

  window_id="${windows[0]}"
  cdp_has_url 'www.icloud.com/mail' || missing_urls+=("$INBOX_URL")
  cdp_has_url 'platform.postiz.com/launches' || missing_urls+=("$CAMPAIGN_HOME_URL")
  cdp_has_url 'lingq.com/settings/referrals' || missing_urls+=("$LINGQ_AFFILIATE_URL")
  cdp_has_url 'bookshop.org/affiliates/profile' || missing_urls+=("$BOOKSHOP_AFFILIATE_URL")
  cdp_has_url 'partners.dub.co/postiz' || missing_urls+=("$POSTIZ_AFFILIATE_URL")
  if [[ -f "$RUNTIME_DIR/workspace.urls" ]]; then
    while IFS= read -r url; do
      workspace_url_allowed "$url" || continue
      cdp_has_exact_url "$url" || missing_urls+=("$url")
    done <"$RUNTIME_DIR/workspace.urls"
  fi
  open_urls_in_window "$window_id" "${missing_urls[@]}" || return 1
  wait_cdp_pages_stable
  deduplicate_browser_tabs
  close_redundant_reddit_home
  wait_cdp_pages_stable
  printf '%s\n' "$window_id" >"$RUNTIME_DIR/main.window"
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
  local window_id
  local -a windows=()
  export DISPLAY="$display_name"
  export DISPLAY_NAME="$display_name"
  while kill -0 "$chrome_pid" 2>/dev/null; do
    read -r width height < <(xdotool getdisplaygeometry)
    mapfile -t windows < <(normal_window_ids "$chrome_pid")
    for window_id in "${windows[@]}"; do
      xdotool windowmove --sync "$window_id" 0 0 >/dev/null 2>&1 || true
      xdotool windowsize --sync "$window_id" "$width" "$height" >/dev/null 2>&1 || true
    done
    sleep 2
  done
}

valid_firefox_viewer() {
  local window_id="$1"
  local properties
  properties="$(DISPLAY="$VIEWER_DISPLAY" xprop -id "$window_id" WM_CLASS _NET_WM_NAME 2>/dev/null || true)"
  [[ "$properties" == *'firefox'* && "$properties" == *'noVNC'* ]]
}

navigate_firefox_viewer() {
  local window_id="$1"
  local url="$2"
  local tries=0
  local state
  valid_firefox_viewer "$window_id" || return 1
  command -v wmctrl >/dev/null 2>&1 || {
    printf 'wmctrl is required to safely refresh the registered Firefox viewer.\n' >&2
    return 1
  }
  DISPLAY="$VIEWER_DISPLAY" wmctrl -ir "$window_id" -b remove,fullscreen
  while (( tries < 20 )); do
    state="$(DISPLAY="$VIEWER_DISPLAY" xprop -id "$window_id" _NET_WM_STATE 2>/dev/null || true)"
    [[ "$state" != *'_NET_WM_STATE_FULLSCREEN'* ]] && break
    tries=$((tries + 1))
    sleep 0.1
  done
  [[ "$state" != *'_NET_WM_STATE_FULLSCREEN'* ]] || {
    printf 'The registered Firefox viewer did not leave fullscreen before navigation.\n' >&2
    return 1
  }
  printf '%s' "$url" | DISPLAY="$VIEWER_DISPLAY" xclip -selection clipboard
  DISPLAY="$VIEWER_DISPLAY" xdotool windowactivate --sync "$window_id"
  sleep 0.5
  DISPLAY="$VIEWER_DISPLAY" xdotool key --clearmodifiers ctrl+l ctrl+v Return
  sleep 0.5
}

fullscreen_firefox_viewer() {
  local window_id="$1"
  local tries=0
  local width height key value
  local current_x current_y current_width current_height
  valid_firefox_viewer "$window_id" || return 1
  command -v wmctrl >/dev/null 2>&1 || {
    printf 'wmctrl is required to fullscreen the registered Firefox viewer.\n' >&2
    return 1
  }
  DISPLAY="$VIEWER_DISPLAY" wmctrl -ir "$window_id" -b add,fullscreen
  DISPLAY="$VIEWER_DISPLAY" wmctrl -ia "$window_id"
  while (( tries < 20 )); do
    current_x=""
    current_y=""
    current_width=""
    current_height=""
    while IFS='=' read -r key value; do
      case "$key" in
        X) current_x="$value" ;;
        Y) current_y="$value" ;;
        WIDTH) current_width="$value" ;;
        HEIGHT) current_height="$value" ;;
      esac
    done < <(DISPLAY="$VIEWER_DISPLAY" xdotool getwindowgeometry --shell "$window_id" 2>/dev/null || true)
    read -r width height < <(DISPLAY="$VIEWER_DISPLAY" xdotool getdisplaygeometry)
    if [[ "$current_x" == 0 && "$current_y" == 0 && "$current_width" == "$width" && "$current_height" == "$height" ]]; then
      return 0
    fi
    tries=$((tries + 1))
    sleep 0.1
  done
  printf 'The registered Firefox viewer did not reach full-screen geometry.\n' >&2
  return 1
}

refresh_registered_viewers() {
  local viewer_file="$RUNTIME_DIR/viewer.window"
  [[ -f "$viewer_file" ]] || return 0
  local window_id
  window_id="$(<"$viewer_file")"
  navigate_firefox_viewer "$window_id" "$NOVNC_URL"
  fullscreen_firefox_viewer "$window_id"
}

register_viewer() {
  local viewer="${1:-}"
  [[ -n "$viewer" ]] || {
    printf 'Usage: %s register-viewer FIREFOX_WINDOW\n' "$0" >&2
    return 2
  }
  valid_firefox_viewer "$viewer" || {
    printf 'Viewer is not a live Firefox noVNC window on %s.\n' "$VIEWER_DISPLAY" >&2
    return 1
  }
  printf '%s\n' "$viewer" >"$RUNTIME_DIR/viewer.window"
  refresh_registered_viewers
  write_handoff
}

write_handoff() {
  {
    printf 'Current noVNC URL: %s\n' "$NOVNC_URL"
    printf 'X display: %s\n' "$DISPLAY_NAME"
    printf 'VNC: 127.0.0.1:%s\n' "$VNC_PORT"
    printf 'CDP: http://127.0.0.1:%s\n' "$CDP_PORT"
    printf 'Profile: %s\n' "$PROFILE_DIR"
    printf 'tmux session: %s\n' "$TMUX_SESSION"
    printf 'Owned PID files: %s/*.pid\n' "$RUNTIME_DIR"
    if [[ -f "$RUNTIME_DIR/viewer.window" ]]; then
      printf 'Firefox viewer: %s on %s\n' "$(<"$RUNTIME_DIR/viewer.window")" "$VIEWER_DISPLAY"
    fi
  } >"$RUNTIME_DIR/handoff.txt"
}

status() {
  local ok=0
  for spec in \
    "xvfb.pid|Xvfb $DISPLAY_NAME" \
    "x11vnc.pid|rfbport $VNC_PORT" \
    "novnc.pid|$NOVNC_PORT" \
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
  printf 'CDP http://127.0.0.1:%s\n' "$CDP_PORT"
  return "$ok"
}

start_stack() {
  mkdir -p "$RUNTIME_DIR" "$PROFILE_DIR"
  rm -f -- \
    "$RUNTIME_DIR/affiliate-novnc.pid" \
    "$RUNTIME_DIR/affiliate-x11vnc.pid" \
    "$RUNTIME_DIR/campaign-novnc.pid" \
    "$RUNTIME_DIR/campaign-x11vnc.pid" \
    "$RUNTIME_DIR/affiliate.window" \
    "$RUNTIME_DIR/campaign.window" \
    "$RUNTIME_DIR/affiliate-viewer.window" \
    "$RUNTIME_DIR/campaign-viewer.window"
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

  DISPLAY="$DISPLAY_NAME" nohup /opt/google/chrome/chrome \
    --user-data-dir="$PROFILE_DIR" \
    --remote-debugging-address=127.0.0.1 \
    --remote-debugging-port="$CDP_PORT" \
    --remote-allow-origins="http://127.0.0.1:$CDP_PORT" \
    --window-position=0,0 \
    --window-size="$DISPLAY_WIDTH,$DISPLAY_HEIGHT" \
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
  nohup bash -c "$(declare -f normal_window_ids); $(declare -f fit_window_loop); fit_window_loop '$chrome_pid' '$DISPLAY_NAME'" \
    >"$RUNTIME_DIR/fit.log" 2>&1 &
  printf '%s\n' "$!" >"$RUNTIME_DIR/fit.pid"
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
  if pid_alive "$RUNTIME_DIR/chrome.pid" "$PROFILE_DIR"; then
    save_browser_workspace
  fi
  stop_one "fit.pid" "fit_window_loop" || true
  stop_one "chrome.pid" "$PROFILE_DIR" || true
  stop_one "novnc.pid" "$NOVNC_PORT" || true
  stop_one "x11vnc.pid" "rfbport $VNC_PORT" || true
  stop_one "xvfb.pid" "Xvfb $DISPLAY_NAME" || true
}

wait_process_exit() {
  local pid="$1"
  local tries=0
  local state=""
  [[ "$pid" =~ ^[0-9]+$ ]] || return 0
  while kill -0 "$pid" 2>/dev/null; do
    [[ -r "/proc/$pid/stat" ]] && state="$(awk '{print $3}' "/proc/$pid/stat")"
    [[ "$state" == "Z" ]] && return 0
    tries=$((tries + 1))
    (( tries < 40 )) || return 1
    sleep 0.25
  done
}

wait_reserved_runtime_release() {
  local tries=0
  while ss -ltnH | grep -Eq ":($VNC_PORT|$NOVNC_PORT|$CDP_PORT|5937|5938|6137|6138)\\b" \
    || [[ -e "/tmp/.X${DISPLAY_ID}-lock" || -S "/tmp/.X11-unix/X${DISPLAY_ID}" ]]; do
    tries=$((tries + 1))
    (( tries < 80 )) || return 1
    sleep 0.25
  done
}

serve() {
  trap 'stop_stack' EXIT
  trap 'exit 0' HUP INT TERM
  start_stack
  while pid_alive "$RUNTIME_DIR/chrome.pid" "$PROFILE_DIR"; do
    sleep 2
  done
}

start() {
  if status >/dev/null 2>&1; then
    status
    refresh_registered_viewers || printf 'The stack is healthy, but the registered Firefox viewer could not be refreshed.\n' >&2
    return 0
  fi
  if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    printf 'Owned tmux session %s exists but the stack is unhealthy; run stop before relaunch.\n' "$TMUX_SESSION" >&2
    exit 1
  fi
  : >"$RUNTIME_DIR/supervisor.log"
  tmux new-session -d -s "$TMUX_SESSION" \
    "exec '$PROJECT_ROOT/scripts/desktop.sh' _serve >>'$RUNTIME_DIR/supervisor.log' 2>&1"
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
  refresh_registered_viewers || printf 'The stack started, but the registered Firefox viewer could not be refreshed.\n' >&2
}

stop() {
  local supervisor_pid=""
  if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    supervisor_pid="$(tmux list-panes -t "$TMUX_SESSION" -F '#{pane_pid}' 2>/dev/null | head -n 1)"
  fi
  stop_stack
  if ! wait_process_exit "$supervisor_pid"; then
    if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
      tmux kill-session -t "$TMUX_SESSION"
    fi
    wait_process_exit "$supervisor_pid" || {
      printf 'Timed out waiting for the old LazyPromotion supervisor to exit.\n' >&2
      return 1
    }
  elif tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    tmux kill-session -t "$TMUX_SESSION"
  fi
  wait_reserved_runtime_release || {
    printf 'Timed out waiting for LazyPromotion runtime ports or display to be released.\n' >&2
    return 1
  }
  status || true
}

case "${1:-status}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  register-viewer|register-viewers) register_viewer "${2:-}" ;;
  status) status ;;
  _serve) serve ;;
  *) printf 'Usage: %s {start|stop|restart|status|register-viewer}\n' "$0" >&2; exit 2 ;;
esac
