"""Dungeon tiles: floors, walls (face and cap), doors, stairs, the secret passage and
the floor shadows, packed with the trap tiles into one atlas and a Godot TileSet.

    python3 art/build.py env_tiles

Writes assets/tilesets/tile_*.png (one per tile; an animated tile's frames side by
side), tileset_dungeon.png/.json/.tres, and previews in art/out/environment/.

Perspective: top-down with a 3/4 tilt. Floors are seen from above. A wall cell shows
its FACE (the front, lit from the top left) when the cell below it is open, and its
CAP (the dark top) otherwise. Faces also repeat vertically, so a taller wall can stack
two. See NOTES.md.
"""

from __future__ import annotations

import pixel
from environment import _shared as sh
from environment._shared import T, Tile, bands, noise, roll, stamp, tile_of

# =================================================================================
# Floors
# =================================================================================

# Stone flags in a running bond: slab A on rows 0-6 (joint at column 15), slab B on
# rows 8-14 (joint at column 7), joints on rows 7 and 15. Variants split slabs and add
# wear but keep those edge joints, so they mix freely. Highlights stay in the corners:
# flags lie flat, unlike the bevelled wall blocks.
FLOOR_STONE_A = tile_of([
    "LLLGGGGGGGGGGGGD",
    "LGGGGGGGGGGGGGGD",
    "LGGGGDGGGGGGLGGD",
    "GGGGGGGGGGGGGGGD",
    "GGGGGGGGGDGGGGDD",
    "GGLGGGGGGGGGGGDD",
    "GGGGGGGGGGGGDDDD",
    "DDDDDDDDDDDDDDDD",
    "GGGGGGGDLLLGGGGG",
    "GGGGGGGDLGGGGGGG",
    "GGGGLGGDLGGGGDGG",
    "GDGGGGGDGGGGGGGG",
    "GGGGGGDDGGGGGGLG",
    "GGGGGGDDGGGDGGGG",
    "GGGGDDDDGGGGGGGG",
    "DDDDDDDDDDDDDDDD",
], "floor_stone_a")

FLOOR_STONE_B = tile_of([
    "LLGGGDLLLGGGGGGD",
    "LGGGGDLGGGGGGGGD",
    "GGGDGDGGGGGGGGGD",
    "GGGGGDGGGGGDGGGD",
    "GLGGDDGGGGGGGGDD",
    "GGGGDDGGGLGGGGDD",
    "GGDDDDGGGGGGDDDD",
    "DDDDDDDDDDDDDDDD",
    "GGGGGGGDLLGGDLLL",
    "GGGGGGGDLGGGDLGG",
    "GGDGGGGDGGGGDLGG",
    "GGGGGGGDGGGGDGGG",
    "GGGGGLDDGGGDDGGG",
    "GGGGGGDDGGGDDGDG",
    "GGGGDDDDGGDDDGGG",
    "DDDDDDDDDDDDDDDD",
], "floor_stone_b")

FLOOR_STONE_C = tile_of([
    "LLLGGGGGGGDLLGGD",
    "LGGGGGGGGGDLGGGD",
    "GGGGGGGLGGDGGGGD",
    "GGDGGGGGGGDGGGGD",
    "GGGGGGGGGDDGGGDD",
    "LGGGGGGGGDDGGDDD",
    "GGGGGGDDDDDGDDDD",
    "DDDDDDDDDDDDDDDD",
    "GGGGGGDDLLLGGGGG",
    "GGGGGGGDLGGDGGGG",
    "GGLGGGGDLGGGDGGG",
    "GGGGGGGDGGGGDLGG",
    "GDGDGGDDGGGGGDLG",
    "GGDGGGDDGGGGGGDG",
    "GGGGDDDDGGGGGGGG",
    "DDDDDDDDDDDDDDDD",
], "floor_stone_c")


def _cobbles(layout: list[tuple[int, int, int, int]], seed: int) -> list[str]:
    """Rounded cobbles (w, h, top, left) stamped with wrap-around on dark grit."""
    base = bands(noise(seed, cells=8), [(0.0, "K"), (0.45, "D")], 0.3)
    for w, h, top, left in layout:
        stone = sh.bevel(pixel.ellipse(w, h, "G"), "L", "D")
        base = stamp(base, stone, top, left)
    return base


FLOOR_COBBLE_A = tile_of(_cobbles([
    (7, 6, 0, 0), (6, 5, 1, 8), (5, 6, 6, 14), (6, 5, 7, 3), (4, 5, 6, 10),
    (6, 4, 12, 9), (6, 5, 12, 1),
], 11), "floor_cobble_a")

FLOOR_COBBLE_B = tile_of(_cobbles([
    (6, 5, 0, 1), (7, 6, 0, 8), (5, 5, 6, 0), (6, 6, 6, 6), (5, 5, 7, 12),
    (7, 4, 12, 3), (4, 4, 12, 11),
], 12), "floor_cobble_b")


def _dirt(seed: int, pebbles: list[tuple[int, int]], stones: list[tuple[int, int]]) -> list[str]:
    """Packed earth: soft darker patches (a sparse dither of the dark brown), single
    grit specks, small pebbles lit from the top left."""
    import random

    field = noise(seed, cells=4)
    rng = random.Random(seed)
    base = []
    for y in range(T):
        row = []
        for x in range(T):
            v, b = field[y][x], pixel.BAYER[y % 4][x % 4]
            row.append("b" if (v < 0.3 and b < 6) or (v < 0.5 and b < 2) else "B")
        base.append("".join(row))
    for _ in range(7):
        base = stamp(base, ["b"], rng.randrange(T), rng.randrange(T))
    for _ in range(5):
        base = stamp(base, ["T"], rng.randrange(T), rng.randrange(T))
    for y, x in pebbles:
        base = stamp(base, ["Tb"], y, x)
    for y, x in stones:
        base = stamp(base, ["LG", "Gb"], y, x)
    return base


FLOOR_DIRT_A = tile_of(_dirt(21, [(3, 11), (12, 2)], [(9, 6)]), "floor_dirt_a")
FLOOR_DIRT_B = tile_of(_dirt(22, [(1, 4), (10, 13), (14, 8)], []), "floor_dirt_b")
FLOOR_DIRT_C = tile_of(_dirt(23, [(6, 1)], [(2, 12), (12, 4)]), "floor_dirt_c")

# Moss creeping from the joints of the stone flags
MOSS_A = [
    "..............VE",
    "..............V.",
    "................",
    "................",
    "................",
    ".............E..",
    "..EV........VVvV",
    ".VVvVV.....VvvvV",
    "..vV.EV......VE.",
    ".......V........",
    ".......V........",
    "......VvE.......",
    ".......V........",
    "................",
    "VE..............",
    "vVV.........EVVv",
]
MOSS_B = [
    "................",
    "...EVE..........",
    "..EVVVV.........",
    ".EVVvVVE........",
    "..VVvvVV........",
    "...VVvV.........",
    ".....V..........",
    ".....v.......VV.",
    "............VvVE",
    ".......V.....V..",
    ".......v........",
    "................",
    "................",
    "..........E.....",
    ".........EVE....",
    "........VVvVV...",
]
FLOOR_MOSS_A = tile_of(sh.lay(FLOOR_STONE_A, MOSS_A), "floor_moss_a")
FLOOR_MOSS_B = tile_of(sh.lay(FLOOR_STONE_C, MOSS_B), "floor_moss_b")

# Wooden planks: four boards a tile, gaps on rows 3, 7, 11 and 15, ends staggered
FLOOR_WOOD_A = tile_of([
    "TTTTTbTTTTTTTTTT",
    "BBBBBbDBBBBBBBBB",
    "BBbbBbBBBBBBbbBB",
    "bbbbbbbbbbbbbbbb",
    "TTTTTTTTTTTTTbTT",
    "BBBBBBBBBBBBDbBB",
    "BBBBBbbBBBBBBbBB",
    "bbbbbbbbbbbbbbbb",
    "TTTTTTTTTbTTTTTT",
    "BBBBBBBBDbBBBBBB",
    "BbbBBBBBBbBBBBbB",
    "bbbbbbbbbbbbbbbb",
    "TbTTTTTTTTTTTTTT",
    "BbDBBBBBBBBBBBBB",
    "BbBBBBBBbbbBBBBB",
    "bbbbbbbbbbbbbbbb",
], "floor_wood_a")

FLOOR_WOOD_B = tile_of([
    "TTTTTTTTTTbTTTTT",
    "BBBBBBBBBBbDBBBB",
    "BBBBbbbBBBbBBBBB",
    "bbbbbbbbbbbbbbbb",
    "TTTbTTTTTTTTTTTT",
    "BBDbBBBBBTTBBBBB",
    "BBBbBBBBbBBbBBBB",
    "bbbbbbbbbbbbbbbb",
    "TTTTTTTTTTTTTTbT",
    "BBBBBKKKBBBBBDbB",
    "BBBBKKKKKbBBBBbB",
    "bbbbbbbbbbbbbbbb",
    "TTTTTTbTTTTTTTTT",
    "BBBBBDbBBBBBBBBB",
    "BbbBBBbBBBBBbbBB",
    "bbbbbbbbbbbbbbbb",
], "floor_wood_b")


def _ice(seed: int) -> list[str]:
    """Pale sheet ice: frosted white patches on clear blue, straight cracks with a lit
    lip, glints."""
    base = bands(noise(seed, cells=4), [(0.0, "C"), (0.6, "I")], 0.2)
    for y, x, art in [
        (2, 1, ["UU....", "..UUU.", ".....U"]),
        (9, 8, ["U.....", ".UU...", "...UUU", "......"]),
        (12, 0, ["..U", "UU."]),
    ]:
        base = stamp(base, art, y, x)
        lip = ["".join("I" if ch == "U" else "." for ch in row) for row in art]
        base = stamp(base, [r for r in lip], y + 1, x)
        base = stamp(base, art, y, x)
    base = pixel.paint(base, [(5, 12), (13, 10), (1, 9)], "W")
    return base


FLOOR_ICE_A = tile_of(_ice(31), "floor_ice_a")


def _water_frames() -> list[list[str]]:
    """Water: still depths with ripples drifting right 4 pixels a frame, so the
    4-frame loop comes back to its start."""
    deep = bands(noise(41, cells=4), [(0.0, "u"), (0.4, "U")], 0.25)
    ripples = pixel.blank(T, T)
    for y, x, art in [(2, 2, "CCC"), (3, 5, "CC"), (7, 9, "CCCC"), (8, 13, "C"),
                      (12, 4, "CCC"), (13, 0, "CC"), (5, 12, "I")]:
        ripples = stamp(ripples, [art], y, x)
    glint = pixel.blank(T, T)
    frames = []
    for n in range(4):
        layer = roll(ripples, 4 * n, 0)
        g = stamp(glint, ["I"], (3 + 5 * n) % T, (10 + 3 * n) % T)
        frames.append(tile_of(sh.lay(sh.lay(deep, layer), g), f"floor_water_a {n}"))
    return frames


FLOOR_WATER_A = _water_frames()


def _lava_frames() -> list[list[str]]:
    """Lava: dark crust plates floating right on glowing rock, hot seams rising; both
    move 4 pixels a frame, so the 4-frame loop comes back to its start."""
    melt = bands(noise(51, cells=4), [(0.0, "R"), (0.45, "O"), (0.78, "Y")], 0.2)
    crust = pixel.blank(T, T)
    for w, h, top, left in [(6, 4, 1, 1), (5, 3, 9, 8), (4, 3, 5, 12), (3, 2, 13, 2)]:
        plate = sh.bevel(pixel.ellipse(w, h, "r"), "R", "K", "r")
        crust = stamp(crust, plate, top, left)
    frames = []
    for n in range(4):
        m = roll(melt, 0, -4 * n)
        frames.append(tile_of(sh.lay(m, roll(crust, 4 * n, 0)), f"floor_lava_a {n}"))
    return frames


FLOOR_LAVA_A = _lava_frames()

FLOORS: dict[str, list[list[str]]] = {
    "tile_floor_stone_a": [FLOOR_STONE_A],
    "tile_floor_stone_b": [FLOOR_STONE_B],
    "tile_floor_stone_c": [FLOOR_STONE_C],
    "tile_floor_cobble_a": [FLOOR_COBBLE_A],
    "tile_floor_cobble_b": [FLOOR_COBBLE_B],
    "tile_floor_dirt_a": [FLOOR_DIRT_A],
    "tile_floor_dirt_b": [FLOOR_DIRT_B],
    "tile_floor_dirt_c": [FLOOR_DIRT_C],
    "tile_floor_moss_a": [FLOOR_MOSS_A],
    "tile_floor_moss_b": [FLOOR_MOSS_B],
    "tile_floor_wood_a": [FLOOR_WOOD_A],
    "tile_floor_wood_b": [FLOOR_WOOD_B],
    "tile_floor_ice_a": [FLOOR_ICE_A],
    "tile_floor_water_a": FLOOR_WATER_A,
    "tile_floor_lava_a": FLOOR_LAVA_A,
}
FLOOR_FPS = {"tile_floor_water_a": 4, "tile_floor_lava_a": 4}


# =================================================================================
# Walls: a face (front, lit from the top left) and a cap (the dark top) per material
# =================================================================================


def _masonry(courses: list[tuple[int, int, list[tuple[int, int]]]], light: str, body: str,
             dark: str, mortar: str, glint: str, lit: int = 0) -> list[str]:
    """Blocks laid in courses [(top, height, [(left, width), ...])] on mortar, each
    bevelled light on its top and left, dark on its bottom and right, with a glint on
    its lit corner. With lit, only the first lit pixels of the top edge catch the light
    (a softer, rougher material). Blocks wrap round the tile edges, so the face
    repeats."""
    base = [mortar * T] * T
    for top, height, blocks in courses:
        for left, width in blocks:
            block = sh.bevel([body * width] * height, light, dark)
            if lit:
                block = [block[0][:lit] + block[0][lit:].replace(light, body)] + [
                    row[0] + row[1:] for row in block[1:]]
                block = [block[0]] + [(body if r < height - 1 else row[0]) + row[1:]
                                      for r, row in enumerate(block[1:], 1)]
            block = pixel.paint(block, [(0, 0)], glint)
            base = stamp(base, block, top, left)
    return base


def _recolour(art: list[str], ramp: dict[str, str]) -> list[str]:
    """Material-neutral overlay art (0 void, 1 light, 2 body, 3 dark) in a material's
    letters."""
    return pixel.recolour(art, ramp)


# Ashlar: irregular blocks, two courses a tile
STONE_RAMP = {"0": "K", "1": "L", "2": "G", "3": "D", "4": "W"}
WALL_STONE_INTACT = tile_of(pixel.paint(_masonry(
    [(0, 7, [(0, 5), (6, 9)]), (8, 7, [(2, 8), (11, 6)])], "L", "G", "D", "K", "W"),
    [(3, 9), (4, 2), (11, 5), (12, 13), (2, 12), (10, 0)], "D"), "wall_stone_intact")

# Brick: four courses of 3-pixel bricks in a half bond
BRICK_RAMP = {"0": "K", "1": "R", "2": "r", "3": "b", "4": "F"}
WALL_BRICK_INTACT = tile_of(pixel.paint(_masonry(
    [(0, 3, [(0, 7), (8, 7)]), (4, 3, [(4, 7), (12, 7)]),
     (8, 3, [(0, 7), (8, 7)]), (12, 3, [(4, 7), (12, 7)])], "R", "r", "b", "D", "R", lit=4),
    [(1, 3), (5, 9), (9, 12), (13, 6), (13, 14)], "b"), "wall_brick_intact")


def _facets(seed: int, count: int, shades: list[tuple[str, str]], crevice: str) -> list[str]:
    """Rough rock: the tile split into angular facets round count seed points (with
    wrap-around), each facet a (body, rim) pair from shades, a lit rim on its top and
    left, and a crevice along its bottom and right."""
    import random

    rng = random.Random(seed)
    pts = [(rng.uniform(0, T), rng.uniform(0, T)) for _ in range(count)]
    look = [shades[rng.randrange(len(shades))] for _ in pts]

    def owner(y: int, x: int) -> int:
        def d(p: tuple[float, float]) -> float:
            dx = min(abs(x + 0.5 - p[0]), T - abs(x + 0.5 - p[0]))
            dy = min(abs(y + 0.5 - p[1]), T - abs(y + 0.5 - p[1])) * 1.4
            return dx * dx + dy * dy
        return min(range(len(pts)), key=lambda i: d(pts[i]))

    own = [[owner(y, x) for x in range(T)] for y in range(T)]
    rows = []
    for y in range(T):
        row = []
        for x in range(T):
            o = own[y][x]
            body, rim = look[o]
            if own[(y + 1) % T][x] != o or own[y][(x + 1) % T] != o:
                row.append(crevice)
            elif own[(y - 1) % T][x] != o or own[y][(x - 1) % T] != o:
                row.append(rim)
            else:
                row.append(body)
        rows.append("".join(row))
    return rows


def _cave_face() -> list[str]:
    """Rough cave rock: angular facets, some catching the light, crevices between."""
    return _facets(61, 9, [("G", "L"), ("D", "G"), ("G", "L"), ("D", "D")], "K")


CAVE_RAMP = {"0": "K", "1": "G", "2": "D", "3": "K", "4": "L"}
WALL_CAVE_INTACT = tile_of(_cave_face(), "wall_cave_intact")

# Moss grows on the tops of the blocks and hangs in strands down the joints
MOSS_WALL = [
    "...........EEV..",
    "EV........VVvV.E",
    "Vv.........v...V",
    "v..........v....",
    "...........v....",
    "................",
    "................",
    "....V...........",
    "..EVVE......EVVE",
    "..VvvV......VvVv",
    "...v.v.......v..",
    "...v.........v..",
    ".............V..",
    "................",
    "................",
    "........V.......",
]
MOSS_RAMP = STONE_RAMP
WALL_MOSS_INTACT = tile_of(sh.lay(pixel.paint(_masonry(
    [(0, 7, [(0, 5), (6, 9)]), (8, 7, [(2, 8), (11, 6)])], "L", "G", "D", "K", "L"),
    [(3, 9), (11, 5), (12, 13), (5, 2)], "v"), MOSS_WALL), "wall_moss_intact")

# Cracks (shared by every material): 0 is the gap, 1 its lit lower lip
CRACKS = [
    "................",
    "......0.........",
    "......01........",
    ".......0........",
    ".......01.......",
    "........0.......",
    "........00......",
    ".........0......",
    ".........0......",
    "........01......",
    "........0.....0.",
    ".......01....01.",
    "......00....0...",
    ".....0......01..",
    ".............0..",
    "................",
]

# Ruin: a hole broken through to the dark, its rim in shadow, and a heap of fallen
# blocks at the foot of the wall (so a ruined face belongs on the bottom row)
RUIN_HOLE = [
    "................",
    "................",
    "..........3.....",
    ".........303....",
    "....3...30003...",
    "...30333000003..",
    "..3000000000003.",
    "..300000000003..",
    "...30000000003..",
    "...300000000003.",
    "..3000000000003.",
    "..300000000003..",
    "...3000000003...",
    "................",
    "................",
    "................",
]
RUBBLE = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "..........41....",
    "..41.....12223..",
    ".1223...122223..",
    "1222330.1222233.",
    "2223333012233333",
]


def _variants(intact: list[str], ramp: dict[str, str], name: str) -> tuple[list[str], list[str]]:
    cracked = tile_of(sh.lay(intact, _recolour(CRACKS, ramp)), f"wall_{name}_cracked")
    ruined = sh.lay(sh.lay(cracked, _recolour(RUIN_HOLE, ramp)), _recolour(RUBBLE, ramp))
    ruined = tile_of(ruined, f"wall_{name}_ruined")
    return cracked, ruined


WALL_STONE_CRACKED, WALL_STONE_RUINED = _variants(WALL_STONE_INTACT, STONE_RAMP, "stone")
WALL_BRICK_CRACKED, WALL_BRICK_RUINED = _variants(WALL_BRICK_INTACT, BRICK_RAMP, "brick")
WALL_CAVE_CRACKED, WALL_CAVE_RUINED = _variants(WALL_CAVE_INTACT, CAVE_RAMP, "cave")
WALL_MOSS_CRACKED, WALL_MOSS_RUINED = _variants(WALL_MOSS_INTACT, MOSS_RAMP, "moss")

# Caps: the top of the wall mass, seen from above, darker than any floor
WALL_STONE_CAP = tile_of(pixel.recolour(FLOOR_STONE_A, {"L": "G", "G": "D", "D": "K"}), "wall_stone_cap")
WALL_BRICK_CAP = tile_of(pixel.recolour(WALL_BRICK_INTACT, {"F": "R", "R": "r", "r": "b", "b": "K", "D": "K"}),
                         "wall_brick_cap")
WALL_CAVE_CAP = tile_of(_facets(62, 9, [("D", "D"), ("K", "D"), ("D", "G")], "K"), "wall_cave_cap")
WALL_MOSS_CAP = tile_of(sh.lay(WALL_STONE_CAP, pixel.recolour(MOSS_B, {"E": "V", "V": "v"})), "wall_moss_cap")

WALLS: dict[str, dict[str, list[str]]] = {
    "stone": {"cap": WALL_STONE_CAP, "intact": WALL_STONE_INTACT, "cracked": WALL_STONE_CRACKED,
              "ruined": WALL_STONE_RUINED},
    "brick": {"cap": WALL_BRICK_CAP, "intact": WALL_BRICK_INTACT, "cracked": WALL_BRICK_CRACKED,
              "ruined": WALL_BRICK_RUINED},
    "cave": {"cap": WALL_CAVE_CAP, "intact": WALL_CAVE_INTACT, "cracked": WALL_CAVE_CRACKED,
             "ruined": WALL_CAVE_RUINED},
    "moss": {"cap": WALL_MOSS_CAP, "intact": WALL_MOSS_INTACT, "cracked": WALL_MOSS_CRACKED,
             "ruined": WALL_MOSS_RUINED},
}

# =================================================================================
# Doors: 16 x 32, two faces tall, cut into a top tile (drawn over the cell above the
# door, like an upper wall face) and a bottom tile (the door's own cell). A stone arch
# frames a leaf 10 wide; the frame's jambs meet any wall material.
# =================================================================================

DOOR_FRAME = [
    "WLLLLLLLLLLLLLLD",
    "LGGGGGGGGGGGGGGD",
    "LGGGGKKKKKKGGGGD",
    "LGGGK......KGGGD",
    "LGGK........KGGD",
] + ["LGK..........KGD"] * 26 + ["DGK..........KGD"]

# Leaves, 10 x 29, set into the frame at row 3, column 3
WOOD_LEAF = [
    "..bbbbbb..",
    ".BBbTBBbT.",
    "TBBbTBBbTB",
    "TBBbTBBbTB",
    "TBBbTBBbTB",
    "DLDDDLDDDL",
    "TBBbTBBbTB",
    "TBBbTBBbTB",
    "TBbbTBBbTB",
    "TBBbTBBbTB",
    "TBBbTBbbTB",
    "TBBbTBBbTB",
    "TBBbTBBbTB",
    "TBBbTBBbYO",
    "TBBbTBBbOB",
    "TBBbTBBbTB",
    "TBBbTBBbTB",
    "TBbbTBBbTB",
    "TBBbTBBbTB",
    "TBBbTBBbTB",
    "DLDDDLDDDL",
    "TBBbTBBbTB",
    "TBBbTBbbTB",
    "TBBbTBBbTB",
    "TBBbTBBbTB",
    "TBBbTBBbTb",
    "TBBbTBBbTb",
    "TBBbTBBbTb",
    "bbbbbbbbbb",
]

METAL_LEAF = [
    "..DDDDDD..",
    ".DLGGGGGD.",
    "LGGGGGGGGD",
    "LWGGGGGGWD",
    "LGGGGGGGGD",
    "LGDDDDDDGD",
    "LGKGKGKDGD",
    "LGKGKGKDGD",
    "LGKGKGKDGD",
    "LGLLLLLLGD",
    "LGGGGGGGGD",
    "WLLLLLLLLD",
    "DDDDDDDDDD",
    "LGGGGGGGGD",
    "LWGGGGGGWD",
    "LGGGGGGLLD",
    "LGGGGGGDLD",
    "LGGGGGGGGD",
    "LGGGGGGGGD",
    "LWGGGGGGWD",
    "WLLLLLLLLD",
    "DDDDDDDDDD",
    "LGGGGGGGGD",
    "LGGGDGGGGD",
    "LGGGGGGGGD",
    "LWGGGGGGWD",
    "LGGGGGGGGD",
    "LGGGGGGGGD",
    "DDDDDDDDDD",
]

# Open: the dark doorway, the leaf swung inward against the left jamb (seen edge-on),
# and a glimpse of floor beyond at the foot
def _open_leaf(edge: str, band: str) -> list[str]:
    rows = ["..KKKKKK..", ".KKKKKKKK."]
    for r in range(2, 26):
        rows.append((band if r in (5, 20) else edge) + "KKKKKKKK")
    return rows + [edge + "KKDDDDKK", edge + "DDDGDDDD", "bDDGDDDGDD"]


def _door(leaf: list[str], frame: list[str] = DOOR_FRAME) -> list[str]:
    door = sh.over(frame, leaf, 3, 3)
    assert pixel.size(door) == (T, 2 * T)
    return pixel.check(door)


def _halves(door: list[str], name: str) -> tuple[list[str], list[str]]:
    return tile_of(door[:T], f"{name}_top"), tile_of(door[T:], f"{name}_bottom")


DOOR_WOOD_CLOSED = _door(WOOD_LEAF)
DOOR_WOOD_OPEN = _door(_open_leaf("Tb", "LD"))
DOOR_METAL_CLOSED = _door(METAL_LEAF)
DOOR_METAL_OPEN = _door(_open_leaf("LD", "WD"))

# The magical door: a frame of dark stone carved with glowing runes, the arch closed
# by a field of arcane light whose bright bands drift down and right (period 8, two
# pixels a frame, so 4 frames loop).
MAGIC_FRAME = pixel.paint(pixel.recolour(DOOR_FRAME, {"W": "M", "L": "P", "G": "p", "D": "p"}),
                          [(1, 3), (1, 7), (1, 8), (1, 12), (8, 1), (14, 1), (20, 1), (26, 1),
                           (8, 14), (14, 14), (20, 14), (26, 14)], "M")
MAGIC_FRAME_DIM = pixel.recolour(MAGIC_FRAME, {"M": "P"})


def _magic_field(n: int) -> list[str]:
    rows = []
    for y, line in enumerate(WOOD_LEAF):
        row = []
        for x, ch in enumerate(line):
            if ch == ".":
                row.append(".")
                continue
            k = (x + y + 2 * n) % 8
            if k == 0:
                row.append("M")
            elif k == 1 and (x + 2 * y) % 5 == 0:
                row.append("I")
            elif k == 4 or x == 9 or y < 2:
                row.append("p")
            else:
                row.append("P")
        rows.append("".join(row))
    return rows


DOOR_MAGIC_CLOSED = [_door(_magic_field(n), MAGIC_FRAME) for n in range(4)]
_MAGIC_OPEN_LEAF = _open_leaf("KK", "KK")
DOOR_MAGIC_OPEN = _door(pixel.paint(_MAGIC_OPEN_LEAF, [(6, 2), (13, 8), (21, 3)], "&"), MAGIC_FRAME_DIM)

DOORS: dict[str, list[str]] = {
    "wood_closed": DOOR_WOOD_CLOSED,
    "wood_open": DOOR_WOOD_OPEN,
    "metal_closed": DOOR_METAL_CLOSED,
    "metal_open": DOOR_METAL_OPEN,
    "magic_open": DOOR_MAGIC_OPEN,
}


# =================================================================================
# Stairs (floor tiles in a stone rim), the secret passage, shadows
# =================================================================================

# Down: a well in the floor; the treads step down away from the viewer, each narrower
# and darker than the last, into the dark
STAIRS_DOWN = tile_of([
    "LLLLLLLLLLLLLLLD",
    "LDDDDDDDDDDDDDDD",
    "LDKKKKKKKKKKKKDD",
    "LDKKKKDDDDKKKKDD",
    "LDKKKKKKKKKKKKDD",
    "LDKKKDDDGDDKKKDD",
    "LDKKKKKKKKKKKKDD",
    "LDKKGGGDGGGGKKDD",
    "LDKKDDDDDDDDKKDD",
    "LDKGGLGGGGGGGKDD",
    "LDKDGGGGGGGGDKDD",
    "LDKDDDDDDDDDDKDD",
    "LDLLLWLLLLLLLLDD",
    "LDGGGGGGGGGGGGDD",
    "LDDDDDDDDDDDDDDD",
    "DDDDDDDDDDDDDDDD",
], "stairs_down")

# Up: a flight rising away from the viewer; lit treads over shaded risers, the risers
# shorter as they climb, to a bright landing; its right side in shadow
STAIRS_UP = tile_of([
    "DWWWWWWWWWWWWWLK",
    "DLLLLLLLLLLLLLGK",
    "DGGGGGGGGGGGGGDK",
    "DWLLLLLLLLLLLLGK",
    "DGGGGGGGGGGGGGDK",
    "DDDDDDDDDDDDDDDK",
    "DWLLLLLLLLLLLLGK",
    "DGGGGGGGGGGGGGDK",
    "DGGGGGDGGGGGGGDK",
    "DDDDDDDDDDDDDDDK",
    "DWLLLLLLLLLLLLGK",
    "DGGGGGGGGGGGGGDK",
    "DGGGGGGGGGGDGGDK",
    "DGGGGGGGGGGGGGDK",
    "DDDDDDDDDDDDDDDK",
    "KKKKKKKKKKKKKKKK",
], "stairs_up")


# Secret passage: a stone face where a door-shaped seam cuts across the blocks, a
# little off the mortar lines, and the lower stone is worn smooth where hands push.
SECRET_SEAM = [
    "................",
    "................",
    "................",
    "...DDDDDDDDD....",
    "...D.......D....",
    "...D.......D....",
    "...D.......D....",
    "...D.......D....",
    "...D.......D....",
    "...D...L...D....",
    "...D..LL...D....",
    "...D.......D....",
    "...D.......D....",
    "...D.......D....",
    "...D.......D....",
    "................",
]
SECRET_CLOSED = tile_of(sh.lay(WALL_STONE_INTACT, SECRET_SEAM), "secret_stone_closed")
SECRET_OPEN = tile_of(sh.lay(WALL_STONE_INTACT, [
    "................",
    "................",
    "................",
    "...DDDDDDDDDD...",
    "...DKKKKKKKKD...",
    "...DKKKKKKKKD...",
    "...DKKKKKKKKD...",
    "...DKKKKKKKKD...",
    "...DKKKKKKKKD...",
    "...DKKKKKKKKD...",
    "...DKKKKKKKKD...",
    "...DKKKKKKKKD...",
    "...DKKKDDKKKD...",
    "...DKKDDDDKKD...",
    "...DKDD:DD:DD...",
    "....:.:..:..:...",
]), "secret_stone_open")


def _shadow(rows: int) -> list[str]:
    """Translucent shadow over the floor's top rows, cast by a wall face above: solid,
    then a dithered fade."""
    out = []
    for y in range(T):
        if y < rows - 2:
            out.append("_" * T)
        elif y < rows:
            keep = 8 if y == rows - 2 else 4
            out.append("".join("_" if pixel.BAYER[y % 4][x % 4] < keep else "." for x in range(T)))
        else:
            out.append("." * T)
    return out


SHADOW_N = tile_of(_shadow(5), "shadow_n")
SHADOW_W = tile_of(pixel.rotate(pixel.flip(_shadow(5)), 1), "shadow_w")
SHADOW_NW = tile_of(["".join("_" if "_" in (a, b) else "." for a, b in zip(r1, r2))
                     for r1, r2 in zip(SHADOW_N, SHADOW_W)], "shadow_nw")


def _wall_preview() -> list[str]:
    """Per material: cap, intact, cracked, ruined, then a strip of wall: caps over a
    face row (intact, cracked, ruined, intact) over floor, to check the joins."""
    parts = []
    for name, w in WALLS.items():
        caps = pixel.strip([w["cap"]] * 4)
        faces = pixel.strip([w["intact"], w["cracked"], w["ruined"], w["intact"]])
        tall = pixel.strip([w["intact"]] * 4)
        floor = pixel.strip([FLOOR_STONE_A, FLOOR_STONE_B, FLOOR_STONE_C, FLOOR_STONE_A])
        shadow = pixel.strip([SHADOW_N] * 4)
        floor = sh.lay(floor, shadow)
        parts.append(pixel.stack([caps, caps, tall, faces, floor]))
    return pixel.strip(parts, 8)


def _special_preview() -> list[str]:
    """Each door standing in a stretch of stone wall over floor, then stairs and the
    secret passage."""
    face, cap = WALL_STONE_INTACT, WALL_STONE_CAP
    walls = []
    for door in [DOOR_WOOD_CLOSED, DOOR_WOOD_OPEN, DOOR_METAL_CLOSED, DOOR_METAL_OPEN,
                 DOOR_MAGIC_CLOSED[0], DOOR_MAGIC_CLOSED[2], DOOR_MAGIC_OPEN]:
        column = pixel.stack([cap, door, FLOOR_STONE_A])
        side = pixel.stack([cap, face, face, FLOOR_STONE_B])
        walls.append(pixel.strip([side, column, side]))
    extras = [pixel.stack([WALL_STONE_CAP, WALL_STONE_INTACT, x, FLOOR_STONE_A]) for x in (SECRET_CLOSED, SECRET_OPEN)]
    extras += [pixel.stack([FLOOR_STONE_A, x, FLOOR_STONE_C]) for x in (STAIRS_DOWN, STAIRS_UP)]
    return pixel.stack([pixel.strip(walls, 4), pixel.strip(extras, 4)], 4)


def atlas_tiles() -> list[list[Tile]]:
    """Every atlas tile, one list per atlas row. Trap tiles come from env_traps."""
    from environment import env_traps

    floors = [Tile(n, f, False, FLOOR_FPS.get(n, 0), "floor") for n, f in FLOORS.items()]
    doors = []
    for name, art in DOORS.items():
        top, bottom = _halves(art, f"tile_door_{name}")
        doors.append(Tile(f"tile_door_{name}_top", [top], False, 0, "door"))
        doors.append(Tile(f"tile_door_{name}_bottom", [bottom], name.endswith("closed"), 0, "door"))
    walls = []
    for material, parts in WALLS.items():
        for part, art in parts.items():
            walls.append(Tile(f"tile_wall_{material}_{part}", [art], True, 0,
                              "wall_cap" if part == "cap" else "wall_face"))
    return [
        [t for t in floors if len(t.frames) == 1],
        [t for t in floors if len(t.frames) > 1]
        + [Tile("tile_door_magic_closed_top", [d[:T] for d in DOOR_MAGIC_CLOSED], False, 5, "door"),
           Tile("tile_door_magic_closed_bottom", [d[T:] for d in DOOR_MAGIC_CLOSED], True, 5, "door")],
        walls,
        doors,
        [
            Tile("tile_stairs_down", [STAIRS_DOWN], False, 0, "stairs"),
            Tile("tile_stairs_up", [STAIRS_UP], False, 0, "stairs"),
            Tile("tile_secret_stone_closed", [SECRET_CLOSED], True, 0, "secret"),
            Tile("tile_secret_stone_open", [SECRET_OPEN], False, 0, "secret"),
            Tile("tile_shadow_n", [SHADOW_N], False, 0, "overlay"),
            Tile("tile_shadow_w", [SHADOW_W], False, 0, "overlay"),
            Tile("tile_shadow_nw", [SHADOW_NW], False, 0, "overlay"),
        ],
        [Tile(n, [f], solid, 0, "trap") for n, f, solid in env_traps.TRAP_TILES],
    ]


def build() -> None:
    sh.OUT.mkdir(parents=True, exist_ok=True)
    atlas = sh.Atlas(16)
    strips = {}
    for row in atlas_tiles():
        for tile in row:
            atlas.add(tile)
            if tile.group == "trap":
                continue  # env_traps writes trap_*.png into sprites/environment
            if len(tile.frames) > 1:
                strips[tile.name] = pixel.write_strip(sh.TILESETS / tile.name, tile.frames, tile.fps, True,
                                                      preview_dir=sh.OUT / "strips")
            else:
                pixel.write_png(sh.TILESETS / f"{tile.name}.png", tile.frames[0])
        atlas.newline()
    doc = atlas.write(sh.TILESETS / "tileset_dungeon")
    sh.merge_env_json("tiles", {
        "atlas": doc["texture"], "tileset": doc["tileset"], "json": sh.res(sh.TILESETS / "tileset_dungeon.json"),
        "animated_strips": strips,
    })
    pixel.write_contact_sheet(sh.OUT / "tileset_dungeon@4x.png", atlas.image(), T, T, 4)
    print(f"atlas: {len(doc['tiles'])} tiles, {len(doc['animated'])} animated, {len(doc['solid'])} solid")
    seams = [sh.repeat(frames[0], 3, 3) for frames in FLOORS.values()]
    print(sh.preview("floors_3x3", sh.sheet(seams, 5, 4), 4))
    print(sh.preview("walls", _wall_preview(), 4))
    print(sh.preview("specials", _special_preview(), 6))
