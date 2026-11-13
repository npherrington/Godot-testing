---
name: godot-playtest
description: Check acceptance criteria in the running game with the godot MCP tools (run, input, read state, screenshot). Use when playtesting a feature or verifying a visible change.
---

# Playtest

You check what a player would see, in the real running game. Evidence comes from the game, never
from reading code. One criterion at a time: **act, then read state, then look**.

## Tools

| Tool | Use |
| --- | --- |
| `godot_run_project` | Start the game. `{"projectPath": "<absolute project root>", "background": true}`. Call once. |
| `godot_simulate_input` | Drive the game. Actions run in order; see below. |
| `godot_run_script` | Read game state. Prefer this to screenshots for anything a number can answer. |
| `godot_take_screenshot` | Look at the screen: layout, visibility, colours, HUD text. Returns a preview and a file path. |
| `godot_get_ui_elements` | List visible Control nodes (labels, buttons) with text and position. |
| `godot_get_debug_output` | The game's log and errors. Check it at the end of every playtest. |
| `godot_stop_project` | Always call this last, pass or fail. |

The project root is the directory holding `project.godot` (the working directory).

## Driving input

Movement and controls are input **actions** from `project.godot` (`move_left`, `move_right`,
`move_up`, `move_down`, plus whatever the feature added). Hold an action with `hold_ms`:

```json
{"actions": [
  {"type": "action", "action": "move_right", "hold_ms": 500},
  {"type": "wait", "frames": 5}
]}
```

- `hold_ms` up to a few seconds moves the player; at speed 220 px/s, 500 ms is about 110 px.
- To hold two actions at once (diagonal), use `"pressed": true` on both, a `wait`, then
  `"pressed": false` on both.
- Add `"watch": ["/root/Main/Player:position"]` to see a value after every action.
- Keep one batch under about 20 seconds of holds and waits; split longer sequences.

## Reading state

`GameState.snapshot()` holds everything checkable (AGENTS.md rule 1):

```gdscript
extends RefCounted

func execute(scene_tree: SceneTree) -> Variant:
	return scene_tree.root.get_node("GameState").snapshot()
```

Count things by group: `return scene_tree.get_nodes_in_group("coins").size()`.
Read one node: `return scene_tree.get_first_node_in_group("player").global_position`.

## Steering to a target

To reach a thing at a known position, read the player position and the target position with
`run_script`, then hold the actions that close the gap: x first, then y. Hold time in ms is
about `distance_px / 220 * 1000`. Read the position again and correct; two or three corrections is
normal. Walls are at the arena edges (32 px thick).

## The loop, per criterion

1. Note the criterion's expected result.
2. Read the state before (`run_script`).
3. Act (`simulate_input`).
4. Read the state after. Compare with the expected result.
5. If the criterion is about what is seen (a label, a colour, something disappearing), take a
   screenshot and describe what is in it.

## Result file

First line exactly `VERDICT: PASS` (every criterion passed) or `VERDICT: FAIL`. Then one section per
criterion:

```markdown
VERDICT: FAIL

## 1. Collecting a coin adds 10 to the score: PASS
- Before: score 0, coins 5. Held move_right 900 ms toward the coin at (700, 270).
- After: score 10, coins 4. Screenshot: .mcp/godot-runtime/screenshots/....png shows "Score: 10".

## 2. ...: FAIL
- Expected ...; observed .... Evidence: ...
- Likely cause, if you can tell from the evidence: ...

## Debug output
- No errors. (Or: the errors, verbatim.)
```

Any `SCRIPT ERROR` in the debug output fails the playtest, even if every criterion passed.
