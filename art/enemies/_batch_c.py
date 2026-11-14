"""Shared helpers for batch C: wolfman, imp, medusa, goblin_king, ice_elemental.

A leading underscore keeps build.py from treating this as a module. Everything here is
built on pixel.py; nothing from other monsters' modules is imported.

How these monsters are drawn:
- Sprites are written as fills (no outline) and ol() pads them by a pixel and adds the
  K outline, so every silhouette is closed. Inner lines are drawn in the material's
  darkest shade by hand.
- Front and back views are mostly symmetric: sym() builds them from the left half,
  with the right half darkened a step (light from the top left).
- fill_pose() stands an outlined body on the cell's baseline and pastes outlined parts
  (arms, heads) in the body fill's coordinates, as skeleton_warrior's pose() does.
- ring() draws flattened rings for shockwaves, sound and stare waves on the floor plane;
  puff() draws a billowing cloud (smoke, frost, dust).
- tube() draws a tube along a 3D path with a depth buffer and K seams where it crosses
  itself: Medusa's coils and hair-snakes, seen correctly from every view.
- shatter() breaks a sprite into outlined shards that fly apart and land.
"""

from __future__ import annotations

import math
from typing import Callable, Optional

from pixel import (
    COLOURS,
    Sprite,
    blank,
    check,
    outline,
    pad,
    paste,
    size,
    underlay,
)

# The right half of a front or back view, one step darker than the left
SHADE = {"W": "L", "L": "G", "G": "D", "S": "T", "T": "B", "B": "b", "R": "r", "E": "V", "V": "v",
         "C": "U", "U": "u", "I": "C", "Y": "O", "M": "P", "P": "p"}


def ol(sprite: Sprite, diagonal: bool = False) -> Sprite:
    """sprite padded by a pixel all round and outlined in K."""
    return outline(pad(sprite, 1, 1, 1, 1), "K", diagonal)


def sym(half: list[str], shade: dict[str, str] | None = None, odd: bool = False) -> Sprite:
    """A symmetric sprite from its left half; the mirrored right half is recoloured by
    shade. With odd, the half's last column is the centre and is not repeated."""
    table = str.maketrans(shade or {})
    out = []
    for row in half:
        right = row[:-1] if odd else row
        out.append(row + right[::-1].translate(table))
    return out




def compose(w: int, h: int, layers: list[tuple]) -> Sprite:
    """A w x h grid with each (sprite, top, left[, under]) drawn in turn; under puts it
    behind what is already there."""
    out = blank(w, h)
    for layer in layers:
        sprite, top, left = layer[:3]
        under = len(layer) > 3 and layer[3]
        out = (underlay if under else paste)(out, sprite, top, left)
    return out


def ring(
    w: int, h: int, cx: float, cy: float, rx: float, ry: float, letter: str,
    thickness: float = 1.0, edge: str = "", a0: float = 0, a1: float = 360,
    gaps: int = 0, gap_width: float = 0.0, spin: float = 0.0,
) -> Sprite:
    """A w x h sprite with an elliptical ring of radii (rx, ry) round (cx, cy): the
    floor-plane circle of a shockwave or sound wave. thickness is in pixels along x;
    edge, if given, goes on the outermost pixels. a0..a1 limits it to an arc (degrees
    anticlockwise from pointing right); gaps cuts it into dashes."""
    rows = []
    k = rx / ry if ry else 1.0
    for y in range(h):
        line = []
        for x in range(w):
            dx, dy = x + 0.5 - cx, (cy - (y + 0.5)) * k
            d = math.hypot(dx, dy)
            angle = math.degrees(math.atan2(dy, dx)) % 360
            lo, hi = a0 % 360, a1 % 360
            inside = a1 - a0 >= 360 or (lo <= angle <= hi if lo <= hi else angle >= lo or angle <= hi)
            if inside and gaps:
                seg = 360 / gaps
                inside = ((angle - spin) % seg) > gap_width * seg
            if inside and rx - thickness <= d <= rx:
                line.append(edge if edge and d > rx - 1 else letter)
            else:
                line.append(".")
        rows.append("".join(line))
    return rows




def dots(w: int, h: int, points: list[tuple[int, int, str]]) -> Sprite:
    """A w x h sprite with each (row, column, letter) set; off-grid points skipped."""
    grid = [["."] * w for _ in range(h)]
    for r, c, letter in points:
        if 0 <= r < h and 0 <= c < w:
            grid[r][c] = letter
    return ["".join(row) for row in grid]








def check_sprites(namespace: dict) -> None:
    """check() every UPPER_CASE list-of-strings sprite in a module's globals."""
    for name, sprite in list(namespace.items()):
        if name.isupper() and isinstance(sprite, list) and sprite and isinstance(sprite[0], str):
            check(sprite, name)




def lift(sprite: Sprite, n: int, row: int) -> Sprite:
    """n rows removed from row down and the part below pulled up, the top kept: a foot
    lifted off the ground, the leg still on the hip."""
    w, _ = size(sprite)
    return sprite[:row] + sprite[row + n :] + ["." * w] * n


def halves(sprite: Sprite, at: int) -> tuple[Sprite, Sprite]:
    """sprite split into the columns before at and from at on."""
    return [r[:at] for r in sprite], [r[at:] for r in sprite]


def join(left: Sprite, right: Sprite) -> Sprite:
    """Two sprites of one height side by side."""
    return [a + b for a, b in zip(left, right)]


def fill_pose(
    w: int, h: int, body: Sprite, parts: list[tuple] = (), dx: int = 0, dy: int = 1,
    under: list[tuple] = (),
) -> Sprite:
    """body (a fill, unoutlined) outlined and stood on the cell's baseline, centred, then
    moved dx, dy; dy=1 puts the fill's last row on the baseline and its outline below.
    Each (part fill, row, col) in parts is outlined and pasted in the body fill's
    coordinates, and each in under goes behind."""
    from pixel import baseline

    b = ol(body)
    bw, bh = size(b)
    left = (w - bw) // 2 + dx
    top = baseline(h) - bh + dy
    out = paste(blank(w, h), b, top, left)
    for part, r, c in under:
        out = underlay(out, ol(part), top + r, left + c)
    for part, r, c in parts:
        out = paste(out, ol(part), top + r, left + c)
    return out


def puff(r: int, seed: int = 0, body: str = "G", light: str = "L", dark: str = "D", rim: str = "~") -> Sprite:
    """A billowing cloud about 2r across: overlapping balls, each lit on its top left
    and shaded on its bottom right, with a soft translucent rim. Smoke by default; pass
    other letters for frost or dust."""
    import random

    rnd = random.Random(seed)
    n = 2 * r + 4
    c = n / 2
    balls = [(c, c + r * 0.1, r * 0.62)]
    for k in range(7):
        a = math.radians(k * 360 / 7 + rnd.uniform(-12, 12) + 90)
        d = r * rnd.uniform(0.62, 0.72)
        balls.append((c + d * math.cos(a), c - d * math.sin(a) * 0.8, r * rnd.uniform(0.3, 0.4)))
    inside = [[any(math.hypot((x + 0.5 - bx) / br, (y + 0.5 - by) / br) <= 1 for bx, by, br in balls)
               for x in range(n)] for y in range(n)]

    def at(y: int, x: int) -> bool:
        return 0 <= y < n and 0 <= x < n and inside[y][x]

    grid = [["."] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            if not inside[y][x]:
                continue
            if not at(y - 1, x) or not at(y - 1, x - 1) or not at(y - 2, x - 1):
                grid[y][x] = light  # lit where the lumps face up and left
            elif not at(y + 1, x) or not at(y + 1, x + 1) or not at(y + 1, x + 2):
                grid[y][x] = dark
            else:
                grid[y][x] = body
    out = ["".join(row) for row in grid]
    # the soft rim
    return outline(out, rim) if rim else out


# ---------------------------------------------------------------------------------
# Tubes: a snake's coils or a tail, drawn from a 3D path
# ---------------------------------------------------------------------------------

# Screen projection per view, from a creature-space point (x to the creature's left as
# seen from the front, y up, z towards the front): (screen x, depth towards camera)
VIEW_AXES = {
    "down": lambda x, z: (x, z),
    "up": lambda x, z: (-x, -z),
    "right": lambda x, z: (z, -x),
}
TILT = 0.45  # how far nearer points sit lower on screen: the camera looks down a little


def project(path: list[tuple[float, float, float, float]], view: str, cx: float, ground: float):
    """3D samples (x, y, z, radius) as screen samples (sx, sy, depth, radius, t)."""
    axes = VIEW_AXES[view]
    out = []
    n = len(path)
    for i, (x, y, z, r) in enumerate(path):
        sx, depth = axes(x, z)
        out.append((cx + sx, ground - y + depth * TILT, depth, r, i / max(1, n - 1)))
    return out


def tube(
    w: int, h: int, samples: list[tuple[float, float, float, float, float]],
    shade: Callable[[float, float, float], str], seam: float = 0.08,
) -> tuple[Sprite, list[list[Optional[float]]]]:
    """A tube along screen samples (sx, sy, depth, radius, t), drawn as discs with a depth
    buffer. shade(nx, ny, t) picks each pixel's letter from where it sits on the disc
    that won it. Where a nearer part of the tube crosses a farther one (t further apart
    than seam), the farther side gets a K line; the whole is outlined in K. Returns the
    sprite and the depth of each pixel (None where empty)."""
    best: list[list[Optional[tuple]]] = [[None] * w for _ in range(h)]
    for sx, sy, depth, r, t in samples:
        for y in range(int(sy - r) - 1, int(sy + r) + 2):
            for x in range(int(sx - r) - 1, int(sx + r) + 2):
                if not (0 <= x < w and 0 <= y < h):
                    continue
                nx, ny = (x + 0.5 - sx) / r, (y + 0.5 - sy) / r
                d2 = nx * nx + ny * ny
                if d2 > 1:
                    continue
                z = depth + math.sqrt(1 - d2) * r * 0.5
                cur = best[y][x]
                if cur is None or z > cur[0]:
                    best[y][x] = (z, t, nx, ny)
    grid = [["."] * w for _ in range(h)]
    zs: list[list[Optional[float]]] = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            b = best[y][x]
            if b is not None:
                grid[y][x] = shade(b[2], b[3], b[1])
                zs[y][x] = b[0]
    for y in range(h):
        for x in range(w):
            b = best[y][x]
            if b is None:
                continue
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny_, nx_ = y + dy, x + dx
                if 0 <= ny_ < h and 0 <= nx_ < w and best[ny_][nx_] is not None:
                    o = best[ny_][nx_]
                    if abs(o[1] - b[1]) > seam and o[0] > b[0]:
                        grid[y][x] = "K"
                        break
    return outline(["".join(row) for row in grid], "K"), zs


def scales(body: str, light: str, dark: str, belly: str = "", rings: int = 60) -> Callable[[float, float, float], str]:
    """A shade() for tube(): lit on the top left, dark below, a belly stripe along the
    underside if belly is given, and a scale pattern banded along the length."""

    def shade(nx: float, ny: float, t: float) -> str:
        band = int(t * rings)
        if nx + ny < -0.95 or ny < -0.8:
            return light
        if ny > 0.72 or nx + ny > 1.05:
            return dark
        if belly and 0.3 < ny <= 0.72:
            return belly if band % 2 == 0 or ny > 0.5 else body
        if (band + int((nx + 1) * 2)) % 3 == 0 and -0.4 < nx < 0.6:
            return dark
        return body

    return shade


def shatter(sprite: Sprite, cy: float, cx: float, t: float, chunk: int = 5, spread: float = 1.0,
            fall: float = 0.0, seed: int = 0, floor: int | None = None) -> Sprite:
    """sprite broken into irregular shards (about chunk across, cut round random seed
    points), each outlined on its own, thrown out from (cy, cx) by t times its distance
    (spread scales it) and dropped fall * t * t rows, coming to rest on row floor if
    given: a body flying apart."""
    import random

    rnd = random.Random(seed)
    w, h = size(sprite)
    cells = [(y, x) for y in range(h) for x in range(w) if sprite[y][x] in COLOURS and sprite[y][x] != "K"]
    if not cells:
        return blank(w, h)
    ys, xs = [c[0] for c in cells], [c[1] for c in cells]
    n = max(2, (max(ys) - min(ys) + 1) * (max(xs) - min(xs) + 1) // (chunk * chunk))
    seeds = [(rnd.uniform(min(ys), max(ys)), rnd.uniform(min(xs), max(xs))) for _ in range(n)]
    groups: dict[int, list[tuple[int, int]]] = {}
    for y, x in cells:
        k = min(range(n), key=lambda i: (seeds[i][0] - y) ** 2 + (seeds[i][1] - x) ** 2)
        groups.setdefault(k, []).append((y, x))
    out = blank(w, h)
    pieces = []
    for k, px in groups.items():
        top, left = min(p[0] for p in px), min(p[1] for p in px)
        ph, pw = max(p[0] for p in px) - top + 1, max(p[1] for p in px) - left + 1
        grid = [["."] * pw for _ in range(ph)]
        for y, x in px:
            grid[y - top][x - left] = sprite[y][x]
        shard = ol(["".join(r) for r in grid])
        sy, sx = seeds[k]
        jitter = rnd.uniform(0.7, 1.3)
        dx = round((sx - cx) * t * spread * jitter * 0.6)
        dy = round((sy - cy) * t * spread * jitter * 0.4 + fall * t * t * rnd.uniform(0.8, 1.2))
        y = top + dy - 1
        if floor is not None:
            y = min(y, floor - len(shard) + 1)
        pieces.append((y, shard, left + dx - 1))
    for y, shard, x in sorted(pieces, key=lambda p: p[0]):
        out = paste(out, shard, y, x)
    return out
