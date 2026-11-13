#!/usr/bin/env bash
# bin/test.sh [filter]: runs the headless test suite (tests/test_*.gd).
# With a filter, runs only test files or methods whose name contains it.
# Exits 1 on any failing test or any engine/script error in the output.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

args=(--headless --path . --fixed-fps 60 -s res://tests/runner.gd)
[[ $# -gt 0 ]] && args+=(-- "--filter=$1")

out="$(bin/godot "${args[@]}" 2>&1)"
code=$?
printf '%s\n' "$out" | grep -v -E '^Godot Engine v'
if grep -qE 'SCRIPT ERROR|Parse Error|^ERROR:' <<<"$out"; then
  echo "test.sh: the engine reported errors above, so the run fails even if every test passed"
  code=1
fi
exit "$code"
