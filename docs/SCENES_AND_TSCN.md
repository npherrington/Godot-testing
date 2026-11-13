# Scene & TSCN Conventions — Dragon Crystal Game

## 1. Scene File Format Basics

TSCN files are Godot's scene serialization format (INI-style). You'll edit them by hand
for **small scenes** — anything that doesn't need the editor to place dozens of nodes:

```ini
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1_player"]

[sub_resource type="SpriteFrames" id="2_movespritesframes"]
anims = {
    "default": [
        SpriteAnimFrame,
    ],
}

[node name="Player" type="CharacterBody2D"]
script = SubResource(2)

[node name="Sprite2D" parent="." type="Sprite2D"]
```

**Rules:**

| Rule | Reason |
|---|---|
| `load_steps` = number of loaded resources + 1 (base scene object) | If you add a script reference, bump this by 1 |
| All `ext_resource` / `sub_resource` must have sequential IDs that match their `id=` in the file | Godot will fail to load if mismatched |
| Scene hierarchy mirrors `[node]` blocks — child nodes appear after parent with `parent=` | |
| Scripts always use absolute paths (`res://...`) not relative | |

## 2. One Scene Per Concept

Every scene represents **one logical object** — never a bag of unrelated things:

```
scenes/               # one scene per concept
├── main.tscn         # root scene — connects everything but doesn't *be* anything
├── player.tscn       # just the player character + its visual + hitbox
├── hud.tscn          # health bar, food bar, gold display (Control-based UI)
├── enemies/
│   ├── toad.tscn     # toad enemy scene (extends Enemy base class logic)
│   └── ninja.tscn    # ninja enemy scene
├── floor_01.tscn     # individual floor tilemap layout (procedurally created or hand-crafted)
└── pickups/
    ├── food_cake.tscn
    └── sword.tscn
```

**No:** `dungeon.tscn` that contains the player, 20 enemies, HUD, and pickup objects — all of those are separate scenes.

**Exception:** The root `main.tscn` scene is allowed to be a composition scene because it's the bootstrap — but even there, keep nodes minimal (just containers + references).

## 3. Node Naming Conventions in Scenes

Godot's built-in types have specific casing:

| Thing | Scene Name Convention | Example |
|---|---|---|
| Godot built-in node type | The name is the type + PascalCase hint | `CharacterBody2D`, `Sprite2D`, `Area2D` |
| Custom root nodes of scenes | snake_case + concept name | `player`, `hud`, `enemy_spawner` |
| Important children inside parent | $Name (PascalCase) if this script needs them | `$Player`, `$HealthBar` |
| Containers / groups | snake_case descriptive names | `health_container`, `enemies_parent` |

When a script **needs to reach** a sibling node, give it an exact name:
```gdscript
# script attached to HUD parent can access child directly:
$HealthBar.value = current_hp / max_health * 100.0   # $HealthBar is the child
```

When it's purely visual (other scripts won't reference by name), use a group:
```gdscript
# Add "enemies" group to all enemy nodes in scene, then look them up anywhere:
for enemy in get_tree().get_nodes_in_group("enemies"):
    ...
```

## 4. Scene Hierarchy Rules

### Maximum depth: 4 levels from any scene root to a functional child

```
main.tscn (root Node2D)                       ← level 1
└── player_container (Node2D, group "player")  ← level 2
    └── player.gd (Player extends CharacterBody2D)  ← level 3
        └── $Sprite2D                         ← level 3 (deep inside scene's own tree)
```

If you're at level 5+, split into a container:
```gdscript
# BEFORE (too deep):
main → entities → characters → player → Sprite2D    (level 5!)
main → entities → characters → enemy_group → Enemy   (level 5!)

# AFTER (split into scenes):
# main.tscn has just the containers...
# each container spawns player.tscn or enemy.tscn as sub-scenes (1 level of depth)
```

### Children of same type should go in a named parent node

```gdscript
# BAD: sibling nodes with no grouping
main → FoodPickup
main → SwordPickup
main → ShieldPickup    # three unrelated siblings

# GOOD: grouped under parent for discovery and cleanup
main → pickups_parent (Node2D, group "pickups")
    ├── food_cake.tscn       # instance
    ├── sword_pickup.tscn    # instance
    └── shield_pickup.tscn   # instance
```

## 5. Instantiation & Pooling Patterns

### Preload scenes that are referenced frequently
```gdscript
class_name EnemySpawner extends Node2D   # one name per file

# Class-level constant — preloaded at load-time, not per-frame
const ENEMY_PRELOADS := {
    "toad": preload("res://scenes/enemies/toad.tscn"),
    "ninja": preload("res://scenes/enemies/ninja.tscn"),
    "slime_blob": preload("res://scenes/enemies/slime_blob.tscn"),
}

func spawn(type: StringName, pos: Vector2) -> Enemy:
    var instance := ENEMY_PRELOADS[type].instantiate() as Enemy
    instance.global_position = pos
    add_child(instance)
    return instance   # caller can reference it directly
```

### ObjectPool for frequently created/destroyed things (enemies, projectiles)
```gdscript
class_name ObjectPool extends Node

var _pool := []       # free (inactive) instances
var _scene: PackedScene

func init(scene: PackedScene, initial_count: int) -> void:
    _scene = scene
    for i in range(initial_count):
        var inst := scene.instantiate()
        inst.visible = false
        add_child(inst)
        _pool.push_back(inst)

func acquire() -> Node2D:
    if _pool.size() > 0:
        var item := _pool.pop_back() as Node2D
        item.visible = true
        return item
    # pool exhausted — instantiate new (rare case)
    return _scene.instantiate() as Node2D

func release(item: Node2D) -> void:
    item.visible = false
    _pool.push_back(item)
```

## 6. Script-Scene Binding Rules

| Rule | Enforcement |
|---|---|
| Scene file name matches script class name (PascalCase for scene root, snake_case for filename) | `.tscn` → `player.tscn` ↔ `class_name Player`, file `player.gd` |
| One script per scene (no god-object scenes with 5 scripts mixed in) | Linting catches it; the gate fails if a scene has mismatched script |
| Scripts use `extends` to inherit from Godot types directly, not other project scripts except `Node`, `CharacterBody2D`, etc. | Per GDSCRIPT_STYLES.md code-order rule |

## 7. UI/TSCN Scene Structure (HUD Pattern)

UI scenes always follow a consistent hierarchy:
```gdscript
# hud.tscn
<Control (root, full-screen anchored)>    # anchor to screen edges
├── VBoxContainer                         # stack bars vertically
│   ├── HBoxContainer (left label + bar + right label)
│   │   ├── Label "HP"                    # text
│   │   ├── ProgressBar                   # game state binds here
│   │   └── Label (bound to current/max)  # formatted display
│   ├── VBoxContainer (duplicate for food)
│   └── VBoxContainer (duplicate for gold)
└── HBoxContainer                         # inventory row at bottom
    └── Button "I" → opens InventoryPanel scene
```

**Key rule for UI scenes:**
- Root is always `Control`, not `Node2D`
- Use anchors and margins (not fixed positions) so HUD resizes with viewport
- ProgressBars bind to GameState values via signal connection — never polling in `_process()`

## 8. Edit TSCN Files by Hand — When It's Safe

### OK to hand-edit:
- Adding/removing one node per parent
- Changing a property value (position, scale, texture path)
- Adjusting `ext_resource` / `sub_resource` list when adding new scene file references
- Modifying `$` paths inside scripts

### Never hand-edit:
- TileMap layers with 100+ tiles (editor generates these)
- AnimationNode trees (too many connections, hard to serialize manually)
- Any scene you'd open in the Godot editor anyway to tweak visual layout

### When breaking things happens (fix pattern):
```ini
# If Godot complains: "load steps count mismatch"
# Fix bump load_steps by: number_of_new_ext_resource/sub_resource references added

[gd_scene load_steps=4 format=3]      # was 3, now 4 because we added 1 ext_resource
```
