# GDScript Style

How GDScript is written in this project: Godot **4.7.2**, statically typed, tabs, clean under
**gdtoolkit 4.5.0** (`gdformat` + `gdlint`, run by `bin/check.sh`).

The short version agents load is the `gdscript-style` skill (`.opencode/skills/gdscript-style/`).
This page is the long form, with the reasons. If the two ever disagree, the skill wins and this page
gets fixed.

Last checked against the engine and tools: 2026-11-13. Every complete script on this page (each code
block that starts with `extends`) was compiled by Godot 4.7.2 and passes `gdformat --check` and
`gdlint`.

---

## 1. File shape

```gdscript
extends Area2D
## A coin. Adds VALUE to the score when the player walks into it, then disappears.

signal collected(value: int)

enum State { IDLE, TAKEN }

const VALUE := 10

@export var spin_speed := 2.0

var state := State.IDLE

@onready var _body: Polygon2D = $Body


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _process(delta: float) -> void:
	_body.rotation += spin_speed * delta


func _on_body_entered(body: Node2D) -> void:
	if state == State.TAKEN or not body.is_in_group("player"):
		return
	state = State.TAKEN
	collected.emit(VALUE)
	queue_free()
```

### Declaration order

gdlint enforces the order of declarations (`class-definitions-order`), and the official style guide
also orders methods. Together, top to bottom:

| # | What | Enforced by |
| --- | --- | --- |
| 1 | `@tool`, `@icon`, `@static_unload` | gdlint |
| 2 | `class_name` (only when needed, see below) | gdlint |
| 3 | `extends` | gdlint |
| 4 | `##` doc comment, one line saying what this is for | gdlint |
| 5 | `signal`s | gdlint |
| 6 | `enum`s | gdlint |
| 7 | `const`s | gdlint |
| 8 | `static var`s | gdlint |
| 9 | `@export var`s | gdlint |
| 10 | public `var`s, then `_private` vars | gdlint |
| 11 | `@onready var`s, public then private | gdlint |
| 12 | `_static_init()`, then other `static func`s | style guide |
| 13 | built-in virtuals, in this order: `_init`, `_enter_tree`, `_ready`, `_process`, `_physics_process`, then the rest (`_input`, `_unhandled_input`, ...) | style guide |
| 14 | public methods, then `_private` methods and signal handlers | style guide |
| 15 | inner `class`es | style guide |

gdlint treats every function as "others", so it does not catch functions in the wrong order.
Reviewers do.

### `class_name`: only when another script needs the type

A `class_name` puts the name in the global namespace and in `.godot/global_script_class_cache.cfg`.
Add one only when another script needs it as a type (`var target: Enemy`, `body is Enemy`) or
calls its `static func`s. Otherwise, find nodes by group. Scene scripts in this repo
(`player.gd`, `main.gd`) don't have one. Autoloads are already global by their autoload name
(`GameState`), so they must **not** also declare a `class_name` with the same name; Godot rejects that.

---

## 2. Formatting

| Rule | Value | Source |
| --- | --- | --- |
| Indentation | **Tabs**, one per level | style guide; gdlint `tab-characters: 1` |
| Continuation lines | Two extra indent levels, or one inside brackets | style guide; gdformat decides |
| Line length | **100** max (gdlint `max-line-length`); aim for 80 | gdlint default, style guide |
| Between functions and classes | Exactly **two** blank lines | gdformat |
| Trailing whitespace | None | gdlint |
| File length | 1000 lines max | gdlint `max-file-lines` |
| Quotes | Double quotes | style guide |
| Boolean operators | `and` / `or` / `not`, not `&&` / `||` / `!` | style guide |
| Comments | `# ` and `## ` with one space after | style guide |

Don't hand-format. When the gate's `format` step fails, run `bin/format.sh`. It rewrites the files
and is always safe.

---

## 3. Naming

| Thing | Convention | Example |
| --- | --- | --- |
| Files (`.gd`, `.tscn`) | `snake_case` | `game_state.gd`, `coin.tscn` |
| `class_name`, inner classes, node names | `PascalCase` | `Enemy`, `Player`, `HUD` |
| Functions, variables, parameters | `snake_case` | `add_score()`, `max_health` |
| Private members | leading `_` | `_taken`, `_spawn_one()` |
| Signals | `snake_case`, past tense | `collected`, `health_changed` |
| Signal handlers | `_on_<node>_<signal>` or `_on_<signal>` | `_on_body_entered` |
| Constants, enum members | `CONSTANT_CASE` | `MAX_COINS`, `State.IDLE` |
| Enum types | `PascalCase` | `enum State { ... }` |
| `preload` constants | `PascalCase` or `CONSTANT_CASE` | `const CoinScene := preload(...)` |
| Groups | `snake_case`, plural for collections | `coins`, `enemies`, `player` |
| Input actions | `snake_case` verb | `move_left`, `dash` |

These are the gdlint defaults (`gdlint -d` dumps them), and they match the official guide.

---

## 4. Static typing

Type everything. Typed code runs faster, and it is the compiler's only way to catch an agent's
mistakes before runtime.

```gdscript
var speed := 220.0  # inferred float: fine when the type is obvious on the line
var target: Node2D = null  # explicit when the value doesn't show the type
var hits: Array[int] = []
var drops: Dictionary[StringName, float] = {}  # typed dictionaries: Godot 4.4+


func damage_for(level: int, bonus := 0) -> int:  # every parameter and return typed
	return level * 2 + bonus
```

- **`:=` or `: Type =`, never bare `=`.** `var a = 1` is untyped. `var a := 1` infers `int`.
  Use `:=` when the right-hand side makes the type obvious; otherwise write the type.
- **Typed collections:** `Array[Node2D]`, `Dictionary[String, int]`. Both type arguments are
  required for dictionaries (use `Variant` for a side that can be anything). Nested typed
  collections are not supported: `Dictionary[String, Array[int]]` is an error, and
  `Dictionary[String, Array]` is fine.
- **Typed loop variables** when the iterable is untyped: `for key: StringName in drops:`.
- **Return `-> void`** explicitly. A typed function must return on every path.
- **Node references** from `$` are untyped (`Node`). Give them a type:
  `@onready var _label: Label = $Score`. If the node is the wrong type, assigning to a typed
  variable fails loudly when the scene loads, while `$Score as Label` silently gives `null`.
- **Casting:** `x as Type` returns `null` when an object isn't that type, with no error. Check with
  `is` / `is not` when you need certainty: `if body is not CharacterBody2D: return`.
  Casting between incompatible built-in types (`"5" as int`) is an error, not `null`.
- **No nullable types.** GDScript has no `Type?`. Object-typed variables can always hold `null`;
  value types (`int`, `Vector2`, ...) never can. Return `null` from `-> Node2D`, never from `-> int`.

### Warnings as errors

Godot ships with most typing warnings off. Turning them up to *error* (2) makes the import and test
steps fail on the mistakes agents make most. They go in `project.godot` under `[debug]`:

```ini
[debug]

gdscript/warnings/untyped_declaration=2
gdscript/warnings/unsafe_property_access=2
gdscript/warnings/unsafe_call_argument=2
gdscript/warnings/unsafe_cast=2
gdscript/warnings/missing_await=2
```

On 2026-11-13 these five were checked against this repo: with all of them on, every script still
compiles, `bin/test.sh` passes 4/4, and the smoke run is clean. Two related settings are left
off on purpose:

- **`unsafe_method_access`** would catch hallucinated methods (`get_tree().change_scene()`,
  `scene.instance()`, which are Godot 3 names). But it also rejects `load(path).instantiate()` in
  `tests/test_case.gd`, a harness file nobody may edit. Set to 2, it breaks the test runner.
- **`inferred_declaration`** bans `:=`, which the harness and this guide both use.

Only error level matters headless. Warn level (1) shows in the editor, but not in
`bin/check.sh` output.

These settings are **not enabled yet**. `project.godot` says to edit it by hand only for
`[input]` and `[autoload]`, so adding `[debug]` is a decision for the repo owner, not a
feature agent. See [AGENTIC_GODOT.md](AGENTIC_GODOT.md#make-the-compiler-strict).

To silence one warning on purpose, use `@warning_ignore("unused_parameter")` on the line above, or
`@warning_ignore_start("name")` / `@warning_ignore_restore("name")` around a region (Godot 4.4+).
Names are the lowercase setting names.

---

## 5. Newer language features (Godot 4.4 to 4.7)

Models trained mostly on Godot 3 or early Godot 4 code don't know these. All of them compile on
4.7.2 and pass gdtoolkit 4.5.0.

| Feature | Since | Syntax |
| --- | --- | --- |
| Typed dictionaries | 4.4 | `var d: Dictionary[String, int] = {}` |
| `.uid` sidecar files | 4.4 | `player.gd.uid` next to every script. Commit it; move or rename it with its script |
| Region warning ignores | 4.4 | `@warning_ignore_start("unused_variable")` / `@warning_ignore_restore(...)` |
| Inspector button | 4.4 | `@export_tool_button("Bake", "Bake") var bake_action: Callable = bake` (needs `@tool`; the second argument is an editor icon name) |
| Abstract classes and methods | 4.5 | `@abstract class_name Shape`, `@abstract func area() -> float` (no body, no colon) |
| Variadic functions | 4.5 | `func sum(first: float, ...rest: Array) -> float:`. One rest parameter, last, untyped `Array`, no default. There is no spread operator; use `callv()` |
| Raw file paths in exports | 4.5 | `@export_file_path("*.png") var icon_path: String` |
| `missing_await` warning | 4.6 | Calling a coroutine without `await`. Ignored by default |
| Overrides inherit return type | 4.7 | An override of a typed-return method must `return` a value on every path |

**gdformat writes `@abstract` on the same line** as what it annotates:

```gdscript
@abstract class_name Shape
extends Node2D
## Base for shapes. Subclasses must say how big they are.

@abstract func area() -> float
```

If you write `@abstract` on its own line, `bin/format.sh` moves it. Both forms compile.

**Traits did not land.** The PR was closed unmerged. Use composition (child nodes, groups) or a
shared base class.

---

## 6. Godot 4 API, not Godot 3

Most broken GDScript an agent writes is Godot 3 code. The 4.7 compiler rejects the syntax with a
message that names the fix. But **renamed methods on objects compile and only fail at runtime**
(see `unsafe_method_access` above), so learn this table:

| Godot 3 (wrong) | Godot 4 (right) |
| --- | --- |
| `export var x = 1` / `onready var` / `tool` | `@export var x := 1` / `@onready var` / `@tool` |
| `yield(get_tree(), "idle_frame")` | `await get_tree().process_frame` |
| `yield(timer, "timeout")` | `await timer.timeout` |
| `connect("body_entered", self, "_on_hit")` | `body_entered.connect(_on_hit)` |
| `emit_signal("died", x)` | `died.emit(x)` |
| `var x setget set_x` | `var x: int:` with `set(value):` / `get:` blocks, or `var x: int: set = set_x` |
| `KinematicBody2D`, `move_and_slide(vel, Vector2.UP)` | `CharacterBody2D`: set `velocity` (and `up_direction`), then `move_and_slide()` |
| `Sprite`, `Position2D`, `YSort` | `Sprite2D`, `Marker2D`, `y_sort_enabled` |
| `TileMap` (deprecated in 4.3) | `TileMapLayer`, one node per layer |
| `scene.instance()` | `scene.instantiate()` |
| `get_tree().change_scene(path)` | `get_tree().change_scene_to_file(path)` |
| `update()` (redraw) | `queue_redraw()` |
| `filename` | `scene_file_path` |
| `array.empty()` / `remove(i)` / `invert()` | `is_empty()` / `remove_at(i)` / `reverse()` |
| `RectangleShape2D.extents` | `size` (now the full size, not half) |
| `rand_range(a, b)` | `randf_range(a, b)` / `randi_range(a, b)` |
| An override of `_ready()` runs the parent's `_ready()` automatically | It doesn't: call `super()` |
| `Tween` node | `create_tween()` |

### Things that look like GDScript but aren't

These come from Python or C# habits. All of them fail to compile on 4.7.2:

| Not GDScript | Use |
| --- | --- |
| `func f() -> Node?:` (nullable) | `-> Node`, which may return `null` |
| `for k, v in dict:` | `for k in dict:` then `dict[k]` |
| `dict.is_key(k)` | `dict.has(k)` or `k in dict` |
| `@staticmethod` | `static func` |
| `Array[int]()` | `var a: Array[int] = []` |
| `@onready var` inside a function | `@onready` is for member variables only |
| `var (a, b) = pair` (destructuring) | `var a := pair[0]` |
| `"""docstring"""` | `##` comments **above** the function. A bare string compiles, but it's a standalone expression, not documentation |

---

## 7. Strings and output

```gdscript
var line := "Score: %d" % score  # one value
var pos := "(%.1f, %.1f)" % [p.x, p.y]  # several values: an Array
var named := "{who} took {n}".format({"who": who, "n": n})
var quick := str("hp=", hp, " max=", max_hp)  # str() concatenates its arguments
```

- `%` and `format()` are clearer than `+` chains. `+` only joins strings, so `"a" + 1` is an error.
- `print()` for temporary debugging only; remove it before you finish. The gate fails on errors, not
  prints, but noisy output hides the real errors from the next agent.
- `push_error("...")` for "this should never happen". It logs with a stack trace and execution
  continues. **The gate fails on any `ERROR:` line**, so `push_error` in a path that tests hit
  fails `bin/check.sh`. That's intended.
- `push_warning("...")` for recoverable oddities.
- `assert(cond, "msg")` runs only in debug builds and is stripped from release exports. Never put a
  side effect in the condition.

---

## 8. Control flow

- **Early returns** over nesting (gdlint also flags `else` after `return`: `no-else-return`,
  `no-elif-return`).
- **`match`** for three or more branches on one value. `_:` is the default arm.
- **No parentheses** around `if` / `while` conditions.
- At most **6 returns** per function and **10 parameters** (gdlint `max-returns`,
  `function-arguments-number`). Hitting either means the function should be split.

```gdscript
func label_for(state: int) -> String:
	match state:
		0:
			return "idle"
		1:
			return "moving"
		_:
			return "unknown"
```

---

## 9. Godot-specific habits

- **Connect signals in code**, in `_ready()`: `body_entered.connect(_on_body_entered)`. Then the
  connection is visible where the handler is. Don't add `[connection]` entries to `.tscn` files.
- **Physics in `_physics_process`**, visuals in `_process`. Movement uses `velocity` +
  `move_and_slide()`.
- **Input through actions** (AGENTS.md rule 3): `Input.get_vector(...)`,
  `Input.is_action_just_pressed("dash")`. Never `Input.is_key_pressed(KEY_A)` or raw keycodes.
- **Find nodes by group or `%UniqueName`** (AGENTS.md rule 2), never by long `get_node()` paths.
  `$Child` for a node this scene owns directly is fine.
- **`get_tree().get_nodes_in_group("coins")`** returns `Array[Node]`.
  `get_first_node_in_group("player")` returns the node or `null`.
- **State goes through `GameState`** (AGENTS.md rule 1): see [ARCHITECTURE.md](ARCHITECTURE.md).
- **`preload()` in a `const`** for scenes you instance: `const CoinScene := preload("res://scenes/coin.tscn")`.
  A preload of a missing path is a compile error, which is what you want.
- **Defer tree changes made during physics callbacks.** Adding or freeing physics nodes inside
  `body_entered` can error ("Can't change this state while flushing queries"). Use
  `queue_free()` (already deferred), `add_child.call_deferred(node)`, or
  `set_deferred("monitoring", false)`.

---

## 10. Comments

- One `##` doc comment line under `extends`, saying what the script is *for*.
- `##` above a public function to document it. Godot's doc syntax supports
  `@deprecated`, `@experimental` and `@tutorial`. It has no `@param` / `@return`, so describe
  those in the sentence.
- `#` comments say **why**, not what. A comment that repeats the code is noise.
- No commented-out code; git has the history.

---

## Checklist

- [ ] `bin/format.sh` run; `bin/check.sh` passes
- [ ] Every `var`, parameter and return is typed (`:=` or `: Type`)
- [ ] Declarations in the order of section 1; functions: virtuals, public, private
- [ ] Godot 4 names only (section 6); no Python-isms
- [ ] Signals connected in `_ready()` with `.connect(callable)`
- [ ] New state is on `GameState`, reset in `reset()`, in `snapshot()`
- [ ] No `class_name` unless another script uses the type
- [ ] New `.gd` files committed **with** their `.gd.uid`
