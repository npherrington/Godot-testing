"""Shared helpers for the hellhound, vampire, troll and lich (batch D).

Not a module build.py runs (the leading underscore keeps it out of the list). Copied
ideas from skeleton_warrior.py rather than imported, so the reference stays untouched.

Drawing convention used by the batch D monsters:
- Parts are drawn as FILLS: colour only, no outer outline, "." outside.
- union() pastes fills together and outlines the lot in K, so the silhouette's outline
  never breaks. stamp() outlines one part on its own, so it reads as a separate shape
  (a far leg behind the body, an arm across it).
- Coordinates are always cell coordinates: (top, left) of the fill's first pixel.
"""

from __future__ import annotations

import math
import random
import textwrap

from pixel import (
    PREVIEW_BG,
    Sprite,
    blank,
    check,
    outline,
    pad,
    paste,
    size,
    strip,
    underlay,
    write_png,
)


def spr(text: str, name: str = "sprite") -> Sprite:
    """A sprite from a block of text: indentation removed, ragged rows padded with "."."""
    rows = [r.rstrip() for r in textwrap.dedent(text).strip("\n").split("\n")]
    w = max(len(r) for r in rows)
    return check([r.ljust(w, ".") for r in rows], name)


def fill(w: int, h: int, layers: list[tuple[Sprite, int, int]]) -> Sprite:
    """A w x h canvas with each (sprite, top, left) pasted in turn."""
    out = blank(w, h)
    for s, top, left in layers:
        out = paste(out, s, top, left)
    return out


def union(w: int, h: int, layers: list[tuple[Sprite, int, int]], letter: str = "K") -> Sprite:
    """The fills pasted together and outlined as one silhouette."""
    return outline(fill(w, h, layers), letter)


def stamp(base: Sprite, part: Sprite, top: int, left: int, behind: bool = False) -> Sprite:
    """part outlined on its own and drawn over (or behind) base, its fill's top-left at
    (top, left)."""
    framed = outline(pad(part, 1, 1, 1, 1))
    return (underlay if behind else paste)(base, framed, top - 1, left - 1)


def over(base: Sprite, top_layer: Sprite) -> Sprite:
    return paste(base, top_layer, 0, 0)


def behind(base: Sprite, back_layer: Sprite) -> Sprite:
    return underlay(base, back_layer, 0, 0)


def swap(sprite: Sprite, mapping: dict[str, str]) -> Sprite:
    table = str.maketrans(mapping)
    return [row.translate(table) for row in sprite]


def only(sprite: Sprite, keep: str) -> Sprite:
    """sprite with every letter not in keep emptied."""
    return ["".join(ch if ch in keep else "." for ch in row) for row in sprite]


def without(sprite: Sprite, drop: str) -> Sprite:
    return ["".join("." if ch in drop else ch for ch in row) for row in sprite]


def put(sprite: Sprite, points: list[tuple[int, int]], letter: str, empty_only: bool = False) -> Sprite:
    """letter at each (row, column) that lies inside sprite."""
    grid = [list(r) for r in sprite]
    h, w = len(grid), len(grid[0])
    for r, c in points:
        if 0 <= r < h and 0 <= c < w and (not empty_only or grid[r][c] == "."):
            grid[r][c] = letter
    return ["".join(r) for r in grid]


def lift_rows(sprite: Sprite, top: int, bottom: int, dy: int) -> Sprite:
    """Rows top..bottom-1 moved dy rows (negative is up), the rest left alone, drawn over."""
    w, h = size(sprite)
    band = ["." * w] * top + sprite[top:bottom] + ["." * w] * (h - bottom)
    rest = sprite[:top] + ["." * w] * (bottom - top) + sprite[bottom:]
    moved = paste(blank(w, h), band, dy, 0)
    return paste(rest, moved, 0, 0)


def sway(sprite: Sprite, top: int, dx: int, bottom: int = None) -> Sprite:
    """Rows from top down to bottom slid sideways, the bottom row by dx and less going up:
    a hem or a tail swinging. Rows below bottom move the full dx."""
    from pixel import shift
    h = len(sprite)
    bottom = h if bottom is None else bottom
    out = []
    for r, row in enumerate(sprite):
        if r < top or not dx:
            out.append(row)
            continue
        off = round(dx * min(1.0, (r - top + 1) / max(1, bottom - top)))
        out.append(shift([row], off, 0)[0])
    return out


def hflip_part(part: Sprite) -> Sprite:
    return [r[::-1] for r in part]


def glow_edge(sprite: Sprite, letter: str, into: str = "*", diagonal: bool = False) -> Sprite:
    """A translucent halo (into) on empty pixels touching pixels of letter."""
    w, h = size(sprite)
    grid = [list(r) for r in sprite]
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for y in range(h):
        for x in range(w):
            if sprite[y][x] != ".":
                continue
            for dy, dx in steps:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and sprite[ny][nx] in letter:
                    grid[y][x] = into
                    break
    return ["".join(r) for r in grid]


def ring(w: int, h: int, cx: float, cy: float, rx: float, ry: float, letter: str,
         thickness: float = 1.0, a0: float = 0, a1: float = 360) -> Sprite:
    """An elliptical ring (rx, ry radii) round (cx, cy), between angles a0 and a1."""
    rows = []
    for y in range(h):
        line = []
        for x in range(w):
            dx, dy = (x + 0.5 - cx) / rx, (cy - (y + 0.5)) / ry
            d = math.hypot(dx, dy)
            ang = math.degrees(math.atan2(dy * ry, dx * rx)) % 360
            inside = a0 <= ang <= a1 if a0 <= a1 else ang >= a0 or ang <= a1
            t = thickness / max(min(rx, ry), 1)
            line.append(letter if inside and 1 - t <= d <= 1 else ".")
        rows.append("".join(line))
    return rows


def disc(w: int, h: int, cx: float, cy: float, rx: float, ry: float, letter: str) -> Sprite:
    rows = []
    for y in range(h):
        rows.append("".join(
            letter if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1 else "."
            for x in range(w)
        ))
    return rows


def scatter(w: int, h: int, points: list[tuple[int, int, str]]) -> Sprite:
    """A w x h sprite with each (row, column, letter) drawn."""
    grid = [["."] * w for _ in range(h)]
    for r, c, ch in points:
        if 0 <= r < h and 0 <= c < w:
            grid[r][c] = ch
    return ["".join(r) for r in grid]


def rng(seed: int) -> random.Random:
    return random.Random(seed)


# ---------------------------------------------------------------------------------
# Limbs: capsules between joints, shaded with light from the left
# ---------------------------------------------------------------------------------


def capsules(w: int, h: int, segs: list[tuple[float, float, float, float, float]], letter: str) -> Sprite:
    """Each (x0, y0, x1, y1, radius) segment filled with letter; coordinates are pixel
    centres (column + 0.5, row + 0.5)."""
    grid = [["."] * w for _ in range(h)]
    for x0, y0, x1, y1, r in segs:
        lo_x, hi_x = int(min(x0, x1) - r - 1), int(max(x0, x1) + r + 1)
        lo_y, hi_y = int(min(y0, y1) - r - 1), int(max(y0, y1) + r + 1)
        dx, dy = x1 - x0, y1 - y0
        ll = dx * dx + dy * dy
        for y in range(max(0, lo_y), min(h, hi_y + 1)):
            for x in range(max(0, lo_x), min(w, hi_x + 1)):
                px, py = x + 0.5, y + 0.5
                t = 0.0 if ll == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / ll))
                cx, cy = x0 + t * dx, y0 + t * dy
                if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                    grid[y][x] = letter
    return ["".join(r) for r in grid]


def shade(sprite: Sprite, letter: str, light: str, dark: str, light_top: bool = True) -> Sprite:
    """Pixels of letter lit on the edges facing the top left and shaded on those facing
    the bottom right (the edge being an empty pixel next to them)."""
    w, h = size(sprite)
    out = [list(r) for r in sprite]

    def empty(y: int, x: int) -> bool:
        return not (0 <= y < h and 0 <= x < w) or sprite[y][x] == "."

    for y in range(h):
        for x in range(w):
            if sprite[y][x] != letter:
                continue
            if empty(y, x - 1) or (light_top and empty(y - 1, x)):
                out[y][x] = light
            elif empty(y, x + 1) or empty(y + 1, x):
                out[y][x] = dark
    return ["".join(r) for r in out]


def ik(root: tuple[float, float], target: tuple[float, float], l1: float, l2: float,
       bend: int) -> tuple[float, float]:
    """The middle joint of a two-bone limb from root reaching target; bend +1 or -1
    picks which side the joint goes."""
    ax, ay = root
    tx, ty = target
    d = max(0.01, min(math.hypot(tx - ax, ty - ay), l1 + l2 - 0.01))
    base = math.atan2(ty - ay, tx - ax)
    cos_a = max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))
    a = base + bend * math.acos(cos_a)
    return ax + l1 * math.cos(a), ay + l1 * math.sin(a)


def flames(w: int, h: int, tongues: list[tuple[float, float, float]], rim: str = "R",
           mid: str = "O", core: str = "Y", sharp: float = 0.6) -> Sprite:
    """Tongues of fire standing on the bottom edge: each (centre x, height, half width).
    Coloured by depth from the nearest edge (not the bottom, which runs on into the body):
    a rim, a middle band and a hot core."""
    tops = [h] * w
    for c, height, hw in tongues:
        for x in range(w):
            k = 1 - abs(x + 0.5 - c) / hw
            if k > 0:
                tops[x] = min(tops[x], round(h - height * k ** sharp))
    filled = [[y >= tops[x] for x in range(w)] for y in range(h)]
    inf = 99
    dist = [[0 if not filled[y][x] else inf for x in range(w)] for y in range(h)]
    queue = [(y, x) for y in range(h) for x in range(w) if filled[y][x] and (
        x == 0 or x == w - 1 or y == 0 or not filled[y][x - 1] or not filled[y][x + 1] or not filled[y - 1][x])]
    for y, x in queue:
        dist[y][x] = 1
    i = 0
    while i < len(queue):
        y, x = queue[i]
        i += 1
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and dist[ny][nx] > dist[y][x] + 1:
                dist[ny][nx] = dist[y][x] + 1
                queue.append((ny, nx))
    return ["".join(
        "." if not filled[y][x] else rim if dist[y][x] <= 1 else mid if dist[y][x] == 2 else core
        for x in range(w)) for y in range(h)]


def polygon(w: int, h: int, pts: list[tuple[float, float]], letter: str) -> Sprite:
    """A filled polygon (x, y points, pixel-centre coordinates)."""
    rows = []
    n = len(pts)
    for y in range(h):
        py = y + 0.5
        line = []
        for x in range(w):
            px = x + 0.5
            inside = False
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 > py) != (y1 > py) and px < x0 + (py - y0) * (x1 - x0) / (y1 - y0):
                    inside = not inside
            line.append(letter if inside else ".")
        rows.append("".join(line))
    return rows


def line(sprite: Sprite, p0: tuple[float, float], p1: tuple[float, float], letter: str,
         inside_only: bool = False) -> Sprite:
    """A one-pixel line from p0 to p1 (x, y); with inside_only it draws only over pixels
    already drawn."""
    grid = [list(r) for r in sprite]
    h, w = len(grid), len(grid[0])
    (x0, y0), (x1, y1) = p0, p1
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        t = i / n
        x, y = int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)
        if 0 <= y < h and 0 <= x < w and (not inside_only or grid[y][x] != "."):
            grid[y][x] = letter
    return ["".join(r) for r in grid]


def preview(path: str, sprites: list[Sprite], scale: int = 6, gap: int = 1) -> None:
    """Debug: sprites side by side on the preview background, scaled. Only for looking."""
    h = max(len(s) for s in sprites)
    padded = [pad(s, 0, 0, h - len(s), 0) for s in sprites]
    sheet = strip(padded, gap)
    write_png(__import__("pathlib").Path(path), sheet, scale, background=PREVIEW_BG)


__all__ = [
    "spr", "fill", "union", "stamp", "over", "behind", "swap", "only", "without",
    "put", "lift_rows", "hflip_part", "glow_edge", "ring", "disc", "scatter", "rng", "preview",
    "capsules", "shade", "ik", "flames", "sway", "polygon", "line",
]
