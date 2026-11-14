class_name Trap
extends Node2D
## A trap on a floor cell. Fires when the player steps next to it (or onto it), then needs
## COOLDOWN_TURNS turns to re-arm.

const COOLDOWN_TURNS := 10
const DAMAGE_MIN := 10
const DAMAGE_MAX := 15
const ART_PATH := "res://assets/sprites/environment/trap_%s_%s.png"
const KINDS: Dictionary[String, Dictionary] = {
	"pressure_plate":
	{
		"name": "Pressure plate",
		"armed": "up",
		"fired": "down",
		"tiles": [Vector2(0, -8)],
		"color": Color(0.85, 0.75, 0.55),
	},
	"spike_wall":
	{
		"name": "Spike wall",
		"armed": "retracted",
		"fired": "extended",
		"tiles": [Vector2(-8, -16), Vector2(8, -16), Vector2(-8, 0), Vector2(8, 0)],
		"color": Color(0.85, 0.85, 0.95),
	},
}

var kind := "pressure_plate"
var cell := Vector2i.ZERO
## Turns until the trap is armed again; 0 means armed.
var cooldown := 0

var _sprites: Array[Sprite2D] = []

@onready var _art: Node2D = $Art
@onready var _burst: CPUParticles2D = $Burst


func _ready() -> void:
	position = Grid.to_world(cell)
	var tiles: Array = KINDS[kind]["tiles"]
	for offset: Vector2 in tiles:
		var sprite := Sprite2D.new()
		sprite.position = offset
		_art.add_child(sprite)
		_sprites.append(sprite)
	_burst.color = KINDS[kind]["color"]
	_update_art()


func setup(at: Vector2i, new_kind: String, turns_left := 0) -> void:
	cell = at
	kind = new_kind if KINDS.has(new_kind) else "pressure_plate"
	cooldown = turns_left


func is_armed() -> bool:
	return cooldown <= 0


func display_name() -> String:
	var text: String = KINDS[kind]["name"]
	return text


## Fire at the player: returns the damage roll. The caller applies it.
func fire() -> int:
	cooldown = COOLDOWN_TURNS
	_update_art()
	_burst.restart()
	_burst.emitting = true
	modulate = Color(2, 2, 2)
	var tween := create_tween()
	tween.tween_property(self, "modulate", Color.WHITE, 0.3)
	return GameState.rng.randi_range(DAMAGE_MIN, DAMAGE_MAX)


## One turn passes; re-arms when the cooldown runs out.
func tick() -> void:
	if cooldown <= 0:
		return
	cooldown -= 1
	if cooldown == 0:
		_update_art()


func is_showing_fired() -> bool:
	return not _sprites.is_empty() and _sprites[0].texture == _texture("fired")


func to_dict() -> Dictionary:
	return {"kind": kind, "cell": Grid.to_array(cell), "cooldown": cooldown}


func _update_art() -> void:
	var texture := _texture("armed" if is_armed() else "fired")
	for sprite in _sprites:
		sprite.texture = texture


func _texture(state: String) -> Texture2D:
	var file: String = KINDS[kind][state]
	var path := ART_PATH % [kind, file]
	if ResourceLoader.exists(path):
		return load(path) as Texture2D
	return null
