extends Node
## Autoload "GameState": the one place game state lives.
## Tests and playtests read the game through snapshot(), so every feature
## that adds state (score, health, level, timers) adds it here and to snapshot().

signal changed
signal logged(message: String)
## A saved game was read back; main.gd rebuilds the world from the data.
signal loaded(data: Dictionary)

const MAX_HEALTH := 100
const BASE_ATTACK := 8
const BASE_DEFENSE := 0
const LOG_LIMIT := 50
const RNG_SEED := 20261113
const INVENTORY_SIZE := 24
## What the player carries at the start of a run.
const STARTING_ITEMS: Array[String] = ["health_potion", "health_potion"]
## How far the player's torch lights and the player can see, in cells.
const LIGHT_RADIUS := 6
const SAVE_PATH := "user://savegame.json"
const CHECKPOINT_PATH := "user://checkpoint.json"

var health := MAX_HEALTH
var max_health := MAX_HEALTH
var player_cell := Grid.START
var player_facing := Vector2i.DOWN
var turn := 1
## "player" while waiting for the player's action, "enemy" while the enemies act.
var phase := "player"
var defending := false
## Status name ("poison", "freeze") -> turns left.
var statuses: Dictionary[String, int] = {}
var combat_log: Array[String] = []
var actions_resolved := 0
var game_over := false
## Item ids carried, at most INVENTORY_SIZE. Equipped items stay in the inventory.
var inventory: Array[String] = []
var equipped_weapon := ""
var equipped_armor := ""
## The open menu: "" (none), "inventory" or "pause". Player actions wait while one is open.
var menu := ""
var menu_index := 0
var traps_triggered := 0
## Cells the player has seen at least once, and the cells in sight right now.
var explored: Dictionary[Vector2i, bool] = {}
var visible_cells: Dictionary[Vector2i, bool] = {}
## Where the pause menu saves and where checkpoints save. Reset to the defaults by reset();
## tests point them elsewhere so they never touch the player's saves.
var save_path := SAVE_PATH
var checkpoint_path := CHECKPOINT_PATH
## Whether a checkpoint was reached in this run (death then returns there).
var checkpoint_reached := false
## A line of feedback shown in the pause menu ("Game saved.").
var menu_message := ""
## Every random roll in play goes through this, so a run is repeatable from reset().
var rng := RandomNumberGenerator.new()


func reset() -> void:
	health = MAX_HEALTH
	max_health = MAX_HEALTH
	player_cell = Grid.START
	player_facing = Vector2i.DOWN
	turn = 1
	phase = "player"
	defending = false
	statuses.clear()
	combat_log.clear()
	actions_resolved = 0
	game_over = false
	inventory.assign(STARTING_ITEMS)
	equipped_weapon = ""
	equipped_armor = ""
	menu = ""
	menu_index = 0
	traps_triggered = 0
	explored.clear()
	visible_cells.clear()
	save_path = SAVE_PATH
	checkpoint_path = CHECKPOINT_PATH
	checkpoint_reached = false
	menu_message = ""
	rng.seed = RNG_SEED
	changed.emit()


func set_player_cell(cell: Vector2i, facing: Vector2i) -> void:
	player_cell = cell
	player_facing = facing
	changed.emit()


func set_phase(new_phase: String) -> void:
	phase = new_phase
	changed.emit()


func next_turn() -> void:
	turn += 1
	changed.emit()


func can_player_act() -> bool:
	return phase == "player" and not game_over and menu == ""


func get_attack() -> int:
	return BASE_ATTACK + ItemDatabase.stat(equipped_weapon, "attack")


func get_defense() -> int:
	return BASE_DEFENSE + ItemDatabase.stat(equipped_armor, "defense")


## Put an item in the pack. A weapon or armor is equipped when that slot is empty.
## Returns false when the pack is full.
func add_item(item_id: String) -> bool:
	if inventory.size() >= INVENTORY_SIZE:
		return false
	inventory.append(item_id)
	var item_kind := ItemDatabase.kind(item_id)
	if item_kind == "weapon" and equipped_weapon == "":
		equip(inventory.size() - 1)
	elif item_kind == "armor" and equipped_armor == "":
		equip(inventory.size() - 1)
	changed.emit()
	return true


## Equip the weapon or armor in an inventory slot, or take it off if it is already worn.
func equip(index: int) -> bool:
	if index < 0 or index >= inventory.size():
		return false
	var item_id := inventory[index]
	var item_name := ItemDatabase.item_name(item_id)
	match ItemDatabase.kind(item_id):
		"weapon":
			equipped_weapon = "" if equipped_weapon == item_id else item_id
			var verb := "wield" if equipped_weapon == item_id else "put away"
			log_message("You %s the %s." % [verb, item_name])
		"armor":
			equipped_armor = "" if equipped_armor == item_id else item_id
			var verb := "equip" if equipped_armor == item_id else "take off"
			log_message("You %s the %s." % [verb, item_name])
		_:
			return false
	changed.emit()
	return true


## Drink a consumable from an inventory slot. Returns false when it is not a consumable.
func consume(index: int) -> bool:
	if index < 0 or index >= inventory.size():
		return false
	var item_id := inventory[index]
	if ItemDatabase.kind(item_id) != "consumable":
		return false
	inventory.remove_at(index)
	var healed := heal(ItemDatabase.stat(item_id, "heal"))
	log_message("You drink the %s and heal %d." % [ItemDatabase.item_name(item_id), healed])
	changed.emit()
	return true


func is_equipped(item_id: String) -> bool:
	return item_id != "" and (item_id == equipped_weapon or item_id == equipped_armor)


func set_menu(new_menu: String) -> void:
	menu = new_menu
	menu_index = 0
	changed.emit()


## Hurt the player by a raw hit. Defense is taken off (never below 1) and defending halves the
## rest, unless the damage pierces (poison, traps). Returns the damage dealt.
func damage_player(amount: int, pierce := false) -> int:
	if game_over:
		return 0
	var dealt := amount
	if not pierce:
		dealt = maxi(1, amount - get_defense())
		if defending:
			dealt = maxi(1, floori(dealt / 2.0))
	health = maxi(health - dealt, 0)
	if health == 0:
		game_over = true
		log_message("You have fallen...")
	changed.emit()
	return dealt


func heal(amount: int) -> int:
	var healed := mini(amount, max_health - health)
	health += healed
	changed.emit()
	return healed


func log_message(text: String) -> void:
	combat_log.append(text)
	if combat_log.size() > LOG_LIMIT:
		combat_log = combat_log.slice(combat_log.size() - LOG_LIMIT)
	logged.emit(text)
	changed.emit()


## Give the player a status for some turns; a shorter one never cuts a longer one short.
func apply_status(status: String, turns: int) -> void:
	var current: int = statuses.get(status, 0)
	statuses[status] = maxi(current, turns)
	changed.emit()


func has_status(status: String) -> bool:
	var turns: int = statuses.get(status, 0)
	return turns > 0


func snapshot() -> Dictionary:
	var state := {}
	var player := get_tree().get_first_node_in_group("player") as Node2D
	if player:
		state["player_position"] = [
			roundi(player.global_position.x), roundi(player.global_position.y)
		]
	state["player_cell"] = Grid.to_array(player_cell)
	state["player_facing"] = Grid.to_array(player_facing)
	state["health"] = health
	state["max_health"] = max_health
	state["attack"] = get_attack()
	state["defense"] = get_defense()
	state["turn"] = turn
	state["phase"] = phase
	state["defending"] = defending
	state["statuses"] = statuses.duplicate()
	state["combat_log"] = combat_log.duplicate()
	state["actions_resolved"] = actions_resolved
	state["game_over"] = game_over
	state["inventory"] = inventory.duplicate()
	state["equipped_weapon"] = equipped_weapon
	state["equipped_armor"] = equipped_armor
	state["menu"] = menu
	state["menu_index"] = menu_index
	var items: Array[Dictionary] = []
	for node in get_tree().get_nodes_in_group("items"):
		var item := node as Item
		if item:
			items.append(item.to_dict())
	state["items"] = items
	var traps: Array[Dictionary] = []
	for node in get_tree().get_nodes_in_group("traps"):
		var trap := node as Trap
		if trap:
			traps.append(trap.to_dict())
	state["traps"] = traps
	state["traps_triggered"] = traps_triggered
	state["light_radius"] = LIGHT_RADIUS
	state["explored_count"] = explored.size()
	var explored_cells: Array[Array] = []
	for cell: Vector2i in explored:
		explored_cells.append(Grid.to_array(cell))
	state["explored"] = explored_cells
	state["rng_state"] = str(rng.state)
	state["checkpoint_reached"] = checkpoint_reached
	var checkpoints: Array[Dictionary] = []
	for node in get_tree().get_nodes_in_group("checkpoints"):
		var checkpoint := node as Checkpoint
		if checkpoint:
			checkpoints.append(checkpoint.to_dict())
	state["checkpoints"] = checkpoints
	state["visible_count"] = visible_cells.size()
	var enemies: Array[Dictionary] = []
	for node in get_tree().get_nodes_in_group("enemies"):
		var enemy := node as Enemy
		if enemy:
			enemies.append(enemy.to_dict())
	state["enemies"] = enemies
	state["enemy_count"] = enemies.size()
	var dungeon := get_tree().get_first_node_in_group("dungeon") as Dungeon
	state["rooms"] = dungeon.rooms.size() if dungeon else 0
	state["dungeon_seed"] = dungeon.map_seed if dungeon else 0
	var scene := get_tree().current_scene
	state["scene"] = scene.scene_file_path if scene else ""
	return state
