#!/usr/bin/env bash
# bin/check.sh: the gate every change must pass before it counts as done.
#   format  gdformat --check on every .gd file (fix with: bin/format.sh)
#   lint    gdlint
#   import  the project imports with no script or resource errors
#   parse   every .gd file compiles (tests/parse_check.gd), even ones nothing loads yet
#   scenes  every .tscn loads and instances (tests/scene_check.gd), even ones nothing uses yet
#   tests   bin/test.sh
#   smoke   the main scene runs 180 frames headless with no errors
# Prints ok/FAIL per step, with the failing step's output, and exits 1 if any failed.
#
# Godot can hang instead of exiting, so every Godot step has a time limit, in seconds:
#   IMPORT_TIMEOUT (300)  PARSE_TIMEOUT (120)  SCENES_TIMEOUT (120)  SMOKE_TIMEOUT (120)
#   TEST_TIMEOUT (600, read by bin/test.sh)
# A step that runs out of time fails with a TIMEOUT line.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Engine output that fails a step even when the exit code is 0. Godot exits 0 after many errors,
# and reports a scene node whose parent is missing only as a warning before dropping the node.
engine_errors='SCRIPT ERROR|Parse Error|^ERROR:|^WARNING:.*has vanished'

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

no_engine_errors() { # seconds command...: fails when the command fails, times out or prints an engine error
  local secs="$1" out code
  shift
  out="$(bin/with-timeout.sh "$secs" "$@" 2>&1)"
  code=$?
  if ((code != 0)) || grep -qE "$engine_errors" <<<"$out"; then
    printf '%s\n' "$out" | grep -v -E '^Godot Engine v'
    return 1
  fi
}

gd_files=()
while IFS= read -r f; do gd_files+=("$f"); done < <(git ls-files -co --exclude-standard -- '*.gd')
tscn_files=()
while IFS= read -r f; do tscn_files+=("$f"); done < <(git ls-files -co --exclude-standard -- '*.tscn')

parse_all() { # every script compiles, including ones nothing loads yet
  local f paths=()
  for f in "${gd_files[@]}"; do paths+=("res://$f"); done
  no_engine_errors "${PARSE_TIMEOUT:-120}" \
    bin/godot --headless --path . -s res://tests/parse_check.gd -- "${paths[@]}"
}

scenes_all() { # every scene loads and instances, including ones nothing uses yet
  local f paths=()
  for f in ${tscn_files[@]+"${tscn_files[@]}"}; do paths+=("res://$f"); done
  ((${#paths[@]} > 0)) || return 0
  no_engine_errors "${SCENES_TIMEOUT:-120}" \
    bin/godot --headless --path . -s res://tests/scene_check.gd -- "${paths[@]}"
}

step format tools/.venv/bin/gdformat --check "${gd_files[@]}"
step lint tools/.venv/bin/gdlint "${gd_files[@]}"
step import no_engine_errors "${IMPORT_TIMEOUT:-300}" bin/godot --headless --path . --import
step parse parse_all
step scenes scenes_all
step tests bin/test.sh
step smoke no_engine_errors "${SMOKE_TIMEOUT:-120}" \
  bin/godot --headless --path . --fixed-fps 60 --quit-after 180

exit "$fail"
