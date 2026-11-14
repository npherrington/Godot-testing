extends "res://tests/test_case.gd"


func _start() -> Node:
	var main: Node = await spawn("res://scenes/main.tscn")
	for node in tree.get_nodes_in_group("enemies"):
		node.remove_from_group("enemies")
		node.queue_free()
	await physics_frames(1)
	return main


func _player() -> Player:
	return tree.get_first_node_in_group("player") as Player


func test_player_carries_a_torch_light_with_a_6_cell_radius() -> void:
	await _start()
	var torch := _player().get_node_or_null("Torch") as PointLight2D
	check(torch != null and torch.enabled, "the player carries a lit PointLight2D")
	if torch:
		var radius_cells: float = torch.call("radius") / Grid.CELL
		check(radius_cells >= 5.0 and radius_cells <= 7.0, "radius 5-7 cells: %.1f" % radius_cells)
		check(torch.color.r > torch.color.b, "warm torch colour")
	check_eq(GameState.snapshot()["light_radius"], 6, "light radius in the snapshot")


func test_unvisited_cells_are_hidden_and_explored_ones_stay_revealed() -> void:
	var main := await _start()
	check(main.get_node_or_null("%FogOfWar") != null, "fog of war node")
	check(GameState.explored.has(Grid.START), "the start is explored")
	check(not GameState.explored.has(Vector2i(1, 1)), "a far corner is not")
	var total := Grid.SIZE.x * Grid.SIZE.y
	var explored_at_start := GameState.explored.size()
	check(explored_at_start > 0 and explored_at_start < total / 4, "only the area round the start")
	var behind := Vector2i(-1, -1)
	for cell: Vector2i in GameState.visible_cells:
		if cell.x <= Grid.START.x - 4 and cell.y == Grid.START.y:
			behind = cell
	check(behind != Vector2i(-1, -1), "test setup: a visible cell to the left")
	await hold_action("move_right", 50)
	await physics_frames(20)
	check(GameState.player_cell.x >= Grid.START.x + 4, "walked right")
	check(GameState.explored.size() > explored_at_start, "walking explores more")
	check(GameState.explored.has(behind), "cells seen before stay explored")
	check(not GameState.visible_cells.has(behind), "but are out of sight now")


func test_walls_block_sight() -> void:
	await _start()
	var dungeon := tree.get_first_node_in_group("dungeon") as Dungeon
	var room: Rect2i = dungeon.rooms[0]
	var centre := room.position + Vector2i(1, 1)
	_player().place(centre)
	await physics_frames(2)
	var checked := 0
	for dir: Vector2i in [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]:
		if centre + dir * 2 == dungeon.doors[0]:
			continue
		var beyond := centre + dir * 3
		check(not GameState.visible_cells.has(beyond), "behind the room wall: %s" % beyond)
		check(GameState.visible_cells.has(centre + dir * 2), "the wall itself is seen")
		checked += 1
	check_eq(checked, 3, "three solid walls checked")


func test_ambience_and_torch_sounds_loop() -> void:
	var main := await _start()
	var ambience := main.get_node("%Ambience") as AudioStreamPlayer
	var crackle := _player().get_node("TorchSound") as AudioStreamPlayer2D
	check(ambience.stream != null, "ambience has a sound")
	check(crackle.stream != null, "torch crackle has a sound")
	check(
		ambience.stream.resource_path.ends_with("sfx_environment_ambience_loop.ogg"),
		"dungeon ambience loop"
	)
	check(crackle.stream.resource_path.ends_with("sfx_environment_torch_loop.ogg"), "torch loop")
	check((ambience.stream as AudioStreamOggVorbis).loop, "ambience loops")
	check((crackle.stream as AudioStreamOggVorbis).loop, "crackle loops")


func test_light_and_sight_move_with_the_player() -> void:
	await _start()
	var torch := _player().get_node("Torch") as PointLight2D
	var seen_before := GameState.visible_cells.duplicate()
	await hold_action("move_down", 3)
	await physics_frames(20)
	check_eq(GameState.player_cell, Grid.START + Vector2i(0, 1), "stepped down")
	check_eq(torch.global_position, _player().global_position + Vector2(0, -16), "torch follows")
	var newly_seen := 0
	for cell: Vector2i in GameState.visible_cells:
		if not seen_before.has(cell):
			newly_seen += 1
	check(newly_seen > 0, "sight moved with the player")


func test_wall_torches_flicker_and_smoke() -> void:
	await _start()
	var dungeon := tree.get_first_node_in_group("dungeon") as Dungeon
	var torches := tree.get_nodes_in_group("torches")
	check_eq(torches.size(), 8, "wall torches placed")
	for node in torches:
		var torch := node as Node2D
		var cell: Vector2i = torch.get("cell")
		check(dungeon.is_wall(cell) and dungeon.is_walkable(cell + Vector2i.DOWN), "on a wall face")
		var smoking: bool = torch.call("is_smoking")
		check(smoking, "smoke rises")
	var light := (torches[0] as Node).get_node("Light") as PointLight2D
	var first := light.energy
	await physics_frames(7)
	check(not is_equal_approx(light.energy, first), "the light flickers")


func test_darkness_and_mist_cover_the_world() -> void:
	var main := await _start()
	var darkness := main.get_node("Darkness") as CanvasModulate
	check(darkness.color.v < 0.5, "the dungeon is dark away from torches")
	var mist := main.get_node("World/MistA") as Sprite2D
	var start := mist.region_rect.position
	await physics_frames(30)
	check(mist.region_rect.position != start, "the mist drifts")


func test_enemies_out_of_sight_are_hidden_from_the_start() -> void:
	await spawn("res://scenes/main.tscn")
	for node in tree.get_nodes_in_group("enemies"):
		var enemy := node as Enemy
		var in_sight := GameState.visible_cells.has(enemy.cell)
		check_eq(
			enemy.visible, in_sight, "%s at %s shown only in sight" % [enemy.type_id, enemy.cell]
		)
