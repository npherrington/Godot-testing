#!/usr/bin/env bash
#
# bin/build-feature.sh [--model=<provider/model>] [--no-commit] [--max-fixes=<n>]
#                      [--phase-timeout=<minutes>] features/<name>.md
#
# Takes one feature file from spec to a commit on its own branch, unattended:
#
#   plan -> implement -> gate -> playtest -> review -> commit
#
# Each phase is a fresh `opencode run` session with its own agent (.opencode/agents/), so no phase
# carries another's context. Phases pass work along through runs/<name>/handoff.md. The gate is
# bin/check.sh. A failing gate, a FAIL playtest or a CHANGES review sends the work back to the
# implementer, up to --max-fixes rounds in total; then the run stops and leaves the branch for you.
#
#   --model      use this model for every agent, e.g. ollama/qwen3.6:35b-a3b-q4_K_M
#   --no-commit  leave the finished changes uncommitted on the branch
#   --max-fixes  fix rounds across all phases (default 4)
#   --phase-timeout  minutes one agent phase may run before it is stopped, with everything it
#                started (default 90). A stopped phase counts like a failed one: the gate or the
#                missing result file sends the run to a fix round, or stops it.
#
# The feature file may be uncommitted; it rides along and is committed with the feature.
# Everything a run writes (plan, logs, check output, playtest evidence, review): runs/<name>/.
# Stop before the next phase: touch runs/<name>/STOP
#
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

usage() {
  echo "usage: bin/build-feature.sh [--model=<provider/model>] [--no-commit] [--max-fixes=<n>] [--phase-timeout=<minutes>] features/<name>.md" >&2
  exit 2
}

model=""
commit=1
max_fixes=4
phase_timeout=90
feature=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model=*) model="${1#*=}" ;;
    --no-commit) commit=0 ;;
    --max-fixes=*) max_fixes="${1#*=}" ;;
    --phase-timeout=*)
      phase_timeout="${1#*=}"
      [[ "$phase_timeout" =~ ^[1-9][0-9]*$ ]] || usage
      ;;
    -h | --help) usage ;;
    -*) usage ;;
    *)
      [[ -z "$feature" ]] || usage
      feature="$1"
      ;;
  esac
  shift
done
[[ -n "$feature" && -f "$feature" ]] || usage
command -v opencode >/dev/null || { echo "build-feature: opencode is not installed" >&2; exit 1; }
curl -sf --max-time 3 http://localhost:11434/api/version >/dev/null || {
  echo "build-feature: Ollama is not answering on localhost:11434; start the Ollama app" >&2
  exit 1
}
if [[ -n "$(git status --porcelain -- . ':!features')" ]]; then
  echo "build-feature: uncommitted changes outside features/; commit or stash them first" >&2
  exit 1
fi

slug="$(basename "$feature" .md)"
branch="feature/$slug"
run_dir="runs/$slug"
handoff="$run_dir/handoff.md"
title="$(grep -m1 '^# ' "$feature" | sed 's/^# *//' || true)"
title="${title:-$slug}"

if git show-ref --verify --quiet "refs/heads/$branch"; then
  git switch -q "$branch"
else
  git switch -q -c "$branch"
fi
rm -rf "$run_dir"
mkdir -p "$run_dir"
printf '# Handoff: %s\n\nFeature: %s\nBranch: %s\nStarted: %s\n' \
  "$title" "$feature" "$branch" "$(date '+%F %T')" >"$handoff"

fixes=0

log() { printf '\n\033[1m[%s] %s\033[0m\n' "$(date +%T)" "$*" | tee -a "$run_dir/run.log"; }

finish() { # exit-code
  local code="$1"
  if ((code == 0 && commit)); then
    git add -A
    git commit -q -F - <<EOF
feat: $title

Built unattended by bin/build-feature.sh from $feature in $fixes fix round(s).
EOF
    log "committed on $branch: $(git log -1 --format='%h %s')"
  elif ((code == 0)); then
    log "done; changes left uncommitted on $branch (--no-commit)"
  else
    log "stopped; work so far is uncommitted on $branch"
  fi
  log "handoff: $handoff"
  exit "$code"
}

brief() {
  cat <<EOF
Feature file: $feature
Handoff file: $handoff (read it first, and append your own section before you finish)
Run directory: $run_dir
Branch: $branch

Unattended run: nobody will answer questions. Decide, record the decision in the handoff, keep going.
EOF
}

phase() { # agent instructions
  local agent="$1" instructions="$2"
  if [[ -f "$run_dir/STOP" ]]; then
    log "found $run_dir/STOP; stopping before the $agent phase"
    finish 3
  fi
  log "phase: $agent"
  local args=(run --agent "$agent" --auto --archived --title "$slug: $agent")
  if [[ -n "$model" ]]; then args+=(-m "$model"); fi
  local code=0
  bin/with-timeout.sh "$((phase_timeout * 60))" opencode "${args[@]}" "$(brief)

$instructions" 2>&1 | tee -a "$run_dir/$agent.log" || code="${PIPESTATUS[0]}"
  if ((code == 124)); then
    log "the $agent phase was still running after $phase_timeout min and was stopped (see $run_dir/$agent.log)"
  elif ((code != 0)); then
    log "opencode exited non-zero in the $agent phase (see $run_dir/$agent.log)"
  fi
}

fix() { # what-went-wrong
  if ((fixes >= max_fixes)); then
    log "used all $max_fixes fix rounds"
    finish 1
  fi
  fixes=$((fixes + 1))
  phase implementer "Fix round $fixes of $max_fixes. $1
Fix the cause, not the symptom. Keep bin/check.sh passing. Append what you changed to the handoff."
}

gate() {
  while true; do
    log "gate: bin/check.sh"
    if bin/check.sh >"$run_dir/check.txt" 2>&1; then
      log "gate passed"
      return 0
    fi
    cat "$run_dir/check.txt"
    fix "bin/check.sh fails. Its full output is in $run_dir/check.txt."
  done
}

verdict() { # file -> the word after the first "VERDICT:" (models sometimes add a title above it)
  [[ -f "$1" ]] || return 0
  tr -d '\r*' <"$1" | sed -n 's/^[#> ]*VERDICT: *\([A-Z]*\).*/\1/p' | head -1
}

judged_phase() { # agent result-file instructions -> prints the verdict
  local agent="$1" file="$2" instructions="$3" v
  rm -f "$file"
  phase "$agent" "$instructions" >&2
  v="$(verdict "$file")"
  if [[ -z "$v" ]]; then
    log "the $agent phase wrote no verdict; rerunning it once" >&2
    phase "$agent" "$instructions
Your previous attempt did not write $file with a VERDICT line. Write it this time." >&2
    v="$(verdict "$file")"
  fi
  printf '%s' "$v"
}

# 1. Plan
phase planner "Write the implementation plan to $run_dir/plan.md as the feature-plan skill says, then append a short Plan section to the handoff. Change no game files."
[[ -s "$run_dir/plan.md" ]] || phase planner "$run_dir/plan.md is missing or empty. Write it now."
[[ -s "$run_dir/plan.md" ]] || { log "no plan after two attempts"; finish 1; }

# 2. Implement, then gate
phase implementer "Implement $run_dir/plan.md, tests included, and run bin/check.sh until it passes."
gate

# 3. Playtest the running game
while true; do
  v="$(judged_phase playtester "$run_dir/playtest.md" "Check every acceptance criterion in the feature file in the running game, as the godot-playtest skill says. Write $run_dir/playtest.md; its first line must be exactly VERDICT: PASS or VERDICT: FAIL.")"
  log "playtest verdict: ${v:-none}"
  [[ "$v" == "PASS" ]] && break
  [[ -n "$v" ]] || { log "no playtest verdict after two attempts"; finish 1; }
  fix "The playtest failed. $run_dir/playtest.md lists each failed criterion with its evidence."
  gate
done

# 4. Review
while true; do
  v="$(judged_phase reviewer "$run_dir/review.md" "Review this branch's changes (git diff main, plus untracked files) against the feature file, AGENTS.md and $run_dir/plan.md. Write $run_dir/review.md; its first line must be exactly VERDICT: APPROVE or VERDICT: CHANGES.")"
  log "review verdict: ${v:-none}"
  [[ "$v" == "APPROVE" ]] && break
  [[ -n "$v" ]] || { log "no review verdict after two attempts"; finish 1; }
  fix "The review asked for changes. They are listed in $run_dir/review.md; make each one or record in the handoff why not."
  gate
done

finish 0
