#!/usr/bin/env bash
# bin/with-timeout.sh SECONDS COMMAND [ARGS...]: runs COMMAND. If it is still running after SECONDS,
# stops it and every process it started (TERM, then KILL), prints a TIMEOUT line to stderr and
# exits 124. Otherwise exits with COMMAND's own status. Ctrl-C stops the whole tree too.
#
# Godot can hang instead of exiting: a runtime error that skips quit(), a test awaiting a signal
# that never comes, a script that fails to load under -s. macOS has no `timeout` command and ships
# bash 3.2, so this uses only bash 3.2, sleep, kill and pgrep.
set -uo pipefail

if [[ $# -lt 2 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo "usage: bin/with-timeout.sh SECONDS COMMAND [ARGS...]" >&2
  exit 2
fi
secs="$1"
shift

descendants() { # pid -> every descendant pid, deepest first
  local child
  for child in $(pgrep -P "$1" 2>/dev/null); do
    descendants "$child"
    echo "$child"
  done
}

stop_tree() { # pid: TERM the process and its descendants, then KILL whatever is left
  local pids
  pids="$(descendants "$1") $1"
  # shellcheck disable=SC2086 # word splitting is the point: one pid per word
  kill -TERM $pids 2>/dev/null || return 0
  local i
  for i in $(seq 50); do # up to 5 s to exit cleanly
    # shellcheck disable=SC2086
    kill -0 $pids 2>/dev/null || return 0
    sleep 0.1
  done
  # shellcheck disable=SC2086
  kill -KILL $pids 2>/dev/null
  return 0
}

marker="$(mktemp "${TMPDIR:-/tmp}/with-timeout.XXXXXX")"

"$@" <&0 &
pid=$!

(
  sleep "$secs"
  echo timeout >"$marker"
  stop_tree "$pid"
) &
watchdog=$!

trap 'stop_tree "$pid"; stop_tree "$watchdog"; rm -f "$marker"; exit 130' INT TERM

wait "$pid" 2>/dev/null # 2>/dev/null: no "Killed: 9" job notice when the KILL fallback was needed
code=$?
stop_tree "$watchdog"
if [[ -s "$marker" ]]; then
  what="$*"
  what="${what%%$'\n'*}" # first line only: agent prompts are long
  ((${#what} > 120)) && what="${what:0:120}..."
  echo "TIMEOUT: still running after ${secs}s, so it was stopped: $what" >&2
  code=124
fi
rm -f "$marker"
exit "$code"
