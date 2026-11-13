extends "res://tests/test_case.gd"


func test_player_moves_right_while_move_right_is_held() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var player := main.get_node("Player") as Node2D
	var start_x := player.global_position.x
	await hold_action("move_right", 20)
	var moved := player.global_position.x - start_x
	check(moved > 20.0, "player should move right, moved %.1f px" % moved)


func test_player_stops_when_input_is_released() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var player := main.get_node("Player") as Node2D
	await hold_action("move_down", 10)
	var stopped_at := player.global_position
	await physics_frames(10)
	check_eq(player.global_position, stopped_at, "player position after release")


func test_walls_keep_player_inside_arena() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var player := main.get_node("Player") as Node2D
	await hold_action("move_left", 240)
	check(
		player.global_position.x >= 32.0,
		"player passed the left wall: x=%.1f" % player.global_position.x
	)


func test_snapshot_reports_player_position() -> void:
	await spawn("res://scenes/main.tscn")
	var state: Dictionary = GameState.snapshot()
	check(state.has("player_position"), "snapshot should include player_position")
	check_eq(state.get("player_position"), [480, 270], "player starts in the arena centre")
