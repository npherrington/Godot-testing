# Domain Rules — Dragon Crystal Roguelike

Game-specific rules for implementing a dungeon-crawler/roguelike in the style of *Dragon Crystal* (Sega, 1990). These govern what the game does and how mechanics interact.

---

## 1. World Architecture

### 1.1 Floor Structure

The game has exactly **30 floors**. Each floor is a sequence of connected rooms:

| Concept | Rule |
|---|---|
| Floors | `floor_01` through `floor_30` — numbered sequentially in code |
| Rooms per floor | 3–5 rooms per floor, increasing as you progress (more complex) |
| Room sizes | 4×4 to 12×12 tiles (tiles = GridMap cells, each tile is a logical grid cell) |
| Corridors | At least one connecting corridor between adjacent rooms, at minimum 2 tiles wide |
| Final floor | `floor_30` contains the boss room with the Holy Goblet as the win condition |

### Floor Themes (by section from Dragon Crystal Wikipedia)

| Floor Range | Theme / Visual Style | Enemy Density |
|---|---|---|
| 1–5 | Trees, cacti, simple terrain | Low — tutorial-style |
| 6–10 | Sunflowers → Desert variants | Moderate |
| 11–15 | Easter Island statues | Medium — more varied enemies |
| 16–20 | Cave systems, underground water | Higher — tougher enemy combos |
| 21–25 | Ruins, ancient architecture | High |
| 26–30 | Hell/dragon temple, boss arena | Max difficulty |

### 1.2 Room Layout Rules

```
room_layout = {
    "rooms": [          # N rooms per floor
        {
            "grid_position": Vector2i(0, 0),   # which grid cell the room occupies
            "size": Vector2i(6, 4),             # width x height in tiles  
            "exits": ["east", "south"],          # which sides have corridor exits
            "exit_positions": [Vector2i(5, 1)],  # exact exit tile coordinates
        },
    ],
    
    "warp_square": Vector2i(7, 3),  # colored teleport tile (at end of room) — 
                                     # only appears after room is fully cleared
}
```

**Rules for layout generation:**
1. Corridors must be passable at all times (not gated by puzzles)
2. Exit zones are **only** on the edges opposite where you enter (fair routing)
3. Warp tile position: last 2×2 room tiles, color varies per floor theme

---

## 2. Combat Mechanics

### 2.1 Damage Formula (from CombatEngine pattern)

```gdscript
# Pure calculation — no Godot API calls
func calculate_damage(
    base_attack: float,
    defense: float,
    level_bonus: int,
    resistance: float = 0.0,
    crit_chance: float = 0.1
) -> DamageResult:
    
    var effective_attack := base_attack + (level_bonus * 2.0)
    var raw_damage := maxf(effective_attack, defense)   # minimum guaranteed damage
    
    if randf() < resistance:
        return blocked(true, damage_after_defense)
    
    var is_crit := randf() < crit_chance
    var final_damage := (damage_after_defense * (2.0 if is_crit else 1.0)) as int
    
    return DamageResult.new(
        base_damage: damage_after_defense,
        final_damage: final_damage,
        is_crit: is_crit,
    )
```

### 2.2 Enemy Ability Table (Signature Abitities)

Each enemy type has exactly **one unique ability** beyond basic melee:

| Enemy Type | Signature Ability | Counter Strategy |
|---|---|---|
| Toad | Poison (HP over several turns) | Heal before engaging or carry anti-poison |
| Fire Diamond | Dizziness (randomized controls for N seconds) | Wait it out — cannot be resisted by defense stat |
| Ninja | Teleportation to random position on floor | Position strategically; can teleport toward you |
| Slime Blob | Splits into copies when below 50% HP | Kill quickly before splitting |
| Fire Elemental | Area-of-effect damage in radius around it | Keep distance, use ranged attack if available |
| Skeleton Archer | Ranged attack at distance without moving | Close the gap first — melee range negates this ability |

### 2.3 Enemy Spawn Table (by floor section)

```gdscript
enum Section { EARLY = 1, MEDIUM_EARLY = 6, MEDIUM_LATE = 11, LATE_1 = 16, LATE_2 = 21, FINAL = 26 }

@staticmethod
func get_spawn_table(section: Section) -> Array[SpawnEntry]:
    match section:
        Section.EARLY: return [                   # mostly toads + basic skeletons
            SpawnEntry(toad, weight=70),
            SpawnEntry(skeleton_archer, weight=30),
        ]
        Section.MEDIUM_EARLY: return [
            SpawnEntry(fire_diamond, weight=25),    # introduce fire diamond at floor 6+
            SpawnEntry(slimes_blobs, weight=25),
            SpawnEntry(skeleton_archer, weight=30),
            SpawnEntry(toad, weight=20),
        ]
        Section.MEDIUM_LATE: return [              # ninja introduced here
            SpawnEntry(ninja, weight=25),
            SpawnEntry(fire_diamond, weight=25),
            SpawnEntry(slimes_blobs, weight=20),
            SpawnEntry(skeleton_archer, weight=30),
        ]
        Section.FINAL: return [                    # only boss and tough enemies
            SpawnEntry(boss_dragon, weight=1),     # only appears on floor 30
            SpawnEntry(ninja, weight=50),
            SpawnEntry(fire_elemental, weight=25),
            SpawnEntry(skeleton_warrior, weight=25),
        ]
```

### 2.4 Combat Flow (Turn Sequence — Roguelike Style)

1. Player moves one tile in any direction
2. Player's animation plays (movement) — no enemy actions yet
3. All **living enemies** take their action once:
   - If adjacent to player: attack
   - If ranged and in range: fire arrow/projectile
   - Else: move toward player
4. Enemies act **before** the player can act again
5. Standing still = **free** (no enemy turn)

> "This means getting surrounded can be particularly dangerous as every enemy gets one attack for every one attack the player makes." — Dragon Crystal Wikipedia

---

## 3. Food / Starvation System

| Constant | Value | Source |
|---|---|---|
| `FOOD_MAX` | 99 | Maximum food capacity |
| `FOOD_PER_STEP` | 10 | Food consumed per tile moved |
| `FOOD_CAKE_MIN` | 11 | Minimum food from eating cake |
| `FOOD_CAKE_MAX` | 27 | Maximum food from eating cake |
| `FOOD_MEAT_MIN` | 42 | Minimum food from eating meat |
| `FOOD_MEAT_MAX` | 46 | Maximum food from eating meat |

### Starvation Rules

```gdscript
func on_player_movement() -> void:
    GameState.food_points -= FOOD_PER_STEP
    
    if GameState.food_points <= 0:
        handle_starvation_tick()


func handle_starvation_tick() -> void:
    ## Player starves when food reaches 0. Takes HP damage each turn.
    var starvation_hp_loss := (1 + (floor_divide(GameState.current_floor, 5)) as int)
    
    GameState.hp -= starvation_hp_loss
    if hp_changed.is_connected(_on_hp_changed):
        emit("hp_changed", GameState.hp)
    
    if GameState.hp <= 0:
        handle_player_death(reason: "starvation")
```

**Eating items (consumables):** Food items heal hunger, not HP. Separate from the damage system. Eating food consumes **one turn** and is available in the inventory panel.

---

## 4. Item System Rules

### 4.1 Equipment Slots & Types

| Slot | What Goes Here | Example Rarities (Common → Legendary) |
|---|---|---|
| Head | Helmets, crowns, circlets | Bronze Helm → Iron Circlet → Dragon Crown |
| Body | Armor tiers | Robe → Leathers → Chainmail → Plate Mail |
| Main Hand | One-handed weapons | Dagger → Sword → Mace → War Hammer |
| Off-Hand | Shields, rings, amulets | Wooden Shield → Silver Ring → Power Amulet |

### 4.2 Item Identification (Roguelike Tradition)

```
Unidentified item display logic:
    color = get_item_base_color(item_type)     # determines the visual "cover" color
    display_name = "[?] Mystery [TypeLabel]"    # placeholder name
    
    When player uses it or throws it at enemy:
        effect := ItemDB.identify(color, item_type)
        save_identification(item.id, effect)
    
    When displaying the now-identified item in inventory:
        display_name = get_revealed_name(effect)  # e.g., "Potion of Healing"
        color = normal (no longer mystery-colored)
```

### 4.3 Cursed Items

Some items have hidden effects until you discover them:

| Curse | Effect | How to Reveal / Remove |
|---|---|---|
| Hunger Ring | Food depletes twice as fast | Use Bless Book to remove |
| Heavy Armor | Movement speed reduced by 50% | Use Identify scroll, then unequip |
| Cursed Sword | Attacks hit your own HP occasionally? | Throw at holy water / use Remove Curse tome |

---

## 5. Map Representation

### Tile Coordinates

```gdscript
const TILE_SIZE := 32        # pixels per tile (for scaling)
const MAP_WIDTH := 40         # tiles horizontally  
const MAP_HEIGHT := 30        # tiles vertically

# Floor layout is stored as a GridMap with:
# - floor_data[y][x] = TileType enum value for each cell
# - room_bounds = Array of Rect2 defining rooms  
# - warp_squares = Array of Vector2i where the player must step to reach next floor
```

### Color Coding System (items)

Color-blind-safe palettes only. Never rely on color alone — always show inventory entry with both name and icon:

| Color | Possible Effects | UI Label Until Identified |
|---|---|---|
| Red (+orange variants) | Heal, Fire damage | "Red [Type]" or just colored icon box |
| Green (+brown variants) | Map reveal, Speed boost | "Green [Type]" |
| Blue | Shield buff, Water effect | "Blue [Type]" |
| Yellow/Cyan | Special (rare) | Cyan/Yellow variant with sparkle |

---

## 6. Dragon Companion System

The dragon hatches at a level milestone and grows in stages:

| Milestone | Dragon Stage | Visual Change |
|---|---|---|
| Level 1–5 | Egg (follows player) | Small, wobbly egg sprite |
| Level 6–10 | Fledgling dragon | Tiny flying creature, red tint |
| Level 11–20 | Juvenile dragon | Full wingspans, blue/green flame animation |
| Level 21+ | Adult dragon | Large fly-over on boss floors, different particle effects |

### Dragon Behavior

- The dragon **never attacks** in early game (it protects by being visually present)
- At fledgling stage, it occasionally pecks at nearby enemies (minor auto-damage)
- At juvenile+, the dragon breathes fire on the nearest enemy group every 5 turns
- Adult dragon can one-shot certain weak enemy types

---

## 7. Boss Battle Rules (Floor 30 — Holy Goblet)

```gdscript
# Only appears on floor 30:
Boss fight layout:
    arena_size := Vector2i(8, 6)       # large room for combat  
    phases: 3                            # dragon changes attack pattern at HP thresholds
    
phase_1:
    boss_hp = 100
    ability: "fire_breath" — line AOE forward
    
hp <= 66 (phase 2):
    boss_summons_enemies = Array[SpawnEntry]([toad, skeleton_archer])
    ability: "fire_breath" + "summon"
    
hp <= 33 (phase 3):
    ability: "teleport_fire" — teleport to random position then shoot projectile
    
on_death:
    GameState.gold += 1000              # boss gold reward
    GameState.items_collected("holy_goblet")  # → WIN CONDITION
```

---

## 8. Inventory Constraints

| Limit | Value | Reason |
|---|---|---|
| Inventory slots (player) | 24 | Standard roguelike inventory size |
| Item stack limit per slot | 1 (like NetHack — no stacking except consumables of same type) | Each item occupies exactly one slot |
| Max carryable food items | No hard limit — food items are separate from equipment slots | Eating is handled by inventory, not a separate bar |
