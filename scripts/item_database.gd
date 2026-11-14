class_name ItemDatabase
extends RefCounted
## Every item: what it is and what it does. Icons are 16x16 letter matrices in the project's
## palette (see art/README.md), built into textures at runtime until real item art exists at
## assets/sprites/items/item_<id>.png.

const ART_PATH := "res://assets/sprites/items/item_%s.png"

const SWORD: Array[String] = [
	"..............KK",
	".............KWK",
	"............KWLK",
	"...........KWLK.",
	"..........KWLK..",
	".........KWLK...",
	"........KWLK....",
	"..KK...KWLK.....",
	"..KYK.KWLK......",
	"...KYKWLK.......",
	"....KYLK........",
	"....KbYYK.......",
	"...KbK.KYK......",
	"..KbK...KK......",
	".KKK............",
	"................",
]
const SHIELD: Array[String] = [
	"................",
	"..KKKKKKKKKKKK..",
	"..KLLLLLLLLLLK..",
	"..KLRRRRRRRRLK..",
	"..KLRRRYYRRRLK..",
	"..KLRRYWWYRRLK..",
	"..KLRRRYYRRRLK..",
	"..KLRRRRRRRRLK..",
	"...KLRRRRRRLK...",
	"...KLrRRRRrLK...",
	"....KLrRRrLK....",
	".....KLrrLK.....",
	"......KLLK......",
	".......KK.......",
	"................",
	"................",
]
const POTION: Array[String] = [
	"................",
	"......KKKK......",
	"......KBTK......",
	"......KbBK......",
	".......KK.......",
	"......KWIK......",
	".....KWLLIK.....",
	"....KRRRRRRK....",
	"...KRFFRRRRRK...",
	"...KRFRRRRRRK...",
	"...KRRRRRRRRK...",
	"...KrRRRRRRrK...",
	"....KrrrrrrK....",
	".....KKKKKK.....",
	"................",
	"................",
]

const ITEMS: Dictionary[String, Dictionary] = {
	"sword":
	{
		"name": "Sword",
		"kind": "weapon",
		"attack": 4,
		"text": "+4 attack",
		"icon": SWORD,
	},
	"shield":
	{
		"name": "Shield",
		"kind": "armor",
		"defense": 2,
		"text": "+2 defense",
		"icon": SHIELD,
	},
	"health_potion":
	{
		"name": "Health Potion",
		"kind": "consumable",
		"heal": 40,
		"text": "Heals 40",
		"icon": POTION,
	},
}

## The palette letters the icons use (art/pixel.py COLOURS).
const COLOURS: Dictionary[String, Color] = {
	"K": Color8(20, 16, 24),
	"D": Color8(58, 54, 70),
	"G": Color8(104, 102, 118),
	"L": Color8(166, 164, 176),
	"W": Color8(236, 232, 216),
	"b": Color8(62, 38, 32),
	"B": Color8(116, 72, 46),
	"T": Color8(178, 124, 76),
	"r": Color8(104, 22, 36),
	"R": Color8(190, 44, 50),
	"F": Color8(226, 120, 118),
	"Y": Color8(250, 210, 76),
	"I": Color8(192, 234, 242),
}

static var _icons: Dictionary[String, Texture2D] = {}


static func has_item(item_id: String) -> bool:
	return ITEMS.has(item_id)


static func get_item(item_id: String) -> Dictionary:
	return ITEMS.get(item_id, {})


static func item_name(item_id: String) -> String:
	var text: String = get_item(item_id).get("name", item_id)
	return text


static func kind(item_id: String) -> String:
	var text: String = get_item(item_id).get("kind", "")
	return text


static func description(item_id: String) -> String:
	var text: String = get_item(item_id).get("text", "")
	return text


static func stat(item_id: String, key: String) -> int:
	var value: int = get_item(item_id).get(key, 0)
	return value


static func icon(item_id: String) -> Texture2D:
	if _icons.has(item_id):
		return _icons[item_id]
	var texture: Texture2D = null
	var art := ART_PATH % item_id
	if ResourceLoader.exists(art):
		texture = load(art) as Texture2D
	else:
		var pattern: Array = get_item(item_id).get("icon", [])
		var rows: Array[String] = []
		rows.assign(pattern)
		texture = _build_icon(rows)
	_icons[item_id] = texture
	return texture


static func _build_icon(rows: Array[String]) -> Texture2D:
	var image := Image.create_empty(16, 16, false, Image.FORMAT_RGBA8)
	for y in mini(rows.size(), 16):
		for x in mini(rows[y].length(), 16):
			var letter := rows[y][x]
			if COLOURS.has(letter):
				image.set_pixel(x, y, COLOURS[letter])
	return ImageTexture.create_from_image(image)
