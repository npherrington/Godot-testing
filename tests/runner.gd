extends SceneTree
## Headless test runner. Run through bin/test.sh, not directly.
## Finds tests/test_*.gd, runs every test_* method, prints PASS/FAIL lines and a
## summary, and exits 1 when anything failed. Pass `-- --filter=<text>` to run only
## files or methods whose name contains <text>.

const TestCase := preload("res://tests/test_case.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var filter := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--filter="):
			filter = arg.trim_prefix("--filter=")

	var files: Array[String] = []
	for file in DirAccess.get_files_at("res://tests"):
		if file.begins_with("test_") and file.ends_with(".gd") and file != "test_case.gd":
			files.append(file)
	files.sort()

	var passed := 0
	var failed := 0
	for file in files:
		var script := load("res://tests/" + file) as GDScript
		if script == null or not script.can_instantiate():
			print("FAIL %s: does not load (parse error above?)" % file)
			failed += 1
			continue
		var methods: Array[String] = []
		for method in script.get_script_method_list():
			var method_name: String = method["name"]
			if not method_name.begins_with("test_") or method_name in methods:
				continue
			if filter == "" or filter in file or filter in method_name:
				methods.append(method_name)
		for method_name in methods:
			var case: TestCase = script.new()
			case.tree = self
			await case.before_each()
			await case.call(method_name)
			await case.after_each()
			if case.failures.is_empty():
				passed += 1
				print("PASS %s::%s" % [file, method_name])
			else:
				failed += 1
				for message in case.failures:
					print("FAIL %s::%s: %s" % [file, method_name, message])

	print("\n%d passed, %d failed" % [passed, failed])
	quit(1 if failed > 0 else 0)
