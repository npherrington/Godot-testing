extends Node
## Autoload "GameState": the one place game state lives.
## Tests and playtests read the game through snapshot(), so every feature
## that adds state (score, health, level, timers) adds it here and to snapshot().

signal changed


func reset() -> void:
	changed.emit()


func snapshot() -> Dictionary:
	var state := {}
	var player := get_tree().get_first_node_in_group("player") as Node2D
	if player:
		state["player_position"] = [
			roundi(player.global_position.x), roundi(player.global_position.y)
		]
	var scene := get_tree().current_scene
	state["scene"] = scene.scene_file_path if scene else ""
	return state
