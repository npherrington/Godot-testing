extends Node2D
## Root of the game scene. Builds a run (resets state, places the player, enemies, items, traps,
## checkpoints and torches) and rebuilds the world when a saved game is loaded.

const ENEMY_SCENE := preload("res://scenes/enemy.tscn")
const ITEM_SCENE := preload("res://scenes/item.tscn")
const TRAP_SCENE := preload("res://scenes/trap.tscn")
const CHECKPOINT_SCENE := preload("res://scenes/checkpoint.tscn")
const TORCH_SCENE := preload("res://scenes/wall_torch.tscn")
## Items in the rooms, by room index; then loose potions on random floor cells.
const ROOM_ITEMS: Array[String] = ["sword", "shield", "health_potion", "health_potion"]
const LOOSE_POTIONS := 3
const TRAP_KINDS: Array[String] = [
	"spike_wall", "pressure_plate", "spike_wall", "pressure_plate", "spike_wall", "pressure_plate"
]
const CHECKPOINT_COUNT := 2
## Extra candidate cells, so checkpoints can skip spots right next to a trap.
const SPARE_CELLS := 8
const TORCH_COUNT := 8
const TORCH_GAP := 6
const SPAWN_SEED := 99
## Enemies never start closer than this to the player's start cell.
const SAFE_DISTANCE := 6

@onready var _player: Player = %Player
@onready var _enemies: Node2D = %Enemies
@onready var _items: Node2D = %Items
@onready var _traps: Node2D = %Traps
@onready var _checkpoints: Node2D = %Checkpoints
@onready var _torches: Node2D = %Torches
@onready var _ambience: AudioStreamPlayer = %Ambience
@onready var _turns: TurnManager = %TurnManager
@onready var _dungeon: Dungeon = $World/Dungeon


func _ready() -> void:
	GameState.reset()
	GameState.loaded.connect(_on_loaded)
	_player.place(GameState.player_cell)
	var enemy_count := MonsterDatabase.SPAWN_ORDER.size()
	var traps_from := enemy_count + LOOSE_POTIONS
	var checkpoints_from := traps_from + TRAP_KINDS.size()
	var cells := _spawn_cells(checkpoints_from + CHECKPOINT_COUNT + SPARE_CELLS)
	_spawn_enemies(cells.slice(0, enemy_count))
	_place_items(cells.slice(enemy_count, traps_from))
	_place_traps(cells.slice(traps_from, checkpoints_from))
	_place_checkpoints(cells.slice(checkpoints_from))
	_place_torches()
	_start_ambient_sounds()
	# Everything is placed: let listeners (fog of war, HUD) see the whole new run.
	GameState.changed.emit()


## Looping sounds left playing when the game quits leak their playback; stop them on the way out.
func _exit_tree() -> void:
	_ambience.stop()
	(_player.get_node("TorchSound") as AudioStreamPlayer2D).stop()


## Rebuild everything that lives in the world from a save, in the saved order (enemies act in
## group order, so this keeps the turn order).
func _on_loaded(data: Dictionary) -> void:
	_turns.clear()
	for group: String in ["enemies", "items", "traps", "checkpoints"]:
		for node in get_tree().get_nodes_in_group(group):
			node.remove_from_group(group)
			node.queue_free()
	var saved_enemies: Array = data.get("enemies", [])
	for entry: Dictionary in saved_enemies:
		var enemy := ENEMY_SCENE.instantiate() as Enemy
		enemy.restore(entry)
		_enemies.add_child(enemy)
	var saved_items: Array = data.get("items", [])
	for entry: Dictionary in saved_items:
		var item_id: String = entry.get("id", "")
		_add_item(Grid.from_array(entry.get("cell")), item_id)
	var saved_traps: Array = data.get("traps", [])
	for entry: Dictionary in saved_traps:
		var trap := TRAP_SCENE.instantiate() as Trap
		var kind: String = entry.get("kind", "")
		var cooldown: float = entry.get("cooldown", 0)
		trap.setup(Grid.from_array(entry.get("cell")), kind, roundi(cooldown))
		_traps.add_child(trap)
	var saved_checkpoints: Array = data.get("checkpoints", [])
	for entry: Dictionary in saved_checkpoints:
		_add_checkpoint(Grid.from_array(entry.get("cell")), SaveSystem.read_bool(entry, "used"))
	_player.facing = GameState.player_facing
	_player.place(GameState.player_cell)


func _spawn_enemies(cells: Array[Vector2i]) -> void:
	var types := MonsterDatabase.SPAWN_ORDER
	for i in mini(cells.size(), types.size()):
		var enemy := ENEMY_SCENE.instantiate() as Enemy
		enemy.setup(cells[i], types[i])
		_enemies.add_child(enemy)


func _place_items(loose_cells: Array[Vector2i]) -> void:
	for i in mini(ROOM_ITEMS.size(), _dungeon.rooms.size()):
		var room := _dungeon.rooms[i]
		_add_item(room.position + Vector2i(1, 1), ROOM_ITEMS[i])
	for loose_cell in loose_cells:
		_add_item(loose_cell, "health_potion")


func _place_traps(cells: Array[Vector2i]) -> void:
	for i in mini(cells.size(), TRAP_KINDS.size()):
		var trap := TRAP_SCENE.instantiate() as Trap
		trap.setup(cells[i], TRAP_KINDS[i])
		_traps.add_child(trap)


func _place_torches() -> void:
	for torch_cell in _dungeon.torch_cells(TORCH_COUNT, TORCH_GAP):
		var torch := TORCH_SCENE.instantiate()
		torch.call("setup", torch_cell)
		_torches.add_child(torch)


## Checkpoints go on the first candidate cells that are not next to a trap.
func _place_checkpoints(candidates: Array[Vector2i]) -> void:
	var placed := 0
	for candidate in candidates:
		if placed >= CHECKPOINT_COUNT:
			return
		var near_trap := false
		for node in get_tree().get_nodes_in_group("traps"):
			if Grid.distance((node as Trap).cell, candidate) <= 1:
				near_trap = true
		if not near_trap:
			_add_checkpoint(candidate, false)
			placed += 1


func _add_checkpoint(at: Vector2i, used: bool) -> void:
	var checkpoint := CHECKPOINT_SCENE.instantiate() as Checkpoint
	checkpoint.setup(at, used)
	_checkpoints.add_child(checkpoint)


## Dungeon ambience and the player's torch crackle, looped (the sound files are generated
## without a loop flag). Headless runs (tests) have no audio device, and a stream left playing
## there leaks at exit, so they only start with a display. The torch crackle is muted for now:
## its 7 Hz flicker over a low roar sounds like a helicopter.
func _start_ambient_sounds() -> void:
	var torch_sound := _player.get_node("TorchSound") as AudioStreamPlayer2D
	for stream: AudioStream in [_ambience.stream, torch_sound.stream]:
		var ogg := stream as AudioStreamOggVorbis
		if ogg:
			ogg.loop = true
	if DisplayServer.get_name() != "headless":
		_ambience.play()


func _add_item(at: Vector2i, item_id: String) -> void:
	var item := ITEM_SCENE.instantiate() as Item
	item.setup(at, item_id)
	_items.add_child(item)


## Distinct floor cells away from the start, outside rooms, picked with a seeded shuffle.
func _spawn_cells(count: int) -> Array[Vector2i]:
	var candidates: Array[Vector2i] = []
	for floor_cell in _dungeon.floor_cells():
		if (
			Grid.distance(floor_cell, Grid.START) >= SAFE_DISTANCE
			and not _dungeon.is_in_room(floor_cell)
		):
			candidates.append(floor_cell)
	var rng := RandomNumberGenerator.new()
	rng.seed = SPAWN_SEED
	for i in range(candidates.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var swap := candidates[i]
		candidates[i] = candidates[j]
		candidates[j] = swap
	return candidates.slice(0, count)
