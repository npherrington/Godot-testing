# UI art and font: usage notes

Source: `art/ui/` (`ui_font.py`, `ui_hud.py`, `ui_menus.py`, `ui_mock.py` previews only,
`_ui_kit.py` helpers). Rebuild with `python3 art/build.py ui_font ui_hud ui_menus ui_mock`.
Every size, offset and margin below is also in `assets/animations/ui.json`.

## Files

| File (`assets/sprites/ui/` unless noted) | Size | What |
| --- | --- | --- |
| `ui_healthbar_under.png` | 104x12 | empty trough |
| `ui_healthbar_progress.png` | 96x6 | red fill, top rows dithered to white |
| `ui_healthbar_damage.png` | 96x6 | pale fill for the lagging damage bar |
| `ui_healthbar_over.png` | 104x12 | iron frame, open over the fill window at (4, 3) |
| `ui_healthbar_flash.png` + `.tres` | 6 x 104x12 | hit flash, 12 fps, no loop |
| `ui_status_{poison,freeze,burn,petrified}.png` | 12x12 | status icons, K outline |
| `ui_cursor_arrow.png` | 9x9 | menu cursor, tip at (8, 4) |
| `ui_cursor_bob.png` + `.tres` | 6 x 11x9 | cursor nudging right, 12 fps, loops |
| `ui_panel_frame.png` | 24x24 | 9-slice frame for menus and dialogs |
| `ui_menu_background.png` | 64x64 | tileable dungeon wall |
| `ui_inventory_panel.png` | 146x118 | frame, title band, 24 slot wells (6x4) |
| `ui_inventory_slot_{normal,hover,selected,disabled}.png` | 20x20 | slot states |
| `ui_inventory_highlight.png` + `.tres` | 12 x 24x24 | pulsing brackets + glint, 12 fps, loops |
| `ui_button_{normal,hover,pressed,disabled}.png` | 24x20 | 9-slice command button |
| `ui_icon_{attack,defend,item,magic,wait,flee}.png` | 14x14 | command icons |
| `assets/fonts/font_dungeon.fnt` + `_0.png` | | BMFont, white glyphs |
| `assets/fonts/font_dungeon_outline.fnt` + `_0.png` | | same glyphs, 1-px K outline baked in |

## Keep it crisp

All of this is drawn for the 960x540 viewport (1 art pixel = 2 screen pixels at 1080p).
Set the HUD root's `texture_filter` to **Nearest** (children inherit it). The alternative is
the project setting `rendering/textures/canvas_textures/default_texture_filter = Nearest`;
I didn't change `project.godot`. Without one of these, the 2x stretch blurs both art and text.

## Health bar (`TextureProgressBar`)

Use two bars stacked at the same position. The back one shows the trough and the damage
chunk; the front one shows the real value and the frame.

```gdscript
@onready var damage_bar: TextureProgressBar = %DamageBar  # under: ui_healthbar_under, progress: ui_healthbar_damage
@onready var bar: TextureProgressBar = %Bar  # progress: ui_healthbar_progress, over: ui_healthbar_over
@onready var flash: AnimatedSprite2D = %HitFlash  # sprite_frames: ui_healthbar_flash.tres, centered = false, child of Bar

func _ready() -> void:
	for b: TextureProgressBar in [damage_bar, bar]:
		b.texture_progress_offset = Vector2(4, 3)  # the fill window inside the 104x12 frame
		b.max_value = 100
	flash.hide()
	flash.animation_finished.connect(flash.hide)

func set_health(value: float) -> void:
	bar.value = value  # drops at once
	var tween := create_tween()
	tween.tween_interval(0.3)
	tween.tween_property(damage_bar, "value", value, 0.4)  # the pale chunk drains after it
	flash.show()
	flash.play(&"default")
```

- Leave `fill_mode` at Left to Right and `nine_patch_stretch` off. The progress textures are
  exactly window-sized (96x6), so the fill maps linearly onto 0-100.
- When healing, set `damage_bar.value` first (or together) so no chunk shows.

## 9-slice margins

| Texture | Patch margins (all sides) | Content margins (L, T, R, B) |
| --- | --- | --- |
| `ui_panel_frame.png` | 8 | 8, 8, 8, 8 |
| `ui_button_*.png` | 4 | 4, 3, 4, 3; pressed 4, 4, 4, 2 (the face sinks 1 px) |

- The centres are flat colour and the edges uniform (the build asserts this), so Stretch
  and Tile give the same result.
- Buttons are drawn at their natural height of 20. A 14-px icon fits exactly in the
  content area. Stretch them horizontally.
- For a frame on its own, use `NinePatchRect` with `patch_margin_* = 8`.
- For containers and buttons, use `StyleBoxTexture` with the margins above:

```gdscript
func make_box(path: String, margin: int, content: Array[int]) -> StyleBoxTexture:
	var box := StyleBoxTexture.new()
	box.texture = load(path)
	box.texture_margin_left = margin
	box.texture_margin_top = margin
	box.texture_margin_right = margin
	box.texture_margin_bottom = margin
	box.content_margin_left = content[0]
	box.content_margin_top = content[1]
	box.content_margin_right = content[2]
	box.content_margin_bottom = content[3]
	return box

# theme.set_stylebox(&"normal", &"Button", make_box("res://assets/sprites/ui/ui_button_normal.png", 4, [4, 3, 4, 3]))
# ... hover (also use it for focus), pressed with [4, 4, 4, 2], disabled
# theme.set_stylebox(&"panel", &"PanelContainer", make_box("res://assets/sprites/ui/ui_panel_frame.png", 8, [8, 8, 8, 8]))
```

- **Button colours:** `font_color` W `#ece8d8`, `font_hover_color` Y `#fad24c`,
  `font_disabled_color` G `#686676`.
- **Disabled icons:** tint with `icon_disabled_color` (e.g. `#3a3646`).
- **Command menu:** a `GridContainer` (2 columns) of 68-px-wide buttons in a `PanelContainer`
  comes to 156x84.

## Inventory

- **Panel:** `ui_inventory_panel.png` is 146x118, with a 6x4 grid of 20x20 slots on a
  22-px pitch.
- **Slot positions:** a slot's top-left inside the panel is `(8 + 22 * col, 24 + 22 * row)`.
  `inventory.slots` in ui.json lists all 24, row by row.

  |  | col 0 | 1 | 2 | 3 | 4 | 5 |
  | --- | --- | --- | --- | --- | --- | --- |
  | x | 8 | 30 | 52 | 74 | 96 | 118 |

  Rows 0-3 are at y = 24, 46, 68, 90.
- **Items:** draw a 16x16 item at the slot + (2, 2).
- **Title:** the band is at (4, 4) and is 138x14. Put the title Label at y = 6 inside it.
- **Slot states:** the panel already shows every slot as `normal`. Put
  `ui_inventory_slot_<state>.png` over a slot for hover, selected or disabled (a locked slot).
- **Highlight:** `ui_inventory_highlight.tres` is 24x24. Place it at the slot's position
  minus (2, 2), `centered = false`, and it loops.
- **As a container:** a `GridContainer` with `columns = 6` and `h_separation = v_separation = 2`
  at (8, 24) lines up with the wells.

## Status icons, cursor, background

- **Status icons:** 12x12, and they read on any background thanks to the K outline. Space
  them 13-14 px apart.
- **Cursor:** `ui_cursor_arrow.png`'s tip is at (8, 4), so put that pixel just left of the
  selected item. `ui_cursor_bob.tres` (11x9 frames) is the same arrow nudging right 0-2 px.
- **Menu background:** a `TextureRect` with `stretch_mode = STRETCH_TILE`. It tiles
  seamlessly at 64x64.

## Font

**Glyphs:**
- ASCII 32-126, white `W` on transparent.
- 7 px cap height, 5 px x-height, 2 px descenders.
- Proportional: capitals 5 wide, most lowercase 4, `i l I 1 . , : ; ! ' |` narrow. Each
  advances its width + 1, and space advances 3.
- Digits all advance 6, so numbers don't jitter in the HUD.
- Distinct shapes: `0` is slashed, `1` has a foot, `l` has a tail, `I` has serifs, `g` hooks,
  `q` drops straight.

**Metrics:**
- `font_dungeon`: line height 11, baseline 8.
- `font_dungeon_outline`: the same glyphs with a 1-px K outline baked in (8-neighbour).
  Its line height is 12 so stacked outlines don't touch. Use it over the game world.
- **Sizes:** `font_size = 16` draws 1:1, and `32` draws an exact 2x.
  - The `.fnt` declares `size=16` on purpose: Godot uses that number only as the size it
    draws 1:1, and 16 is Godot's default. So a Label with no override is already crisp.
  - Other sizes scale by fractions and look uneven.

**Colour:** tint with `font_color` or `modulate`. The page is RGBA8 and Godot multiplies it.
Glyphs are the palette's warm white, so tints land a touch warmer than the hex you set.
The outline stays near-black under any tint.

**Godot 4.7:** both `.fnt` files import with `font_data_bmfont`. Checked in a scratch project:
- all 95 glyphs are present;
- `fixed_size` is 16;
- "The goblin hits you for 4 damage!" measures 144x11.

```gdscript
const FONT := preload("res://assets/fonts/font_dungeon.fnt")
const FONT_OUTLINE := preload("res://assets/fonts/font_dungeon_outline.fnt")

# LabelSettings: plain font with a 1-px drop shadow
var log_style := LabelSettings.new()
log_style.font = FONT
log_style.font_size = 16
log_style.font_color = Color("ece8d8")  # W; damage F #e27876, heal E #94c64c, gold Y #fad24c, frost C #5eaadc
log_style.shadow_color = Color("141018")  # K
log_style.shadow_offset = Vector2(1, 1)
log_style.shadow_size = 0  # bitmap fonts have no outline pass; 0 keeps it a crisp offset copy
$Log.label_settings = log_style

# theme overrides on one Label: the outlined font for HUD numbers
$HP.add_theme_font_override(&"font", FONT_OUTLINE)
$HP.add_theme_font_size_override(&"font_size", 16)
$HP.add_theme_color_override(&"font_color", Color("ece8d8"))

# or once for the whole UI
var theme := Theme.new()
theme.default_font = FONT
theme.default_font_size = 16
$HUD.theme = theme
```

## Previews (`art/out/ui/`, gitignored)

- **Mock HUD:**
  - `mock_hud.png` at 960x540, and `mock_hud@2x.png` at 1080p.
  - Close-ups: `mock_hud_topleft@4x.png`, `mock_hud_menus@4x.png`,
    `mock_hud_inventory@6x.png`, `mock_hud_log@4x.png`, `mock_hud_log_outlined@4x.png`.
- **Every part:** `ui_sheet@4x.png`, and `parts/*` (one per file).
- **Font:** `font_specimen@3x.png`, and `font_dungeon*_page@4x.png` (the atlas pages).
