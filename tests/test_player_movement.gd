extends "res://tests/test_case.gd"
## Movement basics. Grid steps since 0002 replaced free movement: one cell is 32 px.


func test_player_moves_right_while_move_right_is_held() -> void:
	await spawn("res://scenes/main.tscn")
	var player := tree.get_first_node_in_group("player") as Node2D
	var start_x := player.global_position.x
	await hold_action("move_right", 20)
	await physics_frames(10)
	var moved := player.global_position.x - start_x
	check(moved >= 32.0, "player should move at least one cell right, moved %.1f px" % moved)


func test_player_stops_when_input_is_released() -> void:
	await spawn("res://scenes/main.tscn")
	var player := tree.get_first_node_in_group("player") as Node2D
	await hold_action("move_down", 10)
	await physics_frames(15)
	var stopped_at := player.global_position
	await physics_frames(15)
	check_eq(player.global_position, stopped_at, "player position after release")


func test_walls_keep_player_inside_arena() -> void:
	await spawn("res://scenes/main.tscn")
	var player := tree.get_first_node_in_group("player") as Node2D
	await hold_action("move_left", 240)
	await physics_frames(10)
	check(
		player.global_position.x >= 32.0,
		"player passed the left wall: x=%.1f" % player.global_position.x
	)
	check(GameState.player_cell.x >= 1, "player cell inside the wall ring")


func test_snapshot_reports_player_position() -> void:
	await spawn("res://scenes/main.tscn")
	var state: Dictionary = GameState.snapshot()
	check(state.has("player_position"), "snapshot should include player_position")
	var centre := Grid.to_world(Grid.START)
	check_eq(
		state.get("player_position"),
		[roundi(centre.x), roundi(centre.y)],
		"player starts in the arena centre"
	)
