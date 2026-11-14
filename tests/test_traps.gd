extends "res://tests/test_case.gd"

const TRAP_SCENE := "res://scenes/trap.tscn"


func _start() -> void:
	await spawn("res://scenes/main.tscn")
	for group: String in ["enemies", "traps"]:
		for node in tree.get_nodes_in_group(group):
			node.remove_from_group(group)
			node.queue_free()
	await physics_frames(1)


func _add_trap(at: Vector2i, kind: String) -> Trap:
	var trap := (load(TRAP_SCENE) as PackedScene).instantiate() as Trap
	trap.setup(at, kind)
	tree.current_scene.get_node("%Traps").add_child(trap)
	return trap


func _act(action: String) -> void:
	await hold_action(action, 3)
	await physics_frames(15)


func test_both_trap_kinds_exist_on_the_floor_at_start() -> void:
	await spawn("res://scenes/main.tscn")
	var dungeon := tree.get_first_node_in_group("dungeon") as Dungeon
	var kinds: Dictionary[String, int] = {}
	for node in tree.get_nodes_in_group("traps"):
		var trap := node as Trap
		var seen: int = kinds.get(trap.kind, 0)
		kinds[trap.kind] = seen + 1
		check(dungeon.is_walkable(trap.cell), "trap on floor at %s" % trap.cell)
		check(trap.is_armed(), "armed at start")
		check(Grid.distance(trap.cell, Grid.START) >= 6, "not next to the start")
	check(kinds.has("pressure_plate"), "pressure plates placed")
	check(kinds.has("spike_wall"), "spike walls placed")
	var listed: Array = GameState.snapshot()["traps"]
	check_eq(listed.size(), 6, "traps in the snapshot")


func test_stepping_next_to_a_trap_fires_it() -> void:
	await _start()
	var trap := _add_trap(Grid.START + Vector2i(2, 1), "spike_wall")
	await physics_frames(1)
	await _act("move_right")
	check(not trap.is_armed(), "the trap fired")
	check_eq(trap.cooldown, Trap.COOLDOWN_TURNS - 1, "cooldown started (one round ticked)")
	check_eq(GameState.traps_triggered, 1, "one activation")
	check(GameState.combat_log[-1].begins_with("Spike wall fires!"), "logged")


func test_a_trap_two_cells_away_stays_armed() -> void:
	await _start()
	var trap := _add_trap(Grid.START + Vector2i(3, 0), "pressure_plate")
	await physics_frames(1)
	await _act("move_right")
	check(trap.is_armed(), "two cells away: no activation")
	check_eq(GameState.health, 100, "no damage")


func test_firing_shows_particles_and_the_fired_sprite() -> void:
	await _start()
	var trap := _add_trap(Grid.START + Vector2i(1, -1), "pressure_plate")
	await physics_frames(1)
	check(not trap.is_showing_fired(), "armed sprite before")
	await hold_action("move_up", 3)
	await physics_frames(2)
	var burst := trap.get_node("Burst") as CPUParticles2D
	check(burst.emitting, "the particle burst plays")
	check(trap.is_showing_fired(), "the plate shows pressed")


func test_a_trap_hits_for_10_to_15() -> void:
	await _start()
	GameState.add_item("shield")
	_add_trap(Grid.START + Vector2i(2, 0), "spike_wall")
	await physics_frames(1)
	await _act("move_right")
	var lost := 100 - GameState.health
	check(lost >= 10 and lost <= 15, "trap damage 10-15 through armor, took %d" % lost)


func test_a_trap_rearms_after_10_turns_and_fires_again() -> void:
	await _start()
	var trap := _add_trap(Grid.START + Vector2i(2, 0), "pressure_plate")
	await physics_frames(1)
	await _act("move_right")
	var fired_on := GameState.turn - 1
	for i in 8:
		await _act("defend")
	check(not trap.is_armed(), "still cooling down after 9 turns")
	await _act("defend")
	check(trap.is_armed(), "re-armed 10 turns after it fired")
	check_eq(GameState.turn, fired_on + 10, "on turn %d" % (fired_on + 10))
	check(not trap.is_showing_fired(), "sprite reset")
	await _act("move_left")
	await _act("move_right")
	check_eq(GameState.traps_triggered, 2, "fires again when the player comes back")
