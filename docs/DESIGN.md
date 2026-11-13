# Design Principles — Dragon Crystal Game

---

Last updated: 2026-11-13 ⚠️ This is a meta-doc. Read the detailed conventions below before making any changes.

## Quick Reference (Read First)

| Concern | File | What to look for |
|---|---|---|
| **Code style** | `GDSCRIPT_STYLES.md` | Type annotations, naming, indentation, error handling rules |
| **Architecture** | `ARCHITECTURE.md` | GameState as source of truth, signal contracts, service patterns |
| **Scenes & TSCN** | `SCENES_AND_TSCN.md` | Scene file format, node organization, instantiation |
| **Game domain** | `DOMAIN_RULES.md` | Tiles, turns, items, enemies, food mechanics, map layout |
| **Code templates** | `PATTERNS.md` | Copy-paste-ready blocks for common operations |
| **Tests** | `TESTING_STANDARDS.md` | Headless test patterns, assertion style, GameState querying |

---

## High-Level Goals

1. Build a **top-down dungeon crawler / roguelike** inspired by *Dragon Crystal* (Sega, 1990).
2. Every change must pass `bin/check.sh` before the feature is considered done.
3. Agent consistency — all conventions are explicitly documented here so any reader follows them.

## Architecture Overview

```
GameState (autoload singleton)
    ├── Player stats (HP, food, level, gold, position)
    ├── Current floor (level number, map layout, entities)
    └── Inventory (items, equipment slots)

PlayerInput (action events)
    └─> InputHandler → GameState mutations → Visual update
```

**Golden rule:** Any data that must survive scene changes or be readable by tests lives on the `GameState` autoload. Everything else is transient (animations, effects, temporary caches).

## Rules

```gdscript
# GOOD - fully typed
func add_item(item: InventoryItem) -> bool:
    if items.size() >= max_inventory:
        return false
    items.append(item)
    return true

# BAD - type inference only, not explicit
func add_item(item):
    pass

# BAD - untyped dictionary
var stats = {"hp": 100, "food": 50}
```

Use the following typed patterns consistently:

| Concept | Pattern |
|---|---|
| Collections | `var items: Array[ItemType] = []` (not `Array` or `PackedStringArray`) |
| Dictionaries | Never use untyped dicts for game data. Use classes/structs instead. |
| Optionals | Return `null` only when "not found" or "none equipped". Never for flow control. |
| Enums | Always prefer `enum ItemType { HEAL, POISON, MAP, SPELL }` over strings or ints |

### 2.2 Naming Conventions

| Type | Pattern | Example |
|---|---|---|
| Class names | PascalCase | `GameState`, `PlayerController`, `DungeonMap` |
| GDScript files | snake_case | `game_state.gd`, `dungeon_map.gd` |
| Scene files | snake_case | `player.tscn`, `inventory_panel.tscn` |
| Groups | snake_case plural | `enemies`, `floor_tiles`, `pickups` |
| Variables | snake_case (camelCase for game dev terms) | `hp`, `max_hp`, `food_points`, `gold_count` |
| Constants | UPPER_SNAKE_CASE | `MAX_LEVELS`, `FOOD_PER_STEP = 1` |
| Enums | PascalCase, members UPPER_SNAKE_CASE | `enum ItemType { HEAL, POISON }` |
| Private variables/methods | _snake_case | `_current_floor: int`, `_take_damage()` |
| Signals | PascalCase or present tense verb phrases | `HealthChanged`, `OnPlayerDied` |

### 2.3 Code Structure in Scripts

Every `.gd` file follows this order:

```gdscript
class_name PlayerStats   # Must match filename, always at top

extends Node2D           # Scene type

## High-level doc: one sentence describing purpose
## (What this manages, not how it works)

enum WeaponSlot { MAIN_HAND, OFF_HAND }

@export var max_hp: int = 100
var hp: int = max_hp
var _floor: int = 1       # private convention: underscore prefix

signal health_changed(new_hp: int)

func _ready() -> void:
    pass    # keep minimal — heavy logic belongs in other scripts

func reset() -> void:
    """Restore to initial values."""
    hp = max_hp
```

**Rules:**
- `class_name` always matches filename without extension
- `_process()` and `_physics_process()` only read state + trigger changes. No business logic.
- `_process()` is for non-physics visuals (UI, camera). `_physics_process()` for collision/movement.
- Heavy logic lives in plain methods called from the process hooks.

---

## 3. Game State Patterns

### 3.1 GameState Autoload (`game_state.gd`)

This is the single source of truth. Think of it like a global store:

```gdscript
class_name GameState
extends Node

# === Player Stats ===
@export var max_hp: int = 100
var hp: int = max_hp
var food_points: int = 99
var gold: int = 0
var level: int = 1

# === Floor State ===
var current_floor: int = 1
const max_floor: int = 30

# === Inventory ===
var inventory: Array[InventoryItem] = []
var equipment: Dictionary[StringName, WeaponOrArmor]   # keyed by slot name
```

**Every variable that a test or playtest might read must be here.** That means:
- Player HP, food, gold, level, position
- Current floor number
- Inventory contents (or at least counts/summarized state)
- Flags (e.g., `has_completed_floor`, `dragon_hatched`)

Each variable **must** have:
1. A comment describing what it represents
2. An initial value (default or exported)
3. Reset logic in `reset()`

### 3.2 Snapshot Pattern (`snapshot() / restore_snapshot()`)

For testing, the GameState must expose:

```gdscript
func snapshot() -> Dictionary:
    return {
        "hp": hp,
        "food": food_points,
        "gold": gold,
        "level": level,
        "inventory_size": inventory.size(),
        "current_floor": current_floor,
        # ... extend as needed
    }

func restore_snapshot(data: Dictionary) -> void:
    hp = data["hp"]
    food_points = data["food"]
    gold = data["gold"]
    # ... etc.
```

### 3.3 Event / Signal Pattern

GameState exposes signals for state changes so UI and entities can react:

```gdscript
signal player_hurt(amount: int)
signal player_died()
signal floor_changed(old_floor: int, new_floor: int)
signal item_pickup(item: InventoryItem)
```

When a signal fires, listeners update — not GameState itself. The signal is the **contract**, state mutation happens in `GameState`.

---

## 4. Scene Organization

### 4.1 File-to-Concept Mapping

| Concept | Scene file | Script class | Group(s) |
|---|---|---|---|
| Game (root) | `main.tscn` | `Main` | - |
| Player | `player.tscn` | `Player` | `player`, `character_body_2d` |
| Enemies | `enemies/*.tscn` | Various | `enemies` |
| Floor tiles | `floors/tilemap.tscn` | `TileMapLayer` | - |
| HUD/Stats | `hud.tscn` | `HUD` | `hud`, `ui_layer` |
| Inventory | `inventory_panel.tscn` | `InventoryPanel` | `inventory_ui` |

### 4.2 Scene Hierarchy Rules

- **One node per file.** Never put an entire dungeon in one scene. Each tilemap, entity type, UI panel is a separate scene that main instantiates.
- **Groups over hard links.** Add entities to groups (`enemies`, `pickups`, `interactables`) so other scripts can find them without hard-coded paths.
- **Node names unique within parent** for important nodes (player, doors). Groups for collections.
- **No deep nesting.** Scene tree depth ≤ 4 levels max. Split before getting deeper.

### 4.3 Instantiation Pattern

```gdscript
# GOOD - load once, instantiate as needed
var enemy_scene: PackedScene = preload("res://scenes/enemies/orc.tscn")

func spawn_enemy(pos: Vector2) -> void:
    var instance := enemy_scene.instantiate()
    instance.position = pos
    add_child(instance)
    instance.ready.connect(func(): pass)  # optional init hook
```

---

## 5. Domain-Specific Rules (Roguelike / Dungeon Crawler)

### 5.1 Maze / Floor Generation

- Floors are procedurally generated or hand-crafted tilemaps. Each new floor is a separate scene.
- **Room layout:** Generate rooms with connecting corridors. Fog of war applies per room.
- **Warp squares:** Colored tiles at the end of each room that transport to the next floor. Must require clearing the entire room first.

### 5.2 Turn-Based System

Movement = turn. Enemies act after the player completes a move. This is a **real-time-with-paused-turns** system:
- Player moves one tile → all living enemies get one action → repeat
- Standing still = free (no enemy turns)
- "Surrounded" is mechanically dangerous because every adjacent enemy gets one attack per player move

### 5.3 Food / Starvation Mechanic

This is a critical game mechanic from Dragon Crystal:

```gdscript
# Constants in GameState or DungeonConfig:
const FOOD_PER_STEP := 1        # food consumed per tile move
const FOOD_MAX := 99
const FOOD_CAKE_MIN := 11       # food from eating cake
const FOOD_MEAT_MIN := 42       # food from eating cooked meat

# In update():
if moves_this_floor > 0:
    food_points -= moves_this_floor   # subtract accumulated movement cost
    if food_points <= 0:
        hp -= calculate_starvation_damage()
```

### 5.4 Equipment System

Equipment slots map to stat modifiers:

| Slot | Type | Example |
|---|---|---|
| Head | Helmets | Bronze Helm (+2 HP), Iron Circlet (+3 HP) |
| Body | Armor | Robe, Leathers, Chainmail, Plate Mail |
| Main Hand | Weapons | Dagger, Sword, Mace, War Hammer |
| Off Hand | Shields/Rings | Shield, Power Ring, Hunger Ring (cursed!) |
| Consumable | Potions/Books/Rods | Heal Potion (red/orange), Map Book (green/brown) |

**Key mechanic:** Items are **unidentified** until used or thrown. Identified items get proper names in the inventory panel. This is the "hidden stats" roguelike tradition — colors matter, not descriptions.

### 5.5 Enemy Design

Each enemy type has a signature ability (one per unique enemy):

| Enemy | Signature Ability |
|---|---|
| Toad | Poisons player (HP over time) |
| Fire Diamond | Dizziness (randomized controls) |
| Ninja | Teleportation around map |
| Slime Blob | Splits into copies |
| Dragon Crystal boss | ??? |

Enemies should extend a base `Enemy` class with `attack()` and `ai()`:

```gdscript
class_name Enemy extends CharacterBody2D

enum EnemyType { TOAD, FIRE_DIAMOND, NINJA, SLIME_BLOB }
var _type: EnemyType
var hp: int = 10
var damage: int = 2

func attack(target: Node2D) -> void:
    # Basic attack — override in subclasses for special abilities
    target.hp -= damage
```

### 5.6 Map Representation

Maps are tile-based with coordinate system:

```gdscript
# Tile size: 32x32 pixels (standard for top-down)
const TILE_SIZE := 32        # pixels per tile
const MAP_WIDTH := 40         # tiles horizontally  
const MAP_HEIGHT := 30        # tiles vertically

# Floor data as array of arrays (row-major):
#   floor_data[tile_type][x][y] or similar structure
```

---

## 6. Testing Strategy

Every game mechanic gets a headless test in `tests/`:

| Criterion | Test file |
|---|---|
| Player moves via keyboard | `test_movement.gd` |
| Food decreases per tile moved | `test_starvation.gd` |
| Enemies spawn with correct HP | `test_enemy_ai.gd` |
| Inventory count updates on pickup | `test_inventory.gd` |
| Floor progression (warp squares) | `test_floor_progression.gd` |

**Test principle:** Tests check **visible game state via GameState**, not internal details. If a test can't read the result through `GameState`, the mechanic doesn't expose it properly.

---

## 7. Visual / Art Style

- **Tile size:** 32x32 or 48x48 pixels
- **Color coding:** Items use color-blind-safe palettes (red/orange = heal/poison, green/brown = map/spell)
- **Character appearance changes** when equipment tiers change (Robe → Leathers → Chainmail look different)
- **Dragon companion** appears after hatching: small egg → fledgling → adult dragon (visual stages per level milestone)

---

## 8. Performance Rules

1. Never instantiate objects in `_process()` or the game loop unless intentional (particles).
2. Preload scenes with `preload()` instead of `load()` for frequently used assets.
3. Pool enemies that are killed/respawned to avoid GC pressure: `ObjectPool`.
4. TileMaps use Godot's built-in tilemap layer — no manual sprite management for floors.

---

## 9. File-to-File Relationships (Cheat Sheet)

```
project.godot                ← [autoload] → game_state.gd (GameState)
main.tscn                    ← extends → main.gd
    └─ player_container       ← child of → Player (player.tscn → player.gd)
    └─ tilemap_layer          ← parent of → floor tiles
    └─ hud_container           ← child of → HUD (hud.tscn), reads GameState
        ├─ hp_bar              ← binds to GameState.hp
        ├─ food_bar            ← binds to GameState.food_points
        ├─ gold_display        ← bind to GameState.gold
        └─ inventory_button    ← opens InventoryPanel scene

enemy_pool                  ← pool of → enemy.tscn (preloaded)
dungeon_config.gd           ← constants for: floor themes, room layouts, drop tables
```

---

## 10. Anti-Patterns (Never Do This)

| ❌ Don't | ✅ Do Instead |
|---|---|
| `get_tree().get_root().find_node("Player").get_node(...)` | Use groups: `get_tree().get_nodes_in_group("player")` |
| Raw `Input.is_key_pressed(KEY_A)` | Use input actions from `project.godot` |
| Hard-code colors/tile sizes in script files | `const` or `@export` variables with descriptive names |
| Store game logic in multiple `.gd` files (spread state) | All mutable state on `GameState` |
| Deep scene hierarchies (>4 levels) | Split scenes, use instancing |
| Modifying GameState outside of `game_state.gd` | All mutations through GameState methods only |
