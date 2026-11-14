"""Helpers for the batch-B monsters (dark_mage, zombie, harpy, mimic, basilisk).

Grid tricks the engine doesn't have: an outline that leaves drawn K edges alone, poses
put together from a body and parts, a vertical shear for hinged jaws and lids, burying a
pose in the floor, Bresenham lines, and haze puffs. No drawings live here.
"""

from __future__ import annotations

from pixel import (
    BAYER,
    COLOURS,
    Sprite,
    baseline,
    cell,
    ellipse,
    pad,
    paste,
    shift,
    size,
    underlay,
)


def seal(sprite: Sprite, letter: str = "K") -> Sprite:
    """letter on every empty pixel that touches a drawn, opaque, non-K pixel: the outline
    for fills drawn without one, which leaves edges already outlined in K alone."""
    w, h = size(sprite)
    grid = [list(row) for row in sprite]
    for y in range(h):
        for x in range(w):
            if sprite[y][x] != ".":
                continue
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w:
                    ch = sprite[ny][nx]
                    if ch in COLOURS and ch != letter:
                        grid[y][x] = letter
                        break
    return ["".join(row) for row in grid]


def outlined(sprite: Sprite) -> Sprite:
    """sprite padded by a pixel all round and sealed in K."""
    return seal(pad(sprite, 1, 1, 1, 1))


Part = tuple[Sprite, int, int]  # (sprite, row, column) in the body's own coordinates


def place(
    body: Sprite,
    w: int,
    h: int,
    front: list[Part] = (),
    back: list[Part] = (),
    dx: int = 0,
    dy: int = 0,
    sealed: bool = True,
    haze: list[Part] = (),
) -> Sprite:
    """body standing on the baseline of a w x h cell, centred and moved (dx, dy); each
    back part drawn under it (showing only round it), each front part pasted over it, in
    the body's coordinates. Then the whole silhouette is sealed in K, and each haze part
    (glows, auras: translucent letters) laid under the result, so it never covers the
    body or breaks its outline."""
    bw, bh = size(body)
    left, top = (w - bw) // 2 + dx, baseline(h) - bh + dy
    out = cell(body, w, h, dx, dy)
    for sprite, r, c in back:
        out = underlay(out, sprite, top + r, left + c)
    for sprite, r, c in front:
        out = paste(out, sprite, top + r, left + c)
    out = seal(out) if sealed else out
    for sprite, r, c in haze:
        out = underlay(out, sprite, top + r, left + c)
    return out


def vshear(sprite: Sprite, dy: int, pivot: int = 0) -> Sprite:
    """Columns right of pivot slid up, the last column by dy and less on the way back:
    a lid or jaw tilting open on a hinge at column pivot (negative dy tilts it down)."""
    w, h = size(sprite)
    span = max(1, w - 1 - pivot)
    cols = []
    for x in range(w):
        col = [sprite[y][x] for y in range(h)]
        off = round(dy * (x - pivot) / span) if x > pivot else 0
        if off > 0:
            col = col[off:] + ["."] * off
        elif off < 0:
            col = ["."] * -off + col[:off]
        cols.append(col)
    return ["".join(cols[x][y] for x in range(w)) for y in range(h)]


def bury(f: Sprite, depth: int, floor: int) -> Sprite:
    """f moved depth rows down with everything from row floor down cut away: a figure
    sunk in the ground, showing only what's above it."""
    w, h = size(f)
    moved = shift(f, 0, depth)
    return [row if y < floor else "." * w for y, row in enumerate(moved)]


def line(w: int, h: int, x0: int, y0: int, x1: int, y1: int, letter: str) -> Sprite:
    """A w x h sprite with a one-pixel line from (x0, y0) to (x1, y1)."""
    grid = [["."] * w for _ in range(h)]
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    x, y = x0, y0
    while True:
        if 0 <= x < w and 0 <= y < h:
            grid[y][x] = letter
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
    return ["".join(r) for r in grid]


def _scatter(x: int, y: int) -> float:
    """A fixed, irregular value in [0, 1) per pixel: sparks that don't line up."""
    n = (x * 374761393 + y * 668265263) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n & 0xFFFF) / 65536


def puff(w: int, h: int, letter: str, density: float = 0.6, ox: int = 0, oy: int = 0,
         core: str = "", core_amount: float = 0.0) -> Sprite:
    """An ellipse of translucent haze: solid (at density 1) through its middle, thinned
    by an ordered dither toward a ragged rim; core, if given, sprinkles opaque sparks
    inside."""
    out = []
    for y in range(h):
        ny = (y + 0.5) / h * 2 - 1
        row = []
        for x in range(w):
            nx = (x + 0.5) / w * 2 - 1
            d = nx * nx + ny * ny
            if d > 1.0:
                row.append(".")
                continue
            t = BAYER[(y + oy) % 4][(x + ox) % 4] / 16
            local = density * min(1.0, (1.0 - d) / 0.55)
            if core and d < 0.45 and _scatter(x + ox, y + oy) < core_amount:
                row.append(core)
            elif t < local:
                row.append(letter)
            else:
                row.append(".")
        out.append("".join(row))
    return out


def ring(w: int, h: int, letter: str, rim: str = "", thickness: float = 1.0) -> Sprite:
    """An elliptical ring w x h, thickness in pixels; rim, if given, on its outer edge."""
    out = []
    cx, cy = w / 2, h / 2
    for y in range(h):
        row = []
        for x in range(w):
            nx, ny = (x + 0.5 - cx) / cx, (y + 0.5 - cy) / cy
            d = (nx * nx + ny * ny) ** 0.5
            inner = 1.0 - thickness / min(cx, cy)
            if inner <= d <= 1.0:
                row.append(rim if rim and d > 1.0 - 1.0 / min(cx, cy) else letter)
            else:
                row.append(".")
        out.append("".join(row))
    return out


def disc(d: int, letter: str, rim: str = "") -> Sprite:
    """A filled circle d across; rim, if given, on its outermost pixels."""
    body = ellipse(d, d, letter)
    if not rim:
        return body
    inner = pad(ellipse(d - 2, d - 2, "x"), 1, 1, 1, 1)
    return ["".join(rim if ch != "." and inner[y][x] == "." else ch for x, ch in enumerate(row))
            for y, row in enumerate(body)]


def centred(f: Sprite, sprite: Sprite, top: int) -> Sprite:
    """sprite pasted on f, centred left to right, its top at row top."""
    return paste(f, sprite, top, (len(f[0]) - len(sprite[0])) // 2)


def trim(sprite: Sprite) -> Sprite:
    """sprite cropped to the box round its drawn pixels."""
    rows = [y for y, row in enumerate(sprite) if row.strip(".")]
    cols = [x for x in range(len(sprite[0])) if any(row[x] != "." for row in sprite)]
    if not rows:
        return ["."]
    return [row[cols[0] : cols[-1] + 1] for row in sprite[rows[0] : rows[-1] + 1]]


def shade(mask: Sprite, light: str, mid: str, dark: str, speck: str = "", under: int = 2) -> Sprite:
    """Every drawn pixel of mask coloured by where it sits in the shape, lit from the top
    left: light along the top and left edges, dark along the bottom (under rows deep) and
    right edges, mid inside; speck, if given, scattered over the mid as a scale or grain
    texture in a staggered grid."""
    h, w = len(mask), len(mask[0])

    def on(x: int, y: int) -> bool:
        return 0 <= x < w and 0 <= y < h and mask[y][x] != "."

    out = []
    for y in range(h):
        row = []
        for x in range(w):
            if not on(x, y):
                row.append(".")
            elif not on(x, y - 1) or (not on(x - 1, y) and not on(x - 1, y - 1)):
                row.append(light)
            elif any(not on(x, y + k) for k in range(1, under + 1)) or not on(x + 1, y):
                row.append(dark)
            elif speck and (x + 2 * (y // 2)) % 4 == 0 and y % 2 == 0:
                row.append(speck)
            else:
                row.append(mid)
        out.append("".join(row))
    return out
