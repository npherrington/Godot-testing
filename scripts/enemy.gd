class_name Enemy
extends Node2D
## A monster on the grid. Its type (MonsterDatabase) sets its stats and how it moves. It sleeps
## until it notices the player, then decide() returns its actions for TurnManager to resolve.

const SCENE_PATH := "res://scenes/enemy.tscn"
const AGGRO_RANGE := 5
const AMBUSH_RANGE := 3
const STEP_SECONDS := 0.12
const HEALTH_BAR_WIDTH := 24.0
const SPRITE_OFFSET := Vector2(0, -22)
const FX_HEIGHT := Vector2(0, -20)

@export var type_id := "skeleton_warrior"
@export var display_name := "Skeleton"
@export var max_health := 20
@export var damage_min := 5
@export var damage_max := 10
@export var behavior := "chase"

var cell := Vector2i.ZERO
var health := 20
var facing := Vector2i.DOWN
var awake := false
## Status name -> turns left, as for the player.
var statuses: Dictionary[String, int] = {}

var _stats: Dictionary = {}
var _health_set := false
var _dead := false
var _has_split := false
## Turns this enemy has acted since it woke; paces slow movers and special attacks.
var _turns_awake := 0
var _move_tween: Tween

@onready var _sprite: AnimatedSprite2D = $Sprite
@onready var _fallback: Polygon2D = $Fallback


func _ready() -> void:
	if _stats.is_empty() and MonsterDatabase.has_type(type_id):
		_stats = MonsterDatabase.get_stats(type_id)
	if not _health_set:
		health = max_health
	_load_frames()
	position = Grid.to_world(cell)
	play_animation("idle")
	_sprite.animation_finished.connect(_on_animation_finished)


func _draw() -> void:
	if _dead or health >= max_health:
		return
	var top := Vector2(-HEALTH_BAR_WIDTH / 2.0, SPRITE_OFFSET.y * 2.0 - 8.0)
	draw_rect(Rect2(top, Vector2(HEALTH_BAR_WIDTH, 3)), Color(0.1, 0.05, 0.05, 0.9))
	var fill := HEALTH_BAR_WIDTH * float(health) / float(max_health)
	draw_rect(Rect2(top, Vector2(fill, 3)), Color(0.85, 0.2, 0.2, 1))


## Choose where the enemy stands and, optionally, its type, before it enters the tree.
func setup(at: Vector2i, new_type := "") -> void:
	cell = at
	if new_type == "" or not MonsterDatabase.has_type(new_type):
		return
	type_id = new_type
	_stats = MonsterDatabase.get_stats(new_type)
	display_name = _stats["name"]
	max_health = _stats["health"]
	set_health(max_health)
	var damage: Array = _stats["damage"]
	damage_min = damage[0]
	damage_max = damage[1]
	behavior = _stats["behavior"]


## Set health before the enemy enters the tree (a loaded game keeps hurt enemies hurt).
func set_health(value: int) -> void:
	health = clampi(value, 1, max_health)
	_health_set = true


func is_alive() -> bool:
	return not _dead


func has_status(status: String) -> bool:
	var turns: int = statuses.get(status, 0)
	return turns > 0


func apply_status(status: String, turns: int) -> void:
	var current: int = statuses.get(status, 0)
	statuses[status] = maxi(current, turns)


func moves_through_walls() -> bool:
	return behavior == "phase"


## The actions this enemy takes this turn, for TurnManager to resolve in order.
func decide(turns: TurnManager) -> Array[Dictionary]:
	var target := GameState.player_cell
	var distance := Grid.distance(cell, target)
	if not awake:
		if not _notices(target, distance):
			return []
		awake = true
	_turns_awake += 1
	return _act(turns, target, distance)


func attack_action() -> Dictionary:
	var action := {
		"type": "attack",
		"actor": self,
		"target": get_tree().get_first_node_in_group("player"),
		"damage": GameState.rng.randi_range(damage_min, damage_max),
	}
	if _stats.has("status"):
		action["status"] = _stats["status"]
		action["status_turns"] = _stats.get("status_turns", 1)
	return action


func ranged_action() -> Dictionary:
	var ranged: Dictionary = _stats.get("ranged", {})
	var damage: Array = ranged.get("damage", [damage_min, damage_max])
	var damage_low: int = damage[0]
	var damage_high: int = damage[1]
	var action := {
		"type": "attack",
		"actor": self,
		"target": get_tree().get_first_node_in_group("player"),
		"damage": GameState.rng.randi_range(damage_low, damage_high),
		"verb": ranged.get("verb", "shoots"),
		"fx": ranged.get("fx", ""),
	}
	if ranged.has("status"):
		action["status"] = ranged["status"]
		action["status_turns"] = ranged.get("status_turns", 1)
	return action


func move_to(new_cell: Vector2i) -> void:
	facing = new_cell - cell
	cell = new_cell
	play_animation("walk")
	if _move_tween and _move_tween.is_valid():
		_move_tween.kill()
	_move_tween = create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
	_move_tween.tween_property(self, "position", Grid.to_world(cell), STEP_SECONDS)
	_move_tween.finished.connect(_on_step_finished)


## Lose health; wakes the enemy. A slime splits the first time it is hurt. Returns the damage.
func take_damage(amount: int) -> int:
	if _dead:
		return 0
	awake = true
	var dealt := mini(amount, health)
	health -= dealt
	queue_redraw()
	_flash(Color(1, 0.4, 0.4))
	if health <= 0:
		_die()
	elif _stats.has("splits_into") and not _has_split:
		_split()
	return dealt


func tick_statuses() -> void:
	for status: String in statuses.keys():
		statuses[status] -= 1
		if statuses[status] <= 0:
			statuses.erase(status)


func play_attack(target: Vector2i, fx := "") -> void:
	facing = target - cell
	play_animation("attack")
	if fx != "":
		_launch_fx(fx, target)


func play_animation(kind: String) -> void:
	var animation := "%s_%s" % [kind, Grid.name_4(facing)]
	if _sprite.sprite_frames and _sprite.sprite_frames.has_animation(animation):
		_sprite.play(animation)


func to_dict() -> Dictionary:
	return {
		"type": type_id,
		"cell": Grid.to_array(cell),
		"health": health,
		"max_health": max_health,
		"awake": awake,
		"statuses": statuses.duplicate(),
		"turns_awake": _turns_awake,
		"has_split": _has_split,
	}


## Set up from a saved to_dict() entry, before entering the tree.
func restore(data: Dictionary) -> void:
	var saved_type: String = data.get("type", type_id)
	setup(Grid.from_array(data.get("cell")), saved_type)
	var saved_health: float = data.get("health", max_health)
	set_health(roundi(saved_health))
	awake = SaveSystem.read_bool(data, "awake")
	_has_split = SaveSystem.read_bool(data, "has_split")
	var turns: float = data.get("turns_awake", 0)
	_turns_awake = roundi(turns)
	var saved_statuses: Dictionary = data.get("statuses", {})
	for status: String in saved_statuses:
		var left: float = saved_statuses[status]
		statuses[status] = roundi(left)


## This turn's actions, by the type's behavior.
func _act(turns: TurnManager, target: Vector2i, distance: int) -> Array[Dictionary]:
	var actions: Array[Dictionary] = []
	match behavior:
		"phase":
			actions = _chase(turns, target, distance, true)
		"ranged":
			actions = _shoot_from_range(turns, target, distance, 2)
		"hop":
			actions = _chase(turns, target, distance, false, true)
		"lumber":
			if _turns_awake % 2 == 1:
				actions = _chase(turns, target, distance)
		"ambush":
			if _turns_awake % _ranged_value("every", 4) == 1 and _can_shoot(target, distance):
				actions = [ranged_action()]
			else:
				actions = _chase(turns, target, distance)
		"shamble":
			if distance == 1 or _turns_awake % 2 == 1:
				actions = _chase(turns, target, distance)
		"kite":
			actions = _shoot_from_range(turns, target, distance, 3)
		"sprint":
			actions = _sprint(turns, target, distance)
		"erratic":
			actions = _erratic(turns, target, distance)
		_:
			actions = _chase(turns, target, distance)
	return actions


func _notices(target: Vector2i, distance: int) -> bool:
	if behavior == "ambush":
		return distance <= AMBUSH_RANGE
	if distance > AGGRO_RANGE:
		return false
	var dungeon := get_tree().get_first_node_in_group("dungeon") as Dungeon
	return behavior == "phase" or dungeon == null or dungeon.has_line_of_sight(cell, target)


func _chase(
	turns: TurnManager, target: Vector2i, distance: int, through_walls := false, four_way := false
) -> Array[Dictionary]:
	if distance == 1:
		return [attack_action()]
	return _move(turns.step_toward(cell, target, through_walls, four_way))


## Ranged types stay at least min_distance away and shoot when the player is in range and sight.
func _shoot_from_range(
	turns: TurnManager, target: Vector2i, distance: int, min_distance: int
) -> Array[Dictionary]:
	if distance < min_distance:
		var away := turns.step_away(cell, target)
		if away != cell:
			return _move(away)
		if distance == 1:
			return [attack_action()]
	if _can_shoot(target, distance):
		return [ranged_action()]
	return _move(turns.step_toward(cell, target))


func _sprint(turns: TurnManager, target: Vector2i, distance: int) -> Array[Dictionary]:
	if distance == 1:
		return [attack_action()]
	var first := turns.step_toward(cell, target)
	if first == cell:
		return []
	var actions := _move(first)
	if Grid.distance(first, target) > 1:
		var second := turns.step_toward(first, target)
		if second != first:
			actions.append({"type": "move", "actor": self, "to": second})
	return actions


func _erratic(turns: TurnManager, target: Vector2i, distance: int) -> Array[Dictionary]:
	if distance == 1:
		return [attack_action()]
	if _can_shoot(target, distance) and GameState.rng.randf() < 0.5:
		return [ranged_action()]
	if GameState.rng.randf() < 0.5:
		var dir := Grid.DIRS_8[GameState.rng.randi_range(0, Grid.DIRS_8.size() - 1)]
		if turns.is_free(cell + dir) and turns.can_step(cell, dir):
			return _move(cell + dir)
	return _move(turns.step_toward(cell, target))


func _can_shoot(target: Vector2i, distance: int) -> bool:
	if not _stats.has("ranged") or distance < 2 or distance > _ranged_value("range", 0):
		return false
	var dungeon := get_tree().get_first_node_in_group("dungeon") as Dungeon
	return dungeon == null or dungeon.has_line_of_sight(cell, target)


func _ranged_value(key: String, default: int) -> int:
	var ranged: Dictionary = _stats.get("ranged", {})
	var value: int = ranged.get(key, default)
	return value


func _move(to: Vector2i) -> Array[Dictionary]:
	if to == cell:
		return []
	return [{"type": "move", "actor": self, "to": to}]


func _split() -> void:
	_has_split = true
	var turns := get_tree().get_first_node_in_group("turn_manager") as TurnManager
	if turns == null:
		return
	for dir in Grid.DIRS_8:
		var spot := cell + dir
		if turns.is_free(spot) and turns.can_step(cell, dir):
			var spawn := (load(SCENE_PATH) as PackedScene).instantiate() as Enemy
			var child_type: String = _stats["splits_into"]
			spawn.setup(spot, child_type)
			spawn.awake = true
			spawn.position = position
			get_parent().add_child(spawn)
			spawn.move_to(spot)
			GameState.log_message("%s splits in two!" % display_name)
			return


func _launch_fx(effect: String, target: Vector2i) -> void:
	var path := MonsterDatabase.fx_path(type_id, effect)
	if not ResourceLoader.exists(path):
		return
	var fx := AnimatedSprite2D.new()
	fx.sprite_frames = load(path) as SpriteFrames
	fx.position = position + FX_HEIGHT
	fx.z_index = 5
	var end := Grid.to_world(target) + FX_HEIGHT
	fx.rotation = (end - fx.position).angle()
	get_parent().add_child(fx)
	fx.play("default")
	var tween := fx.create_tween()
	tween.tween_property(fx, "position", end, 0.06 * Grid.distance(cell, target))
	tween.tween_callback(fx.queue_free)


func _die() -> void:
	_dead = true
	remove_from_group("enemies")
	queue_redraw()
	if _sprite.visible and _sprite.sprite_frames:
		var animation := "death_%s" % Grid.name_4(facing)
		if _sprite.sprite_frames.has_animation(animation):
			_sprite.play(animation)
			return
	var tween := create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.3)
	tween.finished.connect(queue_free)


func _flash(color: Color) -> void:
	modulate = color
	var tween := create_tween()
	tween.tween_property(self, "modulate", Color.WHITE, 0.25)


func _on_step_finished() -> void:
	if not _dead:
		play_animation("idle")


func _on_animation_finished() -> void:
	if _dead:
		queue_free()
	elif not str(_sprite.animation).begins_with("idle"):
		play_animation("idle")


func _load_frames() -> void:
	var path := MonsterDatabase.frames_path(type_id)
	if not ResourceLoader.exists(path):
		_sprite.visible = false
		_fallback.visible = true
		return
	_sprite.sprite_frames = load(path) as SpriteFrames
	_sprite.offset = SPRITE_OFFSET
	_sprite.visible = true
	_fallback.visible = false
	if behavior == "phase":
		_sprite.self_modulate.a = 0.8
