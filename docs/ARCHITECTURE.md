# Architecture

How the game is put together, and why it's shaped for a coding model. The model builds it. Tests
check it headless. A playtest checks it in a running window, reading state through the godot MCP.
All three need the game to be **inspectable**: state in one known place, things
findable by group, input through named actions. AGENTS.md rules 1 to 3 say this in short; this page
explains it.

Last checked: 2026-11-13, against Godot 4.7.2 and the code in this repo. The examples are from
the reference feature in [PATTERNS.md](PATTERNS.md), which compiles and passes its tests.

---

## 1. The pieces

```
project.godot      [autoload] GameState  ->  scripts/game_state.gd   (lives for the whole run)
                   [input]    move_*, ... (named actions)

scenes/main.tscn   Main (Node2D, scripts/main.gd)          the game scene; reset on load
  ├─ Background, Walls                                     static arena
  ├─ Player        (instance of player.tscn, group "player")
  ├─ ...           (coins, enemies: instanced or spawned; each kind in its own group)
  └─ HUD           (CanvasLayer, reads GameState)
```

| Piece | Owns | Doesn't |
| --- | --- | --- |
| **`GameState`** (autoload) | All state a test or player would check: score, health, counts, flags. The methods that change it. `reset()`, `snapshot()`, signals | Nodes, visuals, input |
| **`main.gd`** | Starting a game (`GameState.reset()`), spawning, restart, wiring scenes together | Rules of any one kind of thing |
| **One scene + script per kind of thing** (`player`, `coin`, `enemy`, `hud`) | Its own movement, visuals and collisions. It calls `GameState` methods when something counts | Other scenes' children; state that matters beyond itself |
| **Pure rules** (`static func`s) | Formulas: damage, scoring, thresholds | Anything with a node |

---

## 2. `GameState`: one source of truth

`GameState` is an autoload. Godot creates it at startup, as `/root/GameState`, before any scene,
and keeps it across scene changes and restarts. Every script can use it by name.

**Everything checkable lives on it** (AGENTS.md rule 1): a variable, reset in `reset()`, included
in `snapshot()`. The full current pattern is in [PATTERNS.md](PATTERNS.md#gamestate). Its core:

```gdscript
signal changed

var score := 0


func reset() -> void:
	score = 0
	changed.emit()


func collect_coin(value: int) -> void:
	score += value
	changed.emit()


func snapshot() -> Dictionary:
	return {"score": score}
```

### Why one place

- **Tests** read `GameState.score`, and nothing else has to be found.
- **A playtest** reads it live: `godot_run_script` returns `GameState.snapshot()` as JSON, and
  `godot_simulate_input` can watch `/root/GameState:score` after every simulated input.
- **Restarts are trivial:** `reset()` puts everything back. Node state is rebuilt anyway when
  the scene reloads.
- **Review** (yours or the model's) sees every piece of game state in one file.

### Rules for state

1. **Change it through methods.** Write `GameState.collect_coin(10)`, not `GameState.score += 10`.
   The method is where validation lives (no negative damage, nothing after game over) and where
   `changed` is emitted. A direct write skips both, and the HUD goes stale.
2. **`reset()` resets everything** to its starting value and emits `changed`. `main.gd` calls it in
   `_ready()`, so each new game (and each test that spawns main) starts clean.
   Configuration such as `rng_seed` is the one exception: `reset()` reads it but doesn't clear it.
3. **`snapshot()` returns plain values**: ints, floats, bools, strings, Arrays of those. The MCP
   bridge serialises the result to JSON. Round floats you'll compare
   (`roundi(position.x)`), and put vectors in as `[x, y]`. Include **counts** a criterion talks about
   (`"coins_left": get_tree().get_nodes_in_group("coins").size()`).
4. **Transient things stay on their node:** velocity, animation frame, a cooldown counter, whether
   *this* coin was already taken. If no criterion, test or other script needs it, it isn't
   game state.
5. **No `class_name` on autoloads.** The autoload name is already global, and a matching
   `class_name` is an error.

---

## 3. Signals: who tells whom

```
Player walks into Coin
  -> Coin._on_body_entered(body)           the coin notices (physics callback)
  -> GameState.collect_coin(10)            state changes in one place
  -> GameState.changed.emit()              ...and says so
  -> HUD._refresh()                        listeners redraw
```

- **Things call `GameState` methods; `GameState` emits; listeners react.** The emitter doesn't know
  who listens, so a new HUD element never needs `GameState` changes.
- **`changed`** (no arguments) is enough for most listeners: they just re-read what they show.
  Add a specific signal when listeners need *the event*, not the new state: `game_over`,
  `collected(value: int)`. Type the parameters.
- **Connect in code**, in `_ready()`: `GameState.changed.connect(_refresh)`. When the listening
  node is freed, Godot removes its connections, so scene reloads don't leave dangling ones.
- **Names are past tense, snake_case:** `changed`, `died`, `coin_collected`.
- **Emit with `signal_name.emit(args)`**, not `emit_signal("signal_name")`.
- Don't use signals to ask questions or get return values. Call a method.

---

## 4. Pure rules: static functions

A formula that doesn't need a node (damage after armour, a score bonus, a level threshold) goes in
a `static func`, in a script with a `class_name` so others can call it:

```gdscript
class_name Rules
extends RefCounted
## Pure game rules: numbers in, numbers out. No nodes or tree, so tests call them directly.


## Damage after armour; a hit always does at least 1.
static func damage_after_armor(damage: int, armor: int) -> int:
	return maxi(damage - armor, 1)
```

Callers use `Rules.damage_after_armor(5, 2)`. Tests check every edge case without a scene
([TESTING_STANDARDS.md §10](TESTING_STANDARDS.md#10-pure-logic-test-without-a-scene)). Don't make
these autoloads or nodes. Only add this layer when there's a real formula; a one-line `score += 10`
doesn't need one.

---

## 5. Finding nodes

In order of preference (AGENTS.md rule 2):

| Need | Use | Example |
| --- | --- | --- |
| Data | `GameState` | `GameState.health` |
| All things of a kind, anywhere | Group | `get_tree().get_nodes_in_group("coins")` |
| The one thing of a kind | Group | `get_tree().get_first_node_in_group("player") as Node2D` |
| A child this scene owns | `$Name` or `%UniqueName`, cached in `@onready` | `@onready var _score: Label = %Score` |
| Another scene's internals | **Don't.** Signal, group or `GameState` | |

- Every kind of thing gets a group named after it, set on the scene root in its `.tscn`
  (`groups=["coins"]`). Spawned instances inherit it. Tests and playtests count by group.
- `get_node("/root/Main/World/Coins/Coin3")` and other long paths break the moment a node moves or
  is renamed. The self-review step in AGENTS.md checks for them.
- The test harness uses `main.get_node("Player")`. That's a direct child of the scene the test
  spawned, which is fine.

---

## 6. Scene lifecycle

| Moment | What happens |
| --- | --- |
| Game launch | Autoloads are created (`GameState`). Then `run/main_scene` (`main.tscn`) loads and becomes `current_scene` |
| `_ready()` order | **Children before parents.** `HUD._ready()` (connects to `changed`) runs before `Main._ready()` (calls `reset()`), so the HUD sees the reset |
| Restart | `get_tree().reload_current_scene()`. The old scene is freed and a new `main` is built; `GameState` survives, and `main._ready()` resets it |
| Changing level | `get_tree().change_scene_to_file("res://scenes/level_2.tscn")`. Again, state that must survive belongs on `GameState` |
| Test | The harness instances main under the root and makes it `current_scene`, the same as a launch |

Both scene-change calls are deferred: the swap happens at the end of the frame.

---

## 7. Input

Actions are defined in `project.godot` `[input]` and read with `Input` (AGENTS.md rule 3):

```gdscript
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if Input.is_action_just_pressed("restart"):
		get_tree().reload_current_scene()
```

- A new control means a new action in `[input]` with a keyboard event, using a
  `physical_keycode`: `R` is 82, `Space` is 32, and Godot's own key constants cover the rest.
- **Poll in `_process` / `_physics_process`.** Both the test harness (`Input.action_press`) and the
  MCP playtest drive polled input. The harness doesn't trigger `_input()` callbacks
  ([TESTING_STANDARDS.md §7](TESTING_STANDARDS.md#7-input)).
- Never `Input.is_key_pressed(KEY_R)` or keycodes in scripts.

---

## 8. Determinism

Agents debug by re-running, so runs should repeat:

- **Fixed timestep in tests and smoke runs** (`--fixed-fps 60`). Count cooldowns and intervals in
  physics frames, or derive them from `delta` in `_physics_process`.
- **One random source:** `GameState.rng` (a `RandomNumberGenerator`), seeded in `reset()` from
  `GameState.rng_seed` (0 means random). Never global `randf()` in game code; tests can't control it.
- **No wall-clock time** (`Time.get_ticks_msec()`) in game rules.

---

## 9. Anti-patterns

| Don't | Do |
| --- | --- |
| Keep score or health on the player node | A variable on `GameState`, with a method to change it |
| `GameState.health -= 1` from another script | `GameState.damage_player(1)` |
| Forget `reset()` or `snapshot()` for a new variable | Add all three: the variable, its reset, its snapshot entry |
| Poll `GameState` every frame in the HUD | Connect to `GameState.changed` |
| `get_node("../../World/Player")` | `get_tree().get_first_node_in_group("player")` |
| `emit_signal("changed")`, `connect("changed", self, "_on_changed")` | `changed.emit()`, `changed.connect(_on_changed)` |
| Spawn or free physics nodes directly inside `body_entered` | `queue_free()`, `add_child.call_deferred(node)` |
| `randi()` for game randomness | `GameState.rng.randi_range(a, b)` |
| A manager autoload per system (`ScoreManager`, `EnemyManager`) | One `GameState`; the spawning logic lives in `main.gd` or a spawner node |
| Object pools, service layers, event buses "for later" | The simplest thing that meets the criteria (AGENTS.md rule 6). Add structure when a feature needs it |
