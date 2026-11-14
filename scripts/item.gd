class_name Item
extends Node2D
## An item lying on a dungeon cell, waiting to be picked up with interact.

var item_id := "health_potion"
var cell := Vector2i.ZERO

@onready var _icon: Sprite2D = $Icon


func _ready() -> void:
	position = Grid.to_world(cell)
	_icon.texture = ItemDatabase.icon(item_id)
	var rest := _icon.position.y
	var tween := create_tween().set_loops()
	tween.tween_property(_icon, "position:y", rest - 2.0, 0.6)
	tween.tween_property(_icon, "position:y", rest, 0.6)


func setup(at: Vector2i, new_item_id: String) -> void:
	cell = at
	item_id = new_item_id


func to_dict() -> Dictionary:
	return {"id": item_id, "cell": Grid.to_array(cell)}
