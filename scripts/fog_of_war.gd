extends Node2D
## Fog of war. Cells the player has never seen are black; seen cells out of sight are dimmed.
## What the player can see is recomputed when the player's cell changes, and stored in
## GameState (explored, visible_cells). Enemies out of sight are hidden.

const UNSEEN := Color(0, 0, 0, 1)
const REMEMBERED := Color(0, 0, 0, 0.55)

var _last_cell := Vector2i(-1, -1)


func _ready() -> void:
	GameState.changed.connect(_on_state_changed)
	_on_state_changed()


func _draw() -> void:
	for y in Grid.SIZE.y:
		for x in Grid.SIZE.x:
			var cell := Vector2i(x, y)
			if not GameState.explored.has(cell):
				draw_rect(_rect(cell), UNSEEN)
			elif not GameState.visible_cells.has(cell):
				draw_rect(_rect(cell), REMEMBERED)


## Recompute sight from a cell: within the light radius and not behind a wall.
func reveal(center: Vector2i) -> void:
	var dungeon := get_tree().get_first_node_in_group("dungeon") as Dungeon
	var radius := GameState.LIGHT_RADIUS
	GameState.visible_cells.clear()
	for dy in range(-radius, radius + 1):
		for dx in range(-radius, radius + 1):
			var cell := center + Vector2i(dx, dy)
			if not Grid.in_bounds(cell) or Vector2(dx, dy).length() > radius + 0.5:
				continue
			if dungeon and not dungeon.has_line_of_sight(center, cell):
				continue
			GameState.visible_cells[cell] = true
			GameState.explored[cell] = true
	_last_cell = center
	queue_redraw()


func _on_state_changed() -> void:
	if GameState.player_cell != _last_cell or GameState.visible_cells.is_empty():
		reveal(GameState.player_cell)
	for node in get_tree().get_nodes_in_group("enemies"):
		var enemy := node as Enemy
		if enemy:
			enemy.visible = GameState.visible_cells.has(enemy.cell)


func _rect(cell: Vector2i) -> Rect2:
	return Rect2(Vector2(cell * Grid.CELL), Vector2(Grid.CELL, Grid.CELL))
