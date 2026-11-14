extends "res://tests/test_case.gd"


func _dungeon() -> Dungeon:
	return tree.get_first_node_in_group("dungeon") as Dungeon


func test_arena_is_32_by_32_with_wall_border_and_floor_inside() -> void:
	await spawn("res://scenes/main.tscn")
	var dungeon := _dungeon()
	for i in Grid.SIZE.x:
		check(dungeon.is_wall(Vector2i(i, 0)), "top border wall at %d" % i)
		check(dungeon.is_wall(Vector2i(i, Grid.SIZE.y - 1)), "bottom border wall at %d" % i)
		check(dungeon.is_wall(Vector2i(0, i)), "left border wall at %d" % i)
		check(dungeon.is_wall(Vector2i(Grid.SIZE.x - 1, i)), "right border wall at %d" % i)
	check(dungeon.is_walkable(Grid.START), "the centre is floor")
	var floor_layer := dungeon.get_node("Floor") as TileMapLayer
	var wall_layer := dungeon.get_node("Walls") as TileMapLayer
	check(floor_layer.get_cell_source_id(Grid.START * 2) != -1, "floor tile painted at the centre")
	check(wall_layer.get_cell_source_id(Vector2i.ZERO) != -1, "wall tile painted at the corner")
	check_eq(
		floor_layer.get_used_cells().size(),
		dungeon.floor_cells().size() * 4,
		"every floor cell painted with 2x2 tiles"
	)


func test_rooms_are_3_by_3_floor_with_a_wall_ring_and_one_door() -> void:
	await spawn("res://scenes/main.tscn")
	var dungeon := _dungeon()
	check_eq(dungeon.rooms.size(), Dungeon.ROOM_COUNT, "room count")
	check_eq(GameState.snapshot().get("rooms"), Dungeon.ROOM_COUNT, "snapshot room count")
	for room in dungeon.rooms:
		check_eq(room.size, Vector2i(3, 3), "room interior size")
		var openings := 0
		var outer := room.grow(1)
		for x in range(outer.position.x, outer.end.x):
			for y in range(outer.position.y, outer.end.y):
				var cell := Vector2i(x, y)
				if room.has_point(cell):
					check(dungeon.is_walkable(cell), "room floor at %s" % cell)
				elif dungeon.is_walkable(cell):
					openings += 1
		check_eq(openings, 1, "one door in the ring of room at %s" % room.position)


func test_room_generation_is_deterministic() -> void:
	var scene := load("res://scenes/dungeon.tscn") as PackedScene
	var first := scene.instantiate() as Dungeon
	var second := scene.instantiate() as Dungeon
	tree.root.add_child(first)
	tree.root.add_child(second)
	first.generate(42)
	second.generate(42)
	check_eq(first.rooms, second.rooms, "same seed, same rooms")
	check_eq(first.doors, second.doors, "same seed, same doors")
	first.queue_free()
	second.queue_free()
	await tree.process_frame


func test_room_wall_blocks_the_player() -> void:
	await spawn("res://scenes/main.tscn")
	var room: Rect2i = _dungeon().rooms[0]
	var below := Vector2i(room.position.x, room.end.y + 1)
	if _dungeon().is_walkable(below + Vector2i.UP):
		below = Vector2i(room.end.x - 1, room.end.y + 1)
	check(_dungeon().is_wall(below + Vector2i.UP), "test setup: room wall above")
	var player := tree.get_first_node_in_group("player") as Player
	player.place(below)
	await hold_action("move_up", 30)
	await physics_frames(10)
	check_eq(GameState.player_cell, below, "the room wall stops the player")


func test_dungeon_scene_is_instanced_in_main() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var dungeon := _dungeon()
	check(dungeon != null, "a node in group dungeon")
	if dungeon:
		check_eq(dungeon.scene_file_path, "res://scenes/dungeon.tscn", "instanced from its scene")
		check(main.is_ancestor_of(dungeon), "inside the main scene")


func test_player_cannot_leave_the_arena_at_a_corner() -> void:
	await spawn("res://scenes/main.tscn")
	var player := tree.get_first_node_in_group("player") as Player
	player.place(Vector2i(1, 1))
	await hold_action("move_up_left", 30)
	await hold_action("move_left", 30)
	await hold_action("move_up", 30)
	await physics_frames(10)
	check_eq(GameState.player_cell, Vector2i(1, 1), "stays at the inner corner")
