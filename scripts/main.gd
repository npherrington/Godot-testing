extends Node2D
## Root of the game scene. Owns the arena and the player.


func _ready() -> void:
	GameState.reset()
