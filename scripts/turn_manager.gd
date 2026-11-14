class_name TurnManager
extends Node
## Runs the turns. The player acts, then every enemy in group order, then the round ends
## (statuses tick, the turn number goes up). All actions go through one queue, in order.

signal round_ended(turn: int)

## Frames the enemy phase waits, so the turn indicator and the player's step can be seen.
const ENEMY_DELAY_FRAMES := 6
const POISON_DAMAGE := 3

var queue: Array[Dictionary] = []

var _delay := 0
## Set when the player steps onto a checkpoint; the save happens once the round is over, so a
## reload starts cleanly at the player's turn.
var _checkpoint_pending := false


func _physics_process(_delta: float) -> void:
	if GameState.phase != "enemy" or GameState.game_over:
		return
	_delay -= 1
	if _delay <= 0:
		run_enemy_phase()


## Take the player's action for this turn and hand over to the enemies. Returns false when it
## is not the player's turn.
func player_action(action: Dictionary) -> bool:
	if not GameState.can_player_act():
		return false
	GameState.defending = false
	enqueue(action)
	process_queue()
	if not GameState.game_over:
		_start_enemy_phase()
	return true


func enqueue(action: Dictionary) -> void:
	queue.append(action)


## Resolve queued actions first in, first out. An enemy's turn expands into its own actions,
## which resolve before the next queued entry.
func process_queue() -> void:
	while not queue.is_empty():
		if GameState.game_over:
			queue.clear()
			return
		var action: Dictionary = queue.pop_front()
		_resolve(action)


func run_enemy_phase() -> void:
	for node in get_tree().get_nodes_in_group("enemies"):
		enqueue({"type": "enemy_turn", "actor": node})
	process_queue()
	_end_round()


func enemy_at(cell: Vector2i) -> Enemy:
	for node in get_tree().get_nodes_in_group("enemies"):
		var enemy := node as Enemy
		if enemy and enemy.cell == cell:
			return enemy
	return null


## Whether a character could stand on the cell: inside, not the player, no enemy there.
## Walls block unless through_walls (ghosts).
func is_free(cell: Vector2i, through_walls := false) -> bool:
	if cell == GameState.player_cell or enemy_at(cell) != null:
		return false
	if through_walls:
		return Grid.in_bounds(cell) and not _on_border(cell)
	var dungeon := _dungeon()
	return dungeon == null or dungeon.is_walkable(cell)


## The cell to step to from a cell to get closer to a target: along the shortest path when it
## is free, else the free neighbour that gets closest. The same cell when nothing gets closer.
func step_toward(
	from: Vector2i, target: Vector2i, through_walls := false, four_way := false
) -> Vector2i:
	var dungeon := _dungeon()
	if dungeon and not through_walls and not four_way:
		var path := dungeon.find_path(from, target)
		if not path.is_empty() and path[0] != target and is_free(path[0]):
			return path[0]
	return _greedy_step(from, target, through_walls, true, four_way)


## The free neighbour that gets furthest from a target, or the same cell.
func step_away(from: Vector2i, target: Vector2i) -> Vector2i:
	return _greedy_step(from, target, false, false, false)


func can_step(from: Vector2i, dir: Vector2i) -> bool:
	var dungeon := _dungeon()
	return dungeon == null or dungeon.can_step(from, dir)


func _greedy_step(
	from: Vector2i, target: Vector2i, through_walls: bool, closer: bool, four_way: bool
) -> Vector2i:
	var dungeon := _dungeon()
	var best := from
	var best_score := _score(from, target)
	for dir in Grid.DIRS_8:
		if four_way and dir.x != 0 and dir.y != 0:
			continue
		var to := from + dir
		if not is_free(to, through_walls):
			continue
		if dungeon and not through_walls and not dungeon.can_step(from, dir):
			continue
		var score := _score(to, target)
		if (closer and score < best_score) or (not closer and score > best_score):
			best = to
			best_score = score
	return best


func _score(cell: Vector2i, target: Vector2i) -> float:
	return Grid.distance(cell, target) + Vector2(cell - target).length() * 0.01


func _start_enemy_phase() -> void:
	_delay = ENEMY_DELAY_FRAMES
	GameState.set_phase("enemy")


func _end_round() -> void:
	var frozen := GameState.has_status("freeze")
	_tick_player_statuses()
	for node in get_tree().get_nodes_in_group("enemies"):
		var enemy := node as Enemy
		if enemy:
			enemy.tick_statuses()
	for node in get_tree().get_nodes_in_group("traps"):
		(node as Trap).tick()
	GameState.next_turn()
	round_ended.emit(GameState.turn)
	if GameState.game_over:
		return
	if frozen:
		GameState.log_message("You are frozen solid and lose a turn!")
		_start_enemy_phase()
		return
	GameState.set_phase("player")
	if _checkpoint_pending:
		_checkpoint_pending = false
		if SaveSystem.save_game(GameState.checkpoint_path):
			GameState.log_message("Checkpoint reached. Progress saved.")


func _tick_player_statuses() -> void:
	if GameState.has_status("poison"):
		var dealt := GameState.damage_player(POISON_DAMAGE, true)
		GameState.log_message("Poison burns you for %d." % dealt)
	for status: String in GameState.statuses.keys():
		GameState.statuses[status] -= 1
		if GameState.statuses[status] <= 0:
			GameState.statuses.erase(status)
			GameState.log_message("You are no longer %s." % _status_adjective(status))
	GameState.changed.emit()


func _resolve(action: Dictionary) -> void:
	var kind: String = action.get("type", "")
	var actor: Object = action.get("actor")
	if kind == "enemy_turn":
		_resolve_enemy_turn(actor as Enemy)
		return
	GameState.actions_resolved += 1
	match kind:
		"move":
			var to: Vector2i = action.get("to", Vector2i.ZERO)
			_resolve_move(actor, to)
		"attack":
			_resolve_attack(action)
		"defend":
			GameState.defending = true
			GameState.log_message("You raise your guard.")
		"pickup":
			_resolve_pickup(action)
		"use":
			var index: int = action.get("index", -1)
			GameState.consume(index)
		"wait":
			pass
	GameState.changed.emit()


func item_near(cell: Vector2i) -> Item:
	var best: Item = null
	for node in get_tree().get_nodes_in_group("items"):
		var item := node as Item
		if item == null or Grid.distance(item.cell, cell) > 1:
			continue
		if best == null or item.cell == cell:
			best = item
	return best


func _resolve_pickup(action: Dictionary) -> void:
	var target: Object = action.get("item")
	var item := target as Item
	if item == null or not is_instance_valid(item):
		return
	if GameState.inventory.size() >= GameState.INVENTORY_SIZE:
		GameState.log_message("Your pack is full.")
		return
	GameState.log_message("You pick up the %s." % ItemDatabase.item_name(item.item_id))
	GameState.add_item(item.item_id)
	item.remove_from_group("items")
	item.queue_free()


func _resolve_enemy_turn(enemy: Enemy) -> void:
	if enemy == null or not is_instance_valid(enemy) or not enemy.is_alive():
		return
	if enemy.has_status("freeze"):
		GameState.log_message("%s is frozen." % enemy.display_name)
		return
	var actions := enemy.decide(self)
	for i in range(actions.size() - 1, -1, -1):
		queue.push_front(actions[i])


func _resolve_move(actor: Object, to: Vector2i) -> void:
	var player := actor as Player
	if player:
		player.step_to(to)
		_trigger_traps()
		_touch_checkpoint()
		return
	var enemy := actor as Enemy
	if enemy and enemy.is_alive() and is_free(to, enemy.moves_through_walls()):
		enemy.move_to(to)


func _touch_checkpoint() -> void:
	for node in get_tree().get_nodes_in_group("checkpoints"):
		var checkpoint := node as Checkpoint
		if checkpoint and checkpoint.cell == GameState.player_cell:
			checkpoint.activate()
			GameState.checkpoint_reached = true
			_checkpoint_pending = true


## Clear anything queued or pending (a loaded game starts fresh at the player's turn).
func clear() -> void:
	queue.clear()
	_delay = 0
	_checkpoint_pending = false


## Armed traps next to (or under) the player fire after the player moves.
func _trigger_traps() -> void:
	for node in get_tree().get_nodes_in_group("traps"):
		var trap := node as Trap
		if trap == null or not trap.is_armed():
			continue
		if Grid.distance(trap.cell, GameState.player_cell) > 1 or GameState.game_over:
			continue
		var dealt := GameState.damage_player(trap.fire(), true)
		GameState.traps_triggered += 1
		GameState.log_message("%s fires! You take %d." % [trap.display_name(), dealt])
		var player := get_tree().get_first_node_in_group("player") as Player
		if player:
			player.flash_hurt()


func _resolve_attack(action: Dictionary) -> void:
	var attacker: Object = action.get("actor")
	var target: Object = action.get("target")
	var damage: int = action.get("damage", 0)
	var verb: String = action.get("verb", "hits")
	var enemy_target := target as Enemy
	if attacker is Player and enemy_target and enemy_target.is_alive():
		(attacker as Player).play_attack(enemy_target.cell)
		var dealt := enemy_target.take_damage(damage)
		GameState.log_message("You hit %s for %d." % [enemy_target.display_name, dealt])
		if not enemy_target.is_alive():
			GameState.log_message("%s is slain!" % enemy_target.display_name)
		return
	var enemy_attacker := attacker as Enemy
	if enemy_attacker and target is Player and enemy_attacker.is_alive():
		var fx: String = action.get("fx", "")
		enemy_attacker.play_attack(GameState.player_cell, fx)
		var dealt := GameState.damage_player(damage)
		(target as Player).flash_hurt()
		GameState.log_message("%s %s you for %d." % [enemy_attacker.display_name, verb, dealt])
		var status: String = action.get("status", "")
		if status != "" and not GameState.game_over:
			var turns: int = action.get("status_turns", 1)
			GameState.apply_status(status, turns)
			GameState.log_message("You are %s!" % _status_adjective(status))


func _status_adjective(status: String) -> String:
	match status:
		"poison":
			return "poisoned"
		"freeze":
			return "frozen"
	return status


func _on_border(cell: Vector2i) -> bool:
	return cell.x == 0 or cell.y == 0 or cell.x == Grid.SIZE.x - 1 or cell.y == Grid.SIZE.y - 1


func _dungeon() -> Dungeon:
	return get_tree().get_first_node_in_group("dungeon") as Dungeon
