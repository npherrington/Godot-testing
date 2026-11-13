# GDScript Style Guide — Dragon Crystal

Last updated: 2026-11-13

## 1. File Structure

Every `.gd` file starts with:
```gdscript
class_name ClassName    # Must match filename exactly (without .gd)
extends Node            # or SceneTree, Node2D, etc.

## One-line purpose: what this class *manages*
## NOT how it works — that goes on functions below

var constant_like_value := 42     # new-style type inference for locals
```

**Always** at the top: `class_name` matching filename, then `extends`, then a doc comment summarizing purpose in one sentence.

## 2. Type Annotations

### Parameters and Returns — Always explicit
```gdscript
# GOOD - every parameter typed, return type declared
func find_item_by_type(item_type: Inventory.ItemType) -> InventoryItem?:
    for item in inventory:
        if item.type == item_type:
            return item
    return null

# BAD - implicit returns (lint errors or warnings)
func find_item(type: Inventory.ItemType):
    pass

# BAD - no parameters typed (harder to read intent)
func add_item(item):
    pass
```

### Inferred locals — new-style (`:=`) over old-style (`var x: Type = value`)
```gdscript
# GOOD - compiler infers type from initialization
var step := 10              # inferred int
var items := Array[Item]()  # generic array
var data: Dictionary[StringName, float]  # explicit dict typing

# BAD - redundant type annotation on init (old style)
var step: int = 10          # works but is verbose
```

### Use generics consistently for arrays and dictionaries
```gdscript
# GOOD
var enemies: Array[Enemy] = []
var drops: Dictionary[StringName, float]  # drop rate per item type

# BAD - untyped (lint error)
var enemies: Array = []       # Array is the wrong type hint
var drops: Dictionary = {}    # Ditto
```

## 3. Naming Conventions

| Category | Convention | Example |
|---|---|---|
| class_name / file | PascalCase / snake_case | `GameState`, `game_state.gd` |
| variables (pub) | snake_case | `max_hp`, `food_remaining` |
| variables (priv) | _snake_case | `_current_room`, `_last_damage_time` |
| constants | UPPER_SNAKE_CASE | `FOOD_PER_TURN = 1`, `MAX_LEVELS` |
| Signals | snake_case (past tense / event name) — per [official Godot docs](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html#naming-conventions) | `score_changed`, `enemy_spawned` |
| Enums | PascalCase class name, CONSTANT_CASE values — per [official Godot docs](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html#constants-and-enums) | `enum ItemType { HEAL, POISON }` |
| Groups (scene) | snake_case plural | `enemies`, `floor_tiles`, `pickups` |
| scenes files | snake_case | `player.tscn`, `hud.tscn` |

**Special names:** Always use Godot's built-in constants when available. Never magic numbers for these:
- Directional axes: `HORIZONTAL = Vector2.RIGHT.x` (don't hardcode `1`)
- Gravity: `ProjectSettings.get("physics/2d/default_gravity")` not `980`

## 4. Code Organization Within a File

Order of declaration in every file **(always this order)** — matches the [official Godot order](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html#code-order):

```gdscript
class_name ClassName
extends NodeType

## Doc summary

# --- 1. signals (come FIRST) ---
signal score_changed

# --- 2. enums ---
enum ItemType { HEAL, POISON, MAP }

# --- constants & @export (top-level or editor-exposed) ---
const MAX_LEVELS := 30
@export var max_hp: int = 100

# --- member variables (all types explicit) ---
var hp: int = max_hp
var _private_cache := Array[String]()

# --- 5. @onready (cached node refs, set right before _ready()) ---
@onready var health_bar: ProgressBar = $UI/HBar

# --- 6. Godot lifecycle hooks in order ---
func _init() -> void: ...
func _enter_tree() -> void: ...
func _ready() -> void: ...
func _process(delta: float) -> void: ...
func _physics_process(delta: float) -> void: ...
func _input(event: InputEvent) -> void: ...
func _unhandled_key_input(event: InputEventKey) -> void: ...

# --- 7. public methods (all typed signatures, doc comments for API) ---
func add_item(item: InventoryItem) -> bool:
    ## Add item to inventory if space available.
    ## @return true if added, false if inventory full

# --- 8. private methods (_ prefix) ---
func _calculate_damage() -> int:
    ...
```

**Rules:**
- Order is strictly the one above. Signals → Enum → Const → @export → regular var → onready → lifecycle → public → private.
- Group related variables with two blank lines between logical sections.
- Two blank lines between consecutive function blocks.

## 5. Indentation and Line Length

| Rule | Value |
|---|---|
| Indentation | **Tabs** (never spaces) per Godot official style guide and gdformat rules |
| Line length | Max ~90 characters. Break before operators not after assignment, or at commas in multiline calls |
| Trailing whitespace | None — strip trailing whitespace |
| Newlines between functions | Exactly two blank lines |

```gdscript
# GOOD - long lines broken at the dot operator
var result := calculate_damage(
    base_damage,
    level_modifier,
    enemy.resistance_type
)

# BAD - over-indented deeply
func nested_function():
    if condition:
        for item in list:
            print(item.value * 2.5 + extra_calculation())

```

## 6. Strings and Format Strings

Prefer format strings (`%` or `%s`) over string concatenation:
```gdscript
# GOOD - format string (fast, readable)
var msg := "Player hit for %d damage." % damage_amount

# GOOD - for complex multi-value messages
var report := "%(player)s took %(damage)d hits from %(enemy)s" % {
    "player": player_name,
    "damage": damage_amount,
    "enemy": enemy.name,
}

# BAD - string concatenation (slow and ugly)
var bad_msg := "Player hit for " + str(damage_amount) + " damage."
```

Use `str()` only for converting non-string values in error messages:
```gdscript
push_error("[GameState] Invalid floor: %s" % str(floor_number))
```

## 7. Collections and Iteration

### Arrays - always with type parameters, never untyped
```gdscript
# GOOD - typed array
var enemies := Array[Enemy]()
enemies.append(new_enemy)               # append adds one element
enemies += more_enemies                 # += works with other arrays

# BAD - untyped (lint error on `for e in enemies` without type hint)
var enemies: Array = []          # should be Array[Enemy]
```

### Dictionary iteration patterns
```gdscript
# GOOD - use built-in methods over manual index
for key in values.keys():
    ...

for value in values.values():
    ...

for key, value in values:         # tuple unpacking (cleaner than [key])
    ...

# Checking existence with is_key() not `in` on keys()
if values.is_key(target):        # O(1) vs iterating all keys
    ...
```

### Avoid for loops with indices where possible
```gdscript
# GOOD - enumerate when you need position AND value
var i := 0
for item in items:
    if item.is_valid:
        do_thing(item, i)
    i += 1

# Even better - use an explicit index variable outside the loop for counters
```

## 8. Conditional and Branching Patterns

### Use match over chained elif when there are multiple conditions on one variable
```gdscript
func describe_equipment(slot: Equipment.Slot) -> String:
    match slot:
        Equipment.Slot.HEAD: return "[Head]" + get_head_description()
        Equipment.Slot.BODY: return "[Body]" + get_body_description()
        _: return "[Unknown] " + str(slot)

# If elif is fine too, but match is more readable with 3+ branches on the same variable
```

### Always use early returns to avoid deep nesting
```gdscript
func take_damage(amount: int) -> bool:
    # Guard clause — exits early if no damage needed
    if amount <= 0:
        return false
    
    # Now we know amount > 0, so the rest is "happy path" logic
    hp -= amount
    if hp <= 0:
        die()
        return true
    return false
```

### No parentheses around conditions in `if` / `for` — they are optional and generally discouraged
```gdscript
# GOOD - no parens
if hp > 0:
    attack(enemy)

for item in inventory:
    print_item(item.type)

# BAD - unnecessary
if (hp > 0):
    ...
```

## 9. Godot-Specific Patterns

### `_ready()` — light initialization only
Think of it as `__init__` / `setup`. Load textures, connect signals during `_ready()`, but **never** start game logic here — that happens in a separate `start_game()` method called from the main scene.

```gdscript
func _ready() -> void:
    # Only setup — no "if first_frame" patterns
    var hud := $HUD as Control      # safe cast with 'as'
    player = find_player_node()     # reference to another node in tree
    
    # Connect signals during ready
    player.hp_changed.connect(_on_player_hp_changed)

func start_game() -> void:
    # Heavy initialization — called from main scene after setup
    load_floor(1)
    reset_to_initial_state()
```

### Use `as` for safe casting in Godot 4+
```gdscript
# GOOD - clean typing syntax (Godot 4.x)
var sprite := $Character as Sprite2D
var body := get_node("/root/GameState") as Node  # fallback if null

# BAD - old syntax
var sprite := ($Character as StringName)  # wrong operator precedence
```

### Never use `get_node("path/to/node")` with long strings — groups are your friend
```gdscript
# GOOD - via group (one-liner, works across scenes)
for enemy in get_tree().get_nodes_in_group("enemies"):
    ...

# GOOD - find children by name only one level deep
var target := $Player as CharacterBody2D   # direct child access with $name

# BAD - long string paths (breaks if someone renames a node)
var target := get_node("Root/Entities/Characters/Player")  # fragile
```

## 10. Comments and Documentation

Comment style uses `##` (doc comments) for public API, `#` for implementation details:

```gdscript
func add_item(item: InventoryItem) -> bool:
    ## Add item to inventory if space available.
    ## @param item The item instance to add
    ## @return true if added, false if inventory full
    if items.size() >= max_inventory:
        return false  # guard clause
    items.push_front(item)  # most recent at front of UI
    item_added.emit(item)              # direct signal call (Godot 4.x preferred over emit_signal())
    return true

func _calculate_resistance() -> float:       # private helper — no doc comment needed
    var base := 0.1 * level
    var armor_bonus := 0.05 * equipment.bonus_armor
    return clampf(base + armor_bonus, 0.0, 0.8)
```

**Never** write `# TODO` without a scope tag:
```gdscript
# @todo - design: implement item identification mechanic
# @fix - performance: cache tilemap neighbor lookups
# @hack - workaround for Godot node path issue; fix after refactor
```

## 11. Error Handling and Debugging

```gdscript
# Always use push_error() for game-breaking issues (shouldn't happen)
if not player_node:
    push_error("[Player] Missing player reference — game state may be corrupt")

# Use conditional print during development but remove before gate check runs
var debug_label := true  # toggle to disable prints without removing code

# Assertions with @warning_ignore (Godot 4.x warning suppression)
@warning_ignore("untyped_local_constant")
const DEBUG_MODE := false
```

## Summary Checklist Before Committing

- [ ] All parameter types?
- [ ] All return types declared?
- [ ] No untyped `Array` / `Dictionary` (use generics)?
- [ ] No magic numbers (constants for everything)?
- [ ] 4-space indentation throughout?
- [ ] Trailing whitespace removed?
- [ ] Two blank lines between function blocks?
- [ ] Private methods prefixed with `_`?
- [ ] Public API has `##` doc comment?
