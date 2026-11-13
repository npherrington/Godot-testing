extends SceneTree
## Harness for bin/check.sh's scenes step: loads and instances every scene passed after `--`,
## then frees it, and exits 1 if any fails. Instancing outside the tree runs no _ready(), so this
## only checks the file. Godot reports some broken scenes only as a warning ("Parent path ... has
## vanished") and drops the node; bin/check.sh fails on those lines too.


func _initialize() -> void:
	var bad := 0
	for path in OS.get_cmdline_user_args():
		var problem := _problem_with(path)
		if problem != "":
			print("scene %s: %s" % [path, problem])
			bad += 1
	quit(1 if bad > 0 else 0)


func _problem_with(path: String) -> String:
	var scene := load(path) as PackedScene
	if scene == null:
		return "does not load (the error above says why)"
	var state := scene.get_state()
	var seen: Dictionary[String, bool] = {}
	for i in state.get_node_count():
		var node_path := str(state.get_node_path(i))
		if seen.has(node_path):
			return "two nodes with the same name at %s; sibling names must differ" % node_path
		seen[node_path] = true
	var node := scene.instantiate()
	if node == null:
		return "does not instantiate (the error above says why)"
	node.free()
	return ""
