class_name SaveSystem
extends RefCounted
## Saving and loading: GameState.snapshot() as JSON on disk, and back. Loading restores
## GameState and emits GameState.loaded so main.gd rebuilds the world.

const VERSION := 1


## Write the game to a JSON file. Returns false when it cannot be written.
static func save_game(path: String) -> bool:
	var data := GameState.snapshot()
	data["version"] = VERSION
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(data, "\t"))
	file.close()
	return true


static func has_save(path: String) -> bool:
	return FileAccess.file_exists(path)


## Read a saved game back. It is the player's turn of the saved turn number afterwards.
## Returns false when there is no valid save at the path.
static func load_game(path: String) -> bool:
	if not FileAccess.file_exists(path):
		return false
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not parsed is Dictionary:
		return false
	var data: Dictionary = parsed
	if read_int(data, "version", 0) != VERSION:
		return false
	_apply(data)
	GameState.loaded.emit(data)
	GameState.changed.emit()
	return true


static func read_int(data: Dictionary, key: String, default: int) -> int:
	var value: Variant = data.get(key, default)
	if value is int or value is float:
		var number: float = value
		return roundi(number)
	return default


static func read_string(data: Dictionary, key: String) -> String:
	var value: Variant = data.get(key, "")
	if value is String:
		var text: String = value
		return text
	return ""


static func read_bool(data: Dictionary, key: String) -> bool:
	return data.get(key, false) == true


static func _apply(data: Dictionary) -> void:
	var state := GameState
	state.health = read_int(data, "health", state.MAX_HEALTH)
	state.max_health = read_int(data, "max_health", state.MAX_HEALTH)
	state.player_cell = Grid.from_array(data.get("player_cell"))
	state.player_facing = Grid.from_array(data.get("player_facing"))
	state.turn = read_int(data, "turn", 1)
	state.phase = "player"
	state.defending = false
	state.game_over = state.health <= 0
	state.actions_resolved = read_int(data, "actions_resolved", 0)
	state.traps_triggered = read_int(data, "traps_triggered", 0)
	state.equipped_weapon = read_string(data, "equipped_weapon")
	state.equipped_armor = read_string(data, "equipped_armor")
	state.checkpoint_reached = read_bool(data, "checkpoint_reached")
	state.menu = ""
	state.menu_index = 0
	state.inventory = _strings(data.get("inventory", []))
	state.combat_log = _strings(data.get("combat_log", []))
	state.statuses.clear()
	var saved_statuses: Dictionary = data.get("statuses", {})
	for status: String in saved_statuses:
		state.statuses[status] = read_int(saved_statuses, status, 0)
	state.explored.clear()
	var saved_explored: Array = data.get("explored", [])
	for pair: Variant in saved_explored:
		state.explored[Grid.from_array(pair)] = true
	state.visible_cells.clear()
	state.rng.state = read_string(data, "rng_state").to_int()


static func _strings(value: Variant) -> Array[String]:
	var result: Array[String] = []
	if value is Array:
		var entries: Array = value
		for entry: Variant in entries:
			if entry is String:
				var text: String = entry
				result.append(text)
	return result
