---
name: feature-plan
description: Write an implementation plan for a feature file, precise enough that an implementer can follow it without guessing. Use when planning a feature.
---

# Feature plan

The implementer is a smaller model working from your plan alone. Every name, path and number it
needs must be in the plan. Prefer the simplest design that meets every acceptance criterion.

## Steps

1. Read the feature file. List its acceptance criteria, numbered as in the file.
2. Read the files the feature touches (at least `scenes/main.tscn`, `scripts/main.gd`,
   `scripts/game_state.gd`, and any scene or script it names).
3. Decide anything the feature leaves open (sizes, positions, colours, counts) and record each
   decision in the plan's Decisions section.
4. Write the plan in the format below.

## Format

```markdown
# Plan: <feature title>

## Criteria
1. <criterion 1, copied>
2. ...

## Decisions
- <what the feature left open, and what you chose>

## Changes
### scripts/game_state.gd (edit)
- Add `var score := 0`. In `reset()`, set `score = 0`. Add `func add_score(amount: int) -> void`
  that adds and emits `changed`. Add `"score": score` to `snapshot()`.
### scenes/coin.tscn (new)
- Root `Coin` (Area2D, group `coins`, script `res://scripts/coin.gd`), child `Body` (Polygon2D,
  gold, 16x16), child `Collision` (CollisionShape2D, CircleShape2D radius 10).
### ...

## Tests
### tests/test_coins.gd (new)
- `test_collecting_a_coin_adds_ten_to_the_score` (criterion 1): spawn main, put the player 60 px
  left of the first coin, hold move_right 30 frames, expect `GameState.score == 10`.
- ...

## Playtest notes
- How a playtester reaches and checks each criterion in the running game (positions to steer to,
  what to read from `GameState.snapshot()`, what should be on screen).
```

## Rules

- Every criterion maps to at least one test and a playtest note.
- Name every new node, group, signal, action, variable and file exactly.
- Edits to `.tscn` files: say which nodes to add, with type, parent, properties and position.
- New state follows AGENTS.md rule 1; new controls rule 3.
- Do not plan changes outside the feature's scope, or to the harness (`bin/`, `tools/`,
  `.opencode/`, `tests/runner.gd`, `tests/test_case.gd`, `tests/parse_check.gd`,
  `tests/scene_check.gd`), or to the `[debug]` warning levels in `project.godot`.
