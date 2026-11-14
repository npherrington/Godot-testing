extends "res://tests/test_case.gd"

const ENEMY_SCENE := "res://scenes/enemy.tscn"


func _clear_enemies() -> void:
	for node in tree.get_nodes_in_group("enemies"):
		node.remove_from_group("enemies")
		node.queue_free()


func _add(type_id: String, at: Vector2i, awake := true) -> Enemy:
	var enemy := (load(ENEMY_SCENE) as PackedScene).instantiate() as Enemy
	enemy.setup(at, type_id)
	enemy.awake = awake
	tree.current_scene.get_node("%Enemies").add_child(enemy)
	return enemy


func _defend_turns(count: int) -> void:
	for i in count:
		await hold_action("defend", 3)
		await physics_frames(15)


func _logged(fragment: String) -> bool:
	for line in GameState.combat_log:
		if fragment in line:
			return true
	return false


func _start() -> void:
	await spawn("res://scenes/main.tscn")
	_clear_enemies()
	await physics_frames(1)


func test_database_has_ten_types_with_stats_and_behavior() -> void:
	check_eq(MonsterDatabase.SPAWN_ORDER.size(), 10, "ten monster types")
	for type_id in MonsterDatabase.SPAWN_ORDER:
		check(MonsterDatabase.has_type(type_id), "%s is in the database" % type_id)
		var stats := MonsterDatabase.get_stats(type_id)
		for key: String in ["name", "health", "damage", "behavior"]:
			check(stats.has(key), "%s has %s" % [type_id, key])
	for required: String in ["skeleton_warrior", "ghost", "goblin", "slime", "ogre"]:
		check(required in MonsterDatabase.SPAWN_ORDER, "%s is one of the ten" % required)


func test_every_type_has_its_own_existing_sprite() -> void:
	var paths: Dictionary[String, bool] = {}
	for type_id in MonsterDatabase.SPAWN_ORDER:
		var path := MonsterDatabase.frames_path(type_id)
		check(ResourceLoader.exists(path), "sprite exists: %s" % path)
		check(not paths.has(path), "sprite not shared: %s" % path)
		paths[path] = true
	await _start()
	var skeleton := _add("skeleton_warrior", Vector2i(3, 3), false)
	var ogre := _add("ogre", Vector2i(5, 3), false)
	await physics_frames(1)
	var skeleton_frames := (skeleton.get_node("Sprite") as AnimatedSprite2D).sprite_frames
	var ogre_frames := (ogre.get_node("Sprite") as AnimatedSprite2D).sprite_frames
	check(skeleton_frames != ogre_frames, "different types draw different sprites")
	check_eq(ogre_frames.resource_path, MonsterDatabase.frames_path("ogre"), "ogre's sheet")


func test_behaviors_are_all_different() -> void:
	var behaviors: Dictionary[String, bool] = {}
	for type_id in MonsterDatabase.SPAWN_ORDER:
		var behavior: String = MonsterDatabase.get_stats(type_id)["behavior"]
		check(not behaviors.has(behavior), "behavior %s used once" % behavior)
		behaviors[behavior] = true


func test_ghost_walks_through_walls() -> void:
	await _start()
	var dungeon := tree.get_first_node_in_group("dungeon") as Dungeon
	var room: Rect2i = dungeon.rooms[0]
	var inside := room.position
	var wall := inside + Vector2i.UP
	var outside := inside + Vector2i(0, -3)
	if not dungeon.is_walkable(outside):
		inside = Vector2i(room.position.x, room.end.y - 1)
		wall = inside + Vector2i.DOWN
		outside = inside + Vector2i(0, 3)
	(tree.get_first_node_in_group("player") as Player).place(outside)
	var ghost := _add("ghost", inside)
	await _defend_turns(1)
	check_eq(ghost.cell, wall, "the ghost moved into the wall toward the player")
	check(dungeon.is_wall(ghost.cell), "standing inside a wall")


func test_goblin_throws_rocks_from_range() -> void:
	await _start()
	var goblin := _add("goblin", Grid.START + Vector2i(3, 0))
	await _defend_turns(1)
	check(_logged("Goblin throws a rock at you"), "rock thrown")
	check_eq(goblin.cell, Grid.START + Vector2i(3, 0), "it stays at range to throw")
	check(GameState.health < 100, "the rock hurt")


func test_dark_mage_backs_away_to_cast() -> void:
	await _start()
	var mage := _add("dark_mage", Grid.START + Vector2i(2, 0))
	await _defend_turns(1)
	check_eq(Grid.distance(mage.cell, Grid.START), 3, "the mage stepped back to range 3")


func test_slime_splits_when_first_hurt() -> void:
	await _start()
	var slime := _add("slime", Grid.START + Vector2i(1, 0), false)
	await physics_frames(1)
	await hold_action("move_right", 3)
	await physics_frames(15)
	var types: Array[String] = []
	for node in tree.get_nodes_in_group("enemies"):
		types.append((node as Enemy).type_id)
	check(slime.is_alive(), "the slime survives one hit")
	check_eq(types.size(), 2, "the slime split in two")
	check("slime_small" in types, "a slime spawn appeared")
	check(_logged("Slime splits in two!"), "the split is logged")


func test_slime_hops_only_in_four_directions() -> void:
	await _start()
	var slime := _add("slime", Grid.START + Vector2i(3, 3))
	await _defend_turns(1)
	var moved := slime.cell - (Grid.START + Vector2i(3, 3))
	check(absi(moved.x) + absi(moved.y) == 1, "one orthogonal hop, moved %s" % moved)


func test_ogre_acts_every_other_turn() -> void:
	await _start()
	var ogre := _add("ogre", Grid.START + Vector2i(4, 0))
	await _defend_turns(1)
	check_eq(ogre.cell, Grid.START + Vector2i(3, 0), "moves on its first turn")
	await _defend_turns(1)
	check_eq(ogre.cell, Grid.START + Vector2i(3, 0), "rests on its second")
	await _defend_turns(1)
	check_eq(ogre.cell, Grid.START + Vector2i(2, 0), "moves again on its third")


func test_wolfman_runs_two_cells_a_turn() -> void:
	await _start()
	var wolfman := _add("wolfman", Grid.START + Vector2i(5, 0))
	await _defend_turns(1)
	check_eq(wolfman.cell, Grid.START + Vector2i(3, 0), "two cells in one turn")


func test_spider_waits_in_ambush_then_webs_the_player() -> void:
	await _start()
	var spider := _add("spider", Grid.START + Vector2i(5, 0), false)
	await _defend_turns(1)
	check(not spider.awake, "asleep while the player is 5 away")
	spider.setup(Grid.START + Vector2i(5, 0))
	(tree.get_first_node_in_group("player") as Player).place(Grid.START + Vector2i(2, 0))
	var turn_before := GameState.turn
	await _defend_turns(1)
	await physics_frames(15)
	check(spider.awake, "wakes within 3 cells")
	check(_logged("Spider spits a web at you"), "web shot")
	check(_logged("frozen solid"), "the web froze the player")
	check_eq(GameState.turn - turn_before, 2, "the frozen turn was skipped")


func test_zombie_bite_poisons() -> void:
	await _start()
	_add("zombie", Grid.START + Vector2i(1, 0))
	await _defend_turns(1)
	check(_logged("Zombie hits you"), "zombie bit")
	check(GameState.has_status("poison"), "the bite poisons")


func test_types_have_different_health_and_damage() -> void:
	var healths: Dictionary[int, bool] = {}
	var damages: Dictionary[String, bool] = {}
	for type_id in MonsterDatabase.SPAWN_ORDER:
		var stats := MonsterDatabase.get_stats(type_id)
		var health: int = stats["health"]
		healths[health] = true
		damages[str(stats["damage"])] = true
	check(healths.size() >= 7, "at least 7 different health values, got %d" % healths.size())
	check(damages.size() >= 6, "at least 6 different damage ranges, got %d" % damages.size())


func test_start_spawns_one_of_each_type_with_its_stats() -> void:
	await spawn("res://scenes/main.tscn")
	var spawned: Array[String] = []
	for node in tree.get_nodes_in_group("enemies"):
		var enemy := node as Enemy
		spawned.append(enemy.type_id)
		var stats := MonsterDatabase.get_stats(enemy.type_id)
		check_eq(enemy.max_health, stats["health"], "%s health" % enemy.type_id)
		check_eq(enemy.display_name, stats["name"], "%s name" % enemy.type_id)
		check_eq([enemy.damage_min, enemy.damage_max], stats["damage"], "%s damage" % enemy.type_id)
		var sprite := enemy.get_node("Sprite") as AnimatedSprite2D
		check_eq(
			sprite.sprite_frames.resource_path, MonsterDatabase.frames_path(enemy.type_id), "sheet"
		)
	var expected: Array[String] = MonsterDatabase.SPAWN_ORDER.duplicate()
	expected.sort()
	spawned.sort()
	check_eq(spawned, expected, "one of each type")
