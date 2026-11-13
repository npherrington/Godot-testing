extends RefCounted
## Base class for tests. A test file is tests/test_<thing>.gd that starts with
##     extends "res://tests/test_case.gd"
## and has methods named test_<behaviour>(). Each test method gets a fresh instance.
## Use `await` with spawn(), physics_frames() and hold_action().

var tree: SceneTree
var failures: Array[String] = []
var _spawned: Array[Node] = []


func before_each() -> void:
	pass


func after_each() -> void:
	for action in InputMap.get_actions():
		Input.action_release(action)
	for node in _spawned:
		if is_instance_valid(node):
			node.queue_free()
	_spawned.clear()
	await tree.process_frame


## Instance a scene under the root and wait one frame so _ready() has run.
## Set as_current to make it tree.current_scene, as the game does for the main scene.
func spawn(scene_path: String, as_current := true) -> Node:
	var node: Node = load(scene_path).instantiate()
	tree.root.add_child(node)
	if as_current:
		tree.current_scene = node
	_spawned.append(node)
	await tree.process_frame
	return node


func physics_frames(count: int) -> void:
	for i in count:
		await tree.physics_frame


## Hold an input action (from project.godot [input]) for a number of physics frames.
func hold_action(action: String, frames: int) -> void:
	Input.action_press(action)
	await physics_frames(frames)
	Input.action_release(action)


## Press and release an action, as a single tap.
func tap_action(action: String) -> void:
	await hold_action(action, 1)
	await physics_frames(1)


func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)


func check_eq(actual: Variant, expected: Variant, message: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [message, str(expected), str(actual)])
