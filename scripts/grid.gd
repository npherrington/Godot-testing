class_name Grid
extends RefCounted
## Grid maths for everything that stands on a cell. One cell is 32x32 world pixels, drawn as
## 2x2 tiles of the 16 px tileset so tiles and 32x48 characters share one pixel size.

const CELL := 32
const SIZE := Vector2i(32, 32)
const START := Vector2i(16, 16)
## Where a character's feet go inside its cell (sprites put their feet on the node position).
const FEET := Vector2(16, 26)
const DIRS_8: Array[Vector2i] = [
	Vector2i(1, 0),
	Vector2i(1, 1),
	Vector2i(0, 1),
	Vector2i(-1, 1),
	Vector2i(-1, 0),
	Vector2i(-1, -1),
	Vector2i(0, -1),
	Vector2i(1, -1),
]
const NAMES_8: Array[String] = [
	"right", "down_right", "down", "down_left", "left", "up_left", "up", "up_right"
]


static func to_world(cell: Vector2i) -> Vector2:
	return Vector2(cell * CELL) + FEET


static func to_cell(pos: Vector2) -> Vector2i:
	return Vector2i(floori(pos.x / CELL), floori(pos.y / CELL))


static func cell_centre(cell: Vector2i) -> Vector2:
	return Vector2(cell * CELL) + Vector2(CELL, CELL) / 2.0


## Chebyshev distance: the number of 8-way steps between two cells.
static func distance(a: Vector2i, b: Vector2i) -> int:
	return maxi(absi(a.x - b.x), absi(a.y - b.y))


static func in_bounds(cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.y >= 0 and cell.x < SIZE.x and cell.y < SIZE.y


## Direction name with 8 ways ("down_right") for the player's sprite sheet.
static func name_8(dir: Vector2i) -> String:
	var index := DIRS_8.find(dir.sign())
	return NAMES_8[index] if index >= 0 else "down"


## Direction name with 4 ways for enemy sprite sheets.
static func name_4(dir: Vector2i) -> String:
	if dir == Vector2i.ZERO:
		return "down"
	if absi(dir.x) > absi(dir.y):
		return "right" if dir.x > 0 else "left"
	return "down" if dir.y > 0 else "up"


static func to_array(cell: Vector2i) -> Array[int]:
	return [cell.x, cell.y]


static func from_array(value: Variant) -> Vector2i:
	if not value is Array:
		return Vector2i.ZERO
	var pair: Array = value
	if pair.size() != 2:
		return Vector2i.ZERO
	var x: float = pair[0]
	var y: float = pair[1]
	return Vector2i(roundi(x), roundi(y))
