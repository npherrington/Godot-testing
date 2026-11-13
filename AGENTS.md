# Godot Lab

A small top-down 2D game in Godot 4.7 (GDScript), built one feature file at a time by agents.

## Commands

| Command | What it does |
| --- | --- |
| `bin/check.sh` | **The gate.** Format, lint, import, parse, scenes, tests, smoke run. A change is done only when this passes. |
| `bin/test.sh [filter]` | Headless tests only, optionally filtered by file or method name |
| `bin/format.sh` | Fix formatting (run this when the gate's `format` step fails) |
| `bin/build-feature.sh features/<f>.md` | The unattended pipeline: plan, implement, gate, playtest, review, commit |

## Layout

- `project.godot`: settings, input actions (`[input]`), autoloads (`[autoload]`). Its `[debug]`
  warning levels are part of the gate: never lower or remove them; fix the code they flag.
- `scenes/*.tscn`: one scene per thing (`main`, `player`, ...). `main.tscn` is the game.
- `scripts/*.gd`: one script per scene, same name. `game_state.gd` is the `GameState` autoload.
- `tests/test_*.gd`: tests. `runner.gd`, `test_case.gd`, `parse_check.gd` and `scene_check.gd` are the harness; do not edit them.
- `features/`: feature files, the specs. `runs/<feature>/`: a run's plan, logs, evidence (not committed).
- `bin/`, `tools/`, `.opencode/`, `opencode.jsonc`: the harness. Do not edit them.

## Rules

1. **State lives in `GameState`.** Anything a test or playtest needs to check (score, health,
   counts, flags) is a variable on `GameState`, reset in `reset()` and included in `snapshot()`.
2. **Find nodes by group or unique name, never by long paths.** Add new things to a group named
   after them (`coins`, `enemies`) so tests and the playtester can count them.
3. **Input goes through actions.** Add new controls to `[input]` in `project.godot`; read them
   with `Input.is_action_*`, never raw keycodes.
4. **Every acceptance criterion gets a test** in `tests/`, written the way the `godot-testing` skill says.
5. **Typed GDScript, tabs, snake_case.** Load the `gdscript-style` skill before writing GDScript and
   `godot-scenes` before writing or editing a `.tscn` file.
6. Keep changes to what the feature asks for. No refactors on the side.
