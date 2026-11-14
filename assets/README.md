# assets/: the game's art and sound

Everything here is **generated**. Don't edit these files by hand:

- Images come from the letter-matrix scripts in `art/`; see `art/README.md`.
- Sounds come from `art/audio/`.

To change something, edit its script and rebuild:

```sh
python3 art/build.py                 # every image, plus palette.png/.gpl/.hex
python3 art/build.py player ghost    # just these modules
python3 art/audio/build_audio.py     # every sound and track
```

All art is original and uses one 24-colour palette: `palette.png`, `palette.gpl` (GIMP or
Aseprite) and `palette.hex`. Translucent pixels (shadows, smoke, mist, glows) reuse those colours
at part alpha.

## Layout

```
assets/
├── sprites/
│   ├── player/        char_player_<state>.png/.tres (normal, injured, frozen, poisoned)
│   ├── enemies/       char_<monster>_normal.png/.tres, fx_<monster>_<effect>.png/.tres
│   ├── environment/   decor_*, trap_*, effects, light_torch.png
│   └── ui/            ui_<component>_<state>.png
├── tilesets/          tile_<type>_<variant>.png, tileset_dungeon.png/.json/.tres
├── fonts/             BMFont: .fnt + page PNG
├── sounds/sfx/        sfx_<category>_<action>.ogg
├── sounds/music/      music_<theme>_<variant>.ogg
└── animations/        player.json, enemies/<monster>.json, environment.json, ui.json
```

## Pixel art in Godot

- **Nearest filtering:** use nearest filtering, or every sprite blurs. Either set Project Settings →
  Rendering → Textures → Canvas Textures → Default Texture Filter to **Nearest**, or set
  `texture_filter = TEXTURE_FILTER_NEAREST` on the nodes that draw art.
- **Scale:** the game renders at 960x540 and is stretched to the window (`canvas_items`). One art
  pixel is two screen pixels at 1920x1080.

## Characters

Each character sheet comes with a ready `SpriteFrames` resource (`.tres`) beside it. Its animations
are named `<animation>_<direction>`.

| | Directions | Animations (frames) | fps |
| --- | --- | --- | --- |
| Player, 32x48 | `down down_right right up_right up up_left left down_left` | `idle` 4, `walk` 8, `attack` 6, `defend` 2 | 5, 10, 10, 6 |
| Enemies, 32x48 or 48x48 | `down up left right` | `idle` 4, `walk` 8, `attack` (and maybe `attack2`), `special`, `death` 4-6 | 5-10 |

- **Looping:** `attack`, `defend`, `special` and `death` don't loop. Wait for `animation_finished`,
  then go back to `idle`. For `death`, free the node instead.
- **Origin:** every frame has the feet at the same point.
  - The JSON in `animations/` gives that point (`origin`).
  - It also gives the `AnimatedSprite2D` offset (`godot_offset`) that puts the feet on the
    node's position, so a character's `position` is where it stands.
  - A drop shadow is baked in under the feet.
- **Effects:** projectiles and ability effects are `fx_<monster>_<effect>.tres`, with one
  animation, `default`. Each monster's JSON lists its effects and what its `special` does.
- **Player states:** `char_player_injured`, `_frozen` and `_poisoned` are the same frames
  recoloured. Swap the `SpriteFrames` and keep the animation playing.

```gdscript
@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D

const DIRECTIONS_8: Array[String] = [
	"right", "down_right", "down", "down_left", "left", "up_left", "up", "up_right"
]


func _ready() -> void:
	sprite.sprite_frames = load("res://assets/sprites/player/char_player_normal.tres")
	sprite.offset = Vector2(0, -22)  # godot_offset in assets/animations/player.json
	sprite.play("idle_down")


## The 8-way direction name for a movement vector (Godot's y points down).
func direction_name(v: Vector2) -> String:
	return DIRECTIONS_8[wrapi(roundi(v.angle() / (PI / 4.0)), 0, 8)]


## Enemies have four directions.
func direction_name_4(v: Vector2) -> String:
	if absf(v.x) > absf(v.y):
		return "right" if v.x > 0.0 else "left"
	return "down" if v.y > 0.0 else "up"


func set_state(state: String) -> void:  # "normal", "injured", "frozen", "poisoned"
	var animation := sprite.animation
	var frame := sprite.frame
	sprite.sprite_frames = load("res://assets/sprites/player/char_player_%s.tres" % state)
	sprite.play(animation)
	sprite.frame = frame
```

### Monsters

| Monster | Cell | Animations | Effects (`fx_<monster>_<effect>`) | Notes |
| --- | --- | --- | --- | --- |
| `skeleton_warrior` | 32x48 | idle 4, walk 8, attack 6, special 8, death 6 | - | Melee fighter: a rusty short sword and a dented helm. Special: reassemble (collapses into bones and rises again). |
| `ghost` | 32x48 | idle 4, walk 8, attack 7, special 9, death 6 | - | A pale wailing spirit with black eye hollows, long-fingered sleeves and a veil tail; hovers and drifts through walls. Special: phase (turns to veil and fades to two eye-lights, then fades back in). |
| `goblin` | 32x48 | idle 4, walk 8, attack 6, attack2 5, special 7, death 6 | `rock` | A runty green goblin with huge ears, a hooked nose and yellow eyes, in ragged leather, throwing rocks (fx rock). Special: taunt (a cocky hop, arms up, tongue out). |
| `slime` | 32x48 | idle 4, walk 8, attack 7, special 8, death 6 | - | A low lime blob with a half-digested skull inside; hops to move, lunges to engulf. Special: split (stretches, pinches and divides into two slime_small). |
| `slime_small` | 32x48 | idle 4, walk 8, attack 6, special 6, death 5 | - | Half a slime: a small lime blob with a bone inside, spawned in pairs when a slime splits; quick hops. Special: squish (flattens to the floor to duck, pops up). |
| `spider` | 48x48 | idle 4, walk 8, attack 6, special 7, death 6 | `web_shot`, `web` | A giant cave spider: dark bulbous abdomen with pale chevrons, eight red eyes, pale fangs, long high-kneed legs; bites. Special: web (spits fx web_shot, which leaves fx web on the floor as a trap). |
| `ogre` | 48x48 | idle 4, walk 8, attack 7, special 9, death 6 | `shockwave` | A huge hunched ogre: tan hide, pot belly, tiny tusked head, pelt loincloth, a studded club on its shoulder; overhead smash. Special: slam (drives the club into the floor and sends out fx shockwave, a ring of dust). |
| `dark_mage` | 32x48 | idle 4, walk 8, attack 6, special 10, death 6 | `shadow_bolt` | Caster: a hooded sorcerer in purple robes, yellow eyes in a shadowed hood, a staff with a glowing orb. Attack raises the staff and throws a shadow bolt. Special: blink (dissolves into magic haze and reforms). |
| `zombie` | 32x48 | idle 4, walk 8, attack 6, special 10, death 6 | - | Slow shambler: a hunched, rotting grey-green corpse in a torn shirt, one arm reaching, dragging a stiff leg. Attack is a lunging grab and bite. Special: rise (claws up out of the floor, hands first). |
| `harpy` | 32x48 | idle 4, walk 8, attack 6, special 8, death 6 | `gust`, `feathers` | Flying attacker: a bird-woman with a red feather crest, yellow eyes, brown hawk wings for arms and yellow talons, hovering over its shadow. Attack is a talon dive. Special: screech (a wing gust that throws wind and feathers). |
| `mimic` | 32x48 | idle 4, walk 8, attack 6, special 10, death 6 | - | Disguised as treasure: the game's chest, until its lid opens on fangs, a tongue and glowing eyes. Walks by hopping. Attack is a wide chomp. Special: reveal (the lid creaks, eyes open in the gap, then the mouth gapes). |
| `basilisk` | 48x48 | idle 4, walk 8, attack 6, special 8, death 6 | `gaze` | Petrifying gaze: a squat six-legged crested lizard-serpent with olive scales, a bony crown and spine spikes, and burning yellow eyes. Attack is a lunging bite. Special: petrifying gaze (eyes flare, a grey-stone beam goes out). |
| `wolfman` | 32x48 | idle 4, walk 8, attack 6, attack2 6, special 8, death 6 | `howl` | Pack hunter: a hunched grey werewolf in torn trousers with yellow eyes and long claws. attack: claw swipe; attack2: lunging bite. Special: howl (head thrown back, sound rings call the pack to it). |
| `imp` | 32x48 | idle 4, walk 8, attack 6, special 10, death 6 | `fireball` | Fireball caster: a small red devil with ivory horns, purple bat wings, a spade tail and a wide grin, hovering. attack: hurls a fireball (fx fireball). Special: blink (vanishes in a puff of smoke and reappears). |
| `medusa` | 48x48 | idle 4, walk 8, attack 7, special 8, death 6 | `stare` | A gorgon: a woman's torso with gold bands on a coiled green snake tail, a crown of hair-snakes and glowing green eyes. Slithers. attack: tail lash. Special: stone stare (hair-snakes rear, eyes flash, a pale ring-wave rolls out and petrifies). |
| `goblin_king` | 48x48 | idle 4, walk 8, attack 6, attack2 6, special 9, death 6 | `war_cry` | Elite goblin boss: big and broad, a lopsided gold crown, an ermine-trimmed red cape, scrap armour and a heavy cleaver. attack: cleaver chop; attack2: shoulder bash. Special: war cry (raises the cleaver and roars; a gold aura pulses out and buffs nearby goblins). |
| `ice_elemental` | 48x48 | idle 4, walk 8, attack 6, special 9, death 6 | `ice_shard`, `frost_nova` | A floating figure of jagged ice round a glowing core, shards orbiting it, hovering over its shadow. attack: hurls an ice shard (fx ice_shard). Special: frost nova (draws its shards in, then a ring of frost bursts out across the floor and freezes; fx frost_nova). |
| `hellhound` | 48x48 | idle 4, walk 8, attack 6, special 8, death 6 | `fire_breath` | Lean charcoal hound split by glowing ember cracks, with a flaming mane and tail and burning eyes; bites with a lunge. Special: fire breath (rears back and pours a cone of flame from its jaws; fx fire_breath). |
| `vampire` | 32x48 | idle 4, walk 8, attack 6, special 8, death 6 | `drain` | Gaunt pale noble: slicked black hair, red eyes and fangs, a high-collared black cape lined in red; rakes with its claws. Special: life drain (throws the cape open like bat wings and pulls in streams of blood mist; fx drain). |
| `troll` | 48x48 | idle 4, walk 8, attack 6, special 8, death 6 | `regen` | Tall, gangly troll: mossy grey-green hide, a knobbed hunched back, arms that drag its knuckles, a hooked nose and small yellow eyes; swipes with a long arm. Special: regenerate (hunches, glows green as motes of life rise, straightens healed; fx regen). |
| `lich` | 48x48 | idle 4, walk 8, attack 7, attack2 8, special 10, death 6 | `death_bolt`, `nova`, `summon_circle` | The final boss: a floating skeletal sorcerer-king in tattered purple robes, jagged gold crown, cold blue eye-lights, a soul-gem in its open ribcage and a horned staff. Attack: death bolt (fx death_bolt). Attack 2: staff-slam nova (fx nova). Special: raise dead (lifts the staff, a summoning circle burns into the floor and bony hands claw up; fx summon_circle). |

## Tiles and the dungeon

Full notes: `art/environment/NOTES.md`. Preview: `art/out/environment/mock_room@3x.png` (after a
build).

- **TileSet:** `tilesets/tileset_dungeon.tres` is a ready `TileSet`.
  - One atlas source (id 0) of 16x16 tiles.
  - A physics layer for collision: walls, caps, closed doors, the closed secret passage, and
    the spike-wall and arrow traps.
  - Animated tiles (water, lava, the magic door) play by themselves.
  - `tileset_dungeon.json` maps each tile's name to its `[column, row]`:
    `layer.set_cell(cell, 0, Vector2i(col, row))`.
- **Floors and walls:**
  - 8 floor kinds, 15 tiles, all seamless; mix the `_a`/`_b`/`_c` variants at random.
  - 12 wall faces: stone, brick, cave and moss, each intact, cracked or ruined.
  - 4 wall caps.
- **Wall layout:**
  - A wall is one cell thick but drawn two faces tall.
  - The wall cell itself shows the lower face, with collision.
  - The same face goes one cell above it, on an overlay `TileMapLayer` with no collision.
  - Side and front walls show caps. The notes have the diagram.
- **Special tiles:**
  - Wooden, metal and magic doors, open and closed, each 16x32 as top and bottom halves.
  - Stairs up and down.
  - The secret passage, closed and open.
  - The pressure plate, and shadow overlays for under the walls.
- **Decorations:**
  - `sprites/environment/` holds 25 kinds of `decor_*`, including chests (closed, open,
    trapped, opening), plus `trap_*` and `fx_*` (fire, smoke, fog, blood).
  - Animated ones have a `SpriteFrames` `.tres` with one animation, `default`.
  - `animations/environment.json` lists every sprite's size, frames, fps, loop and anchor.
  - Floor props stand on their bottom edge; wall props hang from their top.
- **Torchlight:**
  - Give a `PointLight2D` the texture `sprites/environment/light_torch.png`, at about
    `texture_scale = 1.5` and colour `Color(1, 0.82, 0.55)`.
  - Under a dark `CanvasModulate` (about 0.25 grey), this lights about 6 tiles round a torch.

## UI and font

Full notes, with `TextureProgressBar`, 9-slice and font code: `art/ui/NOTES.md`. Preview:
`art/out/ui/mock_hud.png`.

- **Health bar:**
  - `ui_healthbar_under`, `_progress`, `_damage` and `_over` make two stacked
    `TextureProgressBar`s. The damage bar lags behind and drains.
  - `ui_healthbar_flash` is the hit flash, 12 fps, no loop.
- **Inventory:**
  - `ui_inventory_panel` has 24 slots, 6x4. Slot (col, row) is at `(8 + 22*col, 24 + 22*row)`.
  - `ui_inventory_slot_{normal,hover,selected,disabled}`, plus the animated
    `ui_inventory_highlight`.
- **Commands:**
  - `ui_button_{normal,hover,pressed,disabled}`, a 9-slice with margin 4.
  - `ui_icon_{attack,defend,item,magic,wait,flee}`.
  - `ui_cursor_arrow`, plus the animated `ui_cursor_bob`.
- **Menus:** `ui_menu_background` is a tileable 64x64 dungeon wall. `ui_panel_frame` is a
  9-slice with margin 8.
- **Status icons:** `ui_status_{poison,freeze,burn,petrified}`.
- **Fonts:**
  - `fonts/font_dungeon.fnt` (white glyphs) and `font_dungeon_outline.fnt` (with a baked 1-px
    dark outline, for text over the game world).
  - BMFont, ASCII 32-126.
  - Use `font_size` 16 (1:1) or 32 (2x). Other sizes scale unevenly.

## Sound

Full notes: `art/audio/README.md`.

- **Sound effects:** 34 in `sounds/sfx/`, one or more per spec category.
  - Player footsteps, attacks and pickups.
  - Combat swings, spells (fire, ice, dark, arcane), hits and a miss.
  - Enemy growls, screeches and death screams.
  - Torch and ambience loops.
  - UI move, click, confirm and cancel.
- **Music:** 7 tracks in `sounds/music/`:
  - `music_main_loop`
  - `music_battle_loop`
  - `music_boss_loop`
  - `music_victory_fanfare` (doesn't loop)
  - `music_ambient_crypt`, `_caverns` and `_depths`
- **Looping:** the `.import` files aren't committed, so Godot won't loop an OGG unless code
  says so. Set `(stream as AudioStreamOggVorbis).loop = true` on the `*_loop` files, the
  environment loops and the ambient tracks.

## Testing

`tests/test_assets.gd` runs in `bin/check.sh`. It checks the following load in Godot:
- the player's 8 directions × 4 states, with the spec's frame counts
- all 20 monsters' 4 directions and animations
- every `SpriteFrames` resource
- the tileset, the fonts and every sound

Rebuild with `python3 art/build.py` after changing any art script, and commit the script and its
outputs together.
