extends Sprite2D
## A tiling mist layer that drifts slowly over the world.

@export var drift := Vector2(6, 2)

var _offset := Vector2.ZERO


func _process(delta: float) -> void:
	_offset += drift * delta
	region_rect.position = _offset
