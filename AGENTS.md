# Godot Lab

A small top-down 2D game in Godot 4.7 (GDScript), built one feature file at a time.

## Commands

| Command | What it does |
| --- | --- |
| `bin/check.sh` | **The gate.** Format, lint, import, parse, scenes, tests, smoke run. A change is done only when this passes. |
| `bin/test.sh [filter]` | Headless tests only, optionally filtered by file or method name |
| `bin/format.sh` | Fix formatting (run this when the gate's `format` step fails) |

## Layout

- `project.godot`: settings, input actions (`[input]`), autoloads (`[autoload]`). Its `[debug]`
  warning levels are part of the gate: never lower or remove them; fix the code they flag.
- `scenes/*.tscn`: one scene per thing (`main`, `player`, ...). `main.tscn` is the game.
- `scripts/*.gd`: one script per scene, same name. `game_state.gd` is the `GameState` autoload.
- `tests/test_*.gd`: tests. `runner.gd`, `test_case.gd`, `parse_check.gd` and `scene_check.gd` are the harness; do not edit them.
- `features/`: feature files, the specs. `runs/<feature>/`: your plan and playtest notes (not committed).
- `bin/`, `tools/`, `.opencode/`, `opencode.jsonc`: the harness. Do not edit them.
- `docs/`: long reference for people. Don't load it whole; the skills are the short versions.

## Building a feature

Work one step at a time, and finish each step before starting the next.

1. **Plan.** Read the feature file and the files it touches. Load `feature-plan` and write
   `runs/<feature>/plan.md`. If the session gets long or restarts, reread the plan, not the chat.
2. **Build.** Change the scenes and scripts, and write a test for each acceptance criterion.
3. **Gate.** Run `bin/check.sh`. Fix the **first** failure only, then run it again. Never weaken
   or delete a test to make it pass. If the same failure survives 3 attempts, stop and say what
   you tried.
4. **Playtest.** Load `godot-playtest` and check each criterion in the running game. Write
   `runs/<feature>/playtest.md`. If something fails, go back to step 2.
5. **Self-review.** Read `git diff` and check: each criterion is met and tested, rules 1 to 6
   below hold, and nothing outside the feature changed. Then summarise. Don't commit unless asked.

## Rules

1. **State lives in `GameState`.** Anything a test or playtest needs to check (score, health,
   counts, flags) is a variable on `GameState`, reset in `reset()` and included in `snapshot()`.
2. **Find nodes by group or unique name, never by long paths.** Add new things to a group named
   after them (`coins`, `enemies`) so tests and playtests can count them.
3. **Input goes through actions.** Add new controls to `[input]` in `project.godot`; read them
   with `Input.is_action_*`, never raw keycodes.
4. **Every acceptance criterion gets a test** in `tests/`, written the way the `godot-testing` skill says.
5. **Typed GDScript, tabs, snake_case.** Load the `gdscript-style` skill before writing GDScript and
   `godot-scenes` before writing or editing a `.tscn` file.
6. Keep changes to what the feature asks for. No refactors on the side.
