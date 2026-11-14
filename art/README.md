# art/: the source of every image in assets/

Every sprite, tile, UI piece and font glyph is a **letter matrix** in a Python script here, one
character per pixel, written to PNG by `pixel.py`. Edit the strings, rebuild, look at the render.
No PIL, no numpy: plain Python 3. This folder has a `.gdignore`, so Godot skips it. Previews go to
`art/out/`, which is gitignored.

```sh
python3 art/build.py                  # everything (also writes assets/palette.*)
python3 art/build.py slime ghost      # just these modules
python3 art/build.py --gifs slime     # plus GIF previews in art/out/slime/gifs/
python3 art/build.py --list
python3 art/peek.py assets/sprites/enemies/char_ghost_normal.png --rows 8-11 --scale 6
                                      # blow up sheet rows to look at (writes art/out/peek.png)
python3 art/audio/build_audio.py      # sounds and music (separate build)
```

A module is a `.py` file in `art/`, `art/enemies/`, `art/environment/` or `art/ui/` with a
`build()` function. `enemies/skeleton_warrior.py` is the reference character: read it before
drawing another one.

## The palette: 24 colours, one letter each

The spec allows 24 colours, and `pixel.COLOURS` holds exactly 24. Nothing else can be drawn.

| Ramp (dark to light) | Letters | For |
| --- | --- | --- |
| Stone and bone | `K D G L W` | outline, stone, iron, steel, bone, highlights |
| Wood, skin | `b B T S` | wood, leather, dirt, fur, skin, parchment |
| Red | `r R F` | blood, cloth, health, flesh, tongues |
| Fire | `r R O Y W` | flame, torchlight, gold (`Y`), rust (`O`) |
| Green | `v V E` | moss, goblin skin, slime, poison |
| Blue | `u U C I` | water, ice, magic, frost |
| Purple | `p P M` | robes, curses, magic glow |

Translucent letters reuse a palette colour at part alpha, so they don't add colours:

| Letter | Colour | For |
| --- | --- | --- |
| `_` | `K` | drop shadow |
| `~` | `G` | smoke |
| `:` | `L` | mist, dust |
| `;` | `I` | ghost veil, frost haze |
| `*` | `Y` | glow, sparks |
| `^` | `O` | fire haze |
| `=` | `C` | ice or arcane haze |
| `%` | `E` | poison mist |
| `&` | `M` | magic haze |
| `!` | `R` | blood mist, life drain |

`.` is empty.

## House style

These keep 20 monsters, the tiles and the UI looking like one game.

- **Outlines:**
  - A 1-pixel `K` outline goes round every character, prop and icon silhouette.
  - Inner lines use the material's darkest shade (`b`, `D`, `v`, `u`, `p`), not `K`, unless
    they're a deep gap.
- **Light:**
  - Light comes from the top left. Lighten the top and left edges of a form, and shade the bottom
    and right.
  - Use 2-3 shades per material (the spec's "2-3 tint shades per colour").
- **No anti-aliasing:**
  - Edges are hard.
  - Ordered dithering (`pixel.dither`, or a hand-drawn checker) is only for soft transitions:
    gradients, glows, mist.
- **Readable in the dark:**
  - The game is dark, with torchlight.
  - Give every monster bright eyes (`Y`, `R`, `C`, `E`, `W`, 1-2 pixels) and a silhouette no
    other monster shares.
- **Scale:**
  - A tile is 16x16.
  - A humanoid stands about 26-32 pixels tall in a 32x48 cell.
  - Big monsters use a 48x48 cell and stand up to about 44 tall.
- **Footing:**
  - Feet stand on the cell's baseline (`pixel.cell` and `pixel.baseline` put them there).
  - `write_character` adds a translucent drop shadow under them, so don't draw one.
  - Flying monsters hover a few rows above the baseline, over their shadow.
- **Originality:** draw everything fresh. Trace or copy nothing from another game's sprites.

## Characters

A character module builds a `pixel.Character` and calls `pixel.write_character` on it. That writes,
per state:

- `assets/sprites/<player|enemies>/char_<name>_<state>.png`: the sheet. Each row is one
  (animation, direction) pair, in the order the animations are given, with directions in
  `DIRECTIONS_4` or `DIRECTIONS_8` order. Frames run left to right.
- `char_<name>_<state>.tres`: a Godot `SpriteFrames` cutting that sheet. Each animation is
  named `<animation>_<direction>` (`walk_left`, `attack_up_right`), with its fps and loop set.
- `assets/animations/player.json` or `assets/animations/enemies/<name>.json`: frame size, the
  origin under the feet, the `AnimatedSprite2D` offset, rows and frame counts, fps, loop, and
  effects.
- `art/out/<name>/sheet_<state>@3x.png`: a contact sheet to look at.

Rules, which `write_character` asserts:

- **Player:**
  - 8 directions: `down`, `down_right`, `right`, `up_right`, `up`, `up_left`, `left`,
    `down_left`.
  - `idle` 4 frames, `walk` 8, `attack` 6, `defend` 2.
  - States `normal`, `injured`, `frozen` and `poisoned`, recoloured from `normal` by
    `pixel.STATES`.
- **Enemies:**
  - 4 directions: `down`, `up`, `left`, `right`.
  - `idle` 4 frames, `walk` 8, `attack` (plus an optional `attack2`), `special` 2-12, and `death`
    4-6, which doesn't loop.
- **Left is mirrored:** draw `right` (and `up_right`, `down_right`). `pixel.mirror()` adds the
  left-hand directions as flips.
- **Frame size:** every frame is a full cell: `(32, 48)` or `(48, 48)`.
- **Effects:**
  - Projectiles and ability effects (a thrown rock, a fireball, a web) are `pixel.Effect`s on the
    character.
  - Each is written as `fx_<name>_<effect>.png` with its own `SpriteFrames` (animation
    `default`), and listed in the JSON.

### Drawing a character fast

- **Draw only what changes.** Draw each pose at its natural size and build frames from it:
  - `cell()` places the pose on the cell.
  - Share rows between poses (`HEAD + legs_a`, as `skeleton_warrior.py` does).
  - `paste()` a weapon on.
- **Animate with the transforms:**
  - `shift` (bob, lunge)
  - `squash` and `stretch` (breathe, wind up)
  - `shear` (lean)
  - `silhouette` (hit flash)
  - `dissolve` (fade out, ghosts, death)
  - `rotate` (topple)
  - `recolour` (glow, charge-up)
- **Draw three views:** `down` (facing the camera), `up` (the back) and `right` (profile, facing
  right). Left is mirrored.
- **Look at every render.** Open `art/out/<name>/sheet_normal@3x.png`, and fix what reads badly:
  - stray pixels
  - a broken outline
  - a pose that jumps between frames
  - a walk that slides instead of stepping

## Environment and UI

- **Naming:**
  - Tiles: `tile_[type]_[variant].png`
  - Decorations: `decor_[type]_[variant].png`
  - Traps: `trap_[type]_[state].png`
  - UI: `ui_[component]_[state].png`
- **Animations:** animated pieces are strips written by `pixel.write_strip`. Each strip's JSON
  entry goes in `assets/animations/environment.json`.
- **Tile atlas:** tiles are 16x16 and also go into one atlas,
  `assets/tilesets/tileset_dungeon.png`, for a Godot `TileSet`. Its JSON names each tile's
  atlas coordinates.
