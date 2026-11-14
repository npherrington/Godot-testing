"""font_dungeon: the game's pixel font, ASCII 32-126, written as a BMFont.

Each glyph is a W-on-transparent letter matrix, 7 rows at cap height and 2 rows of
descender (9 rows), of its own width: capitals and digits 5 wide, most lowercase 4, the
narrow ones (i l I 1 punctuation) less. Every glyph advances its width + 1, so there is
always a 1-pixel gap; digits all advance 6 so numbers line up in the HUD.

Two fonts come out of the same matrices:
- font_dungeon.fnt + font_dungeon_0.png: plain white glyphs. Tint with font_color.
- font_dungeon_outline.fnt + font_dungeon_outline_0.png: the same glyphs with a 1-pixel
  K outline baked in (8-neighbour), for text over the game world. The outline sits in
  the 1-pixel gap, so the advances are the same.

Distinctions to keep when editing: 0 is slashed, O round, o small; 1 has a flag and a
foot, l a tail, I serifs; g hooks back, q drops straight.
"""

from __future__ import annotations

import pixel
from ui import _ui_kit as kit

FACE = "Dungeon"
LINE_HEIGHT = 11  # rows per line
LINE_HEIGHT_OUTLINED = 12  # one more, so outlines on stacked lines don't touch
TOP = 1  # empty rows above the cap height
BASE = TOP + 7  # baseline: cap rows TOP..TOP+6, descender below
SPACE = 3  # advance of " "
CAP, DESC = 7, 2
PAGE_W = 128
# The BMFont "size" is nominal for a hand-drawn font: Godot only uses it as the font's
# fixed_size, the font_size it draws at 1:1. 16 is Godot's default font size, so a Label
# with no size override draws these glyphs pixel for pixel; 32 draws them at exactly 2x.
# (Godot's BMFont import defaults to fractional scaling and *.import is gitignored here,
# so a fixed_size of 11 would leave the default 16 drawing at a blurry 1.45x.)
NOMINAL_SIZE = 16

# fmt: off
GLYPHS: dict[str, list[str]] = {
    "!": ["W", "W", "W", "W", "W", ".", "W"],
    '"': ["W.W", "W.W", "...", "...", "...", "...", "..."],
    "#": [".....", ".W.W.", "WWWWW", ".W.W.", "WWWWW", ".W.W.", "....."],
    "$": ["..W..", ".WWWW", "W.W..", ".WWW.", "..W.W", "WWWW.", "..W.."],
    "%": ["WW..W", "WW..W", "...W.", "..W..", ".W...", "W..WW", "W..WW"],
    "&": [".WW..", "W..W.", "W.W..", ".W...", "W.W.W", "W..W.", ".WW.W"],
    "'": ["W", "W", ".", ".", ".", ".", "."],
    "(": [".W", "W.", "W.", "W.", "W.", "W.", ".W"],
    ")": ["W.", ".W", ".W", ".W", ".W", ".W", "W."],
    "*": [".....", "..W..", "W.W.W", ".WWW.", "W.W.W", "..W..", "....."],
    "+": [".....", "..W..", "..W..", "WWWWW", "..W..", "..W..", "....."],
    ",": ["..", "..", "..", "..", "..", "..", ".W", "W."],
    "-": ["....", "....", "....", "WWWW", "....", "....", "...."],
    ".": [".", ".", ".", ".", ".", ".", "W"],
    "/": ["..W", "..W", ".W.", ".W.", ".W.", "W..", "W.."],
    "0": [".WWW.", "W...W", "W..WW", "W.W.W", "WW..W", "W...W", ".WWW."],
    "1": ["..W..", ".WW..", "W.W..", "..W..", "..W..", "..W..", "WWWWW"],
    "2": [".WWW.", "W...W", "....W", "...W.", "..W..", ".W...", "WWWWW"],
    "3": ["WWWW.", "....W", "....W", ".WWW.", "....W", "....W", "WWWW."],
    "4": ["...W.", "..WW.", ".W.W.", "W..W.", "WWWWW", "...W.", "...W."],
    "5": ["WWWWW", "W....", "WWWW.", "....W", "....W", "W...W", ".WWW."],
    "6": [".WWW.", "W....", "W....", "WWWW.", "W...W", "W...W", ".WWW."],
    "7": ["WWWWW", "....W", "...W.", "..W..", "..W..", "..W..", "..W.."],
    "8": [".WWW.", "W...W", "W...W", ".WWW.", "W...W", "W...W", ".WWW."],
    "9": [".WWW.", "W...W", "W...W", ".WWWW", "....W", "....W", ".WWW."],
    ":": [".", ".", "W", ".", ".", ".", "W"],
    ";": ["..", "..", ".W", "..", "..", "..", ".W", "W."],
    "<": ["...", "..W", ".W.", "W..", ".W.", "..W", "..."],
    "=": ["....", "....", "WWWW", "....", "WWWW", "....", "...."],
    ">": ["...", "W..", ".W.", "..W", ".W.", "W..", "..."],
    "?": [".WWW.", "W...W", "....W", "...W.", "..W..", ".....", "..W.."],
    "@": [".WWW.", "W...W", "W.WWW", "W.W.W", "W.WWW", "W....", ".WWWW"],
    "A": [".WWW.", "W...W", "W...W", "WWWWW", "W...W", "W...W", "W...W"],
    "B": ["WWWW.", "W...W", "W...W", "WWWW.", "W...W", "W...W", "WWWW."],
    "C": [".WWW.", "W...W", "W....", "W....", "W....", "W...W", ".WWW."],
    "D": ["WWWW.", "W...W", "W...W", "W...W", "W...W", "W...W", "WWWW."],
    "E": ["WWWWW", "W....", "W....", "WWWW.", "W....", "W....", "WWWWW"],
    "F": ["WWWWW", "W....", "W....", "WWWW.", "W....", "W....", "W...."],
    "G": [".WWW.", "W...W", "W....", "W.WWW", "W...W", "W...W", ".WWWW"],
    "H": ["W...W", "W...W", "W...W", "WWWWW", "W...W", "W...W", "W...W"],
    "I": ["WWW", ".W.", ".W.", ".W.", ".W.", ".W.", "WWW"],
    "J": ["..WWW", "....W", "....W", "....W", "W...W", "W...W", ".WWW."],
    "K": ["W...W", "W..W.", "W.W..", "WW...", "W.W..", "W..W.", "W...W"],
    "L": ["W...", "W...", "W...", "W...", "W...", "W...", "WWWW"],
    "M": ["W...W", "WW.WW", "W.W.W", "W.W.W", "W...W", "W...W", "W...W"],
    "N": ["W...W", "W...W", "WW..W", "W.W.W", "W..WW", "W...W", "W...W"],
    "O": [".WWW.", "W...W", "W...W", "W...W", "W...W", "W...W", ".WWW."],
    "P": ["WWWW.", "W...W", "W...W", "WWWW.", "W....", "W....", "W...."],
    "Q": [".WWW.", "W...W", "W...W", "W...W", "W.W.W", "W..W.", ".WW.W"],
    "R": ["WWWW.", "W...W", "W...W", "WWWW.", "W.W..", "W..W.", "W...W"],
    "S": [".WWWW", "W....", "W....", ".WWW.", "....W", "....W", "WWWW."],
    "T": ["WWWWW", "..W..", "..W..", "..W..", "..W..", "..W..", "..W.."],
    "U": ["W...W", "W...W", "W...W", "W...W", "W...W", "W...W", ".WWW."],
    "V": ["W...W", "W...W", "W...W", ".W.W.", ".W.W.", "..W..", "..W.."],
    "W": ["W...W", "W...W", "W...W", "W.W.W", "W.W.W", "WW.WW", "W...W"],
    "X": ["W...W", "W...W", ".W.W.", "..W..", ".W.W.", "W...W", "W...W"],
    "Y": ["W...W", "W...W", ".W.W.", "..W..", "..W..", "..W..", "..W.."],
    "Z": ["WWWWW", "....W", "...W.", "..W..", ".W...", "W....", "WWWWW"],
    "[": ["WW", "W.", "W.", "W.", "W.", "W.", "WW"],
    "\\": ["W..", "W..", ".W.", ".W.", ".W.", "..W", "..W"],
    "]": ["WW", ".W", ".W", ".W", ".W", ".W", "WW"],
    "^": [".W.", "W.W", "...", "...", "...", "...", "..."],
    "_": [".....", ".....", ".....", ".....", ".....", ".....", ".....", "WWWWW"],
    "`": ["W.", ".W", "..", "..", "..", "..", ".."],
    "a": ["....", "....", ".WW.", "...W", ".WWW", "W..W", ".WWW"],
    "b": ["W...", "W...", "WWW.", "W..W", "W..W", "W..W", "WWW."],
    "c": ["....", "....", ".WWW", "W...", "W...", "W...", ".WWW"],
    "d": ["...W", "...W", ".WWW", "W..W", "W..W", "W..W", ".WWW"],
    "e": ["....", "....", ".WW.", "W..W", "WWWW", "W...", ".WWW"],
    "f": ["..WW", ".W..", "WWW.", ".W..", ".W..", ".W..", ".W.."],
    "g": ["....", "....", ".WWW", "W..W", "W..W", "W..W", ".WWW", "...W", "WWW."],
    "h": ["W...", "W...", "WWW.", "W..W", "W..W", "W..W", "W..W"],
    "i": ["W", ".", "W", "W", "W", "W", "W"],
    "j": ["..W", "...", "..W", "..W", "..W", "..W", "..W", "W.W", ".W."],
    "k": ["W...", "W...", "W..W", "W.W.", "WW..", "W.W.", "W..W"],
    "l": ["W.", "W.", "W.", "W.", "W.", "W.", ".W"],
    "m": [".....", ".....", "WWWW.", "W.W.W", "W.W.W", "W.W.W", "W.W.W"],
    "n": ["....", "....", "WWW.", "W..W", "W..W", "W..W", "W..W"],
    "o": ["....", "....", ".WW.", "W..W", "W..W", "W..W", ".WW."],
    "p": ["....", "....", "WWW.", "W..W", "W..W", "W..W", "WWW.", "W...", "W..."],
    "q": ["....", "....", ".WWW", "W..W", "W..W", "W..W", ".WWW", "...W", "...W"],
    "r": ["....", "....", "W.WW", "WW..", "W...", "W...", "W..."],
    "s": ["....", "....", ".WWW", "W...", ".WW.", "...W", "WWW."],
    "t": ["...", ".W.", "WWW", ".W.", ".W.", ".W.", "..W"],
    "u": ["....", "....", "W..W", "W..W", "W..W", "W..W", ".WWW"],
    "v": [".....", ".....", "W...W", "W...W", ".W.W.", ".W.W.", "..W.."],
    "w": [".....", ".....", "W...W", "W...W", "W.W.W", "W.W.W", ".W.W."],
    "x": [".....", ".....", "W...W", ".W.W.", "..W..", ".W.W.", "W...W"],
    "y": ["....", "....", "W..W", "W..W", "W..W", "W..W", ".WWW", "...W", "WWW."],
    "z": ["....", "....", "WWWW", "...W", ".WW.", "W...", "WWWW"],
    "{": ["..W", ".W.", ".W.", "W..", ".W.", ".W.", "..W"],
    "|": ["W", "W", "W", "W", "W", "W", "W", "W", "W"],
    "}": ["W..", ".W.", ".W.", "..W", ".W.", ".W.", "W.."],
    "~": [".....", ".....", ".WW.W", "W..W.", ".....", ".....", "....."],
}
# fmt: on

CHARS = [chr(c) for c in range(32, 127)]
Sprite = pixel.Sprite


def _cell(ch: str) -> Sprite:
    """The glyph padded to its full 9 rows (cap + descender)."""
    rows = GLYPHS[ch]
    w = len(rows[0])
    return pixel.check(rows + ["." * w] * (CAP + DESC - len(rows)), f"glyph {ch!r}")


def advance(ch: str) -> int:
    if ch == " ":
        return SPACE
    if ch.isdigit():
        return 6  # tabular digits
    return len(GLYPHS[ch][0]) + 1


def _offset_x(ch: str) -> int:
    """Narrow digits are centred in the 5-wide digit column."""
    if ch.isdigit():
        return (5 - len(GLYPHS[ch][0])) // 2
    return 0


def glyph(ch: str, outlined: bool) -> Sprite:
    g = _cell(ch)
    if outlined:
        g = pixel.outline(pixel.pad(g, 1, 1, 1, 1), "K", diagonal=True)
    return g


def text_width(s: str) -> int:
    return sum(advance(ch) for ch in s) - (1 if s else 0)


def line_height(outlined: bool) -> int:
    return LINE_HEIGHT_OUTLINED if outlined else LINE_HEIGHT


def text(s: str, colour: str = "W", outlined: bool = False, shadow: str = "") -> Sprite:
    """s rendered as one line, as Godot draws it at font_size = the font's size: the
    line's top-left is the sprite's (0, 0), the outline may reach 1 pixel left of it, so
    the sprite starts 1 column early when outlined (draw it at x - 1). colour recolours
    the W; shadow puts a 1-px drop shadow of that letter down-right, as a LabelSettings
    shadow does."""
    pad = 1 if outlined else 0
    w = max(1, text_width(s)) + 2 * pad + (1 if shadow else 0)
    h = line_height(outlined)
    out = pixel.blank(w, h)
    layers = []
    x = 0
    for ch in s:
        if ch != " " and ch in GLYPHS:
            layers.append((x + _offset_x(ch), glyph(ch, outlined)))
        x += advance(ch)
    if shadow:
        for gx, g in layers:
            out = pixel.paste(out, pixel.silhouette(g, shadow), TOP + 1 - pad, gx + 1)
    for gx, g in layers:
        out = pixel.paste(out, pixel.recolour(g, {"W": colour}), TOP - pad, gx)
    return out


def text_lines(lines: list[str], colour: str = "W", outlined: bool = False, shadow: str = "") -> Sprite:
    return pixel.stack([text(s, colour, outlined, shadow) if s else ["."] * line_height(outlined) for s in lines])


# ---------------------------------------------------------------------------------
# BMFont writer
# ---------------------------------------------------------------------------------


def _pack(outlined: bool) -> tuple[Sprite, dict[str, tuple[int, int, int, int]]]:
    """All glyphs on one page, rows left to right, 1 pixel apart. Returns the page and
    each char's (x, y, w, h)."""
    gh = CAP + DESC + (2 if outlined else 0)
    rects: dict[str, tuple[int, int, int, int]] = {}
    x, y = 1, 1
    for ch in CHARS:
        if ch == " ":
            continue
        gw = len(glyph(ch, outlined)[0])
        if x + gw + 1 > PAGE_W:
            x, y = 1, y + gh + 1
        rects[ch] = (x, y, gw, gh)
        x += gw + 1
    height = 1
    while height < y + gh + 1:
        height *= 2
    page = pixel.blank(PAGE_W, height)
    for ch, (gx, gy, _, _) in rects.items():
        page = pixel.paste(page, glyph(ch, outlined), gy, gx)
    return page, rects


def _write_font(name: str, outlined: bool) -> dict:
    page, rects = _pack(outlined)
    png = f"{name}_0.png"
    pixel.write_png(kit.FONTS / png, page)
    pixel.write_png(kit.OUT / f"{name}_page@4x.png", page, 4, pixel.PREVIEW_BG)
    pad = 1 if outlined else 0
    lines = [
        f'info face="{FACE}{" Outline" if outlined else ""}" size={NOMINAL_SIZE} bold=0 italic=0 charset="" '
        f"unicode=1 stretchH=100 smooth=0 aa=1 padding=0,0,0,0 spacing=1,1 outline=0",
        f"common lineHeight={line_height(outlined)} base={BASE} scaleW={PAGE_W} scaleH={len(page)} pages=1 packed=0 "
        f"alphaChnl=0 redChnl=4 greenChnl=4 blueChnl=4",
        f'page id=0 file="{png}"',
        f"chars count={len(CHARS)}",
    ]
    for ch in CHARS:
        if ch == " ":
            x = y = w = h = 0
            xo = yo = 0
        else:
            x, y, w, h = rects[ch]
            xo, yo = _offset_x(ch) - pad, TOP - pad
        lines.append(
            f"char id={ord(ch):<4} x={x:<5} y={y:<5} width={w:<5} height={h:<5} xoffset={xo:<5} "
            f"yoffset={yo:<5} xadvance={advance(ch):<5} page=0  chnl=15"
        )
    lines.append("kernings count=0")
    fnt = kit.FONTS / f"{name}.fnt"
    fnt.parent.mkdir(parents=True, exist_ok=True)
    fnt.write_text("\n".join(lines) + "\n")
    return {
        "fnt": kit.res(fnt),
        "page": kit.res(kit.FONTS / png),
        "font_size_1x": NOMINAL_SIZE,
        "font_size_2x": NOMINAL_SIZE * 2,
        "line_height": line_height(outlined),
        "base": BASE,
        "cap_height": CAP,
        "descender": DESC,
        "outline": outlined,
    }


def _specimen() -> None:
    """Previews: the full set, the confusable groups, sample lines, plain and outlined."""
    sets = [CHARS[1:33], CHARS[33:65], CHARS[65:]]
    lines = ["".join(s) for s in sets] + [
        "",
        "g j p q y   0 O o   1 l I   ( ) [ ] { }",
        ". , : ; ! ? ' \" - _ + = * / \\ | ~ ^ ` @ # $ % &",
        "",
        "The goblin hits you for 4 damage!",
        "Level 3 - Floor B2",
        "HP 72/100  Gold 1,048  Turn 15",
        "You quaff the potion. You feel better.",
        "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
        "the quick brown fox jumps over the lazy dog",
    ]
    plain = text_lines(lines)
    outlined = text_lines(lines, outlined=True)
    sheet = pixel.stack([pixel.pad(plain, 4, 4, 4, 4), pixel.pad(outlined, 4, 4, 4, 4)], 4)
    pixel.write_png(kit.OUT / "font_specimen@3x.png", sheet, 3, pixel.PREVIEW_BG)
    pixel.write_png(kit.OUT / "font_specimen@2x.png", sheet, 2, pixel.PREVIEW_BG)


def build() -> None:
    for ch in CHARS[1:]:
        assert ch in GLYPHS, f"no glyph for {ch!r}"
        _cell(ch)
    fonts = {
        "font_dungeon": _write_font("font_dungeon", outlined=False),
        "font_dungeon_outline": _write_font("font_dungeon_outline", outlined=True),
    }
    kit.merge_json("fonts", fonts)
    _specimen()
    print(f"ui_font: {len(CHARS)} glyphs, line height {LINE_HEIGHT}, base {BASE}")
