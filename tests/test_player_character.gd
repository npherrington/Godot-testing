extends "res://tests/test_case.gd"


func _player() -> Player:
	return tree.get_first_node_in_group("player") as Player


func test_player_scene_has_a_sprite_node() -> void:
	var player: Node = await spawn("res://scenes/player.tscn")
	var sprite := player.get_node_or_null("Sprite") as AnimatedSprite2D
	check(sprite != null, "player.tscn should have an AnimatedSprite2D named Sprite")
	if sprite:
		check(sprite.sprite_frames != null, "the sprite has frames loaded")
		check(sprite.visible, "the sprite is visible")


func test_player_has_idle_and_walk_animations_in_eight_directions() -> void:
	await spawn("res://scenes/main.tscn")
	var sprite := _player().get_node("Sprite") as AnimatedSprite2D
	for direction in Grid.NAMES_8:
		for kind: String in ["idle", "walk"]:
			var animation := "%s_%s" % [kind, direction]
			check(sprite.sprite_frames.has_animation(animation), "has %s" % animation)
	check(sprite.animation.begins_with("idle_"), "idle at rest, got %s" % sprite.animation)
	check(sprite.is_playing(), "the idle animation plays")
	await hold_action("move_right", 4)
	check_eq(sprite.animation, &"walk_right", "walk plays while stepping right")
	await physics_frames(20)
	check_eq(sprite.animation, &"idle_right", "back to idle facing right")


func test_holding_two_directions_steps_diagonally() -> void:
	await spawn("res://scenes/main.tscn")
	Input.action_press("move_up")
	Input.action_press("move_right")
	await physics_frames(4)
	Input.action_release("move_up")
	Input.action_release("move_right")
	await physics_frames(10)
	check_eq(GameState.player_cell, Grid.START + Vector2i(1, -1), "one diagonal step up-right")


func test_diagonal_action_steps_diagonally() -> void:
	await spawn("res://scenes/main.tscn")
	await hold_action("move_down_left", 3)
	await physics_frames(10)
	check_eq(GameState.player_cell, Grid.START + Vector2i(-1, 1), "one diagonal step down-left")


func test_one_short_press_moves_exactly_one_cell() -> void:
	await spawn("res://scenes/main.tscn")
	# hold_action shows an action for frames - 1 physics frames, so this is a 2-frame key press.
	await hold_action("move_right", 3)
	await physics_frames(15)
	check_eq(GameState.player_cell, Grid.START + Vector2i(1, 0), "one cell right")
	check_eq(_player().position, Grid.to_world(Grid.START + Vector2i(1, 0)), "snapped to the grid")


func test_wall_blocks_the_player() -> void:
	await spawn("res://scenes/main.tscn")
	var dungeon := tree.get_first_node_in_group("dungeon") as Dungeon
	var room: Rect2i = dungeon.rooms[0]
	var outside := Vector2i(room.position.x - 2, room.position.y)
	check(dungeon.is_wall(outside + Vector2i(1, 0)), "test setup: a room wall to the right")
	_player().place(outside)
	await hold_action("move_right", 30)
	await physics_frames(10)
	check_eq(GameState.player_cell, outside, "the wall stops the player")


func test_player_starts_in_the_centre_with_100_health() -> void:
	await spawn("res://scenes/main.tscn")
	var state := GameState.snapshot()
	check_eq(state.get("player_cell"), [16, 16], "start cell is the arena centre")
	check_eq(state.get("health"), 100, "starting health")
