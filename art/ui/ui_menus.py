"""Menu pieces: the 9-slice panel frame, the dungeon-wall menu background, inventory slots
and panel, the command buttons and command icons.

- ui_panel_frame.png        24 x 24, 9-slice margins 8 on every side, flat centre
- ui_menu_background.png    64 x 64, tiles seamlessly
- ui_inventory_slot_<state>.png   20 x 20: normal, hover, selected, disabled
- ui_inventory_highlight.png      12 frames of 24 x 24 at 12 fps, loops; sits 2 px out
                                  from the slot it highlights
- ui_inventory_panel.png    146 x 118: the frame, a title band and 24 slot wells (6 x 4)
- ui_button_<state>.png     24 x 20, 9-slice margins 4: normal, hover, pressed, disabled
- ui_icon_<command>.png     14 x 14: attack, defend, item, magic, wait, flee
"""

from __future__ import annotations

import pixel
from ui import _ui_kit as kit

Sprite = pixel.Sprite

# ---------------------------------------------------------------------------------
# Panel frame (9-slice)
# ---------------------------------------------------------------------------------

# Iron frame, 4 px: K outline, a lit bevel (L then G) on the top and left and a shaded
# one (D) on the bottom and right, a K inner line; gold corner brackets with a rivet.
# The centre is flat D, so it stretches cleanly.
FRAME = 24


def _bevel(i: int, j: int, s: int, lit: str, shade: str) -> tuple[int, str]:
    """(distance from the edge, which side's colour) for cell (i, j) of an s x s box."""
    d = min(i, j, s - 1 - i, s - 1 - j)
    shaded = (i == s - 1 - d or j == s - 1 - d) and not (i == d or j == d)
    return d, shade if shaded else lit


def panel_frame() -> Sprite:
    s = FRAME
    grid = []
    for i in range(s):
        row = ""
        for j in range(s):
            d, side = _bevel(i, j, s, "tl", "br")
            if d == 0:
                ch = "K"
            elif d == 1:
                ch = "L" if side == "tl" else "D"
            elif d == 2:
                ch = "G" if side == "tl" else "D"
            elif d == 3:
                ch = "K"
            else:
                ch = "D"
            row += ch
        grid.append(row)
    grid = pixel.paint(grid, [(0, 0), (0, s - 1), (s - 1, 0), (s - 1, s - 1)], ".")
    for top in (True, False):
        for left in (True, False):
            grid = _bracket(grid, top, left)
    return grid


def _bracket(grid: Sprite, top: bool, left: bool) -> Sprite:
    """A gold L over one corner: 2 px thick, 5 long, K-capped, with a rivet."""
    s = len(grid)
    r_out, r_in = (1, 2) if top else (s - 2, s - 3)
    c_out, c_in = (1, 2) if left else (s - 2, s - 3)
    span = range(1, 6) if left else range(s - 6, s - 1)
    rspan = range(1, 6) if top else range(s - 6, s - 1)
    end_c = 6 if left else s - 7
    end_r = 6 if top else s - 7
    pts: list[tuple[tuple[int, int], str]] = []
    pts += [((r_out, c), "Y" if top else "O") for c in span]
    pts += [((r_in, c), "O") for c in span]
    pts += [((r, c_out), "Y" if left else "O") for r in rspan]
    pts += [((r, c_in), "O") for r in rspan]
    pts += [((r_out, end_c), "K"), ((r_in, end_c), "K"), ((end_r, c_out), "K"), ((end_r, c_in), "K")]
    pts += [((r_out, c_out), "Y" if (top or left) else "O"), ((r_in, c_in), "W" if (top and left) else "Y")]
    for (r, c), ch in pts:
        grid = pixel.paint(grid, [(r, c)], ch)
    return grid


FRAME_MARGIN = 8

# ---------------------------------------------------------------------------------
# Menu background: tileable dungeon wall, 64 x 64
# ---------------------------------------------------------------------------------

# Brick faces, 15 x 7. The wall lays them in courses 8 high (a K mortar row on top) and
# 16 wide (a K mortar column on the left), every other course offset by 8.
_BRICKS: dict[str, Sprite] = {
    "a": [
        "GGGGGGGGGGGGGGD",
        "GDDDDDDDDDDDDDD",
        "GDDDGDDDDDDDDDD",
        "GDDDDDDDDDDKDDD",
        "GDDDDDDDDDDDDDD",
        "GDDDDDDDDGDDDDD",
        "DDDDDDDDDDDDDDK",
    ],
    "b": [  # cracked
        "GGGGGGGGDGGGGGD",
        "GDDDDDDKDDDDDDD",
        "GDDDDDKDDDDDDDD",
        "GDDDDDDKKDDGDDD",
        "GDGDDDDDDKDDDDD",
        "GDDDDDDDDKDDDDD",
        "DDDDDDDDKDDDDDK",
    ],
    "c": [  # moss along the bottom
        "GGGGGGGGGGGGGGD",
        "GDDDDDDDDDDDDDD",
        "GDDDDDDDGDDDDDD",
        "GDDDDDDDDDDDDDD",
        "GDDDDvDDDDDDvDD",
        "GvDDvVvDDDvvVvD",
        "vVvvVEVvvvVVVVv",
    ],
    "d": [  # darker, worn
        "GDGDGGGGGGDGGGD",
        "DDKDDDDDDDDDDKD",
        "GDDDDKDDDDDDDDD",
        "DDDDDDDDDKDDDDD",
        "GDDKDDDDDDDDDDD",
        "DDDDDDDKDDDDKDD",
        "DKDDDDDDDDDDDKK",
    ],
    "e": [  # chipped corner, top right
        "GGGGGGGGGGGK...",
        "GDDDDDDDDDDDKK.",
        "GDDDDDDDDDDDDDK",
        "GDDGDDDDDDDDDDD",
        "GDDDDDDDDDDDDDD",
        "GDDDDDDDDDDGDDD",
        "DDDDDDDDDDDDDDK",
    ],
    "f": [  # a speckled, slightly paler stone
        "GGGGGGGGGGGGGGD",
        "GDGDDDGDDDGDDDD",
        "GDDDGDDDGDDDGDD",
        "GDGDDDGDDDGDDDD",
        "GDDDGDDDGDDDGDD",
        "GDGDDDGDDDGDDDD",
        "DDDDDDDDDDDDDDK",
    ],
}
_WALL = [  # one letter per brick, 4 per course, 8 courses
    "abca",
    "dafb",
    "aeda",
    "cabd",
    "bada",
    "aceb",
    "dbaa",
    "acda",
]


def menu_background() -> Sprite:
    wall = kit.fill(64, 64, "K")
    for course, letters in enumerate(_WALL):
        y = course * 8 + 1
        offset = 8 if course % 2 else 0
        for n, letter in enumerate(letters):
            x = n * 16 + offset + 1
            wall = kit.wrap_paste(wall, _BRICKS[letter], y, x)
    # chipped corners show mortar: '.' left the K under them; moss creeping in the joints
    wall = pixel.paint(wall, [(48, 21), (48, 22), (40, 9), (24, 57), (24, 58), (25, 58)], "v")
    return wall


# ---------------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------------

SLOT = 20
GAP = 2
COLS, ROWS = 6, 4
GRID_X, GRID_Y = 8, 24
PANEL_W = GRID_X * 2 + COLS * SLOT + (COLS - 1) * GAP
PANEL_H = GRID_Y + ROWS * SLOT + (ROWS - 1) * GAP + 8


def _slot(outline_tl: str, outline_br: str, rim_tl: str, rim_br: str, floor: Sprite) -> Sprite:
    """A 20 x 20 well: outline, a 1-px rim (shaded top-left, lit bottom-right: it's
    sunk in), and a 16 x 16 floor for the item."""
    s = SLOT
    grid = [["."] * s for _ in range(s)]
    for i in range(s):
        for j in range(s):
            d = min(i, j, s - 1 - i, s - 1 - j)
            br = i == s - 1 - d or j == s - 1 - d
            if d == 0:
                grid[i][j] = outline_br if br and not (i == d or j == d) else outline_tl
            elif d == 1:
                grid[i][j] = rim_br if br and not (i == d or j == d) else rim_tl
            else:
                grid[i][j] = floor[i - 2][j - 2]
    for i, j in [(0, 0), (0, s - 1), (s - 1, 0), (s - 1, s - 1)]:
        grid[i][j] = "."
    return ["".join(r) for r in grid]


def slot_normal() -> Sprite:
    floor = kit.fill(16, 16, "D")
    floor = pixel.paint(floor, [(0, c) for c in range(16)] + [(r, 0) for r in range(16)], "K")
    return _slot("K", "K", "K", "G", floor)


def slot_hover() -> Sprite:
    """Lifted: the rim lit all round, the floor a shade lighter, glints in the corners."""
    floor = kit.fill(16, 16, "G")
    floor = pixel.paint(floor, [(0, c) for c in range(16)] + [(r, 0) for r in range(16)], "D")
    s = _slot("K", "K", "L", "L", floor)
    return pixel.paint(s, [(1, 1), (1, 2), (2, 1)], "W")


def slot_selected() -> Sprite:
    floor = kit.fill(16, 16, "D")
    floor = pixel.paint(floor, [(0, c) for c in range(16)] + [(r, 0) for r in range(16)], "b")
    s = _slot("Y", "O", "K", "K", floor)
    return pixel.paint(s, [(0, 1), (1, 0)], "W")


def slot_disabled() -> Sprite:
    """Locked: dark, no lip, hatched."""
    floor = kit.fill(16, 16, "K")
    floor = pixel.paint(floor, [(r, c) for r in range(16) for c in range(16) if (r + c) % 4 == 3], "D")
    return _slot("K", "K", "D", "D", floor)


def inventory_highlight() -> list[Sprite]:
    """Gold corner brackets that breathe out and back around a 20 x 20 slot, with a
    white glint running round the slot's rim. 24 x 24, the slot at (2, 2)."""
    size = SLOT + 4
    frames = []
    # (offset out from the slot, bracket colour) per frame
    pulse = [(0, "O"), (0, "Y"), (1, "Y"), (1, "W"), (2, "W"), (2, "W"),
             (2, "Y"), (1, "Y"), (1, "Y"), (0, "Y"), (0, "O"), (0, "O")]
    perimeter = _ring(2, 2, SLOT)
    for n, (out, colour) in enumerate(pulse):
        f = pixel.blank(size, size)
        lo, hi = 2 - out, size - 3 + out
        arm = 4
        pts = []
        for x0, dx in [(lo, 1), (hi, -1)]:
            for y0, dy in [(lo, 1), (hi, -1)]:
                pts += [(y0, x0 + dx * k) for k in range(arm)] + [(y0 + dy * k, x0) for k in range(arm)]
        pts = [(y, x) for y, x in pts if 0 <= y < size and 0 <= x < size]
        f = pixel.paint(f, pts, colour)
        # the glint: a 6-pixel streak running clockwise round the slot's rim, 6 pixels a
        # frame, so it sweeps without gaps
        step = len(perimeter) // len(pulse)
        head = n * step
        for k, letter in enumerate("WWYY**"):
            y, x = perimeter[(head - k) % len(perimeter)]
            f = pixel.paint(f, [(y, x)], letter)
        frames.append(f)
    return frames


def _ring(x0: int, y0: int, s: int) -> list[tuple[int, int]]:
    """The (row, col) cells round an s x s square at (x0, y0), clockwise from top-left,
    skipping the cut corners."""
    top = [(y0, x0 + i) for i in range(1, s - 1)]
    right = [(y0 + i, x0 + s - 1) for i in range(1, s - 1)]
    bottom = [(y0 + s - 1, x0 + i) for i in range(s - 2, 0, -1)]
    left = [(y0 + i, x0) for i in range(s - 2, 0, -1)]
    return top + right + bottom + left


def slot_positions() -> list[list[int]]:
    """[x, y] of each slot's top-left in the panel, row by row."""
    return [[GRID_X + c * (SLOT + GAP), GRID_Y + r * (SLOT + GAP)] for r in range(ROWS) for c in range(COLS)]


def inventory_panel() -> Sprite:
    p = kit.nine(panel_frame(), FRAME_MARGIN, FRAME_MARGIN, FRAME_MARGIN, FRAME_MARGIN, PANEL_W, PANEL_H)
    # title band: a darker plaque with an engraved line under it
    band = kit.fill(PANEL_W - 8, 15, "K")
    band = pixel.paint(band, [(14, c) for c in range(PANEL_W - 8)], "G")
    band = pixel.paint(band, [(r, 0) for r in range(14)] + [(0, c) for c in range(PANEL_W - 8)], "K")
    p = pixel.paste(p, band, 4, 4)
    # gold studs at the band's ends, where the title doesn't reach
    for x in (8, PANEL_W - 11):
        p = pixel.paste(p, ["KYK", "YWO", "KOK"], 9, x)
    well = slot_normal()
    for x, y in slot_positions():
        p = pixel.paste(p, well, y, x)
    return p


# ---------------------------------------------------------------------------------
# Command buttons (9-slice) and icons
# ---------------------------------------------------------------------------------

BTN_W, BTN_H = 24, 20
BTN_MARGIN = 4


def _button(face: str, hi: str, side: str, depth: str, outline: str, outline_br: str, sink: int = 0) -> Sprite:
    """A raised key: outline, a 1-px highlight on the top and left, face, a shaded right
    edge, 2 rows of depth under it. sink pushes the face down (pressed)."""
    w, h = BTN_W, BTN_H
    rows = []
    for y in range(h):
        if y == 0:
            row = "." + outline * (w - 2) + "."
        elif y == h - 1:
            row = "." + outline_br * (w - 2) + "."
        elif y < 1 + sink:
            row = outline + "K" * (w - 2) + outline_br
        elif y == 1 + sink:
            row = outline + hi * (w - 3) + side + outline_br
        elif y >= h - 3 + sink:
            row = outline + depth * (w - 2) + outline_br
        else:
            row = outline + hi + face * (w - 4) + side + outline_br
        rows.append(row)
    return rows


def button_normal() -> Sprite:
    return _button("G", "L", "D", "D", "K", "K")


def button_hover() -> Sprite:
    b = _button("G", "W", "D", "D", "Y", "O")
    return b


def button_pressed() -> Sprite:
    return _button("D", "G", "D", "K", "K", "K", sink=1)


def button_disabled() -> Sprite:
    b = _button("D", "D", "K", "K", "K", "K")
    return pixel.paint(b, [(y, x) for y in range(2, BTN_H - 3) for x in range(2, BTN_W - 2) if (x + y) % 2 == 0], "D")


def _sword() -> Sprite:
    """The attack icon: a sword point up-right, built along its diagonal, then outlined."""
    g = [["."] * 14 for _ in range(14)]

    def put(r: int, c: int, ch: str) -> None:
        g[r][c] = ch

    put(1, 12, "W")
    for i in range(1, 7):
        put(1 + i, 12 - i, "L")
        put(1 + i, 11 - i, "W")
    for k, ch in zip(range(-2, 3), "OYYYO"):
        put(8 + k, 4 + k, ch)
    put(7, 3, "Y")
    put(9, 5, "O")
    put(9, 3, "B")
    put(10, 2, "B")
    put(10, 3, "b")
    put(11, 1, "Y")
    put(12, 1, "O")
    put(11, 2, "O")
    return pixel.outline(["".join(r) for r in g], "K")


ICONS: dict[str, Sprite] = {
    "defend": [
        ".KKKKKKKKKKKK.",
        "KLLLLLLLLLLLGK",
        "KLCCCCUUUUUuDK",
        "KLCCCUUKUUUuDK",
        "KLCCUUKYKUUuDK",
        "KLCUUKYWOKUuDK",
        "KLCUUUKOKUUuDK",
        ".KLUUUUKUUuDK.",
        ".KLUUUUUUUuDK.",
        "..KLUUUUUuDK..",
        "..KLUUUUuuDK..",
        "...KLUUuuDK...",
        "....KLuuDK....",
        ".....KKKK.....",
    ],
    "item": [
        ".....KKKK.....",
        "....KTBBbK....",
        "....KKKKKK....",
        ".....KIWK.....",
        ".....KIWK.....",
        "....KKILKK....",
        "...KIWLLLLK...",
        "..KIWRRRRRLK..",
        "..KWRFRRRRrK..",
        "..KLRFRRRRrK..",
        "..KLRRRRRrrK..",
        "...KLRRrrrK...",
        "....KKKKKK....",
        "..............",
    ],
    "magic": [
        "......K.......",
        ".....KMK...K..",
        ".....KMK..KMK.",
        "....KPWPK..K..",
        "....KMWMK.....",
        ".KKKPMWMPKKK..",
        "KMMMWWWWWMMMK.",
        ".KKKPMWMPKKK..",
        "....KMWMK.....",
        "....KPWPK.....",
        "..K..KMK......",
        ".KMK.KMK......",
        "..K...K.......",
        "..............",
    ],
    "wait": [
        ".KKKKKKKKKKKK.",
        "KTTTTTTTTTTTBK",
        "KBBBBBBBBBBBbK",
        ".KKKKKKKKKKKK.",
        "..KIWYYYYCK...",
        "...KIYYYCK....",
        "....KIYCK.....",
        "....KCYIK.....",
        "...KCIYIIK....",
        "..KCIIYYYIK...",
        ".KKKKKKKKKKKK.",
        "KTTTTTTTTTTTBK",
        "KBBBBBBBBBBBbK",
        ".KKKKKKKKKKKK.",
    ],
    "flee": [
        "..............",
        "....KKKKKK....",
        "....KSSSTK....",
        "....KTTTBK....",
        ".KKK.KTBBK....",
        "KLLLKKTBBK....",
        ".KKK.KTBBK....",
        ".....KTBBBKK..",
        ".KKKKKTBBBBBK.",
        "KLLLKTTBBBBBBK",
        ".KKKKBBBBBBBBK",
        "....KbbbbbbbbK",
        ".....KKKKKKKK.",
        "..............",
    ],
}


def icons() -> dict[str, Sprite]:
    return {"attack": _sword(), **ICONS}


def build() -> None:
    kit.assert_nine(panel_frame(), *[FRAME_MARGIN] * 4, "ui_panel_frame")
    for state, fn in [("normal", button_normal), ("hover", button_hover), ("pressed", button_pressed), ("disabled", button_disabled)]:
        kit.assert_nine(fn(), *[BTN_MARGIN] * 4, f"ui_button_{state}")
    frame = kit.save("ui_panel_frame", panel_frame(), 8)
    bg = kit.save("ui_menu_background", menu_background(), 4)
    pixel.write_png(kit.OUT / "parts" / "ui_menu_background_tiled@2x.png", kit.tile(menu_background(), 192, 128), 2)
    slots = {
        state: kit.save(f"ui_inventory_slot_{state}", fn(), 8)
        for state, fn in [("normal", slot_normal), ("hover", slot_hover), ("selected", slot_selected), ("disabled", slot_disabled)]
    }
    highlight = kit.strip_out("ui_inventory_highlight", inventory_highlight(), loop=True)
    panel = kit.save("ui_inventory_panel", inventory_panel(), 4)
    buttons = {
        state: kit.save(f"ui_button_{state}", fn(), 8)
        for state, fn in [("normal", button_normal), ("hover", button_hover), ("pressed", button_pressed), ("disabled", button_disabled)]
    }
    icon_paths = {}
    for name, art in icons().items():
        assert pixel.size(art) == (14, 14), f"icon {name}: {pixel.size(art)}"
        icon_paths[name] = kit.save(f"ui_icon_{name}", art, 8)
    kit.merge_json("panel_frame", {
        "texture": frame, "size": [24, 24],
        "patch_margins": {"left": FRAME_MARGIN, "top": FRAME_MARGIN, "right": FRAME_MARGIN, "bottom": FRAME_MARGIN},
        "content_margins": {"left": 8, "top": 8, "right": 8, "bottom": 8},
    })
    kit.merge_json("menu_background", {"texture": bg, "size": [64, 64], "tiles": True})
    kit.merge_json("inventory", {
        "panel": panel,
        "panel_size": [PANEL_W, PANEL_H],
        "grid": [COLS, ROWS],
        "slot_size": [SLOT, SLOT],
        "slot_pitch": [SLOT + GAP, SLOT + GAP],
        "item_offset": [2, 2],
        "item_area": [16, 16],
        "title_rect": [4, 4, PANEL_W - 8, 14],
        "slots": slot_positions(),
        "slot_textures": slots,
        "highlight": highlight | {"offset": [-2, -2], "notes": "draw at the slot's position minus (2, 2)"},
    })
    kit.merge_json("buttons", {
        "size": [BTN_W, BTN_H],
        "textures": buttons,
        "patch_margins": {"left": BTN_MARGIN, "top": BTN_MARGIN, "right": BTN_MARGIN, "bottom": BTN_MARGIN},
        "content_margins": {"left": 4, "top": 3, "right": 4, "bottom": 3},
        "pressed_content_margins": {"left": 4, "top": 4, "right": 4, "bottom": 2},
        "icons": icon_paths,
        "icon_size": [14, 14],
    })
    print(f"ui_menus: frame, background, 4 slots, highlight, panel {PANEL_W}x{PANEL_H}, 4 buttons, {len(icon_paths)} icons")
