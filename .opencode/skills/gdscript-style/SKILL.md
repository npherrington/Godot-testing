---
name: gdscript-style
description: GDScript conventions for this project (Godot 4.7, typed, tabs, gdlint/gdformat clean). Load before writing or changing any .gd file.
---

# GDScript style

`bin/check.sh` runs gdformat and gdlint; code that follows this passes both.

## Shape

```gdscript
extends Area2D
## One line saying what this node is for.

signal collected(value: int)

const VALUE := 10

@export var speed := 120.0

var _taken := false

@onready var _sprite: Polygon2D = $Body


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if _taken or not body.is_in_group("player"):
		return
	_taken = true
	GameState.add_score(VALUE)
	collected.emit(VALUE)
	queue_free()
```

Order: `extends`, doc comment, signals, enums, constants, `@export` vars, public vars, private
vars, `@onready` vars, built-in callbacks (`_ready`, `_process`, `_physics_process`), public
functions, private functions. Two blank lines between functions.

## Rules

- **Indent with tabs.** Lines at most 100 characters.
- **Type everything**: `var count: int = 0` or `var count := 0`, typed parameters and return types
  (`-> void`). Use `as` to cast nodes: `get_first_node_in_group("player") as Node2D`.
  The gate enforces this: `project.godot` turns untyped declarations, property access on an
  uncast `Node`, and coroutines called without `await` into compile errors. The error message
  names the line and the fix.
- **Names**: files and functions `snake_case`, classes and nodes `PascalCase`, constants
  `UPPER_CASE`, private members start with `_`, signal handlers `_on_<node>_<signal>`.
- **Connect signals in code** in `_ready()` (`body_entered.connect(_on_body_entered)`), not in the
  `.tscn`, so the connection is visible in the script.
- **Game state goes through `GameState`** (scripts/game_state.gd): add a variable, a method that
  changes it (`add_score`), reset it in `reset()`, include it in `snapshot()`, and emit `changed`.
- **No `class_name` unless another script needs the type.** Prefer groups for finding nodes.
- Physics movement in `_physics_process` with `move_and_slide()`; visuals in `_process`.
- Comments say why, not what. One-line doc comment at the top of each script.
- Godot 4 API only: `Callable`/`.connect()`, `@export`, `@onready`, `super()`, `await signal`
  (never Godot 3's `yield`, `connect("signal", self, "method")`, `export var`, `onready var`).
