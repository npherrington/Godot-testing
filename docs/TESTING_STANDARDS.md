# Testing Standards — Dragon Crystal Godot Lab

Writing and maintaining headless tests for the Godot game. This project uses a custom test harness (`tests/test_case.gd`, `tests/runner.gd`, etc.) — not Godot's built-in Testing Framework. These standards cover what to test, how to write it, and when it counts as done.

---

## 1. What Every Feature Needs

**Every acceptance criterion from a feature file maps to one or more test cases.** No exceptions. If you can't verify it in a headless test, the feature is incomplete regardless of what it "looks like."

```
Feature: "Player health decreases when hit"
    → test_player_takes_damage()
    → test_damage_caps_at_max_hp()            # edge case
    → test_undamaged_player_health_is_unchanged()  # regression guard
```

---

## 2. Test File Naming

```
tests/test_<feature_name>.gd          # one file per feature/concept
tests/test_cashe.gd                   # harness (don't edit)
tests/parse_check.gd                  # harness (don't edit)
tests/runner.gd                       # harness (don't edit)

# Examples:
test_player_movement.gd               ✅ existing, already follows naming
test_dragon_crystal_spawn.tscn        ❌ wrong — .tscn test file extension
test_enemy_ai_combat.gd               ✅
test_floor_progression.gd             ✅
```

---

## 3. Test File Structure (Every Test File)

Every test file starts with the harness import:

```gdscript
extends "res://tests/test_case.gd"

# Test class must extend test_case — never write raw code without the parent class

## Brief description of what this tests
## Example: Tests for player movement mechanics, food consumption, and boundary detection.


func test_player_moves_right_while_move_right_is_held() -> void:
# Every method name starts with 'test_' — runner.gd only picks these up
    
    var main := await spawn("res://scenes/main.tscn")
    var player := main.get_node("Player") as Node2D
    
    var start_x := player.global_position.x
    hold_action("move_right", 20)    # built-in helper from test_case parent
    
    var moved := player.global_position.x - start_x
    check(moved > 20.0, "player should move right, moved %.1f px" % moved)


func test_walls_keep_player_inside_arena() -> void:
    var main := await spawn("res://scenes/main.tscn")
    var player := main.get_node("Player") as Node2D
    
    hold_action("move_left", 240)    
    check(
        player.global_position.x >= 32.0,
        "player passed left wall: x=%.1f" % player.global_position.x
    )
```

### Key Rules for Test Files

| Rule | Why |
|---|---|
| Must `extend "res://tests/test_case.gd"` | Runner picks up only these tests |
| Method names must start with `test_` | Same reason — the runner uses introspection |
| Never call `_ready()` or `_process()` in tests | The harness handles game loop timing via `await physics_frames(N)` / `await spawn()` |

---

## 4. Assertion Helpers (What's Available)

The `test_case.gd` parent class provides these built-in helpers — **use them, don't write your own**:

```gdscript
# From test_case.gd (the parent harness class):

check(condition: bool, message: String)          # generic assertion (any condition)
check_eq(a: Variant, b: Variant, context: String = "")  # equivalent values
check_neq(a: Variant, b: Variant, context: String = "") # not equal
check_gt(a: Variant, b: Variant, context: String = "")  # greater than  
check_lt(a: Variant, b: Variant, context: String = "")  # less than
check_gte(a: Variant, b: Variant, context: String = "") # >=
check_lte(a: Variant, b: Variant, context: String = "") # <=

# All fail the test and print the message if assertion is false
```

### When to Use Which

| Condition | Helper | Rationale |
|---|---|---|
| `true/false` check on a value comparison | `check()` + manual boolean expression | Most flexible, works for > checks or complex conditions |
| Exact equality of two values | `check_eq(a, b)` | Clearer intent than `check(a == b)` |
| Inequality | `check_neq(a, b)` | Same — explicit negation |
| Numeric comparisons (>, <, >=, <=) | Dedicated helpers (`check_gt`, `check_lt`, etc.) | Less code + consistent error messages from harness |

---

## 5. Game State Assertions vs Node Assertions

**When you can read the value through GameState → assert on GameState.** This is the ground truth:

```gdscript
# GOOD - asserts on shared state nobody should lie about
func test_player_takes_damage_from_enemy() -> void:
    await spawn("res://scenes/main.tscn")
    var initial_hp := GameState.hp          # read from source of truth
    
    # ... deal damage to player ...
    
    check_eq(GameState.hp, initial_hp - damage_amount, "HP should decrease by damage amount")


# BAD - asserts on a node's variable that might be out of sync with GameState
func test_player_takes_damage_from_enemy() -> void:
    var main := await spawn("res://scenes/main.tscn")
    var player := main.get_node("Player") as Node2D
    check_eq(player.hp, initial_hp - damage_amount, "HP should decrease")  # ❌ unreliable
```

### GameState is ground truth even for non-state values

If you need to check something the game produces but isn't tracked in GameState, **add it to GameState**. Never assert directly on UI nodes or visual elements — they are display-only.

```gdscript
# BEFORE (bad: asserting on a label's text)
check(hud.find_child("HPLabel").text == "90/100", "HUD displays remaining HP")

# AFTER (good: add hp_display to GameState, read from there)
# Add to GameState:
var hp_display_text: String = ""  # in snapshot() and reset() too!
func update_hp_bar(new_hp: int) -> void:
    hp_display_text = "%d/%d" % [new_hp, max_hp]

check_eq(GameState.hp_display_text, "90/100", "HP text format correct")
```

---

## 6. Test Timing Helpers (Built Into Harness)

Every test must handle timing correctly. The harness gives you these helpers:

| Helper | What It Does | Use Case |
|---|---|---|
| `await spawn(path: String)` | Instantiates a scene and waits for it to be in-tree | Starting the game or a sub-scene |
| `hold_action(action_name: String, duration_frames: int)` | Hold an input action for N frames | Continuous movement while test runs |
| `key_press(key_name: String)` | Single key press event | One-shot inputs (inventory toggle, activate) |
| `physics_frames(n: int)` | Wait N physics ticks (usually 1 frame at fixed FPS) | Pause in-game time within test |
| `wait_seconds(seconds: float)` | Real-time wait outside Godot's clock | Long-running tests or timeouts |

### Timing Pattern for Each Kind of Test

**Movement test — hold input for duration, then check final position:**
```gdscript
func test_player_moves_up() -> void:
    var main := await spawn("res://scenes/main.tscn")
    var player := main.get_node("Player") as Node2D
    
    hold_action("move_up", 60)           # hold for 60 frames
    
    check(player.global_position.y < 100.0, "player should move up past y=100")
```

**Single-action test — press once, wait for result:**
```gdscript
func test_pickup_item() -> void:
    var main := await spawn("res://scenes/main.tscn")
    
    key_press("pickup")                    # single tap
    physics_frames(10)                     # short pause to process
    
    check_eq(GameState.inventory.size(), 1, "inventory has exactly one item")
```

**Long-running test — wait for specific condition:**
```gdscript
func test_enemies_spawn_over_time() -> void:
    var main := await spawn("res://scenes/main.tscn")
    
    physics_frames(30)                     # 30 ticks in-game
    check_eq(GameState.enemies_spawned, 2, "two enemies have spawned after 30 ticks")
```

---

## 7. Test Organization Rules

### One test per assertion, not grouped assertions

```gdscript
# GOOD - each test covers one behavior
func test_player_moves_up_when_move_up_pressed() -> void:
    ...
func test_player_moves_down_when_move_down_pressed() -> void:
    ...
func test_player_still_if_no_input() -> void:
    ...

# BAD - one big test for multiple things (one assertion fails, you don't know which broke)
func test_movement_systems() -> void:
    hold_action("move_up", 10)
    check(player.y < start_y, "up")
    
    hold_action("move_left", 10)
    check(player.x > start_x, "left")  # ← if this fails, you don't know what's wrong
    
    hold_action("", 5)                   # no movement
    check_eq(prev_pos, player.pos, "stopped")
```

### Tests should be independent (no shared state between them)

Every test **starts fresh** — it doesn't rely on a previous test having run:

```gdscript
func test_player_takes_damage() -> void:
    var main := await spawn("res://scenes/main.tscn")
    # GameState starts at default values from reset() — never assume it was touched earlier
    check_eq(GameState.hp, 100, "starting HP is 100 (from GameState.reset())")
    
func test_player_has_zero_gold() -> void:
    await spawn("res://scenes/main.tscn")
    # Don't rely on "test_player_takes_damage" running first!
    check_eq(GameState.gold, 0, "starting gold is 0")   # fresh GameState = fresh gold
```

---

## 8. Test Coverage Checklist — What Must Have Tests

Every mechanic in the domain must have at least one test covering its happy path:

| Mechanic | Required Test(s) | File |
|---|---|---|
| Player movement (WASD/dpad) | `test_player_movement.gd` ✓ | ✅ done |
| Food consumption per tile moved | `test_starvation_food_decreases_per_tile()` | new file |
| Eating food restores hunger | `test_eating_restores_food()` | new file |
| Enemy movement toward player | `test_enemy_ai_moves_toward_player()` | new file |
| Enemy ability (each type) | One per enemy in `test_enemy_abilities.gd` | new file |
| Item pickup increases inventory count | `test_pickup_increases_inventory()` | new file |
| Warp square advances floor | `test_warp_square_changes_floor()` | new file |
| Floor 30 wins game | `test_holy_goblet_on_floor_30_says_win()` | new file |
| HP decreases when damaged | `test_player_takes_damage()` | new file |
| Death at zero HP | `test_player_dies_at_zero_hp()` | n

ew file |

---

## 9. Test Writing Anti-Patterns (Never Do This)

| ❌ Don't | ✅ Do Instead | Reason |
|---|---|---|
| Assert on UI node text/position directly | Assert on GameState values, then verify HUD binds to them separately | UI → state; not state → UI. Tests check the logic. |
| Use hardcoded frame counts for timing | Use `physics_frames(N)` or `hold_action()` consistently | Frame counts vary by target FPS |
| Sleep with real-time waits (`OS.delay_msec()`) | Use harness helpers (`physics_frames`, `await spawn()`) | Real-time sleeps are unreliable in headless tests |
| Write integration tests that touch too many subsystems | Split into unit-like behavior tests | Failure debugging is harder with big assertions spread across 20 lines |

---

## 10. When Tests Run

| Trigger | Command | What it checks |
|---|---|---|
| Before every commit (in `bin/check.sh`) | Full run | format → lint → import → parse → tests → smoke |
| Manually while working | `bin/test.sh <filter>` | Only matching tests |
| After `bin/format.sh` fails | `bin/test.sh` | Tests may still pass even if formatting failed — don't skip |

---

## 11. Writing a New Test (Step-by-Step Example)

Let's say we're adding the food mechanic and need our first test:

```gdscript
extends "res://tests/test_case.gd"


### Test: Player loses one food unit per tile moved ###

func test_one_tile_move_consumes_exact_food_units() -> void:
    var main := await spawn("res://scenes/main.tscn")
    var starting_food := GameState.food_points            # 99 at reset
    var player := main.get_node("Player") as Node2D
    
    hold_action("move_right", 10)                        # move 1 tile (10 frames ≈ 1 second at 60 fps
    
    check_eq(GameState.food_points, starting_food - FOOD_PER_STEP,
             "food decreases by exactly one unit per step"
```

---

## Test Writing Checklist Before Committing

- [ ] Every test method name starts with `test_`
- [ ] Each assertion uses `check()`, `check_eq()`, or the dedicated helper (not raw `assert_eq()` calls)  
- [ ] Assertions read from GameState, not individual node properties
- [ ] Tests are independent — they don't share state across test runs
- [ ] No hardcoded timing — use harness helpers (`hold_action`, `physics_frames`)
- [ ] Test covers a single behavior per function (one responsibility each)
