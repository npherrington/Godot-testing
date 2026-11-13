# Architecture Guide — Dragon Crystal Game

## 1. Core Principle: One Source of Truth

All mutable game data lives on the `GameState` autoload singleton. This is your global store, like a Redux store or a MongoDB document for user state. Nothing else should hold authoritative game data.

```gdscript
# GOOD - only GameState knows if player is dead
func is_player_alive() -> bool:
    return GameState.hp > 0

# BAD - scattered state across multiple objects
if enemy.has_died and _player_health <= 0:   # where does health come from?
    ...
```

## 2. Service vs Entity Separation

Godot's node system blurs these but your code should not. Split logic into two categories:

### Services (pure systems, no visual representation)

These manage game-wide mechanics and have no visual component:

| Service | Files that implement it |
|---|---|
| Damage calculations | `combat_engine.gd` |
| Floor generation | `dungeon_gen.gd` |
| Item identification logic | `item_db.gd` (table lookup, not UI) |
| Turn processing queue | `turn_manager.gd` |

**Properties of services:**
- They may or may not be nodes (often they are plain classes with no scene)
- They don't contain rendering code
- They take data in, compute result, return data out
- They call methods on GameState when state needs to change

### Entities (objects that exist on screen)

These represent visual things that appear in the game world:

```gdscript
## Entity — has a presence on-screen and responds to input/environment
func _physics_process(delta: float) -> void:
    move_toward_target()
    handle_collision()

## NEVER put pure calculation here. Delegate to service instead.
func attack(entity: Enemy) -> void:
    var result := CombatEngine.calculate_damage(   # call to service
        self.attack_power,
        entity.resistance,
    )
    GameState.apply_damage(target, result.final_damage)
```

**Rule:** If code calculates damage, generates tiles, or looks up drop tables, it goes in a **service**. If code renders an explosion, plays a sound, moves a sprite — it belongs to the **entity**.

## 3. State Mutation Flow

### Pattern: Event → Service (Pure) → GameState (Mutation) → Signal (React)

```
Player pushes W key
    → Input event fires
    → PlayerController._physics_process reads input
    → Calls CombatEngine.move_player(direction, floor)
    → CombatEngine calculates movement & returns new position
    → GameState.update_player_position(new_pos)
    → GameState emits player_moved(new_pos)
    → HUD listens and updates
```

### State mutations must go through methods, not direct property writes

**Never** do this anywhere except inside GameState:
```gdscript
GameState.hp -= 10  # ❌ bypasses validation
```

Always route through a method with a guard:
```gdscript
func take_damage(amount: int) -> bool:
    if amount <= 0:
        push_error("Invalid damage amount: %d" % amount)
        return false
    hp = clampi(hp - amount, 0, max_hp)
    if hp_changed.is_connected(_on_hp_changed):
        # guard against re-entrancy on death
        hp_changed.emit()     # direct signal method, not emit_signal("name") in Godot 4.x
    if hp <= 0:
        _on_player_died()
    return hp == 0
```

## 4. Signal Design Patterns

### Signals are method signatures, not events with payloads you interpret later

Be explicit about every signal's data contract:
```gdscript
# GOOD - typed signals (Godot 4.x, per official naming guide: snake_case)
signal score_changed(value: int)
signal enemy_spawned(enemy_id: Enemy.EnemyType, at_pos: Vector2)

# BAD - PascalCase signal names (against Godot convention)
signal ScoreChanged(value: int)   # doesn't match Godot's snake_case recommendation  
signal EnemySpawned(...)          # same issue
```

### GameState emits; everyone else listens

Signals create a one-way dependency chain. The emitter doesn't know who is listening — that decoupling lets you swap UI or add new listeners without changing the emitter:
```gdscript
func on_pickup(item: InventoryItem) -> void:
    gold += item.gold_value
    inventory.push_front(item)
    # no one needs to know about these consequences
    gold_changed.emit(gold)        # HUD listens via signal connection
    inventory_updated.emit(item)   # inventory UI panel listens via signal connection
```

## 5. Scene Management

### Loading and instantiation flow

All scenes are preloaded at the class-level:
```gdscript
class_name EnemySpawner extends Node2D   # one name per file

var _enemy_scenes: Dictionary[StringName, PackedScene] = {
    "toad": preload("res://scenes/enemies/toad.tscn"),
    "fire_diamond": preload("res://scenes/enemies/fire_diamond.tscn"),
    "ninja": preload("res://scenes/enemies/ninja.tscn"),
}
```

Always use `preloading` in the class body, never `load()` inside functions except during `_ready()`:
```gdscript
func _ready() -> void:
    # load at startup time only (one-time cost)
    var floor1 := preload("res://scenes/floor_01.tscn").instantiate() as Node2D
    get_parent().add_child(floor1)
```

### Scene hierarchy depth rule

Maximum **4 levels** of nesting from root scene down to visual element:
```
main.tscn (root — Node2D)                     ← 1
├── floor_tilemap.tscn (TileMapLayer)          ← 2
├── player.tscn (CharacterBody2D)              ← 2
├─→ $Sprite2D                                 ← 3 (deep within instantiated scene)
├── hud_ui.tscn (Control)                      ← 2
├─→ $VBoxContainer/HBar [health bar]           ← 3
└── enemies_parent [Node2D, group "enemies"]   ← 2
```

If you find yourself at level 5+, break the scene into an intermediate container.

### Node discovery rules

In order of preference:

1. **$direct-child path** — for a specific node that this script owns
2. **Groups** — `get_tree().get_nodes_in_group("enemies")` for collections across scenes
3. **@onready var with $path** — for nodes needed once at _ready() and cached

```gdscript
var enemy_spawn_area: Area2D      # discovered by group, not name-matching
  
func _ready() -> void:
    # 1) Direct child access (this script owns it)
    player := $Player as CharacterBody2D         
    
    # 2) Onready cache for nodes that need the tree to exist first
    @onready var background: TextureRect = $Background   # one lookup at _ready
    
    # 3) Groups for dynamic collections
    for enemy in get_tree().get_nodes_in_group("enemies"):
        pass   # operate on all enemies regardless of parent node hierarchy
```

## 6. The Main Scene — Bootstrap Pattern

The root scene (`main.tscn`) is your bootstrap: it connects GameState to scenes but doesn't hold game state itself:

```gdscript
class_name Main extends Node2D

var _current_floor := 1

func start_game() -> void:
    load_floor(_current_floor)
    
    # Connect GameState signals to UI updates (one-time setup per scene instance)
    GameState.hp_changed.connect(_on_hp_changed)
    
func _on_hp_changed(current_hp: float, max_hp: float) -> void:
    $HUD/HHealthBar.value = current_hp / max_hp * 100.0
    
func load_floor(floor_id: int) -> void:
    # Clear previous floor nodes
    for child in get_children():
        if child is TileMapLayer or child.name == "Enemies" or child.name.begins_with("player"):
            child.queue_free()
    
    # Load new floor data from GameState service
    var floor_data := DungeonGen.generate_floor(floor_id)
    GameState.set_current_floor(1, floor_data)
```

## 7. Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|---|---|
| Multiple scripts reading/writing `hp` directly on different objects | All HP mutation goes through `GameState.apply_damage()` |
| Scene A finds Scene B's node by hard-coded path | Use groups or signals |
| Services calling GameState methods for state that doesn't actually change | Validate before emitting — no-op changes waste signal listeners |
| Godot lifecycle functions (`_process`, `_physics_process`) doing calculations — they only read state and trigger actions | Move calculation to plain methods, call from process hooks |
| Passing GameState around as a constructor argument everywhere | It's an autoload (singleton) on every frame, accessible by name without reference |
