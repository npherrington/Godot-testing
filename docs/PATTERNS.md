# Patterns

Working code for the things features here usually need. Together these files make one small
feature set: coins and score, a HUD, enemies that chase and hurt the player, a spawner, game over
and restart. They are **copied verbatim** from a build of that feature set, made on 2026-11-13 in a
copy of this repo. There, every file passed `gdformat --check`, `gdlint`, the Godot 4.7.2 import and
compile, and the tests in [TESTING_STANDARDS.md](TESTING_STANDARDS.md) (21 passing, including this
repo's 4). That was with the strict warnings from
[GDSCRIPT_STYLES.md](GDSCRIPT_STYLES.md#warnings-as-errors) turned on.

Use them as shapes, not as features to add. Build what the feature file asks for (AGENTS.md
rule 6), and take names, numbers and sizes from the plan.

| Pattern | Files |
| --- | --- |
| [GameState](#gamestate) | `scripts/game_state.gd` |
| [A pickup](#a-pickup) | `scenes/coin.tscn`, `scripts/coin.gd` |
| [Spawning at clear random spots](#spawning-at-clear-random-spots) | `scripts/main.gd` |
| [A HUD that follows GameState](#a-hud-that-follows-gamestate) | `scenes/hud.tscn`, `scripts/hud.gd` |
| [An enemy that chases and hurts](#an-enemy-that-chases-and-hurts) | `scenes/enemy.tscn`, `scripts/enemy.gd` |
| [Spawning over time](#spawning-over-time) | `scripts/enemy_spawner.gd` |
| [Game over and restart](#game-over-and-restart) | `scripts/main.gd`, `project.godot` |
| [Pure rules](#pure-rules) | `scripts/rules.gd` |
| [Wiring into main.tscn](#wiring-into-maintscn) | `scenes/main.tscn` |
| [Reading state from the playtester](#reading-state-from-the-playtester) | an MCP `run_script` |

---

## GameState

Every checkable value: a variable, a method that changes it and emits `changed`, a line in
`reset()`, an entry in `snapshot()`. Randomness comes from one seeded `rng`.

```gdscript
extends Node
## Autoload "GameState": the one place game state lives.
## Tests and the playtester read the game through snapshot(), so every feature
## that adds state (score, health, level, timers) adds it here and to snapshot().

signal changed
signal game_over

const START_HEALTH := 3

## Seed for rng. 0 picks a new random seed on every reset(). Tests set it before spawning main.
## Configuration, not game state: reset() reads it but never clears it.
var rng_seed := 0

var score := 0
var coins_collected := 0
var health := START_HEALTH
var is_game_over := false
var rng := RandomNumberGenerator.new()


func reset() -> void:
	score = 0
	coins_collected = 0
	health = START_HEALTH
	is_game_over = false
	if rng_seed != 0:
		rng.seed = rng_seed
	else:
		rng.randomize()
	changed.emit()


func collect_coin(value: int) -> void:
	score += value
	coins_collected += 1
	changed.emit()


func damage_player(amount: int) -> void:
	if is_game_over or amount <= 0:
		return
	health = maxi(health - amount, 0)
	if health == 0:
		is_game_over = true
		game_over.emit()
	changed.emit()


func snapshot() -> Dictionary:
	var state := {
		"score": score,
		"coins_collected": coins_collected,
		"coins_left": get_tree().get_nodes_in_group("coins").size(),
		"enemies": get_tree().get_nodes_in_group("enemies").size(),
		"health": health,
		"is_game_over": is_game_over,
	}
	var player := get_tree().get_first_node_in_group("player") as Node2D
	if player:
		state["player_position"] = [
			roundi(player.global_position.x), roundi(player.global_position.y)
		]
	var scene := get_tree().current_scene
	state["scene"] = scene.scene_file_path if scene else ""
	return state
```

Notes:

- `damage_player` ignores bad input and anything after game over. Validation lives in the method,
  which is why nothing else writes `health` directly.
- `game_over` is a separate signal because listeners want the *event*. `changed` still fires, so
  the HUD redraws.
- `snapshot()` reports counts by group (`coins_left`, `enemies`), so tests and the playtester don't
  each count differently.

---

## A pickup

An `Area2D` in a group, which notices the player with `body_entered`, tells `GameState`, and
frees itself.

```ini
[gd_scene format=3]

[ext_resource type="Script" path="res://scripts/coin.gd" id="1_coin"]

[sub_resource type="CircleShape2D" id="CircleShape2D_coin"]
radius = 10.0

[node name="Coin" type="Area2D" groups=["coins"]]
script = ExtResource("1_coin")

[node name="Body" type="Polygon2D" parent="."]
color = Color(1, 0.84, 0.2, 1)
polygon = PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)

[node name="Collision" type="CollisionShape2D" parent="."]
shape = SubResource("CircleShape2D_coin")
```

```gdscript
extends Area2D
## A coin. Walking the player into it adds VALUE to the score, once, and removes the coin.

const VALUE := 10

var _taken := false


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if _taken or not body.is_in_group("player"):
		return
	_taken = true  # body_entered can fire again before queue_free() lands
	GameState.collect_coin(VALUE)
	queue_free()
```

- **`_taken` guards against double counting.** `queue_free()` only takes effect at the end of the
  frame, so another `body_entered` can arrive first.
- `queue_free()` is safe inside a physics callback. `add_child()` isn't: use
  `add_child.call_deferred(...)` there.
- The player is found by **group**, not name or type.

---

## Spawning at clear random spots

`main.gd` spawns the coins, so their number and placement live in one place. The random spot avoids
the walls, the player and other coins, and it draws from `GameState.rng`, so a seed reproduces the
layout.

```gdscript
extends Node2D
## Root of the game scene. Owns the arena and the player, spawns the coins, handles restart.

const CoinScene := preload("res://scenes/coin.tscn")
const COIN_COUNT := 5
## The walkable area inside the 32 px walls.
const ARENA := Rect2(32, 32, 896, 476)
const WALL_MARGIN := 24.0
const MIN_GAP := 64.0

@onready var _player: Node2D = $Player


func _ready() -> void:
	GameState.reset()
	for i in COIN_COUNT:
		var coin := CoinScene.instantiate() as Node2D
		coin.position = _free_spot()
		add_child(coin)


func _process(_delta: float) -> void:
	if GameState.is_game_over and Input.is_action_just_pressed("restart"):
		get_tree().reload_current_scene()


## A random point inside the arena, clear of the walls, the player and other coins.
func _free_spot() -> Vector2:
	var area := ARENA.grow(-WALL_MARGIN)
	var spot := area.get_center()
	for attempt in 100:
		spot = Vector2(
			GameState.rng.randf_range(area.position.x, area.end.x),
			GameState.rng.randf_range(area.position.y, area.end.y)
		)
		if _is_clear(spot):
			return spot
	push_warning("no clear spot after 100 tries; placing at %s" % spot)
	return spot


func _is_clear(spot: Vector2) -> bool:
	if spot.distance_to(_player.position) < MIN_GAP * 1.5:
		return false
	for other: Node2D in get_tree().get_nodes_in_group("coins"):
		if spot.distance_to(other.position) < MIN_GAP:
			return false
	return true
```

- `ARENA` is the inside of the 32 px walls in `main.tscn`. Coins keep `WALL_MARGIN` away from it.
- **Bounded retries** (`for attempt in 100`) instead of `while true`: a crowded arena must not hang
  the game or a test. It warns instead.
- Coins are added one by one, so each new spot checks against the coins already placed.

---

## A HUD that follows GameState

A `CanvasLayer` with labels, found by unique name, redrawn on `GameState.changed`. It never polls.

```ini
[gd_scene format=3]

[ext_resource type="Script" path="res://scripts/hud.gd" id="1_hud"]

[node name="HUD" type="CanvasLayer"]
script = ExtResource("1_hud")

[node name="Score" type="Label" parent="."]
unique_name_in_owner = true
offset_left = 44.0
offset_top = 40.0
offset_right = 244.0
offset_bottom = 66.0
mouse_filter = 2
text = "Score: 0"

[node name="Health" type="Label" parent="."]
unique_name_in_owner = true
offset_left = 44.0
offset_top = 66.0
offset_right = 244.0
offset_bottom = 92.0
mouse_filter = 2
text = "Health: 3"
```

```gdscript
extends CanvasLayer
## Shows the score and health. Redraws whenever GameState changes; never polls.

@onready var _score: Label = %Score
@onready var _health: Label = %Health


func _ready() -> void:
	GameState.changed.connect(_refresh)
	_refresh()


func _refresh() -> void:
	_score.text = "Score: %d" % GameState.score
	_health.text = "Health: %d" % GameState.health
```

- `%Score` works anywhere inside `hud.tscn`, however the labels are nested later.
- `_refresh()` runs once in `_ready()` too, so the HUD is right before anything changes.
- `mouse_filter = 2` (ignore), so labels never swallow clicks meant for the game.

---

## An enemy that chases and hurts

A `CharacterBody2D` that moves toward the player, with a slightly larger `Area2D` hitbox. It
damages the player at most once per cooldown, counted in physics frames so tests are exact.

```ini
[gd_scene format=3]

[ext_resource type="Script" path="res://scripts/enemy.gd" id="1_enemy"]

[sub_resource type="CircleShape2D" id="CircleShape2D_body"]
radius = 14.0

[sub_resource type="CircleShape2D" id="CircleShape2D_hitbox"]
radius = 22.0

[node name="Enemy" type="CharacterBody2D" groups=["enemies"]]
motion_mode = 1
script = ExtResource("1_enemy")

[node name="Body" type="Polygon2D" parent="."]
color = Color(0.9, 0.3, 0.3, 1)
polygon = PackedVector2Array(0, -14, 14, 12, -14, 12)

[node name="Collision" type="CollisionShape2D" parent="."]
shape = SubResource("CircleShape2D_body")

[node name="Hitbox" type="Area2D" parent="."]

[node name="Shape" type="CollisionShape2D" parent="Hitbox"]
shape = SubResource("CircleShape2D_hitbox")
```

```gdscript
extends CharacterBody2D
## An enemy. Walks toward the player and hurts them on contact, at most once per cooldown.

const HIT_COOLDOWN_FRAMES := 60

@export var speed := 90.0

var _cooldown := 0

@onready var _hitbox: Area2D = $Hitbox


func _physics_process(_delta: float) -> void:
	var player := get_tree().get_first_node_in_group("player") as Node2D
	if player == null or GameState.is_game_over:
		velocity = Vector2.ZERO
		return
	velocity = global_position.direction_to(player.global_position) * speed
	move_and_slide()
	if _cooldown > 0:
		_cooldown -= 1
	elif _touching_player():
		GameState.damage_player(1)
		_cooldown = HIT_COOLDOWN_FRAMES


func _touching_player() -> bool:
	for body in _hitbox.get_overlapping_bodies():
		if body.is_in_group("player"):
			return true
	return false
```

- The body's collision stops the enemy at the player. The bigger `Hitbox` is what detects
  "touching".
- `get_overlapping_bodies()` is polled each physics frame instead of `body_entered`, because
  damage must repeat while contact lasts.
- `motion_mode = 1` (floating) is the top-down mode. The default, grounded, assumes gravity and
  floors.

---

## Spawning over time

A frame counter in `_physics_process`, with a cap on how many are alive.

```gdscript
extends Node2D
## Spawns an enemy at a random arena corner every SPAWN_EVERY_FRAMES, up to MAX_ALIVE at once.

const EnemyScene := preload("res://scenes/enemy.tscn")
const SPAWN_EVERY_FRAMES := 180
const MAX_ALIVE := 3
const CORNERS: Array[Vector2] = [
	Vector2(72, 72), Vector2(888, 72), Vector2(72, 468), Vector2(888, 468)
]

var _frames := 0


func _physics_process(_delta: float) -> void:
	if GameState.is_game_over:
		return
	_frames += 1
	if _frames < SPAWN_EVERY_FRAMES:
		return
	_frames = 0
	if get_tree().get_nodes_in_group("enemies").size() >= MAX_ALIVE:
		return
	var enemy := EnemyScene.instantiate() as Node2D
	enemy.position = CORNERS[GameState.rng.randi_range(0, CORNERS.size() - 1)]
	add_child.call_deferred(enemy)  # we're inside a physics step
```

- **`add_child.call_deferred`**, because adding a physics body during a physics step can error.
- A `Timer` node works too under `--fixed-fps`, but a counter is easier to test exactly ("none at
  170 frames, one at 190").
- `const CORNERS: Array[Vector2] = [...]` is a typed constant array.

---

## Game over and restart

`GameState.is_game_over` is the flag. Things that should stop check it (the spawner, the enemy).
`main.gd` restarts on the `restart` action with `reload_current_scene()`, and `main._ready()`
calls `GameState.reset()` on the new scene. The action is added to `project.godot` `[input]`:

```ini
restart={
"deadzone": 0.2,
"events": [Object(InputEventKey,"physical_keycode":82)]
}
```

The restart logic is in `main.gd` above (`_process`). Testing a reload needs care, because the
reloaded scene isn't freed by the harness: see
[TESTING_STANDARDS.md §5](TESTING_STANDARDS.md#5-isolation-what-the-harness-resets-and-what-it-doesnt).

---

## Pure rules

Formulas with no nodes, as `static func`s on a `class_name` script.

```gdscript
class_name Rules
extends RefCounted
## Pure game rules: numbers in, numbers out. No nodes or tree, so tests call them directly.


## Damage after armour; a hit always does at least 1.
static func damage_after_armor(damage: int, armor: int) -> int:
	return maxi(damage - armor, 1)


## Bonus for collecting coins in a streak, capped at 5 coins.
static func streak_bonus(streak: int) -> int:
	return clampi(streak, 0, 5) * 2
```

`extends RefCounted` because it's never instanced, and it needs no scene. Tests call
`Rules.damage_after_armor(5, 2)` directly.

---

## Wiring into main.tscn

The additions to the existing `main.tscn`: two `ext_resource` lines after the existing ones, and
two nodes at the end. The coins aren't in the file; `main.gd` spawns them.

```ini
[ext_resource type="Script" path="res://scripts/main.gd" id="1_main"]
[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="2_player"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="3_hud"]
[ext_resource type="Script" path="res://scripts/enemy_spawner.gd" id="4_spawner"]

...existing sub_resources and nodes, unchanged...

[node name="EnemySpawner" type="Node2D" parent="."]
script = ExtResource("4_spawner")

[node name="HUD" parent="." instance=ExtResource("3_hud")]
```

The HUD goes **last**, so it draws over everything (it's a `CanvasLayer`, so it would anyway; keeping
UI last is still the convention).

---

## Reading state from the playtester

The playtester agent reads the running game with the godot MCP's `godot_run_script`. The script
must extend `RefCounted` and define `execute(scene_tree)`; whatever it returns comes back as JSON:

```gdscript
extends RefCounted


func execute(scene_tree: SceneTree) -> Variant:
	return scene_tree.root.get_node("GameState").snapshot()
```

Everything above shows up there: `{"score": 10, "coins_left": 4, "health": 3, ...}`. If a
criterion can't be read this way, the state is missing from `snapshot()`. Fix the game, not the
playtest. During input, `godot_simulate_input` with `"watch": ["/root/GameState:score"]` samples a
value after every step. See the `godot-playtest` skill.

---

## Not here, on purpose

- **Object pools.** Godot frees and instances small scenes cheaply. Pool only after a profile
  shows a problem.
- **Service layers, event buses, manager autoloads.** One `GameState` plus scene scripts is enough
  at this size ([ARCHITECTURE.md §9](ARCHITECTURE.md#9-anti-patterns)).
- **TileMapLayer levels.** Tile data is binary in the `.tscn`; generate it from a script or the
  editor rather than by hand ([SCENES_AND_TSCN.md §4](SCENES_AND_TSCN.md#4-editing-a-scene-by-hand)).
