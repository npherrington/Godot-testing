extends "res://tests/test_case.gd"

const ENEMY_SCENE := "res://scenes/enemy.tscn"
const ITEM_SCENE := "res://scenes/item.tscn"


func _start() -> Node:
	var main: Node = await spawn("res://scenes/main.tscn")
	for node in tree.get_nodes_in_group("enemies"):
		node.remove_from_group("enemies")
		node.queue_free()
	# These tests are about what gets added: start from an empty pack, not the starting potions.
	GameState.inventory.clear()
	await physics_frames(1)
	return main


func _add_enemy(at: Vector2i) -> Enemy:
	var enemy := (load(ENEMY_SCENE) as PackedScene).instantiate() as Enemy
	enemy.setup(at, "skeleton_warrior")
	enemy.awake = true
	tree.current_scene.get_node("%Enemies").add_child(enemy)
	return enemy


func _drop_item(at: Vector2i, item_id: String) -> Item:
	var item := (load(ITEM_SCENE) as PackedScene).instantiate() as Item
	item.setup(at, item_id)
	tree.current_scene.get_node("%Items").add_child(item)
	return item


func _act(action: String) -> void:
	await hold_action(action, 3)
	await physics_frames(15)


func test_inventory_holds_24_items_and_refuses_the_25th() -> void:
	await _start()
	for i in 24:
		check(GameState.add_item("health_potion"), "item %d fits" % (i + 1))
	check_eq(GameState.inventory.size(), 24, "24 slots filled")
	check(not GameState.add_item("health_potion"), "the 25th does not fit")
	_drop_item(Grid.START + Vector2i(1, 0), "sword")
	await _act("interact")
	check_eq(GameState.inventory.size(), 24, "still 24")
	check_eq(tree.get_nodes_in_group("items").size() > 0, true, "the sword stays on the floor")
	check("Your pack is full." in GameState.combat_log, "full pack is reported")


func test_equipping_a_sword_adds_4_to_attack_and_damage() -> void:
	await _start()
	var bare := GameState.BASE_ATTACK
	check_eq(GameState.get_attack(), bare, "bare-handed attack")
	GameState.add_item("sword")
	check_eq(GameState.equipped_weapon, "sword", "picked-up sword is wielded")
	check_eq(GameState.get_attack(), bare + 4, "sword adds 4")
	var enemy := _add_enemy(Grid.START + Vector2i(1, 0))
	await physics_frames(1)
	await _act("attack")
	check_eq(enemy.health, enemy.max_health - (bare + 4), "the hit uses the sword's attack")
	GameState.equip(0)
	check_eq(GameState.get_attack(), bare, "putting the sword away removes the bonus")


func test_equipping_a_shield_adds_2_defense_and_cuts_damage() -> void:
	await _start()
	GameState.add_item("shield")
	check_eq(GameState.equipped_armor, "shield", "shield equipped")
	check_eq(GameState.get_defense(), 2, "shield adds 2 defense")
	var enemy := _add_enemy(Grid.START + Vector2i(1, 0))
	enemy.damage_min = 8
	enemy.damage_max = 8
	await physics_frames(1)
	await _act("attack")
	check_eq(GameState.health, 94, "an 8 hit lands as 6")
	GameState.equip(0)
	check_eq(GameState.get_defense(), 0, "shield off")
	await _act("attack")
	check_eq(GameState.health, 86, "an 8 hit lands as 8 without it")


func test_health_potion_heals_40_and_is_used_up() -> void:
	await _start()
	GameState.health = 50
	GameState.add_item("health_potion")
	await _act("inventory")
	check_eq(GameState.menu, "inventory", "inventory open")
	await _act("interact")
	check_eq(GameState.health, 90, "healed 40")
	check(GameState.inventory.is_empty(), "the potion is used up")
	check_eq(GameState.menu, "", "the menu closes")
	check_eq(GameState.turn, 2, "drinking took the turn")
	GameState.health = 95
	check_eq(GameState.heal(40), 5, "healing stops at max health")


func test_interact_picks_up_an_adjacent_item() -> void:
	await _start()
	var before := tree.get_nodes_in_group("items").size()
	_drop_item(Grid.START + Vector2i(1, 1), "shield")
	await physics_frames(1)
	await _act("interact")
	check_eq(GameState.inventory, ["shield"] as Array[String], "the shield is in the pack")
	check_eq(tree.get_nodes_in_group("items").size(), before, "and gone from the floor")
	check("You pick up the Shield." in GameState.combat_log, "pickup is logged")
	check_eq(GameState.turn, 2, "picking up takes the turn")


func test_items_out_of_reach_stay() -> void:
	await _start()
	var item := _drop_item(Grid.START + Vector2i(2, 0), "sword")
	await physics_frames(1)
	await _act("interact")
	check(GameState.inventory.is_empty(), "nothing picked up from 2 cells away")
	check(item.is_in_group("items"), "the item stays")
	check_eq(GameState.turn, 1, "no turn spent")


func test_dungeon_has_sword_shield_and_potions_at_start() -> void:
	await spawn("res://scenes/main.tscn")
	var dungeon := tree.get_first_node_in_group("dungeon") as Dungeon
	var counts: Dictionary[String, int] = {}
	for node in tree.get_nodes_in_group("items"):
		var item := node as Item
		var seen: int = counts.get(item.item_id, 0)
		counts[item.item_id] = seen + 1
		check(dungeon.is_walkable(item.cell), "item on floor at %s" % item.cell)
	check_eq(counts.get("sword", 0), 1, "one sword")
	check_eq(counts.get("shield", 0), 1, "one shield")
	var potions: int = counts.get("health_potion", 0)
	check(potions >= 3, "potions to find")
	var listed: Array = GameState.snapshot()["items"]
	check_eq(listed.size(), 7, "items in the snapshot")


func test_inventory_panel_lists_items() -> void:
	var main := await _start()
	GameState.add_item("sword")
	GameState.add_item("health_potion")
	var panel := main.get_node("HUD").get_node("%InventoryPanel") as Control
	check(not panel.visible, "hidden until opened")
	await _act("inventory")
	check(panel.is_visible_in_tree(), "inventory key opens it")
	var slots := main.get_node("HUD").get_node("%Slots")
	check_eq(slots.get_child_count(), 24, "24 slots drawn")
	var first := slots.get_child(0).get_child(0) as TextureRect
	var third := slots.get_child(2).get_child(0) as TextureRect
	check(first.texture != null, "the sword's icon is shown")
	check(third.texture == null, "an empty slot is empty")
	var details := main.get_node("HUD").get_node("%Details") as Label
	check("Sword" in details.text and "equipped" in details.text, "details: %s" % details.text)
	await _act("move_right")
	check_eq(GameState.menu_index, 1, "the cursor moves")
	check(GameState.can_player_act() == false, "the player waits while it is open")
	check_eq(GameState.player_cell, Grid.START, "moving the cursor did not move the player")
	await _act("inventory")
	check(not panel.visible, "inventory key closes it")


func test_player_starts_with_two_potions() -> void:
	await spawn("res://scenes/main.tscn")
	check_eq(
		GameState.inventory,
		["health_potion", "health_potion"] as Array[String],
		"two potions in the pack at the start"
	)
	check_eq(GameState.equipped_weapon, "", "no weapon yet")
