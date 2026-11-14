"""HUD pieces: the health bar (for TextureProgressBar), status icons and the menu cursor.

Health bar, 104 x 12, the fill window at (4, 3), 96 x 6:
- ui_healthbar_under.png     the empty trough, full size
- ui_healthbar_progress.png  red fill, window size; top rows dither up to white
- ui_healthbar_damage.png    pale fill, window size, for the lagging "damage chunk" bar
- ui_healthbar_over.png      iron frame, full size, transparent over the window
- ui_healthbar_flash.png     6-frame hit flash over the whole bar, 12 fps, no loop

Status icons, 12 x 12 with a K outline: poison, freeze, burn, petrified.
Cursor: ui_cursor_arrow.png (9 x 9) and ui_cursor_bob strip (12 fps, loops).
"""

from __future__ import annotations

import pixel
from ui import _ui_kit as kit

Sprite = pixel.Sprite

BAR_W, BAR_H = 104, 12
WIN_X, WIN_Y, WIN_W, WIN_H = 4, 3, 96, 6

# ---------------------------------------------------------------------------------
# Health bar
# ---------------------------------------------------------------------------------

# The frame's end caps, 4 wide; the middle column repeats between them. Light from the
# top left: the top and left bevels are lit (L, G), the bottom and right in shade (D).
# Rows 3-8 between the caps are the window ('.').
_CAP_L = [
    ".KKK",
    "KLLL",
    "KLGK",
    "KLGK",
    "KLGK",
    "KLWK",
    "KLGK",
    "KGGK",
    "KGGK",
    "KGGK",
    "KDDD",
    ".KKK",
]
_MID = ["K", "L", "K", ".", ".", ".", ".", ".", ".", "K", "D", "K"]
_CAP_R = [
    "KKK.",
    "LLGK",
    "KGDK",
    "KDDK",
    "KDDK",
    "KDDK",
    "KDGK",
    "KDDK",
    "KDDK",
    "KDDK",
    "DDDK",
    "KKK.",
]
_TICKS = (WIN_X + 24, WIN_X + 48, WIN_X + 72)  # quarter marks notched in the top bevel


def healthbar_over() -> Sprite:
    mid_w = BAR_W - 8
    rows = [_CAP_L[r] + _MID[r] * mid_w + _CAP_R[r] for r in range(BAR_H)]
    for x in _TICKS:
        rows = pixel.paint(rows, [(1, x), (10, x)], "G")
        rows = pixel.paint(rows, [(1, x - 1)], "W")
    return rows


def _band(w: int, patterns: list[str]) -> Sprite:
    """One row per 4-pixel pattern, repeated across w. The dither phases are hand-set so
    each column steps light to dark down the rows instead of forming stripes."""
    return [(pat * (w // len(pat) + 1))[:w] for pat in patterns]


def healthbar_progress() -> Sprite:
    return _band(WIN_W, [
        "WFWF",  # shine: white and pink
        "FRFR",  # each column goes W-F-R or F-R-R: a dithered step down
        "RRRR",
        "RRRR",
        "RrRr",
        "rrrr",
    ])


def healthbar_damage() -> Sprite:
    return _band(WIN_W, [
        "WWWW",
        "WWWW",
        "WWWW",
        "WSWW",
        "SWSW",
        "SSSS",
    ])


def healthbar_under() -> Sprite:
    """The empty trough: black under the top lip, dark red rising toward the lit bottom lip."""
    trough = _band(WIN_W, [
        "KKKK",
        "KKKK",
        "KKKK",
        "KKKK",
        "KrKr",
        "rrrr",
    ])
    base = kit.fill(BAR_W, BAR_H, "K")
    base = pixel.paint(base, [(0, 0), (0, BAR_W - 1), (BAR_H - 1, 0), (BAR_H - 1, BAR_W - 1)], ".")
    return pixel.paste(base, trough, WIN_Y, WIN_X)


def healthbar_flash() -> list[Sprite]:
    """A hit: the frame and window flash white, cool through pink and red, and fade."""
    over = healthbar_over()
    solid = pixel.paste(over, kit.fill(WIN_W, WIN_H, "W"), WIN_Y, WIN_X)
    frame_only = pixel.silhouette(over, "W")
    win_mist = pixel.paste(pixel.blank(BAR_W, BAR_H), kit.fill(WIN_W, WIN_H, "!"), WIN_Y, WIN_X)
    frames = [
        pixel.silhouette(solid, "W"),
        pixel.paste(win_mist, pixel.dither(pixel.silhouette(solid, "W"), "W", ".", 0.5), 0, 0),
        pixel.paste(win_mist, pixel.silhouette(over, "F"), 0, 0),
        pixel.paste(pixel.dissolve(win_mist, 0.5), pixel.silhouette(over, "R"), 0, 0),
        pixel.dissolve(pixel.silhouette(over, "!"), 0.25),
        pixel.dissolve(pixel.silhouette(over, "!"), 0.75),
    ]
    del frame_only
    return frames


# ---------------------------------------------------------------------------------
# Status icons, 12 x 12, K outline
# ---------------------------------------------------------------------------------

ICON_POISON = [
    ".KK...K.....",
    "KWEK.KEK....",
    "KEEK.KEVK...",
    ".KK.KEEVK...",
    "...KEEVVVK..",
    "...KEWVVVVK.",
    "..KEWVVVVVvK",
    "..KEWVVVVVvK",
    "..KEVVVVVvvK",
    "..KVVVVVvvvK",
    "...KvvvvvvK.",
    "....KKKKKK..",
]

ICON_FREEZE = [
    ".....KK.....",
    "..KK.KIK.KK.",
    "..KIKKCKKIK.",
    "...KCKCKCK..",
    ".KKKKCICKKKK",
    "KICCCIWICCCK",
    ".KKKKCICKKKK",
    "...KCKCKCK..",
    "..KIKKCKKIK.",
    "..KK.KIK.KK.",
    ".....KK.....",
    "............",
]

ICON_BURN = [
    ".....K......",
    "....KOK..K..",
    "....KOOKKOK.",
    "...KOYOKOOK.",
    "..KOOYYOOOK.",
    "..KOYYYYOK..",
    ".KROYWWYOOK.",
    ".KROYWWWYOK.",
    ".KRROYWYORK.",
    "..KRROOORK..",
    "...KKRRRK...",
    "....KKKK....",
]

ICON_PETRIFIED = [  # a faceted stone, lit top face, split by a crack
    "...KKKKK....",
    "..KLLLLLKK..",
    ".KLLWLLLLLK.",
    "KGGLLLLLLGDK",
    "KGGGGGKGGDDK",
    "KGGGGKGGGDDK",
    "KGLGGGKGGDDK",
    "KGGGGKKGGDDK",
    "KGGGGKGGGDDK",
    ".KGGDGKGGDK.",
    "..KDDDDDDDK.",
    "...KKKKKKK..",
]


# ---------------------------------------------------------------------------------
# Cursor
# ---------------------------------------------------------------------------------

CURSOR = [
    "KK.......",
    "KYK......",
    "KYYK.....",
    "KYYYK....",
    "KYYOOK...",
    "KYOOK....",
    "KOOK.....",
    "KOK......",
    "KK.......",
]


def cursor_bob() -> list[Sprite]:
    """The arrow nudging right and back, in an 11-wide cell: 6 frames at 12 fps."""
    cell = pixel.pad(CURSOR, 0, 2, 0, 0)
    return [pixel.shift(cell, dx, 0) for dx in (0, 0, 1, 2, 2, 1)]


def build() -> None:
    files = {
        "under": kit.save("ui_healthbar_under", healthbar_under()),
        "progress": kit.save("ui_healthbar_progress", healthbar_progress()),
        "damage": kit.save("ui_healthbar_damage", healthbar_damage()),
        "over": kit.save("ui_healthbar_over", healthbar_over()),
    }
    flash = kit.strip_out("ui_healthbar_flash", healthbar_flash(), loop=False)
    icons = {}
    for name, art in [("poison", ICON_POISON), ("freeze", ICON_FREEZE), ("burn", ICON_BURN), ("petrified", ICON_PETRIFIED)]:
        assert pixel.size(art) == (12, 12), f"status {name}: {pixel.size(art)}"
        icons[name] = kit.save(f"ui_status_{name}", art, 8)
    cursor = kit.save("ui_cursor_arrow", CURSOR, 8)
    bob = kit.strip_out("ui_cursor_bob", cursor_bob(), loop=True)
    kit.merge_json("healthbar", {
        "size": [BAR_W, BAR_H],
        "textures": files,
        "texture_progress_offset": [WIN_X, WIN_Y],
        "fill_rect": [WIN_X, WIN_Y, WIN_W, WIN_H],
        "flash": flash | {"notes": "AnimatedSprite2D over the bar at (0, 0), centered off; play on a hit, hide when finished"},
    })
    kit.merge_json("status_icons", {"size": [12, 12], "icons": icons})
    kit.merge_json("cursor", {
        "texture": cursor,
        "size": list(pixel.size(CURSOR)),
        "hotspot": [8, 4],
        "bob": bob | {"notes": "the arrow's tip is at (8, 4) in frame 0; frames nudge it 0-2 px right"},
    })
    print("ui_hud: healthbar, flash, 4 status icons, cursor")
