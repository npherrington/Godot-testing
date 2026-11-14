"""Helpers shared by batch A's enemies: ghost, goblin, slime, slime_small, spider, ogre.

The leading underscore keeps build.py from treating this as a module to build.

- ol(): pad a fill-only drawing by a pixel and outline it in K, so poses can be drawn
  as flat colour and still get an unbroken outline.
- stand(): an outlined pose on the cell with its fill (not its outline) on the baseline.
- Canvas: a mutable grid with lines, for legs, strands and effects.
- dome_shade() / blob(): a lit dome for the slimes.
- ring(): an elliptical ring (shockwaves, web rings), top-down so wider than tall.
- sway(): rows below a pivot slid sideways, the lower the further (tails, wisps).
- resize(): nearest-neighbour scaling, for squash and stretch of a whole shape.
"""

from __future__ import annotations

import math

from pixel import Sprite, blank, cell, erase, outline, pad, paste, shift, size, underlay


def ol(sprite: Sprite, letter: str = "K") -> Sprite:
    """sprite with a one-pixel border added all round and outlined in letter."""
    return outline(pad(sprite, 1, 1, 1, 1), letter)


def stand(outlined: Sprite, w: int, h: int, dx: int = 0, dy: int = 0) -> Sprite:
    """An ol()-ed pose on a w x h cell, centred, its fill standing on the baseline (the
    outline row under the feet falls into the shadow rows below it)."""
    return cell(outlined, w, h, dx, dy + 1)


def put(base: Sprite, sprite: Sprite, top: int, left: int, behind: bool = False) -> Sprite:
    """paste, or underlay when behind."""
    return (underlay if behind else paste)(base, sprite, top, left)


def sway(sprite: Sprite, dx: int, top: int) -> Sprite:
    """Rows from top down slid sideways, more the lower they are: the last row by dx."""
    h = len(sprite)
    out = []
    for r, row in enumerate(sprite):
        off = round(dx * (r - top + 1) / (h - top)) if r >= top else 0
        out.append(shift([row], off, 0)[0] if off else row)
    return out


def resize(sprite: Sprite, nw: int, nh: int) -> Sprite:
    """Nearest-neighbour scaled to nw x nh."""
    w, h = size(sprite)
    return [
        "".join(sprite[min(h - 1, int((y + 0.5) * h / nh))][min(w - 1, int((x + 0.5) * w / nw))] for x in range(nw))
        for y in range(nh)
    ]


def trim(sprite: Sprite) -> Sprite:
    """sprite with empty rows and columns round the edge removed."""
    rows = [r for r, row in enumerate(sprite) if row.strip(".")]
    if not rows:
        return ["."]
    cols = [c for c in range(len(sprite[0])) if any(row[c] != "." for row in sprite)]
    return [row[cols[0] : cols[-1] + 1] for row in sprite[rows[0] : rows[-1] + 1]]


def replace_in(sprite: Sprite, mapping: dict[str, str], top: int, bottom: int) -> Sprite:
    """Letters swapped by mapping in rows top..bottom-1 only."""
    table = str.maketrans(mapping)
    return [row.translate(table) if top <= r < bottom else row for r, row in enumerate(sprite)]


class Canvas:
    """A w x h grid to draw on with points and lines; rows() gives the sprite."""

    def __init__(self, w: int, h: int, base: Sprite | None = None) -> None:
        self.w, self.h = w, h
        self.g = [list(row) for row in (base or blank(w, h))]

    def set(self, x: float, y: float, ch: str, under: bool = False) -> None:
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h and (not under or self.g[y][x] == "."):
            self.g[y][x] = ch

    def get(self, x: int, y: int) -> str:
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else "."

    def line(self, x0: float, y0: float, x1: float, y1: float, ch: str, under: bool = False) -> None:
        """A Bresenham line, both ends included."""
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.set(x0, y0, ch, under)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def polyline(self, points: list[tuple[float, float]], ch: str, under: bool = False) -> None:
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            self.line(x0, y0, x1, y1, ch, under)

    def blit(self, sprite: Sprite, top: int, left: int, under: bool = False) -> None:
        for r, row in enumerate(sprite):
            for c, ch in enumerate(row):
                if ch != ".":
                    self.set(left + c, top + r, ch, under)

    def rows(self) -> Sprite:
        return ["".join(row) for row in self.g]


def ring(
    w: int, h: int, cx: float, cy: float, rx: float, ry: float, letter: str,
    thickness: float = 1.5, edge: str = "", a0: float = 0, a1: float = 360,
) -> Sprite:
    """A w x h sprite holding an elliptical ring with radii rx, ry round (cx, cy), about
    thickness pixels thick, from angle a0 to a1 (degrees, counter-clockwise from right).
    edge, if given, goes on the outermost pixels."""
    out = []
    for y in range(h):
        line = []
        for x in range(w):
            dx, dy = x + 0.5 - cx, cy - (y + 0.5)
            n = math.hypot(dx / rx, dy / ry)
            if n == 0:
                line.append(".")
                continue
            reach = math.hypot(dx, dy) / n  # the ring's radius along this direction
            inset = (1 - n) * reach  # pixels inside the ring's rim
            angle = math.degrees(math.atan2(dy, dx)) % 360
            lo, hi = a0 % 360, a1 % 360
            inside = (a1 - a0) >= 360 or (lo <= angle <= hi if lo <= hi else angle >= lo or angle <= hi)
            if inside and 0 <= inset < thickness:
                line.append(edge if edge and inset < 1 else letter)
            else:
                line.append(".")
        out.append("".join(line))
    return out


def dome(w: int, h: int, lean: float = 0.0, flat: float = 2.4) -> list[list[bool]]:
    """A mask of a dome w wide at its foot and h tall, standing on its last row: round on
    top. lean slides the top sideways by up to that many pixels (positive is right); the
    mask has margin(lean) empty columns each side so nothing is cut off and the foot
    stays centred."""
    m = margin(lean)
    mask = []
    for y in range(h):
        t = (h - y - 0.5) / h  # 0 at the foot, 1 at the top
        half = (w / 2) * max(0.0, 1 - t**flat) ** 0.5
        cx = m + w / 2 + lean * t
        mask.append([abs(x + 0.5 - cx) <= half for x in range(w + 2 * m)])
    return mask


def margin(lean: float) -> int:
    return math.ceil(abs(lean))


def blob(
    w: int, h: int, light: str, mid: str, dark: str, glint: str = "W", lean: float = 0.0,
    flat: float = 2.4,
) -> Sprite:
    """A dome w x h shaded as lit from the top left: light, mid and dark bands, a glint
    near the top left, the foot row in the dark shade. Fill only; ol() it after
    pasting on whatever goes inside."""
    mask = dome(w, h, lean, flat)
    m = margin(lean)
    lx, ly, lz = -0.5, 0.75, 0.45
    norm = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / norm, ly / norm, lz / norm
    lum: dict[tuple[int, int], float] = {}
    for y in range(h):
        t = (h - y - 0.5) / h
        cx = m + w / 2 + lean * t
        for x in range(w + 2 * m):
            if mask[y][x]:
                nx = (x + 0.5 - cx) / (w / 2)
                nz = math.sqrt(max(0.0, 1 - nx * nx - t * t))
                lum[(y, x)] = nx * lx + t * ly + nz * lz
    # The glint: the few brightest pixels, a small blob of them
    count = max(1, round(len(lum) / 70))
    glints = set(sorted(lum, key=lambda k: -lum[k])[:count]) if glint else set()
    rows = []
    for y in range(h):
        line = []
        for x in range(w + 2 * m):
            i = lum.get((y, x))
            if i is None:
                ch = "."
            elif y == h - 1 or i <= 0.38:
                ch = dark
            elif (y, x) in glints:
                ch = glint
            elif i > 0.86:
                ch = light
            else:
                ch = mid
            line.append(ch)
        rows.append("".join(line))
    return rows


# ---------------------------------------------------------------------------------
# Slimes: slime.py and slime_small.py share the body
# ---------------------------------------------------------------------------------

# A skull half dissolved inside the big slime; the small ones carry a bone
GUT_SKULL = [
    "..LLL..",
    ".LWLLG.",
    "LLLLLGG",
    "LDDLDDG",
    ".LLLGG.",
    "..GDG..",
]
GUT_BONE = [
    "WL..",
    ".LG.",
    "..GG",
]

# (eye, mouth) per mood. The eye is the screen-left one; the right is its mirror.
FACES = {
    "calm": (["KKK", "WWK", "WWK"], ["KKKKKK", ".W..W."]),
    "open": (["KKK", "WWK", "WWK"], ["KKKKKKKK", "KWvvvvWK", "KvvvvvvK", "KvvvvvvK", ".KKKKKK."]),
    "shut": (["...", "KKK", "WWK"], ["KKKKKK"]),
    "dead": (["K.K", ".K.", "K.K"], [".KKKK."]),
    "small": (["KK", "WK"], ["KKKK"]),
    "small_open": (["KK", "WK"], ["KKKK", "KvvK", ".KK."]),
    "small_shut": (["..", "KK"], ["KKKK"]),
    "small_dead": (["K.", ".K"], ["KK"]),
}


def slime(
    w: int, h: int, view: str, mood: str = "calm", lean: float = 0.0, gut: Sprite | None = GUT_SKULL,
    bubbles: bool = True,
) -> Sprite:
    """A slime body w x h for view (down, up, right), fill only: the lit dome, the face
    (none from behind), and what it's digesting inside. ol() it to outline."""
    body = blob(w, h, "E", "V", "v", lean=lean)
    small = mood.startswith("small") or w < 16

    def centre(y: int) -> int:
        return int(round(margin(lean) + w / 2 + lean * (h - y - 0.5) / h))

    # What it's digesting sits low, to one side, toward the back in profile
    if gut and h >= len(gut) + 2:
        gw, gh = size(gut)
        gy = h - gh - (0 if small else 1)
        gx = {"down": centre(gy) + w // 8, "up": centre(gy) - w // 8 - gw, "right": centre(gy) - w // 4 - gw // 2}[view]
        body = paste(body, gut, gy, gx)
    if bubbles and not small and h >= 12:
        by = h // 2
        body = paste(body, ["W"], by + 1, centre(by) - w // 4 - 1)
        body = paste(body, ["E"], by + 4, centre(by) - w // 6)
        body = paste(body, ["E"], 3, centre(3) + w // 6)
    if view == "up" or mood == "none":
        return body
    eye, mouth = FACES[mood]
    ew, eh = size(eye)
    mw, mh = size(mouth)
    ey = max(1, round(h * (0.25 if small else 0.28)))
    my = ey + eh + (0 if small else 1)
    if view == "down":
        gap = 1 if small else max(1, round(w * 0.08))
        c = centre(ey)
        body = paste(body, eye, ey, c - gap - ew)
        body = paste(body, [r[::-1] for r in eye], ey, c + gap)
        return paste(body, mouth, my, centre(my) - mw // 2)
    # Profile: one eye near the front; the mouth on the front edge, or a notch cut into
    # it when open (the outline then runs round the inside of the maw)
    front = max(x for x, ch in enumerate(body[ey + eh - 1]) if ch != ".")
    body = paste(body, [r[::-1] for r in eye], ey, front - ew - (1 if small else 2))
    if mood in ("open", "small_open"):
        depths = [1, 2, 3, 2, 1] if small else [2, 4, 5, 5, 3, 1]
        for i, d in enumerate(depths):
            y = my - 1 + i
            if 0 <= y < h - 1:
                edge = max(x for x, ch in enumerate(body[y]) if ch != ".")
                body = erase(body, y, edge - d + 1, 1, d)
        edge = max(x for x, ch in enumerate(body[my - 1]) if ch != ".")
        return paste(body, ["W"], my, edge) if not small else body
    edge = max(x for x, ch in enumerate(body[my]) if ch != ".")
    length = 2 if small else 4
    body = paste(body, ["K" * length], my, edge - length + 1)
    if mood == "calm":
        body = paste(body, ["W"], my + 1, edge - 1)
    return body


def edge_shade(mask: Sprite, light: str, mid: str, dark: str, keep: str = "") -> Sprite:
    """Every drawn pixel (except letters in keep) shaded by where it sits: light where
    there's nothing above or to the left, dark where there's nothing below or to the
    right, mid inside. Lit from the top left."""
    h, w = len(mask), len(mask[0])

    def empty(y: int, x: int) -> bool:
        return not (0 <= y < h and 0 <= x < w) or mask[y][x] == "."

    out = []
    for y, row in enumerate(mask):
        line = []
        for x, ch in enumerate(row):
            if ch == "." or ch in keep:
                line.append(ch)
            elif empty(y - 1, x) or empty(y, x - 1):
                line.append(light)
            elif empty(y + 1, x) or empty(y, x + 1):
                line.append(dark)
            else:
                line.append(mid)
        out.append("".join(line))
    return out


def orb(w: int, h: int, light: str, mid: str, dark: str, glint: str = "") -> Sprite:
    """A filled ellipse w x h shaded as a ball lit from the top left: light, mid and dark
    bands, and a glint on the brightest few pixels if given. Fill only."""
    lx, ly, lz = -0.5, 0.75, 0.45
    norm = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / norm, ly / norm, lz / norm
    lum: dict[tuple[int, int], float] = {}
    for y in range(h):
        for x in range(w):
            nx = (x + 0.5 - w / 2) / (w / 2)
            ny = (h / 2 - y - 0.5) / (h / 2)
            if nx * nx + ny * ny <= 1.0:
                nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
                lum[(y, x)] = nx * lx + ny * ly + nz * lz
    count = max(1, round(len(lum) / 60))
    glints = set(sorted(lum, key=lambda k: -lum[k])[:count]) if glint else set()
    rows = []
    for y in range(h):
        line = []
        for x in range(w):
            i = lum.get((y, x))
            if i is None:
                line.append(".")
            elif (y, x) in glints:
                line.append(glint)
            elif i > 0.8:
                line.append(light)
            elif i > -0.05:
                line.append(mid)
            else:
                line.append(dark)
        rows.append("".join(line))
    return rows


def tube(
    w: int, h: int, points: list[tuple[float, float]], radii: list[float], light: str, mid: str,
    dark: str, hi: float = 0.8, lo: float = -0.05,
) -> Sprite:
    """A w x h sprite holding a limb: tapered capsules joining points (x, y), each point
    radii[i] pixels thick, shaded as a rounded tube lit from the top left. Fill only."""
    lx, ly, lz = -0.5, 0.75, 0.45
    norm = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / norm, ly / norm, lz / norm
    rows = []
    for y in range(h):
        line = []
        for x in range(w):
            px, py = x + 0.5, y + 0.5
            best = None
            for (ax, ay), (bx, by), ra, rb in zip(points, points[1:], radii, radii[1:]):
                vx, vy = bx - ax, by - ay
                l2 = vx * vx + vy * vy
                t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / l2)) if l2 else 0.0
                qx, qy = ax + vx * t, ay + vy * t
                r = ra + (rb - ra) * t
                d = math.hypot(px - qx, py - qy)
                if d <= r and (best is None or d / r < best[0]):
                    best = (d / r, (px - qx) / r, (py - qy) / r)
            if best is None:
                line.append(".")
                continue
            _, nx, ny = best
            nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
            i = nx * lx - ny * ly + nz * lz
            line.append(light if i > hi else mid if i > lo else dark)
        rows.append("".join(line))
    return rows


def inlay(base: Sprite, part: Sprite, top: int, left: int, inner: str, behind: bool = False) -> Sprite:
    """part (fill only) outlined and pasted on base with its fill's top-left at (top,
    left): its outline is K where it meets empty space and inner where it crosses what
    base already has, so a limb over a body gets a soft inner line, not a black one.
    With behind, only the parts of it outside base show."""
    out = [list(row) for row in base]
    h, w = len(base), len(base[0])
    o = outline(pad(part, 1, 1, 1, 1), "K")
    for r, row in enumerate(o):
        y = top - 1 + r
        if not 0 <= y < h:
            continue
        for c, ch in enumerate(row):
            x = left - 1 + c
            if ch == "." or not 0 <= x < w:
                continue
            under = base[y][x]
            if behind and under != ".":
                continue
            fill = 1 <= r <= len(part) and 1 <= c <= len(part[0]) and part[r - 1][c - 1] != "."
            if fill:
                out[y][x] = ch
            else:
                out[y][x] = "K" if under in ".K" else inner
    return ["".join(row) for row in out]
