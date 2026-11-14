extends CanvasLayer
## On-screen information and menus: health bar, status icons, turn indicator, combat log, the
## inventory screen and the pause menu. Redraws when GameState changes. Menu keys are read here;
## the player ignores input while a menu is open. Art and font follow art/ui/NOTES.md.

const LOG_LINES := 6
const FONT := preload("res://assets/fonts/font_dungeon.fnt")
const FONT_OUTLINE := preload("res://assets/fonts/font_dungeon_outline.fnt")
const SLOT_PATH := "res://assets/sprites/ui/ui_inventory_slot_%s.png"
const BUTTON_PATH := "res://assets/sprites/ui/ui_button_%s.png"
const FRAME_PATH := "res://assets/sprites/ui/ui_panel_frame.png"
const STATUS_ICON_PATH := "res://assets/sprites/ui/ui_status_%s.png"
## Top-left of each inventory slot inside the panel art (assets/animations/ui.json).
const SLOT_ORIGIN := Vector2(8, 24)
const SLOT_PITCH := 22.0
const COLUMNS := 6
const PAUSE_OPTIONS: Array[String] = ["Resume", "Save Game", "Load Game", "Restart", "Quit"]
const MENU_ACTIONS: Array[String] = [
	"inventory", "pause", "interact", "move_up", "move_down", "move_left", "move_right"
]
## Palette colours (art/pixel.py): W text, Y gold, F hurt, E poison, C frost.
const WHITE := Color("ece8d8")
const GOLD := Color("fad24c")
const HURT := Color("e27876")
const STATUS_LOOK: Dictionary[String, Array] = {
	"poison": ["Poisoned", Color("94c64c")],
	"freeze": ["Frozen", Color("5eaadc")],
}

var _was_down: Dictionary[String, bool] = {}
var _slots: Array[TextureRect] = []
var _icons: Array[TextureRect] = []
var _marks: Array[Label] = []
var _buttons: Array[Button] = []
var _normal_style: StyleBoxTexture
var _hover_style: StyleBoxTexture
var _shown_health := -1
var _shown_statuses := ""
var _damage_tween: Tween

@onready var _root: Control = $Root
@onready var _health_bar: TextureProgressBar = %HealthBar
@onready var _damage_bar: TextureProgressBar = %DamageBar
@onready var _health_flash: AnimatedSprite2D = %HealthFlash
@onready var _health_label: Label = %HealthLabel
@onready var _stats: Label = %StatsLabel
@onready var _status_panel: PanelContainer = %StatusPanel
@onready var _status_list: VBoxContainer = %StatusList
@onready var _turn_label: Label = %TurnLabel
@onready var _combat_log: Label = %CombatLog
@onready var _game_over: Label = %GameOverLabel
@onready var _inventory: TextureRect = %InventoryPanel
@onready var _slot_root: Control = %Slots
@onready var _highlight: AnimatedSprite2D = %Highlight
@onready var _details: Label = %Details
@onready var _pause_menu: Control = %PauseMenu
@onready var _button_box: VBoxContainer = %Buttons
@onready var _message: Label = %Message
@onready var _cursor: AnimatedSprite2D = %Cursor


func _ready() -> void:
	_root.theme = _make_theme()
	for label: Label in [_combat_log, _game_over, _details, %ControlsHint]:
		label.add_theme_font_override("font", FONT_OUTLINE)
	_health_flash.animation_finished.connect(_health_flash.hide)
	_build_slots()
	_build_pause_buttons()
	_highlight.play("default")
	_cursor.play("default")
	GameState.changed.connect(refresh)
	refresh()


func _physics_process(_delta: float) -> void:
	var pressed: Dictionary[String, bool] = {}
	for action in MENU_ACTIONS:
		var down := Input.is_action_pressed(action)
		pressed[action] = down and not _was_down.get(action, false)
		_was_down[action] = down
	if GameState.game_over:
		if pressed["interact"]:
			_return_from_death()
	elif GameState.menu == "inventory":
		_inventory_input(pressed)
	elif GameState.menu == "pause":
		_pause_input(pressed)
	elif GameState.menu == "" and GameState.phase == "player":
		if pressed["inventory"]:
			GameState.set_menu("inventory")
		elif pressed["pause"]:
			GameState.menu_message = ""
			GameState.set_menu("pause")


func refresh() -> void:
	_refresh_health()
	_refresh_statuses()
	var players_turn := GameState.phase == "player"
	_turn_label.text = (
		"Turn %d - %s" % [GameState.turn, "Your turn" if players_turn else "Enemy turn"]
	)
	_turn_label.add_theme_color_override("font_color", GOLD if players_turn else HURT)
	var lines := GameState.combat_log.slice(maxi(0, GameState.combat_log.size() - LOG_LINES))
	_combat_log.text = "\n".join(lines)
	_game_over.visible = GameState.game_over
	var back_to := "return to the checkpoint" if GameState.checkpoint_reached else "try again"
	_game_over.text = "You have fallen.\nPress F to %s." % back_to
	_stats.text = (
		"ATK %d  DEF %d  Pack %d/%d"
		% [
			GameState.get_attack(),
			GameState.get_defense(),
			GameState.inventory.size(),
			GameState.INVENTORY_SIZE
		]
	)
	_refresh_inventory()
	_refresh_pause_menu()


## Pick a pause menu option by its index in PAUSE_OPTIONS.
func choose_pause_option(index: int) -> void:
	match PAUSE_OPTIONS[index]:
		"Resume":
			GameState.set_menu("")
		"Save Game":
			var saved := SaveSystem.save_game(GameState.save_path)
			GameState.menu_message = "Game saved." if saved else "Could not save."
			GameState.changed.emit()
		"Load Game":
			if SaveSystem.load_game(GameState.save_path):
				GameState.log_message("Game loaded.")
			else:
				GameState.menu_message = "No saved game yet."
				GameState.changed.emit()
		"Restart":
			get_tree().reload_current_scene()
		"Quit":
			get_tree().quit()


## The bar drops at once; the pale damage chunk behind it drains a moment later, with a flash.
func _refresh_health() -> void:
	_health_bar.max_value = GameState.max_health
	_damage_bar.max_value = GameState.max_health
	_health_label.text = "%d/%d" % [GameState.health, GameState.max_health]
	if GameState.health == _shown_health:
		return
	var hurt := _shown_health >= 0 and GameState.health < _shown_health
	_shown_health = GameState.health
	_health_bar.value = GameState.health
	if _damage_tween and _damage_tween.is_valid():
		_damage_tween.kill()
	if not hurt:
		_damage_bar.value = GameState.health
		return
	_damage_tween = create_tween()
	_damage_tween.tween_interval(0.3)
	_damage_tween.tween_property(_damage_bar, "value", float(GameState.health), 0.4)
	_health_flash.show()
	_health_flash.play("default")


func _refresh_statuses() -> void:
	var key := str(GameState.statuses)
	if key == _shown_statuses:
		return
	_shown_statuses = key
	for row: Node in _status_list.get_children().slice(1):
		_status_list.remove_child(row)
		row.queue_free()
	for status: String in GameState.statuses:
		var look: Array = STATUS_LOOK.get(status, [status.capitalize(), WHITE])
		var row := HBoxContainer.new()
		row.name = status.capitalize()
		row.add_theme_constant_override("separation", 4)
		var icon := TextureRect.new()
		icon.name = "Icon"
		var icon_path := STATUS_ICON_PATH % status
		if ResourceLoader.exists(icon_path):
			icon.texture = load(icon_path) as Texture2D
		icon.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
		row.add_child(icon)
		var label := Label.new()
		label.name = "Text"
		var title: String = look[0]
		label.text = "%s %d" % [title, GameState.statuses[status]]
		var colour: Color = look[1]
		label.add_theme_color_override("font_color", colour)
		row.add_child(label)
		_status_list.add_child(row)
	_status_panel.visible = not GameState.statuses.is_empty()
	_status_panel.reset_size()


func _pause_input(pressed: Dictionary[String, bool]) -> void:
	if pressed["pause"]:
		GameState.set_menu("")
		return
	var index := GameState.menu_index
	if pressed["move_down"]:
		index = (index + 1) % PAUSE_OPTIONS.size()
	if pressed["move_up"]:
		index = (index - 1 + PAUSE_OPTIONS.size()) % PAUSE_OPTIONS.size()
	if index != GameState.menu_index:
		GameState.menu_index = index
		GameState.changed.emit()
	if pressed["interact"]:
		choose_pause_option(GameState.menu_index)


func _return_from_death() -> void:
	if GameState.checkpoint_reached and SaveSystem.load_game(GameState.checkpoint_path):
		GameState.log_message("You wake at the checkpoint.")
	else:
		get_tree().reload_current_scene()


func _make_theme() -> Theme:
	var theme := Theme.new()
	theme.default_font = FONT
	theme.default_font_size = 16
	theme.set_color("font_color", "Label", WHITE)
	theme.set_stylebox("panel", "PanelContainer", _box(FRAME_PATH, 8, [8, 6, 8, 6]))
	_normal_style = _box(BUTTON_PATH % "normal", 4, [4, 3, 4, 3])
	_hover_style = _box(BUTTON_PATH % "hover", 4, [4, 3, 4, 3])
	theme.set_stylebox("normal", "Button", _normal_style)
	theme.set_stylebox("hover", "Button", _hover_style)
	theme.set_stylebox("pressed", "Button", _box(BUTTON_PATH % "pressed", 4, [4, 4, 4, 2]))
	theme.set_stylebox("disabled", "Button", _box(BUTTON_PATH % "disabled", 4, [4, 3, 4, 3]))
	theme.set_color("font_color", "Button", WHITE)
	theme.set_color("font_hover_color", "Button", GOLD)
	theme.set_color("font_pressed_color", "Button", GOLD)
	return theme


func _box(path: String, margin: int, content: Array[int]) -> StyleBoxTexture:
	var box := StyleBoxTexture.new()
	box.texture = load(path) as Texture2D
	box.texture_margin_left = margin
	box.texture_margin_top = margin
	box.texture_margin_right = margin
	box.texture_margin_bottom = margin
	box.content_margin_left = content[0]
	box.content_margin_top = content[1]
	box.content_margin_right = content[2]
	box.content_margin_bottom = content[3]
	return box


func _build_pause_buttons() -> void:
	for i in PAUSE_OPTIONS.size():
		var button := Button.new()
		button.name = PAUSE_OPTIONS[i].replace(" ", "") + "Button"
		button.text = PAUSE_OPTIONS[i]
		button.focus_mode = Control.FOCUS_NONE
		button.custom_minimum_size = Vector2(0, 20)
		button.pressed.connect(choose_pause_option.bind(i))
		_button_box.add_child(button)
		_buttons.append(button)


func _refresh_pause_menu() -> void:
	_pause_menu.visible = GameState.menu == "pause"
	for i in _buttons.size():
		var selected := i == GameState.menu_index and GameState.menu == "pause"
		_buttons[i].add_theme_stylebox_override(
			"normal", _hover_style if selected else _normal_style
		)
		_buttons[i].add_theme_color_override("font_color", GOLD if selected else WHITE)
	_message.text = GameState.menu_message
	if _pause_menu.visible:
		_place_cursor.call_deferred()


## Point the cursor's tip (8, 4) just left of the selected button.
func _place_cursor() -> void:
	if GameState.menu_index >= _buttons.size():
		return
	var button := _buttons[GameState.menu_index]
	var target := button.global_position - _pause_menu.global_position
	_cursor.position = target + Vector2(-11, roundf(button.size.y / 2.0) - 4)


func _inventory_input(pressed: Dictionary[String, bool]) -> void:
	if pressed["inventory"] or pressed["pause"]:
		GameState.set_menu("")
		return
	var index := GameState.menu_index
	if pressed["move_right"]:
		index += 1
	if pressed["move_left"]:
		index -= 1
	if pressed["move_down"]:
		index += COLUMNS
	if pressed["move_up"]:
		index -= COLUMNS
	_select_slot(clampi(index, 0, GameState.INVENTORY_SIZE - 1))
	if pressed["interact"]:
		_use_selected()


func _select_slot(index: int) -> void:
	if index != GameState.menu_index:
		GameState.menu_index = index
		GameState.changed.emit()


## Equip or take off a weapon or armor (free), or drink a potion (closes the menu and takes
## the turn).
func _use_selected() -> void:
	var index := GameState.menu_index
	if index >= GameState.inventory.size():
		return
	var item_id := GameState.inventory[index]
	if ItemDatabase.kind(item_id) != "consumable":
		GameState.equip(index)
		return
	GameState.set_menu("")
	var turns := get_tree().get_first_node_in_group("turn_manager") as TurnManager
	var player := get_tree().get_first_node_in_group("player")
	if turns:
		turns.player_action({"type": "use", "actor": player, "index": index})


func _build_slots() -> void:
	var normal := load(SLOT_PATH % "normal") as Texture2D
	for i in GameState.INVENTORY_SIZE:
		var slot := TextureRect.new()
		slot.texture = normal
		slot.position = _slot_position(i)
		slot.gui_input.connect(_on_slot_input.bind(i))
		_slot_root.add_child(slot)
		var icon := TextureRect.new()
		icon.position = Vector2(2, 2)
		icon.size = Vector2(16, 16)
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		slot.add_child(icon)
		var mark := Label.new()
		mark.text = "E"
		mark.position = Vector2(13, 8)
		mark.mouse_filter = Control.MOUSE_FILTER_IGNORE
		mark.add_theme_font_override("font", FONT_OUTLINE)
		mark.add_theme_color_override("font_color", GOLD)
		slot.add_child(mark)
		_slots.append(slot)
		_icons.append(icon)
		_marks.append(mark)


## Click a slot to select it; click the selected one again to use it.
func _on_slot_input(event: InputEvent, index: int) -> void:
	var click := event as InputEventMouseButton
	if click == null or not click.pressed or click.button_index != MOUSE_BUTTON_LEFT:
		return
	if index == GameState.menu_index:
		_use_selected()
	else:
		_select_slot(index)


func _refresh_inventory() -> void:
	_inventory.visible = GameState.menu == "inventory"
	if _slots.is_empty():
		return
	for i in _slots.size():
		var item_id := GameState.inventory[i] if i < GameState.inventory.size() else ""
		_icons[i].texture = ItemDatabase.icon(item_id) if item_id != "" else null
		_marks[i].visible = GameState.is_equipped(item_id)
	var index := GameState.menu_index
	_highlight.position = _slot_position(index) - Vector2(2, 2)
	if index < GameState.inventory.size():
		var item_id := GameState.inventory[index]
		var worn := " (equipped)" if GameState.is_equipped(item_id) else ""
		_details.text = (
			"%s - %s%s\nF: use / equip    I: close"
			% [ItemDatabase.item_name(item_id), ItemDatabase.description(item_id), worn]
		)
	else:
		_details.text = "Empty slot\nI: close"


func _slot_position(index: int) -> Vector2:
	return SLOT_ORIGIN + Vector2(index % COLUMNS, floori(index / float(COLUMNS))) * SLOT_PITCH
