"""Dungeon props: decorations (decor_[type]_[variant]) and the treasure chest.

    python3 art/build.py env_props

Each prop is drawn without its outline (outlined() adds the K outline) and set on a
16x16, 16x32 or 32x32 canvas, standing on the canvas's bottom with a translucent drop
shadow. Wall-mounted ones (torch, banner, chains, cobweb) hang from the canvas's top and
cast no shadow. Writes assets/sprites/environment/decor_*.png (strips with SpriteFrames
for the animated ones), the "props" section of assets/animations/environment.json, and
art/out/environment/props@4x.png.
"""

from __future__ import annotations

import pixel
from environment import _shared as sh
from environment._chest import (CHEST_CLOSED, CHEST_LID_CRACKED, CHEST_LID_HALF, CHEST_OPEN,
                                CHEST_TRAPPED)
from environment._shared import outlined, on_canvas

# =================================================================================
# Flames, shared by the torch, the brazier and the candles
# =================================================================================

# Small flame for the wall torch, 6 x 8, four flickers
TORCH_FLAMES = [
    [
        "..R...",
        "..OR..",
        ".ROOR.",
        ".OYYO.",
        "ROYWYO",
        "ROYWYR",
        ".OYYO.",
        "..OO..",
    ],
    [
        ".R....",
        ".OR...",
        "ROOR..",
        "OYYOR.",
        "OYWYOR",
        "ROYWYR",
        ".OYYO.",
        "..OO..",
    ],
    [
        "...R..",
        "..RO..",
        "..OOR.",
        ".OYYO.",
        "ROYWYO",
        "OYWWYR",
        ".OYYO.",
        "..OO..",
    ],
    [
        "......",
        "...R..",
        "..ROR.",
        ".ROYOR",
        ".OYWYO",
        "ROYWYR",
        ".OYYO.",
        "..OO..",
    ],
]

# Big flame for the brazier and the fire effect, 10 x 12, four flickers
BIG_FLAMES = [
    [
        "....R.....",
        "....RR....",
        "...ROR....",
        "...ROOR...",
        "..ROYOR.R.",
        "..OYYOROR.",
        ".ROYWYOOR.",
        ".OYWWYYOR.",
        "ROYWWWYOOR",
        "OYYWWWYYOR",
        ".OYYWYYOO.",
        "..OOOOOO..",
    ],
    [
        "......R...",
        ".....RR...",
        ".R..ROR...",
        ".R.ROOR...",
        "..RROYOR..",
        "..ROYYOR..",
        ".ROYWYYOR.",
        ".OYWWYYOR.",
        "ROYWWWYOOR",
        "OYYWWWYYOR",
        ".OYYWYYOO.",
        "..OOOOOO..",
    ],
    [
        "...R..R...",
        "...RR.RR..",
        "..ROR.ROR.",
        "..ROOROOR.",
        "..ROYOYOR.",
        ".ROYYYYOR.",
        ".OYYWYYOR.",
        ".OYWWWYOR.",
        "ROYWWWYOOR",
        "OYYWWWYYOR",
        ".OYYWYYOO.",
        "..OOOOOO..",
    ],
    [
        "...R......",
        "...RR.....",
        "...ROR..R.",
        "...ROOR.R.",
        "..ROYORR..",
        "..ROYYOR..",
        ".ROYYWYOR.",
        ".OYYWWYOR.",
        "ROYWWWYOOR",
        "OYYWWWYYOR",
        ".OYYWYYOO.",
        "..OOOOOO..",
    ],
]


def glow(sprite: list[str]) -> list[str]:
    """A one-pixel translucent halo round a flame."""
    return pixel.outline(pixel.pad(sprite, 1, 1, 1, 1), "*")


# =================================================================================
# Stonework: pillars, statue, altar, rubble
# =================================================================================

PILLAR = [
    "LLLLLLLLLLLLLG",
    "LWWWWLLLLLLLLG",
    "LLLLLLLLLLLLGG",
    "GGGGGGGGGGGGGD",
    "DDDDDDDDDDDDDD",
    "..GGGGGGGGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGGGDDD..",
    "..LWLLGGGGDD..",
    "..LWLLGDGGDD..",
    "..LWLLGGDGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGGGGDD..",
    "..LWLGGGGGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGGGGDD..",
    "..GGGGGGGGDD..",
    ".LLLLLLLLLLLG.",
    "LLLLLLLLLLLLLG",
    "LGGGGGGGGGGGGD",
    "LGGGGGGGGGGGGD",
    "DDDDDDDDDDDDDD",
]

PILLAR_BROKEN = [
    "....WL........",
    "..LLGLW..LL...",
    "..LGGGLLLGGL..",
    "..LWLGGGGGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGDGGDD..",
    "..LWLLGGDGDD..",
    "..LWLLGGGGDD..",
    "..LWLLGGGGDD..",
    "..GGGGGGGGDD..",
    ".LLLLLLLLLLLG.",
    "LLLLLLLLLLLLLG",
    "LGGGGGGGGGGGGD",
    "LGGGGGGGGGGGGD",
    "DDDDDDDDDDDDDD",
]
# A chunk of the fallen drum lies at its foot
PILLAR_CHUNK = ["LWLG", "LLGD", "GDDD"]

# A hooded guardian, hands resting on a sword set point-down before it, on a plinth
STATUE = [
    ".....LLLG.....",
    "....LWLLGG....",
    "...LLGGGGGD...",
    "...LGDDDDGD...",
    "...LGDKKDGD...",
    "...LGDDDDGD...",
    "..LLLGGGGGGD..",
    ".LLGGGGGGGGGD.",
    ".LGGGLWLGGGGD.",
    ".LGGLWLLLGGGD.",
    ".LGLLLWLLGGGD.",
    ".LGGDWLGDGGGD.",
    ".LGGGWLGGDGGD.",
    "LLGGGWLGGGDGGD",
    "LGGGGWLGGGDGGD",
    "LGGDGWLGGGGDGD",
    "LGGDGWLGGGGDGD",
    "LGDGGWLGGDGDGD",
    "LGDGGWLGGDGGDD",
    "LGDGGDLGGDGGDD",
    "LGDGGGDGGDGGDD",
    "DDDDDDDDDDDDDD",
    "LLLLLLLLLLLLLG",
    "LWWLLLLLLLLLGG",
    "LGGGGGGGGGGGGD",
    "LGGGGDGGGGGGGD",
    "DDDDDDDDDDDDDD",
]

# A stone altar with a purple runner and two candles; flames are added per frame
ALTAR = [
    "...WL.................WL...",
    "...LG.................LG...",
    "...LG.................LG...",
    "LLLLLLLLLLLLLLLLLLLLLLLLLLG",
    "LWWLLLLLMPPPPPPPPPpLLLLLLGG",
    "LLLLLLLLMPPPPPPPPPpLLLLLGGG",
    "GGGGGGGGMPPPPPPPPPpGGGGGGGD",
    "DDDDDDDDMPPPPPPPPPpDDDDDDDD",
    "LGGGGGGDMPPPPYPPPPpLGGGGGGD",
    "LGGGGGGDMPPPYOYPPPpLGGGGGGD",
    "LGGGDGGDMPPPPYPPPPpLGGGDGGD",
    "LGGGGGGDMPPPPPPPPPpLGGGGGGD",
    "LGGGGGGDpMpMpMpMpMpLGGGGGGD",
    "LGGGGGGDDGGGGGGGGGDLGGGGGGD",
    "DDDDDDDDDDDDDDDDDDDDDDDDDDD",
    "LLLLLLLLLLLLLLLLLLLLLLLLLLG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGD",
    "DDDDDDDDDDDDDDDDDDDDDDDDDDD",
]
ALTAR_FLAMES = [["Y", "O"], ["Y", "R"], ["W", "O"], ["Y", "O"]]


def _rubble(layout: list[tuple[int, int, int, int]], w: int, h: int) -> list[str]:
    base = pixel.blank(w, h)
    for lw, lh, top, left in layout:
        lump = sh.bevel(pixel.ellipse(lw, lh, "G"), "L", "D")
        base = pixel.paste(base, lump, top, left)
    return base


RUBBLE_A = _rubble([(6, 5, 2, 0), (5, 4, 0, 5), (7, 5, 3, 5), (4, 3, 5, 1), (3, 3, 6, 10)], 13, 9)
RUBBLE_B = _rubble([(5, 4, 1, 2), (8, 6, 2, 4), (4, 3, 5, 0), (3, 2, 6, 11)], 14, 8)

# =================================================================================
# Bones
# =================================================================================

BONES_A = [
    ".WL.......WL.",
    "WWLLLLLLLLWLG",
    "LLGGGGGGGGLGG",
    ".GG.......GG.",
    ".............",
    "...WL........",
    "..WLG...WL...",
    ".WLG....LG...",
    ".LG..........",
]

BONES_B = [  # a ribcage: the spine, ribs curling out on both sides
    "..WL.WL.WL...",
    ".W..W..W..L..",
    "W..W..W..L...",
    "LGLGLGLGLGLG.",
    "W..W..W..L...",
    ".W..W..W..L..",
    "..LG.LG.LG...",
]

SKULL = [
    "..WWWWL..",
    ".WWWWWWL.",
    "WWWWWWWLG",
    "WKKWWKKLG",
    "WKKWWKKGG",
    ".WLWKWLG.",
    "..WKWKG..",
    "..LGLGG..",
]


def _skull_pile() -> list[str]:
    """Skulls heaped back to front, a long bone poking out."""
    s = outlined(SKULL)  # 11 x 10
    bone = outlined(["WL........WL", "LWWLLLLLLLLG", ".G........G."])
    pile = pixel.blank(28, 20)
    for top, left, art in [(0, 9, s), (2, 3, bone), (5, 4, s), (5, 14, s), (10, 0, s),
                           (10, 9, s), (10, 17, s)]:
        pile = pixel.paste(pile, art, top, left)
    return pile


# =================================================================================
# Wood: barrel, crate, table, chair, bookshelf, cot, weapon rack, coffin
# =================================================================================

BARREL = [
    "..DGGGGGGD..",
    ".DTTbTTTbTD.",
    "DTTTbTTTbTTD",
    ".DGGGGGGGGD.",
    "DLGGGGGGGGGD",
    ".TTbBBbBBbb.",
    "BTTbBBbBBbbb",
    "BTTbBBbBBbbb",
    "GLLGGGGGGGDD",
    "BTTbBBbBBbbb",
    "BTTbBBbBBbbb",
    "BTTbBBbBBbbb",
    "GLLGGGGGGGDD",
    "BTTbBBbBBbbb",
    ".TTbBBbBBbb.",
    "..bbbbbbbb..",
]

CRATE = [
    "STTTTTTTTTTT",
    "TSTTTTTTTTTB",
    "TTTTTTTTTTBB",
    "bbbbbbbbbbbb",
    "TTTTTTTTTTTb",
    "TbBBBBBBTBTb",
    "TBbBBBBTBBTb",
    "TBBbBBTBBBTb",
    "TBBBbTBBBBTb",
    "TBBBTbBBBBTb",
    "TBBTBBbBBBTb",
    "Tbbbbbbbbbbb",
]

TABLE = [
    "STTTTTTTTTTTTTTTTTTTTTTTTTTB",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTB",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTb",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBb",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTb",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTb",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBb",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTb",
    "bbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBb",
    "bTBbbbbbbbbbbbbbbbbbbbbbTBbb",
    ".TB.....................TBb.",
    ".TB.....................TBb.",
    ".TB.....................TBb.",
    ".TB.....................TBb.",
    ".TB.....................TBb.",
    ".bb.....................bbb.",
]
# Things on the table: a pewter mug and an open book
TABLE_MUG = outlined(["LWG.", "LGDG", "LGDG", "GDD."])
TABLE_BOOK = outlined(["WWLWW", "WLGWL", "rrrrr"])

CHAIR = [
    ".TTTTTTTT.",
    "TBBBBBBBBb",
    "TB.b..b.Tb",
    "TB.b..b.Tb",
    "TB.b..b.Tb",
    "TBBBBBBBTb",
    "STTTTTTTTT",
    "TTTTTTTTTB",
    "bbbbbbbbbb",
    "TB......Tb",
    "TB......Tb",
    "TB......Tb",
    "bb......bb",
]

# Book spines on one shelf: (light, dark, rows short of the shelf's full height)
SHELF_BOOKS = [
    [("R", "r", 0), ("U", "u", 1), ("V", "v", 0), (".", ".", 0), ("P", "p", 2), ("T", "B", 0),
     ("R", "r", 1), ("U", "u", 0), ("L", "G", 3), ("V", "v", 1), ("P", "p", 0), ("R", "r", 2)],
    [("U", "u", 2), ("T", "B", 0), ("T", "B", 0), ("R", "r", 1), ("V", "v", 0), (".", ".", 0),
     (".", ".", 0), ("S", "T", 4), ("P", "p", 1), ("U", "u", 0), ("R", "r", 0), ("V", "v", 2)],
    [("V", "v", 0), ("R", "r", 2), ("P", "p", 0), ("U", "u", 1), ("R", "r", 0), ("T", "B", 1),
     (".", ".", 0), ("W", "L", 4), ("L", "G", 4), ("U", "u", 0), ("V", "v", 1), ("P", "p", 0)],
]


def _bookshelf() -> list[str]:
    """A tall shelf against the wall: lit top, three shelves of books."""
    w = 28
    rows = ["S" + "T" * (w - 2) + "B", "T" * (w - 1) + "b", "b" * w]
    for books in SHELF_BOOKS:
        shelf = []
        for r in range(6):
            line = "Tb"
            for light, dark, short in books:
                if light == "." or r < short:
                    line += "KK"
                else:
                    line += light + dark
            shelf.append(line + "bb")
        rows += shelf + ["T" + "T" * (w - 3) + "Bb", "b" * w]
    rows += ["TB" + "b" * (w - 4) + "Bb", "bb" + "." * (w - 4) + "bb"]
    return rows


BOOKSHELF = _bookshelf()

COT = [
    "TTTTTTTTTTTTTB",
    "TBBBBBBBBBBBBb",
    "TbbbbbbbbbbbBb",
    "TbSSSSSSSSSTBb",
    "TbSWWWWWWWLSBb",
    "TbSWWWWWWWLTBb",
    "TbSLLLLLLLGTBb",
    "TbSSSSSSSSSTBb",
    "TbFFFFFFFFFRBb",
    "TbRRRRRRRRRrBb",
    "TbRRRRRRRRRrBb",
    "TbRRRRRRRRRrBb",
    "TbRRRRrRRRRrBb",
    "TbRRRRRrRRRrBb",
    "TbRRRRRRRRRrBb",
    "TbRRRRRRRRRrBb",
    "TbRRRrRRRRRrBb",
    "TbRRRRrRRRRrBb",
    "TbRRRRRRRRRrBb",
    "TbRRRRRRRRRrBb",
    "TbrrrrrrrrrrBb",
    "TbSSSSSSSSSTBb",
    "TTTTTTTTTTTTTB",
    "TbbbbbbbbbbbBb",
    "Tb.........TBb",
    "bb.........bbb",
]

WEAPON_RACK = [
    "TB......WL......LWG.......TB",
    "TB.....WLG......LWG.......TB",
    "TB.....WLG.....LLWGL......TB",
    "TB.....WLG......LWG...GLL.TB",
    "TB.....WLG......LWG..GLLLGTB",
    "TBTTTTTWLGTTTTTTLWGTTGLWLGTB",
    "TbbbbbbWLGbbbbbbLWGbbDGLGDTb",
    "TB.....WLG......LWG....TB.TB",
    "TB.....WLG......LWG....TB.TB",
    "TB.....WLG......LWG....TB.TB",
    "TB.....WLG......LWG....TB.TB",
    "TB...OYYOOYO..OYYOOYO..TB.TB",
    "TB.....TBb.......TBb...TB.TB",
    "TB.....TBb.......TBb...TB.TB",
    "TB.....YOb.......YOb...TB.TB",
    "TBTTTTTTTTTTTTTTTTTTTTTTTTTB",
    "TbbbbbbbbbbbbbbbbbbbbbbbbbTb",
    "TB.......................TBb",
    "TB.......................TBb",
    "bb.......................bbb",
]

COFFIN = [
    "...bbbbbbbb...",
    "..bTTTTTTTTb..",
    ".bTTBBBBBBTBb.",
    "bTTBBBBBBBBTBb",
    "bTBBYBBBBYBBBb",
    "bTBBBBBBBBBBBb",
    "bTBBTTTTTTBBBb",
    ".bTBTBBBBbBBb.",
    ".bTBTBBBBbBBb.",
    ".bTBTBBBBbBBb.",
    ".bTBTBBBBbBBb.",
    ".bTBTBBBBbBBb.",
    ".bTBTBBBBbBBb.",
    ".bTBTBBBBbBBb.",
    ".bTBTBBBBbBBb.",
    "..bTBbbbbbBb..",
    "..bTBBBBBBBb..",
    "..bTYBBBBYBb..",
    "..bTBBBBBBBb..",
    "...bbbbbbbb...",
    "...DDDDDDDD...",
]

# =================================================================================
# Small things: candles, urn, sack, mushrooms
# =================================================================================

CANDLES = [
    "...........",
    "...........",
    "..K........",
    ".WLG.......",
    ".WLG...K...",
    ".WLG..WLG..",
    ".WLG..WLG.K",
    ".WLGW.WLGLG",
    ".WLGL.WLGLG",
    "WWLLGLWLGLG",
    "LLLLLLLLLLG",
]
# Each candle's wick tip (row, column) in CANDLES, for the flame
CANDLE_WICKS = [(2, 2), (4, 7), (6, 10)]
CANDLE_FLAMES = [["Y", "O"], ["W", "Y"], ["Y", "R"], ["O", "R"]]

URN = [
    "..TTTTTT..",
    ".TbbbbbbB.",
    "..TbbbbB..",
    "...TTBb...",
    "..TTBBBb..",
    ".TTTBBBBb.",
    "TTOOOOOObb",
    "TTYOYOYObb",
    "TTOOOOOObb",
    "TTTBBBBBbb",
    ".TTBBBBbb.",
    "..TBBBbb..",
    "...bbbb...",
]

SACK = [
    "....TS....",
    "...TSSB...",
    "....TB....",
    "..TTTBBB..",
    ".TSTTTBBb.",
    "TSTTTTBBBb",
    "TTTTTBBBbb",
    "TTTTBBBBbb",
    "TTTBBBbBbb",
    ".TBBBBbbb.",
    "..bbbbbb..",
]

MUSHROOMS = [
    "...ICC........",
    "..ICCCU.......",
    ".ICCCCCU..IC..",
    ".CCUCCUU.ICCU.",
    "...WL...ICCCCU",
    "...WL....UWLU.",
    "...WL.....WL..",
    "..WLL.IU..WL..",
    "..WLLICCU.WL..",
    ".....WL..WLL..",
]

# =================================================================================
# Wall hangings: torch, banner, chains, cobweb
# =================================================================================

TORCH_HOLDER = [
    "GLLLLG",
    "DGGGGD",
    ".DGGD.",
    "..TB..",
    "..TB..",
    ".GLLD.",
    ".DGGD.",
]

BANNER = [
    "LGGGGGGGGGGGGD",
    ".FRRRRRRRRRRr.",
    ".FRRRRRRRRRRr.",
    ".FRRRRRRRRRrr.",
    ".FRRRRYRRRRrr.",
    ".FRRRYOYRRRrr.",
    ".FRRYOROYRRrr.",
    ".FRYORRROYRrr.",
    ".FRRYOROYRRrr.",
    ".FRRRYOYRRRrr.",
    ".FRRRRYRRRRrr.",
    ".FRRRRRRRRRrr.",
    ".FRYYYYYYYRrr.",
    ".FRRRRRRRRRrr.",
    ".FRRRRRRRRRrr.",
    ".FRRRRRRRRRrr.",
    ".FRRRRrRRRRrr.",
    ".FRRRRRRRRRrr.",
    ".FRRRRRRRRRrr.",
    ".FRRRRRRRRRrr.",
    ".FRRRR.RRRRrr.",
    ".FRRR...RRRrr.",
    ".FRR.....RRr..",
    ".FR.......Rr..",
]

CHAIN_LINKS = [".L.", "L.G", ".D.", ".L.", ".G."]  # a ring, then a link seen edge-on
SHACKLE = [".LLG.", "L...G", "L...D", ".GDD."]


def _chains() -> list[str]:
    left = (CHAIN_LINKS * 6)[:24] + SHACKLE
    right = (CHAIN_LINKS * 4)[:17]
    out = pixel.blank(12, 28)
    out = pixel.paste(out, ["GLLG", "DGGD"], 0, 0)
    out = pixel.paste(out, ["GLLG", "DGGD"], 0, 8)
    out = pixel.paste(out, left, 2, 0)
    out = pixel.paste(out, right, 2, 9)
    return out


CHAINS = _chains()

# A corner web, anchored in the top-left corner; strands and faint silk, no outline
COBWEB = [
    "WLLLLLLLLL:LL:L.",
    "LL::L::::L:::...",
    "L:L:::L::L::....",
    "L::L::L:L::.....",
    "LL::LL:LL:......",
    "L:::L:L::.......",
    "L:::LL::........",
    "L:L:L::.........",
    "LL::L:..........",
    "L::L:...........",
    ":::L:...........",
    "L:L:............",
    "L::.............",
    "L:..............",
    ":...............",
    "L...............",
]

# =================================================================================
# Assembly
# =================================================================================


def _standing(body: list[str], w: int, h: int, shadow: int | None = None, dx: int = 0) -> list[str]:
    art = outlined(body)
    width = pixel.size(art)[0]
    return on_canvas(art, w, h, shadow if shadow is not None else min(width + 2, w), dx)


def _hanging(body: list[str], w: int, h: int, top: int = 0, outline: bool = True) -> list[str]:
    art = outlined(body) if outline else body
    aw, _ = pixel.size(art)
    return pixel.check(pixel.paste(pixel.blank(w, h), art, top, (w - aw) // 2))


def torch_frames() -> list[list[str]]:
    frames = []
    for flame in TORCH_FLAMES:
        holder = outlined(TORCH_HOLDER)  # 8 x 9
        f = pixel.blank(16, 16)
        f = pixel.paste(f, glow(flame), 0, 4)
        f = pixel.paste(f, holder, 7, 4)
        f = pixel.paste(f, flame, 1, 5)
        frames.append(pixel.check(f))
    return frames


def brazier_frames() -> list[list[str]]:
    bowl = [
        ".GLLLLLLLLLLG.",
        "GLROYOROYRORLD",
        "LGrRORRORRrRGD",
        "GLLLLLLLLLLLLD",
        "DGGGGGGGGGGGDD",
        ".DGGGGGGGGGDD.",
        "..DDGGGGGDDD..",
        "......GD......",
        "......GD......",
        ".....LGGD.....",
        "....GDGDGD....",
        "...GD.GD.GD...",
        "..GD..GD..GD..",
        ".GD...GD...GD.",
        "GD....GD....GD",
        "D.....DD.....D",
    ]
    stand = on_canvas(outlined(bowl), 16, 32, 14)
    frames = []
    for n, flame in enumerate(BIG_FLAMES):
        f = pixel.paste(stand, glow(flame), 2, 2)
        f = pixel.paste(f, flame, 3, 3)
        f = pixel.paste(f, outlined(bowl)[:3], 14, 0)  # the rim stays in front of the flame
        spark = [(1, 3), (0, 11), (2, 12), (1, 4)][n]
        f = pixel.paint(f, [spark], "*")
        frames.append(pixel.check(f))
    return frames


def candle_frames() -> list[list[str]]:
    base = outlined(CANDLES)  # 13 x 13
    frames = []
    for n in range(4):
        f = pixel.paste(pixel.blank(16, 16), base, 2, 1)
        for i, (r, c) in enumerate(CANDLE_WICKS):
            tip, body = CANDLE_FLAMES[(n + i) % 4]
            y, x = r + 2, c + 1 + 1
            f = pixel.paint(f, [(y - 2, x), (y - 1, x)], tip)
            f = pixel.paint(f, [(y, x)], body)
            for gy, gx in [(y - 1, x - 1), (y - 1, x + 1), (y - 3, x)]:
                if f[gy][gx] == ".":
                    f = pixel.paint(f, [(gy, gx)], "*")
        f = pixel.underlay(f, pixel.ellipse(14, 3, "_"), 13, 1)
        frames.append(pixel.check(f))
    return frames


def altar_frames() -> list[list[str]]:
    base = _standing(ALTAR, 32, 32, 30)
    top = 32 - 1 - len(outlined(ALTAR))
    frames = []
    for n in range(4):
        f = base
        for col in (4, 23):
            x = col + 2
            tip, body = ALTAR_FLAMES[(n + col // 4) % 4]
            f = pixel.paint(f, [(top - 1, x), (top, x)], tip)
            f = pixel.paint(f, [(top + 1, x)], body)
        frames.append(pixel.check(f))
    return frames


def chest_frames() -> dict[str, list[str]]:
    def put(art: list[str]) -> list[str]:
        return on_canvas(art, 32, 32, 28)

    return {
        "closed": put(CHEST_CLOSED),
        "open": put(CHEST_OPEN),
        "trapped": put(CHEST_TRAPPED),
        "opening": [put(a) for a in (CHEST_CLOSED, CHEST_LID_CRACKED, CHEST_LID_HALF, CHEST_OPEN)],
    }


def statics() -> dict[str, tuple[list[str], str]]:
    """name -> (sprite, notes) for every static decoration."""
    table = outlined(TABLE)
    table = pixel.paste(table, TABLE_MUG, 0, 5)
    table = pixel.paste(table, TABLE_BOOK, 2, 17)
    pillar_broken = on_canvas(outlined(PILLAR_BROKEN), 16, 32, 16)
    pillar_broken = pixel.paste(pillar_broken, outlined(PILLAR_CHUNK), 26, 10)
    banner = _hanging(BANNER, 16, 32, 1)
    return {
        "decor_pillar_stone": (_standing(PILLAR, 16, 32), "stands on its floor cell; blocks movement"),
        "decor_pillar_broken": (pillar_broken, ""),
        "decor_statue_guardian": (_standing(STATUE, 16, 32), ""),
        "decor_rubble_a": (_standing(RUBBLE_A, 16, 16), ""),
        "decor_rubble_b": (_standing(RUBBLE_B, 16, 16), ""),
        "decor_bones_a": (_standing(BONES_A, 16, 16, 0), "flat on the floor"),
        "decor_bones_b": (_standing(BONES_B, 16, 16, 0), "flat on the floor"),
        "decor_skull_a": (_standing(SKULL, 16, 16, 10), ""),
        "decor_skull_pile": (_standing(_skull_pile(), 32, 32, 28), ""),
        "decor_barrel_a": (_standing(BARREL, 16, 32), ""),
        "decor_crate_a": (_standing(CRATE, 16, 16), ""),
        "decor_table_wood": (on_canvas(table, 32, 32, 30), ""),
        "decor_chair_wood": (_standing(CHAIR, 16, 32), ""),
        "decor_bookshelf_a": (_standing(_bookshelf(), 32, 32), "against a wall face"),
        "decor_bed_cot": (_standing(COT, 16, 32), "head toward the wall"),
        "decor_weapon_rack": (_standing(WEAPON_RACK, 32, 32), "against a wall face"),
        "decor_coffin_a": (_standing(COFFIN, 16, 32), "lying on the floor, head up"),
        "decor_urn_a": (_standing(URN, 16, 16), ""),
        "decor_sack_a": (_standing(SACK, 16, 16), ""),
        "decor_mushrooms_a": (_standing(MUSHROOMS, 16, 16, 0), "cave floors; give it a faint cyan light"),
        "decor_banner_red": (banner, "hangs on a wall face from the canvas top"),
        "decor_banner_purple": (pixel.recolour(banner, {"R": "P", "r": "p", "F": "M"}), "hangs on a wall face"),
        "decor_chains_hanging": (_hanging(CHAINS, 16, 32, 0), "hangs on a wall face"),
        "decor_cobweb_left": (pixel.check(COBWEB), "top-left corner of a room"),
        "decor_cobweb_right": (pixel.flip(COBWEB), "top-right corner of a room"),
    }


def animated() -> dict[str, tuple[list[list[str]], int, str]]:
    """name -> (frames, fps, notes)."""
    return {
        "decor_torch_wall": (torch_frames(), 6, "on a wall face; pair with a PointLight2D using light_torch.png"),
        "decor_brazier_standing": (brazier_frames(), 6, "stands on the floor; pair with a PointLight2D"),
        "decor_candles_lit": (candle_frames(), 5, "on the floor or a table"),
        "decor_altar_stone": (altar_frames(), 5, "two candles flicker on top"),
    }


# Hung on the wall: their canvas top goes at the top of the upper wall face, and their
# origin is the canvas's top centre. Everything else stands on the floor, its origin
# the canvas's bottom centre (the bottom of the floor cell it stands in).
WALL_MOUNTED = {"decor_torch_wall", "decor_banner_red", "decor_banner_purple", "decor_chains_hanging",
                "decor_cobweb_left", "decor_cobweb_right"}


def build() -> None:
    entries: dict[str, dict] = {}
    for name, (sprite, notes) in statics().items():
        entries[name] = sh.write_static(name, sprite, notes)
    for name, (frames, fps, notes) in animated().items():
        entries[name] = sh.write_anim(name, frames, fps, True, notes)
    chest = chest_frames()
    for state in ("closed", "open", "trapped"):
        entries[f"decor_chest_{state}"] = sh.write_static(f"decor_chest_{state}", chest[state])
    entries["decor_chest_opening"] = sh.write_anim("decor_chest_opening", chest["opening"], 6, False,
                                                   "closed, lid cracked, lid swinging, open; play once")
    for name, entry in entries.items():
        entry["mount"] = "wall" if name in WALL_MOUNTED else "floor"
        if name in WALL_MOUNTED:
            entry["origin"] = [entry.get("size", entry.get("frame_size"))[0] // 2, 0]
    sh.merge_env_json("props", entries)
    looks = [s for s, _ in statics().values()] + [f[0] for f, _, _ in animated().values()]
    looks += [chest["closed"], chest["trapped"]] + chest["opening"]
    print(sh.preview("props", sh.sheet(looks, 8, 4), 4))
    print(f"props: {len(entries)} sprites")
