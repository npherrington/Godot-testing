extends Node2D
## A torch hung on a wall face: animated flame, flickering light and rising smoke.

var cell := Vector2i.ZERO

@onready var _flame: AnimatedSprite2D = $Flame
@onready var _smoke: AnimatedSprite2D = $Smoke


func _ready() -> void:
	position = Vector2(cell * Grid.CELL) + Vector2(Grid.CELL / 2.0, Grid.CELL / 2.0)
	_flame.play("default")
	_smoke.play("default")
	_flame.frame = randi() % 4
	_smoke.frame = randi() % 6


func setup(at: Vector2i) -> void:
	cell = at


func is_smoking() -> bool:
	return _smoke.visible and _smoke.is_playing()
