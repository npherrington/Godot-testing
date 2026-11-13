# Design and Docs Index

Start here. This folder is the long-form reference for how the game is built. Agents load the
short versions, so use this table to decide which page answers which question.

| Who | Reads |
| --- | --- |
| Every agent, every session | `AGENTS.md` (rules, commands, layout) |
| Agents, on demand | `.opencode/skills/*/SKILL.md`: `gdscript-style`, `godot-scenes`, `godot-testing`, `godot-playtest`, `feature-plan`, `feature-spec` |
| People, planners, reviewers | These pages |

**Precedence:** `AGENTS.md`, then the skills, then these pages. If a page here contradicts a skill
or AGENTS.md, the page is wrong: fix it.

## Pages

| Page | Answers |
| --- | --- |
| [AGENTIC_GODOT.md](AGENTIC_GODOT.md) | How agents build and verify Godot work: the loop, the gate, the godot MCP, what the compiler catches, local-model tips |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Where state lives (`GameState`), signals, finding nodes, scene lifecycle, input, determinism |
| [GDSCRIPT_STYLES.md](GDSCRIPT_STYLES.md) | GDScript conventions for Godot 4.7: order, naming, typing, newer syntax, Godot 3 → 4 |
| [SCENES_AND_TSCN.md](SCENES_AND_TSCN.md) | The `.tscn` text format, writing scenes by hand, this project's scenes, `.uid` files |
| [TESTING_STANDARDS.md](TESTING_STANDARDS.md) | The test harness, its helpers, timing, input, isolation, randomness, signals |
| [PATTERNS.md](PATTERNS.md) | Verified, copyable code: pickups, HUD, enemies, spawning, game over, pure rules |
| [DOMAIN_RULES.md](DOMAIN_RULES.md) | Game-specific rules (owner-maintained; see below) |

Every page except DOMAIN_RULES.md was checked against Godot 4.7.2, gdtoolkit 4.5.0 and this repo's
harness on 2026-11-13. Each says what was checked.

---

## Principles

1. **The gate is the definition of done.** `bin/check.sh` passes, or the change isn't finished.
2. **Inspectable over clever.** State on `GameState`, things in groups, input through actions
   (AGENTS.md rules 1 to 3), so tests and the playtester can see everything a criterion is about.
3. **Every acceptance criterion gets a test** that fails without the feature (rule 4).
4. **Typed GDScript, current Godot 4 API.** The compiler is the cheapest reviewer an agent has
   (rule 5).
5. **The simplest thing that meets the criteria** (rule 6). No pools, layers or managers until a
   feature needs one.
6. **One feature file at a time**, each with three to six observable criteria (`feature-spec`
   skill). Bigger ideas become several files built in order.

## Current game

A top-down 2D game, 960×540, in a walled arena: a `Player` (CharacterBody2D) moving with WASD or
the arrow keys, `GameState` as the autoload, no image assets (shapes are `Polygon2D` /
`ColorRect`). Features are added one feature file at a time from `features/`.

---

## Game domain notes

The sections below were in this file before the docs rewrite of 2026-11-13. They are kept
**unchanged**, as the owner's domain notes, alongside [DOMAIN_RULES.md](DOMAIN_RULES.md). They
were not part of that review. Their code snippets predate the standards above, so where they
conflict (typing, `class_name`, writing other nodes' state directly), the standards win.

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

## 7. Visual / Art Style

- **Tile size:** 32x32 or 48x48 pixels
- **Color coding:** Items use color-blind-safe palettes (red/orange = heal/poison, green/brown = map/spell)
- **Character appearance changes** when equipment tiers change (Robe → Leathers → Chainmail look different)
- **Dragon companion** appears after hatching: small egg → fledgling → adult dragon (visual stages per level milestone)
