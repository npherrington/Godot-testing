class_name MonsterDatabase
extends RefCounted
## Every monster type: name, stats, behavior and sprite. Enemy.setup() reads from here.
## Behaviors are implemented in enemy.gd; each type moves in its own way.

const FRAMES_PATH := "res://assets/sprites/enemies/char_%s_normal.tres"
const FX_PATH := "res://assets/sprites/enemies/fx_%s_%s.tres"

const MONSTERS: Dictionary[String, Dictionary] = {
	"skeleton_warrior":
	{
		"name": "Skeleton",
		"health": 20,
		"damage": [5, 8],
		"behavior": "chase",
	},
	"ghost":
	{
		"name": "Ghost",
		"health": 15,
		"damage": [4, 7],
		"behavior": "phase",
	},
	"goblin":
	{
		"name": "Goblin",
		"health": 15,
		"damage": [3, 5],
		"behavior": "ranged",
		"ranged": {"damage": [4, 6], "range": 4, "verb": "throws a rock at", "fx": "rock"},
	},
	"slime":
	{
		"name": "Slime",
		"health": 24,
		"damage": [4, 6],
		"behavior": "hop",
		"splits_into": "slime_small",
	},
	"ogre":
	{
		"name": "Ogre",
		"health": 40,
		"damage": [10, 14],
		"behavior": "lumber",
	},
	"spider":
	{
		"name": "Spider",
		"health": 16,
		"damage": [4, 6],
		"behavior": "ambush",
		"ranged":
		{
			"damage": [1, 2],
			"range": 4,
			"verb": "spits a web at",
			"fx": "web_shot",
			"status": "freeze",
			"status_turns": 1,
			"every": 4,
		},
	},
	"zombie":
	{
		"name": "Zombie",
		"health": 25,
		"damage": [5, 7],
		"behavior": "shamble",
		"status": "poison",
		"status_turns": 2,
	},
	"dark_mage":
	{
		"name": "Dark Mage",
		"health": 18,
		"damage": [3, 5],
		"behavior": "kite",
		"ranged":
		{"damage": [5, 8], "range": 5, "verb": "hurls a shadow bolt at", "fx": "shadow_bolt"},
	},
	"wolfman":
	{
		"name": "Wolfman",
		"health": 22,
		"damage": [5, 8],
		"behavior": "sprint",
	},
	"imp":
	{
		"name": "Imp",
		"health": 12,
		"damage": [4, 7],
		"behavior": "erratic",
		"ranged": {"damage": [4, 7], "range": 3, "verb": "throws a fireball at", "fx": "fireball"},
	},
	"slime_small":
	{
		"name": "Slime Spawn",
		"health": 8,
		"damage": [2, 4],
		"behavior": "hop",
	},
}

## The monsters placed at the start of a run, one of each.
const SPAWN_ORDER: Array[String] = [
	"skeleton_warrior",
	"ghost",
	"goblin",
	"slime",
	"ogre",
	"spider",
	"zombie",
	"dark_mage",
	"wolfman",
	"imp",
]


static func has_type(type_id: String) -> bool:
	return MONSTERS.has(type_id)


static func get_stats(type_id: String) -> Dictionary:
	return MONSTERS.get(type_id, MONSTERS["skeleton_warrior"])


static func frames_path(type_id: String) -> String:
	return FRAMES_PATH % type_id


static func fx_path(type_id: String, effect: String) -> String:
	return FX_PATH % [type_id, effect]
