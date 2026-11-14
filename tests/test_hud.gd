extends "res://tests/test_case.gd"


func _start() -> Node:
	var main: Node = await spawn("res://scenes/main.tscn")
	for node in tree.get_nodes_in_group("enemies"):
		node.remove_from_group("enemies")
		node.queue_free()
	GameState.inventory.clear()
	await physics_frames(2)
	return main


func _hud(main: Node, unique: String) -> Node:
	return main.get_node("HUD").get_node("%" + unique)


func _act(action: String) -> void:
	await hold_action(action, 3)
	await physics_frames(15)


func test_health_bar_top_left_shows_0_to_100() -> void:
	var main := await _start()
	var bar := _hud(main, "HealthBar") as TextureProgressBar
	var label := _hud(main, "HealthLabel") as Label
	check(bar.is_visible_in_tree(), "health bar visible")
	var rect := bar.get_global_rect()
	check(rect.position.x < 120 and rect.position.y < 60, "top-left, at %s" % rect.position)
	check_eq(bar.min_value, 0.0, "from 0")
	check_eq(bar.max_value, 100.0, "to 100")
	check_eq(bar.value, 100.0, "full at start")
	check_eq(label.text, "100/100", "number beside it")
	GameState.damage_player(30, true)
	await physics_frames(2)
	check_eq(bar.value, 70.0, "drops with health")
	check_eq(label.text, "70/100", "number follows")
	var damage := _hud(main, "DamageBar") as TextureProgressBar
	check(damage.value > 70.0, "the damage chunk lags behind")
	await physics_frames(60)
	check_eq(damage.value, 70.0, "then drains")
	GameState.heal(100)
	await physics_frames(2)
	check_eq(bar.value, 100.0, "back to full")


func test_turn_indicator_is_centre_bottom_and_changes_colour() -> void:
	var main := await _start()
	var label := _hud(main, "TurnLabel") as Label
	var rect := label.get_global_rect()
	check(absf(rect.get_center().x - 480.0) < 20.0, "centred, at %.0f" % rect.get_center().x)
	check(rect.position.y > 480.0, "at the bottom, at %.0f" % rect.position.y)
	var players := label.get_theme_color("font_color")
	await hold_action("move_right", 3)
	await physics_frames(1)
	check_eq(label.text, "Turn 1 - Enemy turn", "enemy turn shown")
	check(label.get_theme_color("font_color") != players, "a different colour for the enemies")


func test_inventory_screen_shows_each_item_icon_and_equipped_mark() -> void:
	var main := await _start()
	for item_id: String in ["sword", "shield", "health_potion"]:
		GameState.add_item(item_id)
	await _act("inventory")
	check((_hud(main, "InventoryPanel") as Control).is_visible_in_tree(), "inventory open")
	var slots := _hud(main, "Slots")
	for i in 3:
		var icon := slots.get_child(i).get_child(0) as TextureRect
		check_eq(icon.texture, ItemDatabase.icon(GameState.inventory[i]), "icon in slot %d" % i)
	check((slots.get_child(0).get_child(1) as Label).visible, "sword marked equipped")
	check((slots.get_child(1).get_child(1) as Label).visible, "shield marked equipped")
	check(not (slots.get_child(2).get_child(1) as Label).visible, "potion not marked")


func test_status_icons_show_on_the_right_for_poison_and_freeze() -> void:
	var main := await _start()
	var panel := _hud(main, "StatusPanel") as Control
	check(not panel.visible, "hidden with no status")
	GameState.apply_status("poison", 3)
	GameState.apply_status("freeze", 1)
	await physics_frames(2)
	check(panel.is_visible_in_tree(), "shown with a status")
	check(panel.get_global_rect().position.x > 700.0, "on the right side")
	var list := _hud(main, "StatusList")
	var rows: Array[String] = []
	for row: Node in list.get_children().slice(1):
		var icon := row.get_node("Icon") as TextureRect
		var text := (row.get_node("Text") as Label).text
		rows.append(text)
		check(icon.texture != null, "icon for %s" % text)
	check_eq(rows, ["Poisoned 3", "Frozen 1"] as Array[String], "one row per status")
	var poison_icon := list.get_child(1).get_node("Icon") as TextureRect
	check(poison_icon.texture.resource_path.ends_with("ui_status_poison.png"), "poison icon")
	GameState.statuses.clear()
	GameState.changed.emit()
	await physics_frames(2)
	check(not panel.visible, "hidden again")


func test_pause_menu_wraps_and_the_cursor_follows() -> void:
	var main := await _start()
	await _act("pause")
	var buttons := _hud(main, "Buttons")
	var cursor := _hud(main, "Cursor") as Node2D
	var menu := _hud(main, "PauseMenu") as Control
	await physics_frames(2)
	var first_y := cursor.position.y
	await _act("move_up")
	check_eq(GameState.menu_index, 4, "up from the top wraps to Quit")
	await _act("move_down")
	check_eq(GameState.menu_index, 0, "down from Quit wraps to Resume")
	await _act("move_down")
	await physics_frames(2)
	var second := buttons.get_child(1) as Button
	var expected_y := second.global_position.y - menu.global_position.y
	check(cursor.position.y > first_y, "the cursor moved down")
	check(absf(cursor.position.y - expected_y - (second.size.y / 2.0 - 4.0)) <= 1.0, "beside it")
	check_eq(second.get_theme_color("font_color"), Color("fad24c"), "selected option is gold")


func test_clicking_resume_closes_the_menu() -> void:
	var main := await _start()
	await _act("pause")
	var resume := _hud(main, "Buttons").get_child(0) as Button
	resume.pressed.emit()
	await physics_frames(2)
	check_eq(GameState.menu, "", "Resume closes the menu")
	await _act("move_right")
	check_eq(GameState.player_cell, Grid.START + Vector2i(1, 0), "and play continues")


func test_hud_text_uses_the_pixel_font() -> void:
	var main := await _start()
	for unique: String in ["TurnLabel", "CombatLog", "StatsLabel", "HealthLabel", "Details"]:
		var label := _hud(main, unique) as Label
		var font := label.get_theme_font("font")
		check(font != null and "font_dungeon" in font.resource_path, "%s pixel font" % unique)
	var button := _hud(main, "Buttons").get_child(0) as Button
	check("font_dungeon" in button.get_theme_font("font").resource_path, "buttons too")
