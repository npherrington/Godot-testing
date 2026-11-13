#!/usr/bin/env bash
# bin/check.sh: the gate every change must pass before it counts as done.
#   format  gdformat --check on every .gd file (fix with: bin/format.sh)
#   lint    gdlint
#   import  the project imports with no script or resource errors
#   parse   every .gd file compiles (tests/parse_check.gd), even ones nothing loads yet
#   tests   bin/test.sh
#   smoke   the main scene runs 180 frames headless with no errors
# Prints ok/FAIL per step, with the failing step's output, and exits 1 if any failed.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

fail=0
step() { # name command...
  local name="$1" out
  shift
  if out="$("$@" 2>&1)"; then
    echo "ok   $name"
  else
    echo "FAIL $name"
    printf '%s\n' "$out" | tail -60 | sed 's/^/     /'
    fail=1
  fi
}

no_engine_errors() { # command...: fails when the command fails or prints an engine error
  local out code
  out="$("$@" 2>&1)"
  code=$?
  if (( code != 0 )) || grep -qE 'SCRIPT ERROR|Parse Error|^ERROR:' <<<"$out"; then
    printf '%s\n' "$out" | grep -v -E '^Godot Engine v'
    return 1
  fi
}

gd_files=()
while IFS= read -r f; do gd_files+=("$f"); done < <(git ls-files -co --exclude-standard -- '*.gd')

parse_all() { # every script compiles, including ones nothing loads yet
  local f paths=()
  for f in "${gd_files[@]}"; do paths+=("res://$f"); done
  no_engine_errors bin/godot --headless --path . -s res://tests/parse_check.gd -- "${paths[@]}"
}

step format tools/.venv/bin/gdformat --check "${gd_files[@]}"
step lint tools/.venv/bin/gdlint "${gd_files[@]}"
step import no_engine_errors bin/godot --headless --path . --import
step parse parse_all
step tests bin/test.sh
step smoke no_engine_errors bin/godot --headless --path . --fixed-fps 60 --quit-after 180

exit "$fail"
