extends "res://tests/test_case.gd"

const TEST_SAVE := "user://test_save.json"
const TEST_CHECKPOINT := "user://test_checkpoint.json"


func after_each() -> void:
	for path: String in [TEST_SAVE, TEST_CHECKPOINT]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	await super()


func _start(clear_enemies := false) -> Node:
	var main: Node = await spawn("res://scenes/main.tscn")
	GameState.save_path = TEST_SAVE
	GameState.checkpoint_path = TEST_CHECKPOINT
	GameState.inventory.clear()
	if clear_enemies:
		for group: String in ["enemies", "traps"]:
			for node in tree.get_nodes_in_group(group):
				node.remove_from_group(group)
				node.queue_free()
	await physics_frames(1)
	return main


func _act(action: String) -> void:
	await hold_action(action, 3)
	await physics_frames(15)


func _enemy_summary() -> Array[String]:
	var summary: Array[String] = []
	for node in tree.get_nodes_in_group("enemies"):
		var enemy := node as Enemy
		summary.append("%s@%s:%d" % [enemy.type_id, enemy.cell, enemy.health])
	return summary


func test_snapshot_round_trips_through_json() -> void:
	await _start()
	GameState.add_item("sword")
	var state := GameState.snapshot()
	var parsed: Variant = JSON.parse_string(JSON.stringify(state))
	check(parsed is Dictionary, "snapshot is valid JSON")
	var data: Dictionary = parsed
	for key: String in ["player_cell", "health", "inventory", "enemies", "turn", "items", "traps"]:
		check(data.has(key), "snapshot has %s" % key)
	check_eq(Grid.from_array(data["player_cell"]), Grid.START, "player cell survives JSON")
	check_eq(data["inventory"], ["sword"], "inventory survives JSON")
	var enemies: Array = data["enemies"]
	check_eq(enemies.size(), MonsterDatabase.SPAWN_ORDER.size(), "every enemy serialized")


func test_save_writes_a_json_file() -> void:
	await _start()
	check(SaveSystem.save_game(GameState.save_path), "save reports success")
	check(FileAccess.file_exists(TEST_SAVE), "the file exists")
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(TEST_SAVE))
	check(parsed is Dictionary, "the file is JSON")
	if parsed is Dictionary:
		var data: Dictionary = parsed
		check_eq(SaveSystem.read_int(data, "version", 0), SaveSystem.VERSION, "versioned")
		check_eq(SaveSystem.read_int(data, "health", 0), 100, "health saved")


func test_load_restores_player_inventory_enemies_and_turn() -> void:
	await _start()
	GameState.add_item("sword")
	GameState.health = 77
	await _act("move_down")
	var saved_turn := GameState.turn
	var saved_cell := GameState.player_cell
	var saved_enemies := _enemy_summary()
	var saved_explored := GameState.explored.size()
	SaveSystem.save_game(GameState.save_path)
	await _act("move_down")
	await _act("move_right")
	GameState.health = 20
	GameState.inventory.clear()
	GameState.equipped_weapon = ""
	var victim := tree.get_nodes_in_group("enemies")[0]
	victim.remove_from_group("enemies")
	victim.queue_free()
	check(SaveSystem.load_game(GameState.save_path), "load reports success")
	await physics_frames(2)
	check_eq(GameState.health, 77, "health restored")
	check_eq(GameState.player_cell, saved_cell, "position restored")
	check_eq(
		(tree.get_first_node_in_group("player") as Node2D).position,
		Grid.to_world(saved_cell),
		"player drawn there"
	)
	check_eq(GameState.inventory, ["sword"] as Array[String], "inventory restored")
	check_eq(GameState.get_attack(), GameState.BASE_ATTACK + 4, "the sword is wielded again")
	check_eq(GameState.turn, saved_turn, "turn restored")
	check_eq(GameState.phase, "player", "the player moves first after loading")
	check_eq(_enemy_summary(), saved_enemies, "enemies restored")
	check_eq(GameState.explored.size(), saved_explored, "explored map restored")


func test_load_keeps_enemy_order_and_pacing() -> void:
	await _start(true)
	var enemy_scene := load("res://scenes/enemy.tscn") as PackedScene
	for spec: Array in [["ogre", Vector2i(5, 0)], ["skeleton_warrior", Vector2i(0, 6)]]:
		var enemy := enemy_scene.instantiate() as Enemy
		var kind: String = spec[0]
		var offset: Vector2i = spec[1]
		enemy.setup(Grid.START + offset, kind)
		enemy.awake = true
		tree.current_scene.get_node("%Enemies").add_child(enemy)
	await _act("defend")
	var ogre_cell := (tree.get_nodes_in_group("enemies")[0] as Enemy).cell
	check_eq(ogre_cell, Grid.START + Vector2i(4, 0), "the ogre moved on its first turn")
	SaveSystem.save_game(GameState.save_path)
	SaveSystem.load_game(GameState.save_path)
	await physics_frames(2)
	var order: Array[String] = []
	for node in tree.get_nodes_in_group("enemies"):
		order.append((node as Enemy).type_id)
	check_eq(order, ["ogre", "skeleton_warrior"] as Array[String], "same turn order after load")
	await _act("defend")
	var ogre := tree.get_nodes_in_group("enemies")[0] as Enemy
	check_eq(ogre.cell, ogre_cell, "the loaded ogre still rests on its second turn")
	await _act("defend")
	check_eq(ogre.cell, ogre_cell + Vector2i(-1, 0), "and moves on its third")


func test_stepping_on_a_checkpoint_saves_and_death_returns_there() -> void:
	await _start(true)
	var checkpoints := tree.get_nodes_in_group("checkpoints")
	check_eq(checkpoints.size(), 2, "two checkpoints in the dungeon")
	var checkpoint := checkpoints[0] as Checkpoint
	var checkpoint_cell := checkpoint.cell
	var dungeon := tree.get_first_node_in_group("dungeon") as Dungeon
	var from := checkpoint.cell + Vector2i.LEFT
	var step := "move_right"
	if not dungeon.is_walkable(from):
		from = checkpoint.cell + Vector2i.RIGHT
		step = "move_left"
	(tree.get_first_node_in_group("player") as Player).place(from)
	GameState.health = 64
	await _act(step)
	check_eq(GameState.player_cell, checkpoint.cell, "standing on the checkpoint")
	check(checkpoint.used, "the checkpoint lit up")
	check(FileAccess.file_exists(TEST_CHECKPOINT), "progress saved")
	check(GameState.combat_log.has("Checkpoint reached. Progress saved."), "logged")
	GameState.damage_player(999, true)
	check(GameState.game_over, "test setup: dead")
	await _act("interact")
	check(not GameState.game_over, "back on your feet")
	check_eq(GameState.health, 64, "with the checkpoint's health")
	check_eq(GameState.player_cell, checkpoint_cell, "at the checkpoint")


func test_pause_menu_saves_and_loads() -> void:
	var main := await _start(true)
	var menu := main.get_node("HUD").get_node("%PauseMenu") as Control
	await _act("pause")
	check_eq(GameState.menu, "pause", "pause opens the menu")
	check(menu.is_visible_in_tree(), "the menu shows")
	var buttons := main.get_node("HUD").get_node("%Buttons")
	check_eq(buttons.get_child_count(), 5, "five options")
	await _act("move_down")
	check_eq(GameState.menu_index, 1, "Save Game selected")
	await _act("interact")
	check(FileAccess.file_exists(TEST_SAVE), "saved from the menu")
	check_eq(GameState.menu_message, "Game saved.", "feedback shown")
	await _act("pause")
	check(not menu.visible, "pause again closes it")
	await _act("move_right")
	check_eq(GameState.player_cell, Grid.START + Vector2i(1, 0), "moved after saving")
	await _act("pause")
	await _act("move_down")
	await _act("move_down")
	check_eq(GameState.menu_index, 2, "Load Game selected")
	await _act("interact")
	check_eq(GameState.player_cell, Grid.START, "loaded back to the saved spot")
	check_eq(GameState.menu, "", "the menu closes after loading")


func test_checkpoints_are_not_next_to_traps() -> void:
	await spawn("res://scenes/main.tscn")
	for node in tree.get_nodes_in_group("checkpoints"):
		var checkpoint := node as Checkpoint
		for trap_node in tree.get_nodes_in_group("traps"):
			var trap := trap_node as Trap
			check(Grid.distance(trap.cell, checkpoint.cell) > 1, "trap beside %s" % checkpoint.cell)
