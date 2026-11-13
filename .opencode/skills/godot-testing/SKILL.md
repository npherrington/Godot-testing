---
name: godot-testing
description: Write headless tests for this project's runner (tests/test_*.gd, extends test_case.gd). Use when adding or changing tests, or when bin/test.sh fails.
---

# Tests

Tests run headless with `bin/test.sh` (and inside `bin/check.sh`) at a fixed 60 physics frames per
second, so frame counts are deterministic. Run one file or method with `bin/test.sh <part of name>`.

## Shape of a test file

`tests/test_<thing>.gd`:

```gdscript
extends "res://tests/test_case.gd"


func test_collecting_a_coin_adds_ten_to_the_score() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var coin := main.get_tree().get_nodes_in_group("coins")[0] as Node2D
	var player := main.get_node("Player") as Node2D
	player.global_position = coin.global_position + Vector2(-60, 0)
	await hold_action("move_right", 30)
	check_eq(GameState.score, 10, "score after one coin")
```

- One test method per behaviour, named `test_<what happens>` as a sentence.
- Every test starts with `await spawn("res://scenes/main.tscn")` (or the scene under test). Each
  test gets a fresh scene; the harness frees it and releases all input afterwards.
- Always `await` these helpers.

## Helpers (from test_case.gd)

| Helper | Does |
| --- | --- |
| `await spawn(path)` | Instance the scene as the current scene, wait one frame, return it |
| `await physics_frames(n)` | Step n physics frames (60 = one second of game time) |
| `await hold_action(action, frames)` | Hold an input action for n physics frames, then release |
| `await tap_action(action)` | Press and release an action once |
| `check(condition, message)` | Record a failure when condition is false |
| `check_eq(actual, expected, message)` | Record a failure when they differ, showing both |

## What makes a good test here

- **Drive the game through input actions** (`hold_action`), as a player would. Set positions
  directly only to skip travel that is not what the test is about, as above.
- **Assert on `GameState`** and on groups (`get_nodes_in_group("coins").size()`), not on private
  variables or long node paths.
- **Check the effect, and the absence of a wrong effect**: the score went up by exactly 10, and the
  coin is gone, and a second overlap does not add 10 again.
- A test must fail if the feature is removed. If it would still pass, it tests nothing.
- Signals and physics overlaps need frames to happen: after moving into something, step at least
  2 physics frames before asserting.

## When bin/test.sh fails

- `FAIL file::method: message`: the assertion that failed and its values.
- `does not load`: a parse error in that test file; the engine error above it names the line.
- `SCRIPT ERROR` lines fail the run even when every test passed: fix the runtime error they name.
