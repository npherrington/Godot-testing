extends "res://tests/test_case.gd"

const ACTIONS: Array[String] = [
	"move_up",
	"move_down",
	"move_left",
	"move_right",
	"move_up_left",
	"move_up_right",
	"move_down_left",
	"move_down_right",
	"attack",
	"defend",
	"interact",
	"inventory",
	"pause",
]

const STRICT_WARNINGS: Array[String] = [
	"untyped_declaration",
	"unsafe_property_access",
	"unsafe_call_argument",
	"unsafe_cast",
	"missing_await",
]


func test_project_is_configured_for_godot_4_7() -> void:
	var project_name := str(ProjectSettings.get_setting("application/config/name"))
	check(project_name != "" and project_name != "Godot Lab", "project has its own name")
	var features: PackedStringArray = ProjectSettings.get_setting("application/config/features")
	check("4.7" in features, "config/features should include 4.7, got %s" % str(features))
	check_eq(
		ProjectSettings.get_setting("application/run/main_scene"),
		"res://scenes/main.tscn",
		"main scene"
	)


func test_movement_and_control_actions_exist() -> void:
	for action in ACTIONS:
		check(InputMap.has_action(action), "input action %s should exist" % action)
		if InputMap.has_action(action):
			check(not InputMap.action_get_events(action).is_empty(), "%s has a key" % action)


func test_main_scene_has_world_player_and_hud() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var world := main.get_node_or_null("World") as Node2D
	check(world != null, "Main should have a World node")
	check(main.get_node_or_null("HUD") is CanvasLayer, "Main should have a HUD CanvasLayer")
	var players := tree.get_nodes_in_group("player")
	check_eq(players.size(), 1, "one player in the scene")
	if world != null and players.size() == 1:
		check(world.is_ancestor_of(players[0]), "player lives under World")


func test_strict_gdscript_warnings_are_errors() -> void:
	for warning in STRICT_WARNINGS:
		var setting := "debug/gdscript/warnings/" + warning
		check_eq(ProjectSettings.get_setting(setting), 2, setting)
