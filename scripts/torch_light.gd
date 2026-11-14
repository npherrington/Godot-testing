extends PointLight2D
## A flickering torch light: energy and reach wobble a little, never in step with other torches.

@export var flicker := 0.12

var _base_energy := 1.0
var _base_scale := 1.0
var _phase := 0.0
var _time := 0.0


func _ready() -> void:
	_base_energy = energy
	_base_scale = texture_scale
	_phase = randf() * TAU


func _process(delta: float) -> void:
	_time += delta
	var wobble := sin(_time * 7.3 + _phase) * 0.6 + sin(_time * 13.1 + _phase * 2.0) * 0.4
	energy = _base_energy * (1.0 + flicker * wobble)
	texture_scale = _base_scale * (1.0 + flicker * 0.25 * wobble)


## The light's reach in world pixels at rest (the texture's radius times its scale).
func radius() -> float:
	return texture.get_width() / 2.0 * _base_scale if texture else 0.0
