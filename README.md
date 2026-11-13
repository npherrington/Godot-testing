# Godot Lab

A 2D Godot game built by local coding agents (OpenCode + Ollama). You write feature files; a
pipeline plans, implements, tests, playtests and reviews each one, and commits it on a branch.

## Setup (once)

```bash
brew install --cask godot     # Godot 4.7+
brew install opencode
bin/setup.sh                  # pinned godot-mcp-runtime + gdtoolkit, imports the project
bin/check.sh                  # should print seven "ok" lines
```

Ollama must be running with the models named in `.opencode/agents/*.md`.

## Building a feature

1. Write `features/NNNN-name.md` from `features/TEMPLATE.md` (or run `opencode`, then
   `/spec <idea>`). Acceptance criteria must be checkable: numbers, counts, text on screen.
2. Run it unattended:

   ```bash
   bin/build-feature.sh features/0001-coins-and-score.md
   ```

   plan → implement → gate (`bin/check.sh`) → playtest in the running game → review → commit on
   `feature/<name>`. A failed gate, playtest or review goes back to the implementer, up to 4 rounds.
   An agent phase still running after 90 minutes is stopped (`--phase-timeout=<minutes>`), and
   every Godot run inside the gate has its own time limit, so a hang can't stall the night.
   Everything it wrote and saw is in `runs/<name>/` (`handoff.md` first).
3. Play it yourself: `bin/godot --path .`, or open the project in the Godot editor. Merge the branch
   when you're happy: `git switch main && git merge feature/<name>`.

Or work attended: `opencode`, then `/feature features/0002-....md`, and it stops for your go-ahead
on the plan.

## How it fits together

| Piece | Where | Role |
| --- | --- | --- |
| Agents | `.opencode/agents/` | planner, implementer, playtester, reviewer: each limited to what its job needs |
| Skills | `.opencode/skills/` | GDScript style, writing `.tscn` by hand, tests, playtesting, plans, feature files |
| Gate | `bin/check.sh` | format, lint, import, parse, scenes, tests, smoke run: the definition of done. Strict GDScript warnings (`project.godot` `[debug]`) are errors |
| Tests | `tests/` | headless runner; `bin/test.sh [filter]` |
| Game driver | `godot` MCP (godot-mcp-runtime, pinned in `tools/`) | run the game, input, read state, screenshots |
| Pipeline | `bin/build-feature.sh` | runs the phases as separate sessions, passing a handoff file |
| Rules | `AGENTS.md` | loaded by every agent |

Change an agent's model in its frontmatter, or the whole run's with
`bin/build-feature.sh --model=ollama/<model> ...`.
