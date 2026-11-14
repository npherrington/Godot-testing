"""The pixel engine: every image in assets/ is drawn as letter matrices and written here.

Adapted from the Latitude buddy engine (app/scripts/buddy-sprites/buddy.py): a sprite is
a list of strings, one character per pixel, each character a key of PALETTE. "." is
empty. Every row of a sprite has the same width; check() asserts it.

    python3 art/build.py [module ...] [--gifs]      (see build.py)

Pieces:
- PALETTE: the game's 24 colours, one letter each, plus translucent letters that reuse
  those colours at partial alpha (shadow, smoke, mist, glow). Nothing else can be drawn,
  so every PNG keeps to the spec's 24-colour limit.
- Grid helpers (paste, frame, cell, flip, shift, ...) and transforms for animating a
  drawn pose (squash, shear, dissolve, silhouette, recolour, outline).
- Character and Anim: a character's animations per direction. write_character() writes
  one sprite sheet PNG per state, a Godot SpriteFrames .tres beside each, the animation
  JSON, and previews.
- write_strip(): a one-row animation (torch, fire, a projectile) with its SpriteFrames.
- write_png / write_gif: pure-Python writers, no PIL.

Layers: frame(w, h, layers) draws each (sprite, x, y) with its bottom-left corner at
column x and y = the row just below its last row, as in buddy.compose. A character
cell's feet stand on row h - FOOT - 1; cell(sprite, w, h) puts a pose there, centred.
"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path
from typing import Callable, NamedTuple, Optional

ART = Path(__file__).resolve().parent
ROOT = ART.parent  # the Godot project
ASSETS = ROOT / "assets"
OUT = ART / "out"  # previews; gitignored
GIFS = False  # build.py --gifs sets this; GIFs are slow, contact sheets are not

Sprite = list[str]
Rgb = tuple[int, int, int]
Rgba = tuple[int, int, int, int]

# ---------------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------------

# The 24 colours. A lowercase letter is the shade of its capital where there is one.
# Ramps (dark to light): stone K D G L W, wood b B T S, red r R F, fire r R O Y W,
# green v V E, blue u U C I, purple p P M. Light falls from the top left.
COLOURS: dict[str, Rgb] = {
    "K": (20, 16, 24),  # outline, void, deepest shadow
    "D": (58, 54, 70),  # dark stone, iron shade, mortar
    "G": (104, 102, 118),  # stone, iron
    "L": (166, 164, 176),  # light stone, steel, bone shade
    "W": (236, 232, 216),  # bone, highlight, white
    "b": (62, 38, 32),  # dark brown: wood grain, leather and dirt shade
    "B": (116, 72, 46),  # brown: wood, leather, dirt
    "T": (178, 124, 76),  # tan: light wood, fur, rope, skin shade
    "S": (232, 188, 146),  # skin, sand, parchment
    "r": (104, 22, 36),  # dark red: blood, red shade
    "R": (190, 44, 50),  # red: health, cloth, imp skin
    "F": (226, 120, 118),  # flesh pink: tongues, gums, wounds
    "O": (232, 124, 38),  # orange: fire, torchlight, rust
    "Y": (250, 210, 76),  # yellow: gold, flame core, glowing eyes
    "v": (30, 66, 52),  # dark green: moss and goblin shade
    "V": (60, 126, 66),  # green: goblin skin, moss
    "E": (148, 198, 76),  # lime: slime, poison, venom
    "u": (28, 36, 84),  # navy: blue shade, deep water, night
    "U": (54, 92, 170),  # blue: water, cloth, magic
    "C": (94, 170, 220),  # sky blue: ice, magic light
    "I": (192, 234, 242),  # ice white: frost, ghost light
    "p": (56, 30, 76),  # dark purple: robe shade, shadow magic
    "P": (118, 64, 150),  # purple: robes, magic
    "M": (200, 124, 204),  # lilac: magic glow, ghostly glow
}
assert len(COLOURS) == 24, "the spec allows 24 colours"

# Translucent letters: a palette colour at partial alpha, for shadow, smoke and glow
TRANSLUCENT: dict[str, tuple[str, int]] = {
    "_": ("K", 96),  # drop shadow under characters and props
    "~": ("G", 150),  # smoke
    ":": ("L", 90),  # mist, fog, dust
    ";": ("I", 140),  # ghost veil, frost haze
    "*": ("Y", 140),  # glow: torchlight halo, sparks, gold shine
    "^": ("O", 150),  # fire haze, heat
    "=": ("C", 130),  # ice or arcane haze
    "%": ("E", 130),  # poison haze, venom mist
    "&": ("M", 130),  # magic haze, curse
    "!": ("R", 140),  # blood mist, life drain
}

PALETTE: dict[str, Optional[Rgba]] = {".": None}
PALETTE.update({k: (*v, 255) for k, v in COLOURS.items()})
PALETTE.update({k: (*COLOURS[base], a) for k, (base, a) in TRANSLUCENT.items()})

PREVIEW_BG: Rgb = (44, 40, 52)  # previews sit on dungeon-dark, as the game will


def luminance(letter: str) -> float:
    r, g, b = COLOURS[letter]
    return 0.299 * r + 0.587 * g + 0.114 * b


# ---------------------------------------------------------------------------------
# Sprites
# ---------------------------------------------------------------------------------


def check(sprite: Sprite, name: str = "sprite") -> Sprite:
    assert sprite, f"{name} is empty"
    widths = {len(row) for row in sprite}
    assert len(widths) == 1, f"{name}: rows differ in width: {sorted(widths)}"
    unknown = {ch for row in sprite for ch in row} - PALETTE.keys()
    assert not unknown, f"{name}: characters not in the palette: {unknown}"
    return sprite


def size(sprite: Sprite) -> tuple[int, int]:
    """(width, height)."""
    return len(sprite[0]), len(sprite)


def blank(w: int, h: int) -> Sprite:
    return ["." * w] * h


def paste(base: Sprite, sprite: Sprite, top: int, left: int) -> Sprite:
    """sprite drawn over base with its top-left corner at (top, left); "." in sprite
    leaves base showing, and whatever falls outside base is cut off."""
    grid = [list(row) for row in base]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(sprite):
        y = top + r
        if not 0 <= y < h:
            continue
        for c, pixel in enumerate(row):
            x = left + c
            if pixel != "." and 0 <= x < w:
                grid[y][x] = pixel
    return ["".join(row) for row in grid]


def underlay(base: Sprite, sprite: Sprite, top: int, left: int) -> Sprite:
    """sprite drawn behind base: it shows only where base is "."."""
    grid = [list(row) for row in base]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(sprite):
        y = top + r
        if not 0 <= y < h:
            continue
        for c, pixel in enumerate(row):
            x = left + c
            if pixel != "." and 0 <= x < w and grid[y][x] == ".":
                grid[y][x] = pixel
    return ["".join(row) for row in grid]


def paint(sprite: Sprite, pixels: list[tuple[int, int]], pixel: str) -> Sprite:
    """sprite with each (row, column) in pixels set to pixel."""
    grid = [list(row) for row in sprite]
    for row, column in pixels:
        grid[row][column] = pixel
    return ["".join(row) for row in grid]


def frame(w: int, h: int, layers: list[tuple[Sprite, int, int]]) -> Sprite:
    """A w x h frame with each (sprite, x, y) drawn in turn: bottom-left corner at
    column x, its last row at row y - 1. Off-frame pixels are cut off."""
    out = blank(w, h)
    for sprite, x, y in layers:
        out = paste(out, sprite, y - len(sprite), x)
    return out


FOOT = 2  # rows under the feet, for the drop shadow


def baseline(h: int) -> int:
    """The y a standing pose's layer uses in a cell h tall: feet on row h - FOOT - 1."""
    return h - FOOT


def cell(sprite: Sprite, w: int, h: int, dx: int = 0, dy: int = 0) -> Sprite:
    """sprite on a w x h cell, centred, standing on the baseline, then moved dx right
    and dy down."""
    sw, _ = size(sprite)
    return frame(w, h, [(sprite, (w - sw) // 2 + dx, baseline(h) + dy)])


def flip(sprite: Sprite) -> Sprite:
    """Mirrored left to right."""
    return [row[::-1] for row in sprite]


def flip_v(sprite: Sprite) -> Sprite:
    """Mirrored top to bottom."""
    return sprite[::-1]


def rotate(sprite: Sprite, quarter_turns: int = 1) -> Sprite:
    """Turned clockwise by quarter_turns x 90 degrees; lossless."""
    for _ in range(quarter_turns % 4):
        sprite = ["".join(row[c] for row in reversed(sprite)) for c in range(len(sprite[0]))]
    return sprite


def shift(sprite: Sprite, dx: int, dy: int) -> Sprite:
    """The same size, content moved dx right and dy down; what leaves is cut off."""
    w, h = size(sprite)
    return paste(blank(w, h), sprite, dy, dx)


def crop(sprite: Sprite, top: int, left: int, h: int, w: int) -> Sprite:
    return [row[left : left + w] for row in sprite[top : top + h]]


def pad(sprite: Sprite, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0) -> Sprite:
    w, _ = size(sprite)
    nw = w + left + right
    return ["." * nw] * top + ["." * left + row + "." * right for row in sprite] + ["." * nw] * bottom


def strip(sprites: list[Sprite], gap: int = 0) -> Sprite:
    """Sprites side by side, bottom-aligned."""
    height = max(len(s) for s in sprites)
    padded = [["." * len(s[0])] * (height - len(s)) + s for s in sprites]
    return [("." * gap).join(s[r] for s in padded) for r in range(height)]


def stack(sprites: list[Sprite], gap: int = 0) -> Sprite:
    """Sprites top to bottom, left-aligned, padded to the widest."""
    width = max(len(s[0]) for s in sprites)
    out: Sprite = []
    for n, s in enumerate(sprites):
        if n and gap:
            out += ["." * width] * gap
        out += [row + "." * (width - len(row)) for row in s]
    return out


def recolour(sprite: Sprite, mapping: dict[str, str]) -> Sprite:
    """Each letter in mapping swapped for its value."""
    table = str.maketrans(mapping)
    return [row.translate(table) for row in sprite]


def silhouette(sprite: Sprite, letter: str = "W") -> Sprite:
    """Every drawn pixel as letter, translucent ones left alone: the hit flash."""
    return ["".join(letter if ch in COLOURS else ch for ch in row) for row in sprite]


def outline(sprite: Sprite, letter: str = "K", diagonal: bool = False) -> Sprite:
    """letter on every empty pixel that touches a drawn one."""
    w, h = size(sprite)
    grid = [list(row) for row in sprite]
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for y in range(h):
        for x in range(w):
            if sprite[y][x] != ".":
                continue
            for dy, dx in steps:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and sprite[ny][nx] in COLOURS:
                    grid[y][x] = letter
                    break
    return ["".join(row) for row in grid]


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dissolve(sprite: Sprite, amount: float, ox: int = 0, oy: int = 0) -> Sprite:
    """Ordered-dither fade: amount 0 keeps every pixel, 1 removes them all. The pattern
    is fixed to the grid (ox, oy shift it), so consecutive amounts erase cumulatively."""
    cut = round(amount * 16)
    return [
        "".join(
            "." if BAYER[(y + oy) % 4][(x + ox) % 4] < cut else ch for x, ch in enumerate(row)
        )
        for y, row in enumerate(sprite)
    ]


def dither(sprite: Sprite, letter: str, into: str, amount: float = 0.5, ox: int = 0, oy: int = 0) -> Sprite:
    """Pixels of letter turned to into on an ordered-dither pattern: a soft transition
    between two shades without anti-aliasing. ox, oy shift the pattern."""
    cut = round(amount * 16)
    return [
        "".join(
            into if ch == letter and BAYER[(y + oy) % 4][(x + ox) % 4] < cut else ch
            for x, ch in enumerate(row)
        )
        for y, row in enumerate(sprite)
    ]


def squash(sprite: Sprite, n: int, row: int) -> Sprite:
    """n rows removed from row down, the part above dropped to fill: the same height,
    shorter figure, feet still on the ground. Squash a torso row to breathe."""
    w, h = size(sprite)
    n = max(0, min(n, h - row))  # rows past the bottom aren't there to remove
    return ["." * w] * n + sprite[:row] + sprite[row + n :]


def stretch(sprite: Sprite, n: int, row: int) -> Sprite:
    """row repeated n more times and the top n rows cut: a taller figure, same feet."""
    return (sprite[:row] + [sprite[row]] * n + sprite[row:])[n:]


def shear(sprite: Sprite, dx: int, pivot: int) -> Sprite:
    """Rows above pivot slid sideways, the top row by dx and less on the way down: a
    lean (positive dx leans right). Rows from pivot down stay put."""
    out = []
    for r, row in enumerate(sprite):
        offset = round(dx * (pivot - r) / pivot) if r < pivot and pivot else 0
        out.append(shift([row], offset, 0)[0])
    return out


def ellipse(w: int, h: int, letter: str) -> Sprite:
    """A filled ellipse w x h."""
    rows = []
    for y in range(h):
        ny = (y + 0.5) / h * 2 - 1
        rows.append(
            "".join(
                letter if ((x + 0.5) / w * 2 - 1) ** 2 + ny**2 <= 1.0 else "." for x in range(w)
            )
        )
    return rows


def erase(sprite: Sprite, top: int, left: int, h: int, w: int) -> Sprite:
    """sprite with the h x w box at (top, left) emptied."""
    left = max(left, 0)
    return [
        row[:left] + "." * len(row[left : left + w]) + row[left + w :] if top <= r < top + h else row
        for r, row in enumerate(sprite)
    ]


def arc(
    w: int, h: int, cx: float, cy: float, r: float, a0: float, a1: float, letter: str,
    thickness: float = 1.5, edge: str = "",
) -> Sprite:
    """A w x h sprite holding the arc of radius r round (cx, cy) from angle a0 to a1,
    in degrees counter-clockwise from pointing right (90 is up the screen). edge, if
    given, is drawn on the arc's outermost pixels: a slash smear with a bright rim, a
    shockwave, a halo."""
    import math

    rows = []
    for y in range(h):
        line = []
        for x in range(w):
            dx, dy = x + 0.5 - cx, cy - (y + 0.5)
            d = math.hypot(dx, dy)
            angle = math.degrees(math.atan2(dy, dx)) % 360
            lo, hi = a0 % 360, a1 % 360
            inside = lo <= angle <= hi if lo <= hi else angle >= lo or angle <= hi
            if inside and r - thickness <= d <= r:
                line.append(edge if edge and d > r - 1 else letter)
            else:
                line.append(".")
        rows.append("".join(line))
    return rows


def letters(sprite: Sprite) -> set[str]:
    return {ch for row in sprite for ch in row} - {"."}


# ---------------------------------------------------------------------------------
# Colour states: per-frame transforms that keep to the palette
# ---------------------------------------------------------------------------------


def nearest_in(ramp: str) -> dict[str, str]:
    """Every opaque colour mapped to the colour in ramp with the closest luminance."""
    return {
        k: min(ramp, key=lambda r: abs(luminance(r) - luminance(k))) for k in COLOURS
    }


def frost_rim(sprite: Sprite) -> Sprite:
    """Ice white on every drawn pixel with nothing above it: frost on the top edges."""
    out = [list(row) for row in sprite]
    for y, row in enumerate(sprite):
        for x, ch in enumerate(row):
            if ch in COLOURS and ch != "K" and (y == 0 or sprite[y - 1][x] in ".K"):
                out[y][x] = "I"
    return ["".join(row) for row in out]


_FROZEN = nearest_in("KuUCIW")
_INJURED = {"W": "L", "L": "G", "G": "D", "T": "B", "Y": "O", "C": "U", "E": "V", "M": "P", "I": "C", "U": "u"}


def _injured(sprite: Sprite) -> Sprite:
    """Gear dulled a shade; skin speckled with bruises (F) and cuts (r). The speckle
    pattern is pinned to the sprite's top-left, so it rides along when the figure bobs."""
    drawn = [(y, row) for y, row in enumerate(sprite) if row.strip(".")]
    oy = -drawn[0][0] if drawn else 0
    ox = -min((len(row) - len(row.lstrip(".")) for _, row in drawn), default=0)
    bruised = dither(dither(sprite, "S", "F", 0.25, ox, oy), "F", "r", 0.12, ox, oy)
    return recolour(bruised, _INJURED)
_POISONED = {"S": "E", "F": "E", "T": "V", "W": "I", "R": "r", "Y": "E"}

STATES: dict[str, Callable[[Sprite], Sprite]] = {
    "normal": lambda s: s,
    "injured": _injured,  # gear a shade darker, skin bruised and cut
    "frozen": lambda s: frost_rim(recolour(s, _FROZEN)),  # ice blue, frost on top edges
    "poisoned": lambda s: recolour(s, _POISONED),  # skin and leather sickly green
}

# ---------------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------------

DIRECTIONS_4 = ["down", "up", "left", "right"]
DIRECTIONS_8 = ["down", "down_right", "right", "up_right", "up", "up_left", "left", "down_left"]
MIRRORS = {"left": "right", "up_left": "up_right", "down_left": "down_right"}


class Anim(NamedTuple):
    frames: list[Sprite]  # each a full cell, w x h
    fps: int = 8
    loop: bool = True


class Effect(NamedTuple):
    """A projectile or ability effect that travels or sits apart from the character."""

    name: str  # snake_case; written as fx_<character>_<name>.png
    frames: list[Sprite]  # all one size
    fps: int = 10
    loop: bool = True
    notes: str = ""


class Character(NamedTuple):
    name: str  # snake_case: "skeleton_warrior"
    kind: str  # "player" or "enemies": the folder under assets/sprites
    size: tuple[int, int]  # cell (w, h): (32, 48) or (48, 48)
    animations: dict[str, dict[str, Anim]]  # animation -> direction -> Anim
    notes: str = ""  # one line: the look, and what the special does
    shadow: int = 14  # drop-shadow width under the feet; 0 for none
    states: tuple[str, ...] = ("normal",)
    effects: tuple[Effect, ...] = ()


def mirror(views: dict[str, Anim]) -> dict[str, Anim]:
    """views with left, up_left and down_left added as flips of their right-hand
    sides, where those are drawn."""
    out = dict(views)
    for left, right in MIRRORS.items():
        if right in views and left not in views:
            a = views[right]
            out[left] = Anim([flip(f) for f in a.frames], a.fps, a.loop)
    return out


# Frame counts the spec asks for. Anything not named here (each enemy's attack and
# special) may have 2 to 12 frames.
FRAME_RULES = {
    "player": {"idle": (4, 4), "walk": (8, 8), "attack": (6, 6), "defend": (2, 2)},
    "enemies": {"idle": (4, 4), "walk": (8, 8), "death": (4, 6)},
}


def _validate(char: Character) -> list[str]:
    w, h = char.size
    dirs = DIRECTIONS_8 if char.kind == "player" else DIRECTIONS_4
    rules = FRAME_RULES[char.kind]
    for need in rules:
        assert need in char.animations, f"{char.name}: no {need} animation"
    if char.kind == "enemies":
        attacks = [a for a in char.animations if a.startswith("attack")]
        assert 1 <= len(attacks) <= 2, f"{char.name}: needs 1 or 2 attack animations, has {attacks}"
        assert "special" in char.animations, f"{char.name}: no special animation"
    for anim, views in char.animations.items():
        assert set(views) == set(dirs), f"{char.name} {anim}: directions {sorted(views)}, want {dirs}"
        counts = {len(v.frames) for v in views.values()}
        assert len(counts) == 1, f"{char.name} {anim}: directions differ in frame count {counts}"
        lo, hi = rules.get(anim, (2, 12))
        assert lo <= counts.pop() <= hi, f"{char.name} {anim}: wants {lo}-{hi} frames"
        for d, a in views.items():
            for n, f in enumerate(a.frames):
                check(f, f"{char.name} {anim} {d} {n}")
                assert size(f) == (w, h), f"{char.name} {anim} {d} {n}: {size(f)}, want {(w, h)}"
    return dirs


def with_shadow(f: Sprite, width: int) -> Sprite:
    if not width:
        return f
    w, h = size(f)
    shadow = ellipse(width, 4, "_")
    return underlay(f, shadow, h - FOOT - 2, (w - width) // 2)


def write_character(char: Character) -> None:
    """Sheets, SpriteFrames, JSON and previews for char, one sheet per state.

    Sheet layout: one row per (animation, direction), animations in the order given,
    directions in DIRECTIONS order; frames left to right from column 0."""
    dirs = _validate(char)
    w, h = char.size
    rows: list[tuple[str, str, Anim]] = [
        (anim, d, views[d]) for anim, views in char.animations.items() for d in dirs
    ]
    columns = max(len(a.frames) for _, _, a in rows)
    folder = ASSETS / "sprites" / char.kind
    folder.mkdir(parents=True, exist_ok=True)
    meta_anims: dict[str, dict] = {}
    for r, (anim, d, a) in enumerate(rows):
        meta = meta_anims.setdefault(anim, {"fps": a.fps, "loop": a.loop, "directions": {}})
        meta["directions"][d] = {"row": r, "frames": len(a.frames)}

    sheets = {}
    for state in char.states:
        tint = STATES[state]
        sheet_rows = []
        for _, _, a in rows:
            frames = [tint(with_shadow(f, char.shadow)) for f in a.frames]
            frames += [blank(w, h)] * (columns - len(frames))
            sheet_rows.append(strip(frames))
        sheet = stack(sheet_rows)
        base = f"char_{char.name}_{state}"
        write_png(folder / f"{base}.png", sheet)
        _write_sprite_frames(folder / f"{base}.tres", f"res://assets/sprites/{char.kind}/{base}.png",
                             [(f"{anim}_{d}", r, len(a.frames), a.fps, a.loop) for r, (anim, d, a) in enumerate(rows)],
                             w, h)
        sheets[state] = f"res://assets/sprites/{char.kind}/{base}.png"
        preview = OUT / char.name
        preview.mkdir(parents=True, exist_ok=True)
        write_contact_sheet(preview / f"sheet_{state}@3x.png", sheet, w, h, 3)

    effects = {}
    for fx in char.effects:
        effects[fx.name] = write_strip(
            folder / f"fx_{char.name}_{fx.name}", fx.frames, fx.fps, fx.loop, preview_dir=OUT / char.name
        ) | {"notes": fx.notes}

    meta_doc = {
        "name": char.name,
        "frame_size": [w, h],
        # The point under the feet, and the AnimatedSprite2D offset (centered on) that
        # puts it on the node's position
        "origin": [w // 2, baseline(h)],
        "godot_offset": [0, -(baseline(h) - h // 2)],
        "notes": char.notes,
        "sheets": sheets,
        "sprite_frames": {s: p.replace(".png", ".tres") for s, p in sheets.items()},
        "animations": meta_anims,
        "effects": effects,
    }
    if char.kind == "player":
        json_path = ASSETS / "animations" / "player.json"
    else:
        json_path = ASSETS / "animations" / "enemies" / f"{char.name}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(meta_doc, indent=2) + "\n")

    if GIFS:
        gifs = OUT / char.name / "gifs"
        gifs.mkdir(parents=True, exist_ok=True)
        for anim, d, a in rows:
            write_gif(gifs / f"{anim}_{d}@4x.gif", [with_shadow(f, char.shadow) for f in a.frames], a.fps, 4)
    print(f"{char.name}: {len(rows)} rows x {columns} frames, states {', '.join(char.states)}")


def write_strip(
    path_stem: Path, frames: list[Sprite], fps: int, loop: bool, anim: str = "default",
    preview_dir: Optional[Path] = None,
) -> dict:
    """frames side by side in <path_stem>.png, with <path_stem>.tres holding one
    animation named anim. Returns the JSON entry for it."""
    fw, fh = size(frames[0])
    for n, f in enumerate(frames):
        check(f, f"{path_stem.name} {n}")
        assert size(f) == (fw, fh), f"{path_stem.name} {n}: frames differ in size"
    path_stem.parent.mkdir(parents=True, exist_ok=True)
    png = path_stem.with_suffix(".png")
    write_png(png, strip(frames))
    res = "res://assets/" + png.relative_to(ASSETS).as_posix()
    _write_sprite_frames(path_stem.with_suffix(".tres"), res, [(anim, 0, len(frames), fps, loop)], fw, fh)
    if preview_dir is not None:
        preview_dir.mkdir(parents=True, exist_ok=True)
        write_contact_sheet(preview_dir / f"{path_stem.name}@4x.png", strip(frames), fw, fh, 4)
        if GIFS:
            write_gif(preview_dir / f"{path_stem.name}@4x.gif", frames, fps, 4)
    return {"sheet": res, "sprite_frames": res.replace(".png", ".tres"), "frame_size": [fw, fh],
            "frames": len(frames), "fps": fps, "loop": loop}


def _write_sprite_frames(
    path: Path, texture: str, anims: list[tuple[str, int, int, int, bool]], w: int, h: int
) -> None:
    """A Godot 4 SpriteFrames resource: each (name, row, frames, fps, loop) cut from
    the sheet at texture by AtlasTextures."""
    subs = []
    anim_entries = []
    for name, row, count, fps, loop in anims:
        refs = []
        for n in range(count):
            sid = f"{name}_{n}"
            subs.append(
                f'[sub_resource type="AtlasTexture" id="{sid}"]\n'
                f'atlas = ExtResource("sheet")\n'
                f"region = Rect2({n * w}, {row * h}, {w}, {h})\n"
            )
            refs.append('{\n"duration": 1.0,\n"texture": SubResource("' + sid + '")\n}')
        anim_entries.append(
            '{\n"frames": [' + ", ".join(refs) + "],\n"
            f'"loop": {"true" if loop else "false"},\n'
            f'"name": &"{name}",\n'
            f'"speed": {float(fps)}\n' + "}"
        )
    text = (
        f'[gd_resource type="SpriteFrames" load_steps={len(subs) + 2} format=3]\n\n'
        f'[ext_resource type="Texture2D" path="{texture}" id="sheet"]\n\n'
        + "\n".join(subs)
        + "\n[resource]\n"
        + "animations = [" + ", ".join(anim_entries) + "]\n"
    )
    path.write_text(text)


# ---------------------------------------------------------------------------------
# PNG and GIF
# ---------------------------------------------------------------------------------


def _png_bytes(pixels: list[list[Rgba]]) -> bytes:
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in pixels)

    def chunk(kind: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", len(pixels[0]), len(pixels), 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def _blend(px: Optional[Rgba], bg: Rgb) -> Rgb:
    if px is None:
        return bg
    a = px[3] / 255
    return tuple(round(px[i] * a + bg[i] * (1 - a)) for i in range(3))  # type: ignore[return-value]


def write_png(path: Path, rows: Sprite, scale: int = 1, background: Optional[Rgb] = None) -> None:
    """rows as an RGBA PNG; transparent where ".", unless background is given."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pixels = []
    for row in rows:
        line: list[Rgba] = []
        for ch in row:
            px = PALETTE[ch]
            if background is not None:
                px = (*_blend(px, background), 255)
            elif px is None:
                px = (0, 0, 0, 0)
            line += [px] * scale
        pixels += [line] * scale
    path.write_bytes(_png_bytes(pixels))


def write_contact_sheet(path: Path, sheet: Sprite, w: int, h: int, scale: int) -> None:
    """A preview of a sheet on PREVIEW_BG with a faint line between cells."""
    line = (64, 60, 76)
    pixels = []
    for y, row in enumerate(sheet):
        out: list[Rgba] = []
        for x, ch in enumerate(row):
            on_line = x % w == 0 or y % h == 0
            bg = line if on_line and ch == "." else PREVIEW_BG
            out += [(*_blend(PALETTE[ch], bg), 255)] * scale
        pixels += [out] * scale
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_png_bytes(pixels))


def _lzw(pixels: list[int], min_size: int) -> bytes:
    """GIF's LZW: codes start at min_size + 1 bits and grow to 12, then the table
    starts over."""
    clear, end = 1 << min_size, (1 << min_size) + 1
    size_ = min_size + 1
    out, bits, count = bytearray(), 0, 0

    def emit(code: int) -> None:
        nonlocal bits, count
        bits |= code << count
        count += size_
        while count >= 8:
            out.append(bits & 0xFF)
            bits >>= 8
            count -= 8

    table: dict[tuple[int, int], int] = {}
    next_code = end + 1
    emit(clear)
    prefix = pixels[0]
    for pixel in pixels[1:]:
        code = table.get((prefix, pixel))
        if code is not None:
            prefix = code
            continue
        emit(prefix)
        if next_code < 4096:
            table[(prefix, pixel)] = next_code
            next_code += 1
            if next_code > 1 << size_ and size_ < 12:
                size_ += 1
        else:
            emit(clear)
            table.clear()
            next_code, size_ = end + 1, min_size + 1
        prefix = pixel
    emit(prefix)
    emit(end)
    if count:
        out.append(bits & 0xFF)
    return bytes(out)


def write_gif(path: Path, frames: list[Sprite], fps: int, scale: int = 4) -> None:
    """A looping GIF of frames on PREVIEW_BG; translucent letters blended onto it."""
    keys = list(PALETTE)
    colors = [_blend(PALETTE[k], PREVIEW_BG) for k in keys]
    depth = max(3, (len(keys) - 1).bit_length())
    colors += [(0, 0, 0)] * ((1 << depth) - len(colors))
    index = {key: i for i, key in enumerate(keys)}
    width, height = len(frames[0][0]) * scale, len(frames[0]) * scale
    delay = max(2, round(100 / fps))
    gif = bytearray(b"GIF89a")
    gif += struct.pack("<HHBBB", width, height, 0xF0 | (depth - 1), 0, 0)
    gif += bytes(c for color in colors for c in color)
    gif += b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00"
    for rows in frames:
        big = ["".join(ch * scale for ch in row) for row in rows for _ in range(scale)]
        data = _lzw([index[ch] for row in big for ch in row], depth)
        gif += b"\x21\xf9\x04\x00" + struct.pack("<H", delay) + b"\x00\x00"
        gif += b"\x2c" + struct.pack("<HHHHB", 0, 0, width, height, 0)
        gif += bytes([depth])
        gif += b"".join(
            bytes([len(data[i : i + 255])]) + data[i : i + 255] for i in range(0, len(data), 255)
        )
        gif += b"\x00"
    gif += b"\x3b"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gif)


def write_palette() -> None:
    """assets/palette.png (one swatch per colour, 8x8, in COLOURS order), palette.gpl
    for GIMP or Aseprite, and palette.hex."""
    order = list(COLOURS)
    swatches = strip([[k * 8] * 8 for k in order])
    write_png(ASSETS / "palette.png", swatches)
    gpl = ["GIMP Palette", "Name: dungeon-24", "Columns: 8", "#"]
    gpl += [f"{r:3d} {g:3d} {b:3d}\t{k}" for k, (r, g, b) in COLOURS.items()]
    (ASSETS / "palette.gpl").write_text("\n".join(gpl) + "\n")
    (ASSETS / "palette.hex").write_text("".join("%02x%02x%02x\n" % COLOURS[k] for k in order))
