# Code Patterns — Dragon Crystal Game

Copy-paste-ready patterns for common operations. Every pattern is tagged with what it solves.

---

## Pattern: Typed GameState Query

**Problem:** Scripts need to read state without coupling to specific scenes.

```gdscript
class_name GameManager extends Node

func get_player_position() -> Vector2:
    var player := get_tree().get_first_node_in_group("player") as CharacterBody2D
    if not player:
        push_error("[GameManager] Player node not found in 'player' group")
        return Vector2.ZERO
    return player.global_position


func set_health(value: float) -> void:
    ## Validate before writing — GameState validates its own state
    GameState.hp = clampf(value, 0.0, float(GameState.max_hp))
    GameState.changed.emit()


func get_equipment_count(item_type: Inventory.ItemType) -> int:
    var count := 0
    for item in GameState.inventory:
        if item.type == item_type:
            count += 1
    return count


## Snapshot helper — useful for tests and debugging
func debug_print_state() -> void:
    var snap := GameState.snapshot()
    print("GameState snapshot: %s" % str(snap))
```

---

## Pattern: Item Identification Lookup

**Problem:** Roguelike items are unidentified until first use — colors map to effects.

```gdscript
class_name ItemDB extends Object
## Central database mapping item colors + types to effect values.
## Unidentified items show only color; once identified, replace name with result.

enum Color { RED = 0xFF0000, GREEN = 0x00FF00, BLUE = 0x0000FF, BROWN = 0x8B4513 }
enum EffectType { HEAL_10, HEAL_25, POISON_10, MAP_REVEAL, SPEED_BOOST, CURSE_HUNGER }

@staticmethod
func identify(item: InventoryItem) -> Array[Variant]:
    ## Returns [effect_type, magnitude] for the item's color/type combination.
    ## This is the lookup used when player throws or uses unidentified item.
    
    match item.item_color:
        Color.RED:
            return [_EffectType.HEAL_10 if item.rarity == 1 else _EffectType.HEAL_25, 0]
        Color.GREEN:
            return [EffectType.POISON_10 if item.rarity == 1 else EffectType.HEAL_10, 10]
        Color.BLUE:
            return [EffectType.MAP_REVEAL, 0]
        Color.BROWN:
            return [EffectType.SPEED_BOOST, 5]
        _:
            push_error("[ItemDB] Unknown item color: %d" % item.item_color)
            return [null, 0]


## Once identified — update the InventoryItem in GameState so it gets a known name
@staticmethod
func apply_identification(item: InventoryItem, result: Array[Variant]) -> void:
    var (effect_type: EffectType magnitude: int) = result
    match effect_type:
        EffectType.HEAL_10:
            item.identifier := "Potion of Minor Healing"
        EffectType.HEAL_25:
            item.identifier := "Potion of Healing"
        EffectType.POISON_10:
            item.identifier := "Poison Vial (Minor)"
        _:
            item.identifier = "Unknown Item (%s)" % str(effect_type)
```

---

## Pattern: Spawn Enemy at Random Room Position

**Problem:** Enemies need to appear within bounds of the current room on the floor.

```gdscript
class_name RoomSpawner extends Node2D
## Spawns enemies within a rectangular boundary — the "room" area.

@export var min_distance_from_edges: float = 64.0    # keep enemies away from walls
var _spawn_positions := PackedVector2Array()


func find_spawn_points(room_rect: Rect2, count: int) -> Array[Vector2]:
    ## Find random spawn points within room_rect, keeping edges clear.
    var margin := min_distance_from_edges
    var available_x := rangei(
        room_rect.position.x + margin,
        room_rect.end.x - margin,
        32   # tile size = step
    )
    var available_y := rangei(
        room_rect.position.y + margin,
        room_rect.end.y - margin,
        32
    )
    var points := Array[Vector2]()
    for x in available_x:
        for y in available_y:
            points.push_back(Vector2(x, y))
    
    # Shuffle and take count
    _shuffle_array(points)
    return points.slice(0, count)


func _shuffle_array(arr: Array[Vector2]) -> void:
    """Fisher-Yates shuffle"""
    for i in range(arr.size() - 1, 0, -1):
        var j := randi() % (i + 1)
        var temp := arr[i]
        arr[i] = arr[j]
        arr[j] = temp
```

---

## Pattern: Turn-Based Move Queue

**Problem:** Players pick up food items — each pickup costs some movement turns to process.

```gdscript
class_name MoveProcessor extends Object
## Handles turn processing for player movement. 
## Each tile moved consumes 1 food point and gives enemies one action tick.

@onready var food_per_tile := 1.0

func move_player(from: Vector2, direction: Vector2) -> Dictionary:
    """Process one player movement step.
    
    Returns dict with: success (bool), new_position (Vector2), 
                       food_delta (float), enemy_actions_triggered (int)
    """
    var steps := maxf(1.0, direction.length())
    var new_pos := from + direction * steps
    
    # Check wall collision against GameState floor boundaries
    if is_out_of_bounds(new_pos):
        return {"success": false, "new_position": from, "food_delta": 0.0}
    
    # Consume food for movement
    var cost := food_per_tile * steps
    if GameState.food_points < cost:
        push_error("[MoveProcessor] Not enough food to move")
        return {"success": false, "new_position": from, "food_delta": 0.0}
    
    GameState.food_points -= cost
    
    # Each movement step = one enemy action tick
    var triggered := _process_enemy_actions()
    
    return {
        "success": true,
        "new_position": new_pos,
        "food_delta": -cost,
        "enemy_actions_triggered": triggered,
    }


func is_out_of_bounds(pos: Vector2) -> bool:
    """Check if position is outside floor tilemap bounds."""
    var bounds := DungeonConfig.floor_dimensions(current_floor())
    return (pos.x < 0 or pos.y < 0 
         or pos.x > bounds.width
         or pos.y > bounds.height)


func _process_enemy_actions() -> int:
    """Trigger one action per living enemy. Returns count of actions taken."""
    var action_count := 0
    for enemy in get_tree().get_nodes_in_group("enemies"):
        if not (enemy is Enemy) or enemy.is_dead():
            continue
        var result := EnemyAI.process_action(enemy, GameState.current_floor())
        if target_valid(result):
            _apply_damage_to_player(result.damage_amount)
        action_count += 1
    return action_count


func _apply_damage_to_player(amount: int) -> void:
    GameState.hp -= amount
    GameState.changed.emit()
```

---

## Pattern: Equipment Slot Management

**Problem:** Items go into slots (head, body, weapon, shield); replacing one auto-equips the new and unequips the old.

```gdscript
class_name EquipmentManager extends Node

enum Slot { HEAD = 0, BODY = 1, MAIN_HAND = 2, OFF_HAND = 3, CONSUMABLE = 4 }


func equip(slot: Slot, item: InventoryItem) -> InventoryItem?:
    ## Equip item in slot. Returns previously-equipped item (which goes back to inventory).
    var previous := get_equipment(slot)
    if previous != null:
        # Unequip — return to inventory
        GameState.inventory.push_front(previous)
    
    GameState.equipment[slot] = item
    
    # Apply stat modifiers from item
    apply_slot_mods(slot, item.item_value_dict())
    
    GameState.changed.emit()
    return previous


func unequip(slot: Slot) -> void:
    var item := get_equipment(slot)
    if item == null:
        return
    GameState.equipment[slot] = null
    _remove_slot_mods(slot, item.item_value_dict())
    GameState.changed.emit()


func swap(item_index_a: int, item_index_b: int) -> void:
    """Swap two inventory items (for when player drops one to pick up another of same slot)."""
    var temp := GameState.inventory[item_index_a]
    GameState.inventory[item_index_a] = GameState.inventory[item_index_b]
    GameState.inventory[item_index_b] = temp
```

---

## Pattern: Floor/Warp Square Detection

**Problem:** Player must clear room AND find colored teleport tile to advance.

```gdscript
class_name FloorProgression extends Node

signal floor_complete(floor_id: int, collected_gold: int)


func check_floor_progress(pos: Vector2, current_floor: int) -> bool:
    """Check if player standing on warp square at end of room.
    
    Returns true if progress trigger fire.
    """
    # Check if position is within the "exit zone" of current room
    var exit_zone := DungeonConfig.get_exit_zone(current_floor)
    if not exit_zone.has_point(pos):
        return false
    
    # Check if a warp square (colored tile) exists at this exact position
    var tile_type := get_tile_at_position(pos, "tiles")
    if tile_type == "warp_square":
        GameState.current_floor += 1
        floor_complete.emit(current_floor, GameState.gold)   # listeners receive both values
        return true
    
    return false


func get_tile_at_position(pos: Vector2, layer_name: String) -> String:
    """Lookup tile type at given world position (used for warp square detection)."""
    var map_layer := $MapLayer  # cached in _ready()
    if not map_layer:
        push_error("[FloorProgression] No MapLayer found")
        return ""
    
    var coords := to_local(pos)     # Convert world pos → tilemap coords
    var data := floor_data[coords.x][coords.y]  # [row][col]
    return data["type"] if "type" in data else "empty_floor"
```

---

## Pattern: Preload Scene Pool (for frequent creation/destruction)

**ProBLEM:** Creating PackedScene instances every frame = GC pressure. Pool them instead.

```gdscript
class_name ObjectPool extends Node
## Reuses instantiated scenes rather than creating new ones each time.
## Like a connection pool or object pool in backend systems — same concept.

var _scene: PackedScene
var _available := Array[Node2D]()    # free instances, invisible


func init(scene_path: String, initial_size: int = 50) -> void:
    _scene = preload(scene_path)
    for i in range(initial_size):
        var inst := _scene.instantiate() as Node2D
        add_child(inst)
        inst.visible = false
        _available.push_back(inst)


func acquire(pos: Vector2 = Vector2.ZERO) -> Node2D:
    if _available.size() > 0:
        var item := _available.pop_back() as Node2D
        item.position = pos
        item.visible = true
        return item
    
    # Pool exhausted — create new one (rare case, only during boss spawns)
    var fresh := _scene.instantiate() as Node2D
    add_child(fresh)
    fresh.position = pos
    fresh.visible = true
    return fresh


func release(item: Node2D) -> void:
    item.visible = false
    _available.push_back(item)
```

---

## Pattern: Damage Calculation (Pure Function for Service Layer)

**Problem:** Combat logic needs to be pure, testable, and not depend on nodes.

```gdscript
class_name CombatEngine extends Object
## Pure calculation layer — takes inputs, returns outputs. No Godot API calls.


enum DamageType { PHYSICAL, MAGICAL, MAGIC_RESIST }


func calculate_damage(
    base_attack: float,
    defense: float,
    level_bonus: int,
    resistance: float = 0.0,
    crit_chance: float = 0.1
) -> DamageResult:
    """Calculate final damage from attacker stats vs defender stats.
    
    @param base_attack: raw attack stat of attacker
    @param defense: defense stat of target (mitigates damage)
    @param level_bonus: +X damage per player level (flat modifier)
    @param resistance: resist chance that negates the entire hit
    @param crit_chance: probability roll for double damage
    """
    var effective_attack := base_attack + float(level_bonus) * 2.0  # +2 per level
    var damage_before_defense := maxf(effective_attack, defense)     # guarantee minimum
    var damage_after_defense := clampf(damage_before_defense - defense, 1.0, 99.0)
    
    if randf() < resistance:
        return _DamageResult.new(base_damage: damage_after_defense, is_crit: false, blocked: true)
    
    var is_crit := randf() < crit_chance
    var final_damage := (damage_after_defense * (2.0 if is_crit else 1.0)) as int
    
    return _DamageResult.new(
        base_damage: damage_after_defense,
        final_damage: final_damage,
        is_crit: is_crit,
        blocked: false,
    )
```

---

## Pattern: Toggle Debug Print on/off Without Removing Code

**Problem:** Want debug prints during dev but not pollute output for gate.

```gdscript
class_name PlayerController extends Node2D

var _debug := true     # set to false before committing / before running bin/check.sh


func _process(_delta: float) -> void:
    if _debug:
        print("[Player debug] vel.x=%.1f food=%.2f" % [velocity.x, GameState.food_points])
    
    move_toward_target()
```

---

## Pattern: Connect HUD to GameState Signals

**Problem:** UI must update whenever game state changes — but doing it in `_process()` is wasteful.

```gdscript
class_name HUDControl extends Control

func _ready() -> void:
    # Hook up all HUD bindings during setup, not every frame
    GameState.hp_changed.connect(_on_hp_changed)
    GameState.food_changed.connect(_on_food_changed)
    GameState.gold_changed.connect(_on_gold_changed)


func _on_hp_changed(current_hp: int, max_hp: int) -> void:
    $HealthBar.value = current_hp / max_hp * 100.0
    $HPLabel.text = "%d/%d" % [current_hp, max_hp]


func _on_food_changed(food: float) -> float:
    $FoodBar.value = food / 99.0 * 100.0
    if food < 20:
        $FoodWarning.visible = true   # flash warning when starving
    else:
        $FoodWarning.visible = false


func set_gold(amount: int) -> void:
    $GoldLabel.text = "$%d" % amount
```

---

## Pattern: Input Handling via Actions (Not Raw Keys)

**Correct way per Godot + this project's conventions:**

```gdscript
# In game_state.gd or player controller:
func _unhandled_key_input(event: InputEventKey) -> void:
    if event.keycode == ord("I"):  # inventory toggle — only for one-shot actions
        GameState.inventory_open = not GameState.inventory_open


## For continuous movement — use is_action_pressed NOT raw key codes:
func _physics_process(delta: float) -> void:
    var direction := Vector2.ZERO
    
    if Input.is_action_pressed("move_left"):
        direction.x -= 1
    if Input.is_action_pressed("move_right"):
        direction.x += 1
    if Input.is_action_pressed("move_up"):
        direction.y -= 1
    if Input.is_action_pressed("move_down"):
        direction.y += 1
    
    if direction != Vector2.ZERO:
        direction = direction.normalized()
        velocity = direction * move_speed

```

---

## Pattern: Error Recovery (When GameState Is Corrupt)

```gdscript
func validate_game_state() -> Dictionary:
    """Return a diagnostics report. If invalid, fix what's recoverable."""
    var issues := Array[String]()
    
    if GameState.hp < 0:
        push_error("[GameState] HP went negative! Reset to 0.")
        GameState.hp = 0
        issues.append("hp_underflow")
        
    if GameState.food_points > 99:
        GameState.food_points = 99
        issues.append("food_overflow")
    
    while GameState.inventory.size() > GameState.max_inventory:
        var removed := GameState.inventory.pop_back()   # drop oldest item
        push_error("[%s] Inventory over capacity, dropped: %s" % [removed.name])
        issues.append("inventory_overfull")
    
    return {success: issues.size() == 0, issues: issues}
```
