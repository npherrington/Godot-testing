class_name Checkpoint
extends Node2D
## A shrine tile: a rune ringed by candles. Stepping onto it saves the game; it glows gold once
## used.

const IDLE_RUNE := Color(0.37, 0.67, 0.86, 0.85)
const USED_RUNE := Color(0.98, 0.82, 0.3, 0.95)
const IDLE_LIGHT := Color(0.45, 0.65, 1.0)
const USED_LIGHT := Color(1.0, 0.8, 0.45)

var cell := Vector2i.ZERO
var used := false

@onready var _rune: Polygon2D = $Rune
@onready var _glow: PointLight2D = $Glow


func _ready() -> void:
	position = Grid.to_world(cell)
	for candle in $Candles.get_children():
		var sprite := candle as AnimatedSprite2D
		sprite.play("default")
		sprite.frame = randi() % 4
	_update_look()


func setup(at: Vector2i, was_used := false) -> void:
	cell = at
	used = was_used


## Mark it used (the caller saves the game).
func activate() -> void:
	used = true
	_update_look()


func to_dict() -> Dictionary:
	return {"cell": Grid.to_array(cell), "used": used}


func _update_look() -> void:
	_rune.color = USED_RUNE if used else IDLE_RUNE
	_glow.color = USED_LIGHT if used else IDLE_LIGHT
