#!/usr/bin/env bash
# bin/test.sh [filter]: runs the headless test suite (tests/test_*.gd).
# With a filter, runs only test files or methods whose name contains it.
# Exits 1 on any failing test, when no test ran, or on any engine/script error in the output.
# The whole run is stopped after TEST_TIMEOUT seconds (default 600); a single test is stopped
# after 3600 physics frames by tests/runner.gd.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

args=(--headless --path . --fixed-fps 60 -s res://tests/runner.gd)
[[ $# -gt 0 ]] && args+=(-- "--filter=$1")

out="$(bin/with-timeout.sh "${TEST_TIMEOUT:-600}" bin/godot "${args[@]}" 2>&1)"
code=$?
printf '%s\n' "$out" | grep -v -E '^Godot Engine v'
if ((code == 124)); then
  echo "test.sh: the test run timed out; the last PASS/FAIL line above is the last test that finished"
elif grep -qE 'SCRIPT ERROR|Parse Error|^ERROR:|^WARNING:.*has vanished' <<<"$out"; then
  echo "test.sh: the engine reported errors above, so the run fails even if every test passed"
  code=1
fi
exit "$code"
