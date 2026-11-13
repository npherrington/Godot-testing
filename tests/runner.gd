extends SceneTree
## Headless test runner. Run through bin/test.sh, not directly.
## Finds tests/test_*.gd, runs every test_* method, prints PASS/FAIL lines and a
## summary, and exits 1 when anything failed or no test ran. Pass `-- --filter=<text>` to run
## only files or methods whose name contains <text>.
## A test still running after FRAME_LIMIT physics frames (or `-- --frame-limit=<n>`) fails, and
## the run stops there: the stuck test may still resume later and would disturb the next one.

const TestCase := preload("res://tests/test_case.gd")
## 60 s of game time at the --fixed-fps 60 that bin/test.sh uses.
const FRAME_LIMIT := 3600


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var filter := ""
	var frame_limit := FRAME_LIMIT
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--filter="):
			filter = arg.trim_prefix("--filter=")
		elif arg.begins_with("--frame-limit="):
			frame_limit = arg.trim_prefix("--frame-limit=").to_int()

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
			if not await _finishes_within(case, method_name, frame_limit):
				failed += 1
				var stuck := "still running after %d physics frames" % frame_limit
				print("FAIL %s::%s: %s; stopping the run here" % [file, method_name, stuck])
				print("\n%d passed, %d failed, run stopped early" % [passed, failed])
				quit(1)
				return
			await case.after_each()
			if case.failures.is_empty():
				passed += 1
				print("PASS %s::%s" % [file, method_name])
			else:
				failed += 1
				for message in case.failures:
					print("FAIL %s::%s: %s" % [file, method_name, message])

	print("\n%d passed, %d failed" % [passed, failed])
	if passed + failed == 0:
		print("FAIL no tests ran%s" % (" (nothing matches '%s')" % filter if filter else ""))
		quit(1)
		return
	quit(1 if failed > 0 else 0)


## Runs one test method, stepping physics frames while it awaits. Returns false if it is still
## running after frame_limit frames. A test that never awaits finishes before this checks.
func _finishes_within(case: TestCase, method_name: String, frame_limit: int) -> bool:
	var state := {"done": false}
	var run_test := func() -> void:
		await case.call(method_name)
		state["done"] = true
	run_test.call()
	var frames := 0
	while not state["done"]:
		if frames >= frame_limit:
			return false
		await physics_frame
		frames += 1
	return true
