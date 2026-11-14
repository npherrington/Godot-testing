extends "res://tests/test_case.gd"

const ENEMY_SCENE := "res://scenes/enemy.tscn"


func _clear_enemies() -> void:
	for node in tree.get_nodes_in_group("enemies"):
		node.remove_from_group("enemies")
		node.queue_free()


func _add_enemy(at: Vector2i, enemy_name := "Skeleton") -> Enemy:
	var enemy := (load(ENEMY_SCENE) as PackedScene).instantiate() as Enemy
	enemy.setup(at)
	enemy.awake = true
	enemy.display_name = enemy_name
	tree.current_scene.get_node("%Enemies").add_child(enemy)
	return enemy


func _turn_label(main: Node) -> Label:
	return main.get_node("HUD").get_node("%TurnLabel") as Label


func _log_index(fragment: String) -> int:
	for i in GameState.combat_log.size():
		if fragment in GameState.combat_log[i]:
			return i
	return -1


func test_player_turn_then_enemy_turn_then_next_turn() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	check_eq(GameState.turn, 1, "first turn")
	check_eq(GameState.phase, "player", "player goes first")
	await hold_action("move_right", 3)
	await physics_frames(1)
	check_eq(GameState.phase, "enemy", "enemies act after the player")
	await physics_frames(10)
	check_eq(GameState.phase, "player", "back to the player")
	check_eq(GameState.turn, 2, "turn counter went up")


func test_player_input_is_ignored_during_the_enemy_turn() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	await hold_action("move_right", 3)
	await physics_frames(1)
	check_eq(GameState.phase, "enemy", "test setup: enemy phase")
	await hold_action("move_right", 3)
	await physics_frames(20)
	check_eq(GameState.player_cell, Grid.START + Vector2i(1, 0), "second press was ignored")
	check_eq(GameState.turn, 2, "only one turn passed")


func test_queued_actions_resolve_in_order() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	_add_enemy(Grid.START + Vector2i(1, 0), "Alpha")
	_add_enemy(Grid.START + Vector2i(-1, 0), "Beta")
	await physics_frames(2)
	var resolved_before := GameState.actions_resolved
	await hold_action("defend", 3)
	await physics_frames(15)
	var guard := _log_index("You raise your guard")
	var alpha := _log_index("Alpha hits you")
	var beta := _log_index("Beta hits you")
	check(guard >= 0 and alpha >= 0 and beta >= 0, "all three actions logged")
	check(guard < alpha and alpha < beta, "player first, then enemies in order")
	check_eq(GameState.actions_resolved - resolved_before, 3, "three actions resolved")


func test_queue_runs_first_in_first_out() -> void:
	await spawn("res://scenes/main.tscn")
	var turns := tree.get_first_node_in_group("turn_manager") as TurnManager
	var player := tree.get_first_node_in_group("player")
	turns.enqueue({"type": "wait", "actor": player})
	turns.enqueue({"type": "defend", "actor": player})
	check_eq(turns.queue.size(), 2, "two actions queued")
	turns.process_queue()
	check(turns.queue.is_empty(), "queue drained")
	check(GameState.defending, "the defend action resolved")
	check_eq(GameState.actions_resolved, 2, "both resolved")


func test_poison_deals_damage_each_round_and_wears_off() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	GameState.apply_status("poison", 3)
	check(GameState.has_status("poison"), "status applied")
	await hold_action("defend", 3)
	await physics_frames(15)
	check_eq(GameState.health, 97, "poison hurts 3 at the end of the round")
	check_eq(GameState.statuses.get("poison"), 2, "two rounds left")
	for i in 2:
		await hold_action("defend", 3)
		await physics_frames(15)
	check_eq(GameState.health, 91, "three rounds of poison")
	check(not GameState.has_status("poison"), "poison wore off")


func test_freeze_skips_the_players_turn() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	await hold_action("defend", 3)
	await physics_frames(1)
	GameState.apply_status("freeze", 1)
	await physics_frames(30)
	check_eq(GameState.turn, 3, "the frozen turn passed without input")
	check_eq(GameState.phase, "player", "player acts again after the freeze")
	check(_log_index("frozen solid") >= 0, "freeze is logged")
	check(not GameState.has_status("freeze"), "freeze wore off")


func test_turn_indicator_shows_whose_turn_it_is() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	_clear_enemies()
	var label := _turn_label(main)
	check(label.is_visible_in_tree(), "turn indicator visible")
	check_eq(label.text, "Turn 1 - Your turn", "start of the game")
	await hold_action("move_right", 3)
	await physics_frames(1)
	check_eq(label.text, "Turn 1 - Enemy turn", "during the enemy phase")
	await physics_frames(10)
	check_eq(label.text, "Turn 2 - Your turn", "next turn")


func test_combat_log_shows_the_result_of_an_attack() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	_clear_enemies()
	_add_enemy(Grid.START + Vector2i(1, 0))
	await physics_frames(2)
	await hold_action("attack", 3)
	await physics_frames(15)
	var log_label := main.get_node("HUD").get_node("%CombatLog") as Label
	check(log_label.is_visible_in_tree(), "combat log visible")
	var hit := "You hit Skeleton for %d." % GameState.BASE_ATTACK
	check(hit in log_label.text, "attack result shown: %s" % log_label.text)
	check("Skeleton hits you for" in log_label.text, "enemy reply shown")


func test_action_pressed_mid_step_is_buffered() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	await hold_action("move_right", 3)
	await physics_frames(1)
	check_eq(GameState.phase, "enemy", "test setup: still resolving the step")
	await hold_action("defend", 2)
	await physics_frames(20)
	check_eq(GameState.turn, 3, "the defend pressed mid-step ran once the player could act")
	check(GameState.combat_log.has("You raise your guard."), "defend resolved")


func test_enemies_stop_once_the_player_falls() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	_add_enemy(Grid.START + Vector2i(1, 0), "Alpha")
	_add_enemy(Grid.START + Vector2i(-1, 0), "Beta")
	await physics_frames(2)
	GameState.health = 1
	await hold_action("defend", 3)
	await physics_frames(15)
	check(GameState.game_over, "the first hit is fatal")
	check_eq(_log_index("Beta hits you"), -1, "the second enemy does not act on a corpse")
