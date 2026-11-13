extends SceneTree
## Harness for bin/check.sh's parse step: compiles every script passed after `--`, with the
## project's autoloads available, and exits 1 if any fails. The engine prints each error.


func _initialize() -> void:
	var bad := 0
	for path in OS.get_cmdline_user_args():
		var script := load(path) as Script
		if script == null or not script.can_instantiate():
			print("does not compile: %s" % path)
			bad += 1
	quit(1 if bad > 0 else 0)
