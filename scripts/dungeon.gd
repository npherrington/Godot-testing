class_name Dungeon
extends Node2D
## The arena: a 32x32 grid of floor and wall cells with a few walled 3x3 rooms. Each cell is
## painted with 2x2 tiles from the dungeon tileset. Generation is seeded, so it is repeatable.

const SOURCE_ID := 0
const ROOM_SIZE := 3
const ROOM_COUNT := 4
const FLOOR_TILES: Array[Vector2i] = [Vector2i(0, 0), Vector2i(1, 0), Vector2i(2, 0)]
const ROOM_FLOOR_TILES: Array[Vector2i] = [Vector2i(3, 0), Vector2i(4, 0)]
const WALL_CAP := Vector2i(0, 2)
const WALL_FACE := Vector2i(1, 2)
const WALL_FACE_CRACKED := Vector2i(2, 2)
const SHADOW_N := Vector2i(9, 3)

@export var map_seed := 7

## Interior (floor) rect of each room, in cells.
var rooms: Array[Rect2i] = []
## The door cell of each room, same order as rooms.
var doors: Array[Vector2i] = []

var _walls: Dictionary[Vector2i, bool] = {}
var _astar := AStarGrid2D.new()

@onready var _floor: TileMapLayer = $Floor
@onready var _shadows: TileMapLayer = $Shadows
@onready var _wall_layer: TileMapLayer = $Walls


func _ready() -> void:
	generate(map_seed)


func generate(new_seed: int) -> void:
	map_seed = new_seed
	_walls.clear()
	rooms.clear()
	doors.clear()
	for x in Grid.SIZE.x:
		for y in Grid.SIZE.y:
			if x == 0 or y == 0 or x == Grid.SIZE.x - 1 or y == Grid.SIZE.y - 1:
				_walls[Vector2i(x, y)] = true
	var rng := RandomNumberGenerator.new()
	rng.seed = new_seed
	var attempts := 0
	while rooms.size() < ROOM_COUNT and attempts < 500:
		attempts += 1
		var origin := Vector2i(
			rng.randi_range(3, Grid.SIZE.x - ROOM_SIZE - 3),
			rng.randi_range(3, Grid.SIZE.y - ROOM_SIZE - 3)
		)
		var interior := Rect2i(origin, Vector2i(ROOM_SIZE, ROOM_SIZE))
		if _room_fits(interior):
			_add_room(interior, rng.randi_range(0, 3))
	_build_astar()
	_paint()


func is_wall(cell: Vector2i) -> bool:
	return not Grid.in_bounds(cell) or _walls.has(cell)


func is_walkable(cell: Vector2i) -> bool:
	return Grid.in_bounds(cell) and not _walls.has(cell)


## Whether a one-cell step is allowed: the target is floor and a diagonal step does not cut
## the corner of a wall.
func can_step(from: Vector2i, dir: Vector2i) -> bool:
	var to := from + dir
	if not is_walkable(to):
		return false
	if dir.x != 0 and dir.y != 0:
		return is_walkable(from + Vector2i(dir.x, 0)) and is_walkable(from + Vector2i(0, dir.y))
	return true


func floor_cells() -> Array[Vector2i]:
	var cells: Array[Vector2i] = []
	for y in Grid.SIZE.y:
		for x in Grid.SIZE.x:
			if not _walls.has(Vector2i(x, y)):
				cells.append(Vector2i(x, y))
	return cells


## Wall cells with floor below them (a visible wall face), spread at least min_gap apart, picked
## in a seeded order: where wall torches hang.
func torch_cells(count: int, min_gap: int) -> Array[Vector2i]:
	var faces: Array[Vector2i] = []
	for cell: Vector2i in _walls:
		if is_walkable(cell + Vector2i.DOWN):
			faces.append(cell)
	faces.sort()
	var rng := RandomNumberGenerator.new()
	rng.seed = map_seed * 31 + 5
	for i in range(faces.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var swap := faces[i]
		faces[i] = faces[j]
		faces[j] = swap
	var chosen: Array[Vector2i] = []
	for face in faces:
		var spaced := true
		for other in chosen:
			if Grid.distance(face, other) < min_gap:
				spaced = false
				break
		if spaced:
			chosen.append(face)
		if chosen.size() >= count:
			break
	return chosen


func is_in_room(cell: Vector2i) -> bool:
	for room in rooms:
		if room.has_point(cell):
			return true
	return false


## True when no wall lies on the straight line between two cells (ends excluded).
func has_line_of_sight(from: Vector2i, to: Vector2i) -> bool:
	for cell in line_cells(from, to):
		if cell != from and cell != to and is_wall(cell):
			return false
	return true


## The cells on a Bresenham line from one cell to another, both ends included.
func line_cells(from: Vector2i, to: Vector2i) -> Array[Vector2i]:
	var cells: Array[Vector2i] = []
	var delta := (to - from).abs()
	var step := (to - from).sign()
	var err := delta.x - delta.y
	var cell := from
	while true:
		cells.append(cell)
		if cell == to:
			break
		var e2 := err * 2
		if e2 > -delta.y:
			err -= delta.y
			cell.x += step.x
		if e2 < delta.x:
			err += delta.x
			cell.y += step.y
	return cells


## Shortest 8-way path over floor, from (excluded) to (included). Empty when unreachable.
func find_path(from: Vector2i, to: Vector2i) -> Array[Vector2i]:
	var path: Array[Vector2i] = []
	if not is_walkable(from) or not is_walkable(to):
		return path
	for cell in _astar.get_id_path(from, to):
		path.append(cell)
	if not path.is_empty():
		path.remove_at(0)
	return path


func _room_fits(interior: Rect2i) -> bool:
	var keep_out := interior.grow(3)
	if keep_out.has_point(Grid.START):
		return false
	for room in rooms:
		if keep_out.intersects(room.grow(1)):
			return false
	return true


func _add_room(interior: Rect2i, door_side: int) -> void:
	var outer := interior.grow(1)
	for x in range(outer.position.x, outer.end.x):
		for y in range(outer.position.y, outer.end.y):
			var cell := Vector2i(x, y)
			if not interior.has_point(cell):
				_walls[cell] = true
	var mid := interior.position + Vector2i(1, 1)
	var door: Vector2i = [
		Vector2i(mid.x, outer.position.y),
		Vector2i(outer.end.x - 1, mid.y),
		Vector2i(mid.x, outer.end.y - 1),
		Vector2i(outer.position.x, mid.y),
	][door_side]
	_walls.erase(door)
	rooms.append(interior)
	doors.append(door)


func _build_astar() -> void:
	_astar.region = Rect2i(Vector2i.ZERO, Grid.SIZE)
	_astar.cell_size = Vector2(Grid.CELL, Grid.CELL)
	_astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	_astar.default_compute_heuristic = AStarGrid2D.HEURISTIC_CHEBYSHEV
	_astar.default_estimate_heuristic = AStarGrid2D.HEURISTIC_CHEBYSHEV
	_astar.update()
	for cell: Vector2i in _walls:
		_astar.set_point_solid(cell, true)


func _paint() -> void:
	_floor.clear()
	_shadows.clear()
	_wall_layer.clear()
	for y in Grid.SIZE.y:
		for x in Grid.SIZE.x:
			var cell := Vector2i(x, y)
			if _walls.has(cell):
				_paint_wall(cell)
			else:
				_paint_floor(cell)


func _paint_floor(cell: Vector2i) -> void:
	var tiles := ROOM_FLOOR_TILES if is_in_room(cell) else FLOOR_TILES
	for sub in _subtiles(cell):
		_floor.set_cell(sub, SOURCE_ID, tiles[_hash(sub) % tiles.size()])
	if _walls.has(cell + Vector2i.UP):
		_shadows.set_cell(cell * 2, SOURCE_ID, SHADOW_N)
		_shadows.set_cell(cell * 2 + Vector2i(1, 0), SOURCE_ID, SHADOW_N)


func _paint_wall(cell: Vector2i) -> void:
	var top := cell * 2
	_wall_layer.set_cell(top, SOURCE_ID, WALL_CAP)
	_wall_layer.set_cell(top + Vector2i(1, 0), SOURCE_ID, WALL_CAP)
	var face_visible := (
		Grid.in_bounds(cell + Vector2i.DOWN) and not _walls.has(cell + Vector2i.DOWN)
	)
	for dx in 2:
		var sub := top + Vector2i(dx, 1)
		var face := WALL_FACE_CRACKED if _hash(sub) % 5 == 0 else WALL_FACE
		_wall_layer.set_cell(sub, SOURCE_ID, face if face_visible else WALL_CAP)


func _subtiles(cell: Vector2i) -> Array[Vector2i]:
	var top := cell * 2
	return [top, top + Vector2i(1, 0), top + Vector2i(0, 1), top + Vector2i(1, 1)]


func _hash(sub: Vector2i) -> int:
	return absi(sub.x * 73856093 ^ sub.y * 19349663 ^ map_seed * 83492791)
