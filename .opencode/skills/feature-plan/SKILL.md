---
name: feature-plan
description: Write a short implementation plan for a feature file before building it, so you can follow it step by step and pick it up again after a long or restarted session. Use when starting a feature.
---

# Feature plan

The plan is your memory. A long session loses detail; the plan file doesn't. Decide every name,
path and number now, so building is following, not designing. Prefer the simplest design that
meets every acceptance criterion.

## Steps

1. Read the feature file. List its acceptance criteria, numbered as in the file.
2. Read the files the feature touches (at least `scenes/main.tscn`, `scripts/main.gd`,
   `scripts/game_state.gd`, and any scene or script it names). Don't plan changes to files you
   haven't read.
3. Decide anything the feature leaves open (sizes, positions, colours, counts) and record each
   decision in the Decisions section.
4. Write `runs/<feature>/plan.md` in the format below. Keep it under about 60 lines.

## Format

```markdown
# Plan: <feature title>

## Criteria
1. <criterion 1, copied>
2. ...

## Decisions
- <what the feature left open, and what you chose>

## Changes
- [ ] scripts/game_state.gd (edit): add `var score := 0`; reset in `reset()`; add
      `func add_score(amount: int) -> void` that adds and emits `changed`; add `"score"` to `snapshot()`.
- [ ] scenes/coin.tscn (new): root `Coin` (Area2D, group `coins`, script `res://scripts/coin.gd`),
      child `Body` (Polygon2D, gold, 16x16), child `Collision` (CollisionShape2D, CircleShape2D r=10).
- [ ] ...

## Tests
- [ ] tests/test_coins.gd `test_collecting_a_coin_adds_ten_to_the_score` (criterion 2): spawn main,
      put the player 60 px left of the first coin, hold move_right 30 frames, expect score 10.
- [ ] ...

## Playtest
- Criterion 2: steer to the coin at (x, y); expect `snapshot().score` 0 -> 10, coins 5 -> 4.
- ...
```

Tick the boxes (`- [x]`) as you finish each change, so the plan shows where you are.

## Rules

- Every criterion maps to at least one test and one playtest line.
- Name every new node, group, signal, action, variable and file exactly.
- For `.tscn` edits, say which nodes to add, with type, parent, properties and position.
- New state follows AGENTS.md rule 1; new controls rule 3.
- Don't plan changes outside the feature's scope, to the harness (`bin/`, `tools/`, `.opencode/`,
  `tests/runner.gd`, `tests/test_case.gd`, `tests/parse_check.gd`, `tests/scene_check.gd`), or to
  the `[debug]` warning levels in `project.godot`.
