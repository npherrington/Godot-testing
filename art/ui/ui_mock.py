"""Previews only: a 960 x 540 mock HUD made of the real UI pieces and font, plus a sheet
of every UI part. Writes nothing into assets/.

- art/out/ui/mock_hud.png        the screen at 1x (the game's 960 x 540)
- art/out/ui/mock_hud@2x.png     the same at 1920 x 1080, as it shows at 1080p
- art/out/ui/mock_hud_*@4x.png   close-ups
- art/out/ui/ui_sheet@4x.png     every piece and state on the dungeon-dark background
"""

from __future__ import annotations

import pixel
from ui import _ui_kit as kit
from ui import ui_font as font
from ui import ui_hud as hud
from ui import ui_menus as menus

Sprite = pixel.Sprite
SCREEN_W, SCREEN_H = 960, 540


def _panel(c: kit.Canvas, x: int, y: int, w: int, h: int) -> None:
    m = menus.FRAME_MARGIN
    c.draw(kit.nine(menus.panel_frame(), m, m, m, m, w, h), x, y)


def _label(c: kit.Canvas, s: str, x: int, y: int, colour: str = "W", outlined: bool = False, shadow: str = "K") -> None:
    """Text with its line's top-left at (x, y), as a Label puts it."""
    if outlined:
        c.draw(font.text(s, colour, outlined=True), x - 1, y)
    else:
        c.draw(font.text(s, colour, shadow=shadow), x, y)


def _bar(c: kit.Canvas, x: int, y: int, value: float, lag: float = 0.0, flash: int = -1) -> None:
    """The two TextureProgressBars as Godot draws them: the damage bar (under + damage
    fill at value + lag) under the real one (progress at value + over)."""
    c.draw(hud.healthbar_under(), x, y)
    for tex, v in [(hud.healthbar_damage(), value + lag), (hud.healthbar_progress(), value)]:
        w = round(hud.WIN_W * min(1.0, v))
        if w:
            c.draw([row[:w] for row in tex], x + hud.WIN_X, y + hud.WIN_Y)
    c.draw(hud.healthbar_over(), x, y)
    if flash >= 0:
        c.draw(hud.healthbar_flash()[flash], x, y)


def _button(c: kit.Canvas, state: str, x: int, y: int, w: int, icon: str, label: str) -> None:
    fn = {"normal": menus.button_normal, "hover": menus.button_hover, "pressed": menus.button_pressed,
          "disabled": menus.button_disabled}[state]
    m = menus.BTN_MARGIN
    c.draw(kit.nine(fn(), m, m, m, m, w, menus.BTN_H), x, y)
    sink = 1 if state == "pressed" else 0
    art = menus.icons()[icon]
    if state == "disabled":
        art = pixel.recolour(art, {k: "D" for k in pixel.COLOURS if k != "K"})
        art = pixel.recolour(art, {"K": "K"})
    c.draw(art, x + 4, y + 3 + sink)
    colour = {"disabled": "G", "hover": "Y"}.get(state, "W")
    _label(c, label, x + 21, y + 5 + sink, colour, shadow="K" if state != "disabled" else "")


def mock() -> kit.Canvas:
    c = kit.Canvas(SCREEN_W, SCREEN_H)
    c.tile(menus.menu_background())

    # --- top left: the player's HUD ---------------------------------------------
    _panel(c, 8, 8, 236, 50)
    _label(c, "HP", 16, 16, "W", outlined=True)
    _bar(c, 32, 16, 0.62, lag=0.14)
    _label(c, "62/100", 141, 17, "W", outlined=True)
    _label(c, "Level 3 - Floor B2", 16, 33, "Y", outlined=True)
    x = 132
    for name in ("poison", "burn"):
        c.draw(getattr(hud, f"ICON_{name.upper()}"), x, 33)
        x += 14

    # --- top right: status effects ------------------------------------------------
    _panel(c, SCREEN_W - 8 - 112, 8, 112, 76)
    _label(c, "STATUS", SCREEN_W - 8 - 112 + 10, 13, "L", outlined=True)
    rows = [("poison", "Poisoned", "E"), ("freeze", "Frozen", "C"), ("burn", "Burning", "O"), ("petrified", "Petrified", "L")]
    for n, (name, label, colour) in enumerate(rows):
        y = 27 + n * 13
        c.draw(getattr(hud, f"ICON_{name.upper()}"), SCREEN_W - 8 - 112 + 8, y)
        _label(c, label, SCREEN_W - 8 - 112 + 24, y + 1, colour)

    # --- health bar at several fills ----------------------------------------------
    _panel(c, 8, 64, 236, 112)
    _label(c, "HEALTH BAR", 16, 70, "L", outlined=True)
    for n, (v, lag, note) in enumerate([(1.0, 0.0, "100"), (0.62, 0.14, "62 +lag"), (0.18, 0.0, "18"), (0.0, 0.0, "0")]):
        y = 86 + n * 15
        _bar(c, 16, y, v, lag)
        _label(c, note, 126, y + 1, "L")
    _label(c, "hit flash, frames 1 and 3", 16, 146, "L")
    _bar(c, 16, 158, 0.45, 0.2, flash=1)
    _bar(c, 124, 158, 0.45, 0.2, flash=3)

    # --- inventory ------------------------------------------------------------------
    ix, iy = 262, 64
    c.draw(menus.inventory_panel(), ix, iy)
    title = "INVENTORY"
    _label(c, title, ix + (menus.PANEL_W - font.text_width(title)) // 2, iy + 6, "Y", outlined=True)
    slots = menus.slot_positions()
    states = {1: "hover", 7: "selected", 20: "disabled", 21: "disabled", 22: "disabled", 23: "disabled"}
    items = {0: "item", 1: "attack", 2: "defend", 7: "magic", 8: "item", 13: "wait"}
    for n, (sx, sy) in enumerate(slots):
        st = states.get(n)
        if st:
            c.draw(getattr(menus, f"slot_{st}")(), ix + sx, iy + sy)
        if n in items:
            c.draw(menus.icons()[items[n]], ix + sx + 3, iy + sy + 3)
    hx, hy = slots[7]
    c.draw(menus.inventory_highlight()[3], ix + hx - 2, iy + hy - 2)
    _label(c, "3", ix + slots[0][0] + 14, iy + slots[0][1] + 10, "W", outlined=True)

    # --- command menu ---------------------------------------------------------------
    cx, cy = 426, 64
    bw = 68
    _panel(c, cx, cy, 2 * bw + 4 + 16, 3 * 20 + 2 * 3 + 30)
    _label(c, "COMMAND", cx + 10, cy + 6, "L", outlined=True)
    cmds = [("attack", "Attack", "hover"), ("defend", "Defend", "normal"), ("item", "Item", "pressed"),
            ("magic", "Magic", "normal"), ("wait", "Wait", "normal"), ("flee", "Flee", "disabled")]
    for n, (icon, label, st) in enumerate(cmds):
        bx = cx + 8 + (n % 2) * (bw + 4)
        by = cy + 22 + (n // 2) * 23
        _button(c, st, bx, by, bw, icon, label)
    c.draw(hud.cursor_bob()[3], cx - 2, cy + 22 + 6)

    # --- button states, stretched ---------------------------------------------------
    sx, sy = 590, 64
    _panel(c, sx, sy, 150, 112)
    _label(c, "BUTTONS 9-SLICE", sx + 10, sy + 6, "L", outlined=True)
    for n, st in enumerate(("normal", "hover", "pressed", "disabled")):
        _button(c, st, sx + 8, sy + 22 + n * 22, 134, ["attack", "magic", "item", "flee"][n], st.capitalize())

    # --- icons --------------------------------------------------------------------
    _panel(c, 590, 182, 150, 60)
    _label(c, "ICONS", 600, 188, "L", outlined=True)
    for n, name in enumerate(["attack", "defend", "item", "magic", "wait", "flee"]):
        c.draw(menus.icons()[name], 598 + n * 22, 204)
    for n, name in enumerate(["poison", "freeze", "burn", "petrified"]):
        c.draw(getattr(hud, f"ICON_{name.upper()}"), 600 + n * 22, 223)
    c.draw(hud.CURSOR, 692, 225)

    # --- a dialog -------------------------------------------------------------------
    dx, dy = 750, 92
    _panel(c, dx, dy, 202, 72)
    _label(c, "Rusty Key", dx + 10, dy + 7, "Y", outlined=True)
    for n, line in enumerate(["Opens a door on this", "floor. Its teeth are", "worn smooth."]):
        _label(c, line, dx + 10, dy + 22 + n * 11, "W")
    c.draw(hud.CURSOR, dx + 182, dy + 58)

    # --- message log and the character set ------------------------------------------
    lx, ly, lw, lh = 8, 300, 944, 128
    _panel(c, lx, ly, lw, lh)
    lines = [
        ("The goblin hits you for 4 damage!", "F"),
        ("You swing at the goblin. It dodges.", "W"),
        ("You quaff the potion. You feel better.", "E"),
        ("The air turns to frost around you...", "C"),
        ("Level 3 - Floor B2", "Y"),
        ("", "W"),
        ("".join(chr(c) for c in range(33, 65)), "W"),
        ("".join(chr(c) for c in range(65, 97)), "W"),
        ("".join(chr(c) for c in range(97, 127)), "W"),
        ("g j p q y   0 O o   1 l I   Gold: 1,048  (x2) [B2] {ok} ~50% #3 @5 $9 &", "W"),
    ]
    for n, (line, colour) in enumerate(lines):
        _label(c, line, lx + 10, ly + 8 + n * 11, colour)
    # the same lines in the outlined font, right half
    for n, (line, colour) in enumerate(lines[:5]):
        _label(c, line, lx + 500, ly + 8 + n * 12, colour, outlined=True)
    _label(c, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", lx + 500, ly + 8 + 6 * 12, "W", outlined=True)
    _label(c, "abcdefghijklmnopqrstuvwxyz 0123456789", lx + 500, ly + 8 + 7 * 12, "W", outlined=True)
    _label(c, "!?.,:;'\"()[]{}<>+-*/=_%&#@$^~`|\\", lx + 500, ly + 8 + 8 * 12, "W", outlined=True)

    # --- turn indicator, centre bottom --------------------------------------------------
    tw = 120
    tx, ty = (SCREEN_W - tw) // 2, SCREEN_H - 8 - 52
    _panel(c, tx, ty, tw, 26)
    turn = "YOUR TURN"
    _label(c, turn, tx + (tw - font.text_width(turn)) // 2, ty + 7, "Y", outlined=True)
    c.draw(hud.CURSOR, tx + 8, ty + 8)
    c.draw(pixel.flip(hud.CURSOR), tx + tw - 17, ty + 8)
    return c


def sheet() -> kit.Canvas:
    """Every piece at 1x on the dungeon-dark background, for a 4x contact preview."""
    c = kit.Canvas(340, 300)
    # health bar: its four textures, then the 6 flash frames
    c.draw(hud.healthbar_under(), 4, 4)
    c.draw(hud.healthbar_progress(), 4 + hud.WIN_X, 20)
    c.draw(hud.healthbar_damage(), 4 + hud.WIN_X, 30)
    c.draw(hud.healthbar_over(), 4, 40)
    _bar(c, 4, 56, 0.55, 0.2)
    for n, f in enumerate(hud.healthbar_flash()):
        c.draw(f, 120 + (n % 2) * 110, 4 + (n // 2) * 18)
    # status icons, cursor and its bob frames
    for n, name in enumerate(["poison", "freeze", "burn", "petrified"]):
        c.draw(getattr(hud, f"ICON_{name.upper()}"), 4 + n * 16, 78)
    c.draw(hud.CURSOR, 72, 80)
    for n, f in enumerate(hud.cursor_bob()):
        c.draw(f, 90 + n * 14, 80)
    # slots and the highlight frames
    for n, st in enumerate(("normal", "hover", "selected", "disabled")):
        c.draw(getattr(menus, f"slot_{st}")(), 4 + n * 22, 100)
    for n, f in enumerate(menus.inventory_highlight()):
        c.draw(f, 96 + (n % 6) * 26, 98 if n < 6 else 124)
    # buttons and command icons
    for n, st in enumerate(("normal", "hover", "pressed", "disabled")):
        c.draw(getattr(menus, f"button_{st}")(), 4 + n * 26, 152)
    for n, ic in enumerate(menus.icons().values()):
        c.draw(ic, 112 + n * 18, 155)
    # frame, wall, inventory panel
    c.draw(menus.panel_frame(), 4, 178)
    c.draw(menus.menu_background(), 32, 178)
    c.draw(menus.inventory_panel(), 104, 178)
    return c


def build() -> None:
    c = mock()
    c.write(kit.OUT / "mock_hud.png")
    c.write(kit.OUT / "mock_hud@2x.png", 2)
    c.write(kit.OUT / "mock_hud_topleft@4x.png", 4, (0, 0, 420, 250))
    c.write(kit.OUT / "mock_hud_menus@4x.png", 4, (420, 56, 540, 200))
    c.write(kit.OUT / "mock_hud_inventory@6x.png", 6, (262, 64, 146, 118))
    c.write(kit.OUT / "mock_hud_log@4x.png", 4, (0, 294, 480, 140))
    c.write(kit.OUT / "mock_hud_log_outlined@4x.png", 4, (500, 294, 460, 130))
    sheet().write(kit.OUT / "ui_sheet@4x.png", 4)
    print("ui_mock: art/out/ui/mock_hud.png (+@2x, close-ups), ui_sheet@4x.png")
