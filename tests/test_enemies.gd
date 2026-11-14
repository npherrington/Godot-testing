extends "res://tests/test_case.gd"

const ENEMY_SCENE := "res://scenes/enemy.tscn"


func _clear_enemies() -> void:
	for node in tree.get_nodes_in_group("enemies"):
		node.remove_from_group("enemies")
		node.queue_free()


func _add_enemy(at: Vector2i, awake := true) -> Enemy:
	var enemy := (load(ENEMY_SCENE) as PackedScene).instantiate() as Enemy
	enemy.setup(at)
	enemy.awake = awake
	tree.current_scene.get_node("%Enemies").add_child(enemy)
	return enemy


## One player turn spent defending, then the enemy phase.
func _defend_one_turn() -> void:
	await hold_action("defend", 3)
	await physics_frames(15)


func test_enemy_template_has_health_damage_and_a_sprite() -> void:
	var enemy := await spawn(ENEMY_SCENE) as Enemy
	check(enemy.is_in_group("enemies"), "in group enemies")
	check(enemy.max_health >= 15 and enemy.max_health <= 25, "health 15-25: %d" % enemy.max_health)
	check_eq(enemy.health, enemy.max_health, "starts at full health")
	check(enemy.damage_min >= 5 and enemy.damage_max <= 10, "damage within 5-10")
	check(enemy.damage_min <= enemy.damage_max, "damage range is ordered")
	check(enemy.get_node_or_null("Sprite") is AnimatedSprite2D, "has a Sprite")
	check(enemy.type_id != "" and enemy.display_name != "", "has a type and a name")


func test_awake_enemy_steps_one_cell_toward_the_player_per_turn() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	var enemy := _add_enemy(Grid.START + Vector2i(4, 0))
	await physics_frames(2)
	await _defend_one_turn()
	check_eq(enemy.cell, Grid.START + Vector2i(3, 0), "one step closer after one turn")
	await _defend_one_turn()
	check_eq(enemy.cell, Grid.START + Vector2i(2, 0), "another step after the next turn")


func test_enemy_does_not_move_while_it_is_the_players_turn() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	var enemy := _add_enemy(Grid.START + Vector2i(4, 0))
	await physics_frames(90)
	check_eq(enemy.cell, Grid.START + Vector2i(4, 0), "no move without a player turn")
	check_eq(GameState.phase, "player", "still the player's turn")


func test_adjacent_enemy_hits_for_5_to_10() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	_add_enemy(Grid.START + Vector2i(2, 0))
	await physics_frames(2)
	await hold_action("move_right", 3)
	await physics_frames(15)
	check_eq(GameState.player_cell, Grid.START + Vector2i(1, 0), "player stepped next to it")
	var lost := 100 - GameState.health
	check(lost >= 5 and lost <= 10, "one hit takes 5-10 health, took %d" % lost)
	check("hits you for %d" % lost in GameState.combat_log[-1], "log names the damage")


func test_enemies_spawn_on_floor_away_from_the_player() -> void:
	await spawn("res://scenes/main.tscn")
	var dungeon := tree.get_first_node_in_group("dungeon") as Dungeon
	var state := GameState.snapshot()
	check_eq(state.get("enemy_count"), MonsterDatabase.SPAWN_ORDER.size(), "enemies at start")
	var seen: Dictionary[Vector2i, bool] = {}
	for node in tree.get_nodes_in_group("enemies"):
		var enemy := node as Enemy
		check(dungeon.is_walkable(enemy.cell), "enemy on floor at %s" % enemy.cell)
		check(Grid.distance(enemy.cell, Grid.START) >= 6, "enemy far from start at %s" % enemy.cell)
		check(not seen.has(enemy.cell), "one enemy per cell at %s" % enemy.cell)
		seen[enemy.cell] = true
		check_eq(enemy.position, Grid.to_world(enemy.cell), "drawn on its cell")


func test_hitting_an_enemy_lowers_its_health_and_kills_it_at_zero() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	var enemy := _add_enemy(Grid.START + Vector2i(1, 0), false)
	await physics_frames(2)
	await hold_action("move_right", 3)
	await physics_frames(15)
	check_eq(enemy.health, enemy.max_health - GameState.get_attack(), "bump attack damage")
	check_eq(GameState.player_cell, Grid.START, "attacking does not move the player")
	enemy.health = 1
	await hold_action("move_right", 3)
	await physics_frames(15)
	check(not enemy.is_alive(), "enemy dies at 0 health")
	check_eq(tree.get_nodes_in_group("enemies").size(), 0, "dead enemy leaves the group")
	check("Skeleton is slain!" in GameState.combat_log, "death is logged")
