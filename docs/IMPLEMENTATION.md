# Torchlit Depths: Implementation Notes

As of 2026-11-13. These notes cover features 0001 to 0011 from `dragon_crystal_plan.md`.

The plan is now a playable turn-based dungeon crawler. The gate (`bin/check.sh`) passes every
step: format, lint, import, parse, scenes, 94 tests and the smoke run. Nothing is committed yet.

- **Title:** the plan describes a remake of an existing game. The features were built as an
  original roguelike, working title **Torchlit Depths**, using the project's own art. No content
  from the original game is recreated.
- **Process:** each feature went through plan, build, gate, a live playtest through the Godot
  MCP, and self-review. The per-feature notes are in `runs/<feature>/plan.md` and `playtest.md`
  (not committed), and the shared design is in `runs/ARCHITECTURE.md`. Every playtest verdict
  is PASS.
- **Harness untouched:** `bin/`, `tools/`, `.opencode/`, `opencode.jsonc`, the test harness
  scripts and the `[debug]` warning levels are unchanged.

## How to run and test

To play, run
`/Applications/Godot.app/Contents/MacOS/Godot --path ~/Desktop/godot-lab`, or open the project in
Godot 4.7 and press F5. The goal is to kill all 10 monsters.

| Key | Action |
| --- | --- |
| WASD / arrows | Move one cell (one turn) |
| Q E Z C, numpad 7 9 1 3, or two keys together | Move diagonally |
| Space / J, or walk into a monster | Attack |
| Shift / K | Defend (halves damage until your next turn) |
| F / Enter | Pick up an item; after death, return to the last checkpoint |
| I / Tab | Inventory (move keys pick a slot, F uses or equips it) |
| Esc / P | Pause menu: Resume, Save Game, Load Game, Restart, Quit |

Automated checks:

- `bin/check.sh` runs the full gate.
- `bin/test.sh` runs the headless tests only.
- `bin/test.sh combat` runs one file or method.

Saves are written to
`~/Library/Application Support/Godot/app_userdata/Torchlit Depths/` as `savegame.json` and
`checkpoint.json`. Delete them to start fresh.

## Architecture

### Grid

- One grid cell is 32x32 world pixels. It is drawn as 2x2 tiles from the 16 px tileset, so the
  tiles and the 32x48 characters share one pixel density.
- The arena is 32x32 cells (1024x1024 px), with walls around the edge. The player starts at
  cell (16, 16).
- `scripts/grid.gd` (`Grid`) holds `CELL`, `to_world`, `to_cell`, `DIRS_8` and Chebyshev
  `distance`.
- A Camera2D follows the player, limited to the arena.

### Turn loop

1. The player submits one action (move, attack, defend, pick up or use) to `TurnManager`.
   This is only possible when `GameState.phase == "player"`, no menu is open and the game isn't
   over.
2. The action resolves, and the phase becomes `"enemy"`.
3. After 6 frames, every enemy's turn is queued in group order. Each turn resolves before the
   next one starts.
4. The round ends:
    - statuses tick (poison does 3 damage; freeze skips a turn);
    - trap cooldowns tick;
    - a pending checkpoint save is written;
    - `turn += 1` and the phase returns to `"player"`.

The queue stops and clears as soon as the player dies.

### State

`GameState` (autoload) owns all state that tests and saves need:

- health, player_cell, turn, phase, statuses, defending;
- inventory and equipped items;
- combat_log, explored and visible cells;
- menu, checkpoint, game_over;
- the seeded RNG.

`snapshot()` is also the save format. It adds the enemy, item, trap and checkpoint lists.

### Scene tree (`scenes/main.tscn`)

```
Main
├── Darkness (CanvasModulate)
├── World (y-sorted)
│   ├── Dungeon (TileMapLayers: Floor, Shadows, Walls)
│   ├── Traps / Checkpoints / Items / Enemies
│   ├── Player (Sprite, Camera, Torch light, TorchSound)
│   ├── Torches, MistA, MistB
│   └── FogOfWar
├── Ambience (AudioStreamPlayer)
├── TurnManager
└── HUD (CanvasLayer)
```

### Scripts

| Script | Role |
| --- | --- |
| `grid.gd` | Grid constants and cell/world conversion |
| `dungeon.gd` | Arena and room generation, walkability, line of sight, A* paths, torch spots |
| `player.gd` | 8-way input, input buffer, step and attack animations |
| `turn_manager.gd` | Action queue, enemy phase, end of round, action resolvers |
| `enemy.gd` | Waking, the per-type behaviours, health bar, death |
| `monster_database.gd` | Stats and behaviour for every monster type |
| `item_database.gd`, `item.gd` | Item definitions and world pickups |
| `trap.gd`, `checkpoint.gd` | Traps and checkpoint shrines |
| `fog_of_war.gd`, `torch_light.gd`, `mist.gd`, `wall_torch.gd` | Lighting and atmosphere |
| `save_system.gd` | JSON save and load of the snapshot |
| `hud.gd` | Health, stats, statuses, turn label, log, inventory, pause menu, game over |
| `main.gd` | Spawns the world and rebuilds it after a load |

Nodes are found by group (`player`, `enemies`, `items`, `traps`, `checkpoints`, `torches`,
`dungeon`, `turn_manager`) or by unique name. Art is loaded behind `ResourceLoader.exists()`
checks, so a missing sprite falls back to a coloured shape.

## Features delivered

| Feature | What it delivers | Tests |
| --- | --- | --- |
| 0001 Project setup | Project named Torchlit Depths; 1920x1080 window; pixel-art filtering; all input actions | `test_project_setup.gd` (4) |
| 0002 Player character | Animated 32x48 hero; 8-way grid movement with diagonal grace and key repeat; camera follow | `test_player_character.gd` (7), `test_player_movement.gd` (4) |
| 0003 Dungeon framework | 32x32 walled arena; 4 rooms (3x3 interior, one door each); tile layers; no corner cutting | `test_dungeon.gd` (6) |
| 0004 Enemy AI | Enemy scene; wakes within 5 cells with line of sight; A* chase; adjacent attack; health bar; death | `test_enemies.gd` (6) |
| 0005 Combat manager | Turn controller, ordered action queue, poison and freeze, turn indicator, combat log | `test_combat.gd` (10) |
| 0006 Monster database | 10 spawned monster types plus Slime Spawn, each with its own movement (table below) | `test_monsters.gd` (14) |
| 0007 Item system | 24-slot inventory; sword +4 ATK; shield +2 DEF; potion heals 40; F to pick up | `test_items.gd` (9) |
| 0008 Trap system | 6 traps (pressure plates, spike walls); 10–15 damage through armour; 10-turn re-arm | `test_traps.gd` (6) |
| 0009 Lighting and atmosphere | Flickering torch light, fog of war (radius 6), wall torches with smoke, mist, ambience | `test_lighting.gd` (8) |
| 0010 Save and load | JSON save/load from the pause menu; 2 checkpoint shrines; F after death reloads the checkpoint | `test_save_load.gd` (7) |
| 0011 UI / HUD | Health bar with lagging damage bar, stats, status icons, turn label, log, inventory grid, pause menu | `test_hud.gd` (7) |

`tests/test_assets.gd` (6) comes from the art pipeline, not from these features.

### Monsters

| Monster | HP | Melee | Behaviour |
| --- | --- | --- | --- |
| Skeleton | 20 | 5–8 | Chases you |
| Ghost | 15 | 4–7 | Passes through walls |
| Goblin | 15 | 3–5 | Throws rocks (4–6, range 4) |
| Slime | 24 | 4–6 | Hops; splits into two Slime Spawn (8 HP) when hit |
| Ogre | 40 | 10–14 | Lumbers: acts every other turn |
| Spider | 16 | 4–6 | Ambush: wakes at 3 cells; webs freeze you |
| Zombie | 25 | 5–7 | Shambles; bites poison you |
| Dark Mage | 18 | 3–5 | Keeps its distance; shadow bolt (5–8, range 5) |
| Wolfman | 22 | 5–8 | Sprints two cells a turn |
| Imp | 12 | 4–7 | Moves erratically; fireball (4–7, range 3) |

## Design decisions

- **Original title.** Mechanics only. Nothing is taken from the game the plan names.
- **32 px cells.** The 16 px tiles and 32x48 characters didn't fit one grid. Drawing each cell
  as 2x2 tiles keeps all art at its native pixel size.
- **Fixed seeds.** The map, spawns and RNG are seeded, so tests and playtests are repeatable.
  The RNG state is saved as a string.
- **Input buffer.** Keys pressed during a step animation are kept for 12 frames, so fast play
  doesn't drop inputs. The buffer is skipped while dead or while a menu is open.
- **Placeholder item icons.** The sword, shield and potion are 16x16 pixel art built in code.
  Real art at `assets/sprites/items/item_<id>.png` replaces them automatically.
- **Headless audio.** Ambient sound starts only when there is a display, because a sound still
  playing when a headless run quits is reported as a leak.
- **Torch sound muted.** The generated torch loop pulses at about 7 Hz over a low roar and
  sounds like a helicopter. It no longer plays, and the ambience is lowered from -8 dB to
  -18 dB.
- **Code limits.** gdlint caps a class at 20 public methods, so save file I/O moved from
  `GameState` into `SaveSystem`.

### Balance tuning

A scripted bot played whole runs: it grabs the gear, drinks potions below 40 health and fights
the nearest monster. Before tuning it died on turn 30 with 2 of 10 kills. Four values changed:

| Value | Before | After |
| --- | --- | --- |
| Base attack | 6 | 8 |
| Enemy notice range | 7 cells | 5 cells |
| Potion heal | 30 | 40 |
| Starting potions | 0 | 2 |

After tuning, the same bot reached turn 112 with 8 kills. Most of its deaths were from traps,
which it doesn't avoid. Tests use `GameState.BASE_ATTACK` rather than a hard-coded number.

## Bugs found in playtesting and fixed

| Bug | Fix |
| --- | --- |
| Key presses during a step animation were dropped | 12-frame input buffer |
| All monsters were visible through the fog at the start | `main.gd` emits `changed` after spawning, so the fog updates |
| Monsters kept attacking after the player died | The queue stops and clears on game over (regression test added) |
| The F press used to revive was also buffered as a pickup | No buffering while dead or in a menu |
| A checkpoint spawned next to a trap | Checkpoints skip cells next to traps |
| A pause-menu message overlapped the Quit button | The panel is laid out with a VBox |
| The MCP couldn't click the pause buttons | The buttons have names now |
| Audio was reported as leaking when headless tests quit | Ambient sound only starts with a display |
| The torch sound was like a helicopter | Torch loop muted; ambience lowered |

## Changes outside the new files

- `tests/test_project_setup.gd` was rewritten. The old file used a Godot 3 test framework and
  already failed the gate.
- `tests/test_player_movement.gd` was updated for grid steps. It still has the same 4 checks.
- `project.godot` gained the name, window size, texture filter and input actions.

## Open items

- [ ] No victory screen when all monsters are dead; none of the features asked for one.
- [ ] The layout is the same every run. Random seeds per run would be an easy next step.
- [ ] Item art: add `assets/sprites/items/item_<id>.png` to replace the placeholder icons.
- [ ] Torch sound: regenerate a softer crackle in `art/audio/sfx.py`, then re-enable it in
      `main.gd`.
- [ ] `features/0001-godot-project-setup.md` has the same number as `0001-coins-and-score.md`,
      which was left alone.
- [ ] Traps are the main cause of death. Consider making unfired traps easier to spot.
- [ ] Commit the work once it has been reviewed.
