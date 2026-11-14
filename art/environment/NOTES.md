# Environment art: usage notes

Built by `python3 art/build.py env_tiles env_traps env_props env_effects env_room`.
Sources are letter matrices in `art/environment/` (`_chest.py` holds the chest drawings the
Mimic reuses). Previews go to `art/out/environment/`; start with `mock_room@3x.png`.

## Files

**Tiles: `assets/tilesets/`** (16x16; also packed in the atlas)

| Group | Files |
| --- | --- |
| Floors (8 kinds) | `tile_floor_stone_a/b/c`, `cobble_a/b`, `dirt_a/b/c`, `moss_a/b`, `wood_a/b`, `ice_a`, `water_a` (animated), `lava_a` (animated) |
| Wall faces (4 materials x 3) | `tile_wall_{stone,brick,cave,moss}_{intact,cracked,ruined}` |
| Wall caps | `tile_wall_{stone,brick,cave,moss}_cap` |
| Doors (16x32, two tiles) | `tile_door_{wood,metal,magic}_{closed,open}_{top,bottom}`; `magic_closed_*` animated |
| Stairs | `tile_stairs_down`, `tile_stairs_up` |
| Secret passage | `tile_secret_stone_closed` (a faint door-shaped seam and a worn handhold), `tile_secret_stone_open` |
| Shadow overlays | `tile_shadow_n`, `tile_shadow_w`, `tile_shadow_nw` (translucent) |
| Atlas | `tileset_dungeon.png`, `.json` (name -> `[column, row]`, animated frames/fps, `solid`, `groups`), `.tres` |

Every floor tiles with itself, and the variants of one kind mix freely (they share their edge
joints). Pick variants at random, weighting `_a` highest. Animated tiles also come as frame strips
with their own `SpriteFrames` `.tres`.

**Sprites: `assets/sprites/environment/`**

| Group | Files |
| --- | --- |
| Decorations (25 kinds) | `decor_pillar_stone`, `pillar_broken`, `statue_guardian`, `altar_stone`*, `rubble_a/b`, `bones_a/b`, `skull_a`, `skull_pile`, `barrel_a`, `crate_a`, `table_wood`, `chair_wood`, `bookshelf_a`, `bed_cot`, `weapon_rack`, `coffin_a`, `urn_a`, `sack_a`, `mushrooms_a`, `candles_lit`*, `torch_wall`*, `brazier_standing`*, `banner_red/purple`, `chains_hanging`, `cobweb_left/right` |
| Chest | `decor_chest_closed`, `decor_chest_open`, `decor_chest_trapped`, `decor_chest_opening`* (play once) |
| Traps | `trap_pressure_plate_up/down`, `trap_spike_wall_retracted/extending/extended`, `trap_spike_wall_extend`* and `_retract`* (play once), `trap_arrow_idle`, `trap_arrow_firing`* (play once), `trap_arrow_projectile` (points right; rotate it) |
| Effects | `fx_fire_loop`*, `fx_smoke_loop`* (translucent), `fx_fog_a/b` (64x64 tileable translucent mist), `fx_blood_a..d` (floor decals) |
| Light | `light_torch.png` |

`*` is an animated strip with a `SpriteFrames` `.tres` (one animation, `default`). Canvases are
16x16, 16x32 or 32x32. `assets/animations/environment.json` lists every sprite with its size or
frame size, fps, loop, `origin` and `mount`. Floor props stand on the canvas bottom (origin is the
bottom centre: put it on the bottom edge of the cell they stand in) and carry their own
translucent drop shadow. Wall props (`mount: "wall"`) hang from the canvas top, which goes at the
top of the upper wall face. Trap states and the pressure plate are also atlas tiles.

## Animation

| What | Frames | fps | Loop |
| --- | --- | --- | --- |
| Wall torch, brazier, fire | 4, 4, 6 | 6 | yes |
| Candles, altar candles, magic door shimmer, smoke | 4, 4, 4, 6 | 5 | yes |
| Water, lava (tiles) | 4 | 4 | yes |
| Chest opening, spike wall extend/retract, arrow firing | 4 each | 6 | no |

All loops are seamless: water and lava scroll 4 px a frame round a 16 px tile, smoke puffs rise
2 px a frame 12 px apart, and the shimmer bands repeat every 8 px at 2 px a frame.

## Collision

The TileSet has one physics layer (layer 1). A full-tile square is on every wall face and cap,
`tile_door_*_closed_bottom`, `tile_secret_stone_closed`, `trap_spike_wall_*` and `trap_arrow_*`.
Open doors, door tops, floors (water and lava too), stairs, the pressure plate and shadows have
none. The JSON's `solid` list matches.

## Wall layout

Walls are one cell thick in the map but drawn two faces (32 px) tall, so they stand a little
taller than a character:

```
row 0   cap  cap  cap  cap  cap      rock around the room: caps
row 1   face face DOOR face face     upper faces: overlay layer, no collision
row 2   face face door face face     the back wall's cells: lower faces
row 3   cap  floor ...   floor  cap  side walls: caps
...
row N   cap  cap  cap  cap  cap      front wall: caps
```

1. **Walls layer** (collision on). A wall cell whose south neighbour is open shows a lower face:
   intact, cracked or ruined (ruined has rubble at its foot), or a door bottom, the secret
   passage, an arrow trap or a spike wall. Every other wall cell shows its material's cap.
2. **Upper faces** (an overlay `TileMapLayer`, collision off). It goes one cell above each lower
   face, using the same face tile, or the `_top` half above a door. With y-sorting, a character
   north of a thin wall is hidden behind it, as 3/4 should be.
3. **Shadows** (overlay above the floor, below props): `tile_shadow_n` on the floor row under a
   back wall, `tile_shadow_w` down the floor column beside a west wall, `tile_shadow_nw` in that
   corner. The light comes from the top left, so east and south walls cast none.

Side walls show only caps, so doors are drawn for back (north-facing) walls. A face also stacks
under itself, if you want walls taller still.

## Using the TileSet and the light

- Set a `TileMapLayer`'s `tile_set` to `res://assets/tilesets/tileset_dungeon.tres`: source id 0,
  16x16. Look up atlas coordinates by name in `tileset_dungeon.json`
  (`set_cell(cell, 0, Vector2i(col, row))`). Animated tiles play by themselves.
- Torch light: give a `PointLight2D` the texture `res://assets/sprites/environment/light_torch.png`
  (128x128, white with stepped, dithered alpha). With `texture_scale` 1.5 it lights a radius of
  about 6 tiles. Try a warm colour such as `Color(1, 0.82, 0.55)` and a dark `CanvasModulate`
  (about 0.28 grey). Keep texture filtering on Nearest so the bands stay crisp. The light is not
  palette art. `mock_room_lit@3x.png` approximates the result.
- Set the bottom of `fx_smoke_loop` on its source. Repeat and slowly scroll `fx_fog_a`/`_b`
  (`texture_repeat`, or a `TextureRect`/`Parallax2D`) for drifting fog.
