class_name Player
extends Node2D
## The adventurer. Steps one grid cell at a time in 8 directions with the move_* actions.

## Frames after the first press in which a second key turns the step into a diagonal.
const DIAGONAL_GRACE := 2
## Frames between steps while a direction is held.
const REPEAT_FRAMES := 8
const STEP_SECONDS := 0.12
## Frames a key pressed while the player cannot act (mid-step, enemy turn) is remembered.
const BUFFER_FRAMES := 12
const FRAMES_PATH := "res://assets/sprites/player/char_player_%s.tres"
const SPRITE_OFFSET := Vector2(0, -22)
const DIAGONAL_ACTIONS: Dictionary[String, Vector2i] = {
	"move_up_left": Vector2i(-1, -1),
	"move_up_right": Vector2i(1, -1),
	"move_down_left": Vector2i(-1, 1),
	"move_down_right": Vector2i(1, 1),
}

var cell := Grid.START
var facing := Vector2i.DOWN

var _held := false
var _grace := 0
var _pending := Vector2i.ZERO
var _cooldown := 0
var _stepping := false
var _was_down: Dictionary[String, bool] = {}
var _buffered := ""
var _buffer_left := 0

@onready var _sprite: AnimatedSprite2D = $Sprite
@onready var _fallback: Polygon2D = $Fallback


func _ready() -> void:
	_load_frames("normal")
	place(cell)
	_sprite.animation_finished.connect(_on_animation_finished)


func _physics_process(_delta: float) -> void:
	for action: String in ["attack", "defend", "interact"]:
		# Keys pressed while dead or in a menu belong to the HUD, not to the next turn.
		if _just_pressed(action) and not GameState.game_over and GameState.menu == "":
			_buffered = action
			_buffer_left = BUFFER_FRAMES
	if _buffered != "":
		_buffer_left -= 1
		if can_act():
			_do_action(_buffered)
			_buffered = ""
		elif _buffer_left <= 0 or GameState.menu != "":
			_buffered = ""
	var dir := read_direction()
	if _grace > 0:
		if _steps_in(dir) >= _steps_in(_pending):
			_pending = dir
		_grace -= 1
		if _grace == 0:
			_try_step(_pending)
			_cooldown = REPEAT_FRAMES
		return
	if dir == Vector2i.ZERO:
		_held = false
		_cooldown = 0
		return
	_cooldown = maxi(_cooldown - 1, 0)
	if not can_act():
		return
	if not _held:
		_held = true
		_pending = dir
		_grace = DIAGONAL_GRACE
		return
	if _cooldown > 0:
		return
	_try_step(dir)
	_cooldown = REPEAT_FRAMES


## Put the player on a cell at once, with no animation.
func place(new_cell: Vector2i) -> void:
	cell = new_cell
	position = Grid.to_world(cell)
	GameState.set_player_cell(cell, facing)


func can_act() -> bool:
	return not _stepping and GameState.can_player_act()


## The direction the move actions point to, as a step of -1, 0 or 1 on each axis.
func read_direction() -> Vector2i:
	for action: String in DIAGONAL_ACTIONS:
		if Input.is_action_pressed(action):
			return DIAGONAL_ACTIONS[action]
	return Vector2i(
		int(Input.is_action_pressed("move_right")) - int(Input.is_action_pressed("move_left")),
		int(Input.is_action_pressed("move_down")) - int(Input.is_action_pressed("move_up"))
	)


func play_animation(kind: String) -> void:
	var animation := "%s_%s" % [kind, Grid.name_8(facing)]
	if _sprite.sprite_frames and _sprite.sprite_frames.has_animation(animation):
		_sprite.play(animation)


## Walk one cell along the grid (used by TurnManager to resolve a move).
func step_to(target: Vector2i) -> void:
	facing = target - cell if target != cell else facing
	cell = target
	GameState.set_player_cell(cell, facing)
	_stepping = true
	play_animation("walk")
	var tween := create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
	tween.tween_property(self, "position", Grid.to_world(target), STEP_SECONDS)
	tween.finished.connect(_on_step_finished)


func play_attack(target: Vector2i) -> void:
	if target != cell:
		facing = (target - cell).sign()
		GameState.set_player_cell(cell, facing)
	play_animation("attack")


func flash_hurt() -> void:
	modulate = Color(1, 0.35, 0.35)
	var tween := create_tween()
	tween.tween_property(self, "modulate", Color.WHITE, 0.25)


func _try_step(dir: Vector2i) -> void:
	if dir == Vector2i.ZERO or not can_act():
		return
	facing = dir
	var turns := _turns()
	var target := cell + dir
	var enemy := turns.enemy_at(target) if turns else null
	if enemy:
		_take_turn(_attack_action(enemy))
		return
	var dungeon := get_tree().get_first_node_in_group("dungeon") as Dungeon
	if dungeon and not dungeon.can_step(cell, dir):
		play_animation("idle")
		GameState.set_player_cell(cell, facing)
		return
	_take_turn({"type": "move", "actor": self, "to": target})


## Attack the enemy in the facing cell, or the only adjacent one. No target, no turn spent.
func _attack_nearby() -> void:
	var turns := _turns()
	if turns == null:
		return
	var target := turns.enemy_at(cell + facing)
	if target == null:
		var adjacent: Array[Enemy] = []
		for dir in Grid.DIRS_8:
			var enemy := turns.enemy_at(cell + dir)
			if enemy:
				adjacent.append(enemy)
		if adjacent.size() == 1:
			target = adjacent[0]
	if target == null:
		GameState.log_message("Nothing in reach to attack.")
		return
	_take_turn(_attack_action(target))


func _do_action(action: String) -> void:
	match action:
		"attack":
			_attack_nearby()
		"defend":
			_take_turn({"type": "defend", "actor": self})
			play_animation("defend")
		"interact":
			_interact()


## Pick up the item underfoot or next to the player. Nothing in reach, no turn spent.
func _interact() -> void:
	var turns := _turns()
	var item := turns.item_near(cell) if turns else null
	if item == null:
		GameState.log_message("Nothing here to pick up.")
		return
	_take_turn({"type": "pickup", "actor": self, "item": item})


func _attack_action(enemy: Enemy) -> Dictionary:
	return {"type": "attack", "actor": self, "target": enemy, "damage": GameState.get_attack()}


func _take_turn(action: Dictionary) -> void:
	var turns := _turns()
	if turns:
		turns.player_action(action)
	elif action.get("type") == "move":
		var to: Vector2i = action.get("to", cell)
		step_to(to)


func _turns() -> TurnManager:
	return get_tree().get_first_node_in_group("turn_manager") as TurnManager


func _just_pressed(action: String) -> bool:
	var down := Input.is_action_pressed(action)
	var was: bool = _was_down.get(action, false)
	_was_down[action] = down
	return down and not was


func _on_step_finished() -> void:
	_stepping = false
	play_animation("idle")


func _on_animation_finished() -> void:
	if not str(_sprite.animation).begins_with("idle") and not _stepping:
		play_animation("idle")


func _load_frames(state: String) -> void:
	var path := FRAMES_PATH % state
	if not ResourceLoader.exists(path):
		_sprite.visible = false
		_fallback.visible = true
		return
	var animation := _sprite.animation
	_sprite.sprite_frames = load(path) as SpriteFrames
	_sprite.offset = SPRITE_OFFSET
	_sprite.visible = true
	_fallback.visible = false
	if _sprite.sprite_frames.has_animation(animation):
		_sprite.play(animation)
	else:
		play_animation("idle")


func _steps_in(dir: Vector2i) -> int:
	return absi(dir.x) + absi(dir.y)
