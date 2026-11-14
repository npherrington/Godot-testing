"""Lich: the ultimate boss.

A skeletal sorcerer-king floating in layered, tattered robes of deep purple: a jagged
gold crown, cold blue eye-lights, a high collar of spikes, a soul-gem burning in its
open ribcage, and a black staff crowned with bone horns cradling a second gem. No feet:
the robe frays into drifting strips over its shadow.
Attack: a necrotic bolt from its open hand (fx death_bolt).
Attack 2: it rises, raises the staff and slams it down; dark energy bursts across the
floor (fx nova).
Special, "raise dead": it lifts the staff high and a summoning circle burns into the
floor round it as bony hands claw up (fx summon_circle).
Death: the gem cracks, a cold flash, the robes collapse, the crown falls, all fades.

How it's built:
- The robes are polygons (collar spikes, robe, inner robe, mantle, bell sleeves from
  shoulder to hand), shaded with the light from the top left and outlined in layers so
  the mantle and sleeves read over the robe. The hem is a row of strips whose lengths
  drift every frame: the tatters never hang still.
- The skull, crown, ribcage, staff head and hands are hand-drawn and stamped on.
- pose() takes where the hands, the staff and the body are, so every animation is a list
  of poses plus the magic drawn over them.
- Left is mirror()ed from right.
"""

import math

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    blank,
    dissolve,
    mirror,
    silhouette,
    squash,
    write_character,
)
from enemies._batch_d import (
    disc,
    only,
    fill,
    glow_edge,
    hflip_part,
    line,
    over,
    polygon,
    put,
    ring,
    rng,
    shade,
    spr,
    stamp,
    swap,
    union,
)

W, H = 48, 48
LIFT = 0  # a body offset; the robe stops short of the floor, so it hovers over its shadow

# ---------------------------------------------------------------------------------
# Hand-drawn parts
# ---------------------------------------------------------------------------------

SKULL_D = spr("""
    ..WWWWWW..
    .WWWWWWWLL
    WWWWWWWWWL
    WWWWWWWWLL
    WKKKWWKKKL
    WKCIWWICKL
    LWKKWLKKLL
    .LWWKKWLL.
    .LDWDWDWD.
    ..WDWDWD..
    ...LLLL...
""")
SKULL_U = spr("""
    ..WWWWWW..
    .WWWWWWWWL
    WWWWWWDWWL
    WWWWWDWWLL
    WWWWWWDLLL
    LWWWWDLLLL
    .LLWWLLLL.
    ..LLLLLL..
""")
SKULL_R = spr("""
    ..WWWWW...
    .WWWWWWWW.
    WWWWWWWWWW
    WWWWWWWWWW
    LWWWWWWWWL
    LWWWWKKKWL
    LLWWWKCIKW
    .LLWWWKKWK
    ..LLWWWWWW
    ...LDWDWDW
    ...LWDWDWD
    ....LLLLL.
""")

CROWN_D = spr("""
    Y....Y...Y
    YY..YYY.YY
    YYYYYYYYYY
    WYRYOCYRYO
    OOOOOOOOOO
""")
CROWN_U = swap(hflip_part(CROWN_D), {"R": "O", "C": "Y"})
CROWN_R = spr("""
    Y...Y..Y.
    YY.YYY.YY
    YYYYYYYYY
    WYRYYYRYO
    OOOOOOOOO
""")

RIBS_D = spr("""
    ..WLLW..
    WWLKKLWW
    KWK=IKWK
    WLKICIKW
    KWKCCKWK
    WLWKKWLW
    .KWLLWK.
    ..LWWL..
""")
RIBS_R = spr("""
    WWL.
    KKWL
    WL=I
    KWIC
    WLCC
    KKWL
    .WL.
""")

STAFF_HEAD = spr("""
    L.......L
    WL.....LW
    .W..I..W.
    .WLICILW.
    ..WCICW..
    ...WCW...
    ....D....
""")

HAND_GRIP = spr("""
    .WWL
    WLWL
    WWLL
""")
HAND_OPEN = spr("""
    .WWL.
    WLWLW
    W.W.W
    L...L
""")

# A collapsed robe on the floor: the end of death, the crown comes to rest on it
HEAP = spr("""
    ...........pPPPp..........
    .......pppPPMMPPPppp......
    ....ppPPPppppppPPPPppp....
    ..ppKpppPPppKppppPPpppp...
    .ppppKppppppppKppppppKpp..
    pppKpppppKpppppppKppppppp.
    .pKp.ppK.pKp.ppKpp.pKpp.p.
    ..p...p...p...p....p...p..
""")

BONE_HAND = spr("""
    W.W.W
    WLWLW
    .WWL.
    ..WL.
    ..LW.
    ..WL.
""")

FLARE = spr("""
    ...=...
    .=.I.=.
    ..=I=..
    =IIWII=
    ..=I=..
    .=.I.=.
    ...=...
""")


def _check_all() -> None:
    from pixel import check
    for name, value in list(globals().items()):
        if name.isupper() and isinstance(value, list) and value and isinstance(value[0], str):
            check(value, name)


_check_all()

# ---------------------------------------------------------------------------------
# Robes
# ---------------------------------------------------------------------------------


def tatters(x0: int, x1: int, y: int, k: int, sway_: int = 0, base: str = "p") -> Sprite:
    """Ragged strips hanging from row y between columns x0 and x1; their lengths drift
    with frame k and they trail sway_ pixels at the tips."""
    grid = [["."] * W for _ in range(H)]
    for x in range(x0, x1 + 1):
        n = 1 + int(1.6 + 1.5 * math.sin(x * 1.7 + k * 0.9) + 1.0 * math.sin(x * 0.6 - k * 1.3))
        if (x + k) % 5 == 0:
            n = max(1, n - 2)
        for i in range(n):
            xx = x + round(sway_ * i / 5)
            if 0 <= y + i < H and 0 <= xx < W:
                grid[y + i][xx] = base if i < n - 1 else "K"
    return ["".join(r) for r in grid]


def sleeve(shoulder: tuple[float, float], cuff: tuple[float, float], w0: float, w1: float,
           letter: str = "P") -> Sprite:
    """A bell sleeve from shoulder to cuff, w0 wide at the top and w1 at the cuff, the
    cuff cut ragged."""
    (sx, sy), (cx, cy) = shoulder, cuff
    dx, dy = cx - sx, cy - sy
    n = math.hypot(dx, dy) or 1
    px, py = -dy / n, dx / n
    a = (sx + px * w0 / 2, sy + py * w0 / 2)
    b = (sx - px * w0 / 2, sy - py * w0 / 2)
    c = (cx - px * w1 / 2, cy - py * w1 / 2)
    d = (cx + px * w1 / 2, cy + py * w1 / 2)
    ux, uy = dx / n, dy / n
    jag = []
    for i in range(5):
        t = i / 4
        x = c[0] + (d[0] - c[0]) * t
        y = c[1] + (d[1] - c[1]) * t
        out = 1.6 if i % 2 == 0 else -0.6
        jag.append((x + ux * out, y + uy * out))
    return shade(polygon(W, H, [a, b] + jag, letter), letter, "M", "p")


def fade_hem(body: Sprite, y0: int) -> Sprite:
    """The robe darkens toward the hem: highlights go first, then it dithers into black."""
    out = []
    for r, row in enumerate(body):
        if r >= 30 + y0:
            row = row.replace("P", "p").replace("M", "P")
        if r >= 33 + y0:
            row = "".join("K" if ch == "p" and (x + r) % 2 else ch for x, ch in enumerate(row))
        out.append(row)
    return out


def at(pts, y0: int, x0: int = 0):
    return [(x + x0, y + y0) for x, y in pts]


COLLAR_L = [(20.0, 16.0), (11.0, 7.0), (14.5, 10.5), (13.5, 3.5), (17.0, 9.0), (18.0, 5.0),
            (20.0, 10.0), (21.0, 13.0)]
MANTLE_D = [(9.5, 19.0), (16.0, 13.5), (32.0, 13.5), (38.5, 19.0), (38.5, 22.0), (37.0, 25.0),
            (35.0, 21.5), (33.0, 26.0), (31.0, 21.5), (28.0, 23.0), (20.0, 23.0), (17.0, 21.5),
            (15.0, 26.0), (13.0, 21.5), (11.0, 25.0), (9.5, 22.0)]


def robes_front(y0: int, k: int, sway_: int, back: bool) -> Sprite:
    collar_l = polygon(W, H, at(COLLAR_L, y0), "P")
    collar = fill(W, H, [(collar_l, 0, 0), (hflip_part(collar_l), 0, 0)])
    collar = shade(collar, "P", "M", "p")
    collar = line(collar, (14.5, 7.0 + y0), (19.0, 14.0 + y0), "p", inside_only=True)
    collar = line(collar, (33.5, 7.0 + y0), (29.0, 14.0 + y0), "K", inside_only=True)
    robe = polygon(W, H, at([(15.5, 18.0), (32.5, 18.0), (35.5, 37.0), (12.5, 37.0)], y0), "p")
    layers = [(robe, 0, 0)]
    if not back:
        layers.append((polygon(W, H, at([(20.0, 18.0), (28.0, 18.0), (29.0, 37.0), (19.0, 37.0)], y0), "K"), 0, 0))
    layers.append((tatters(13, 35, 37 + y0, k, sway_), 0, 0))
    body = shade(fill(W, H, layers), "p", "P", "K")
    folds = ((16.5, 14.5), (31.5, 33.5)) if not back else ((17.5, 15.5), (24.0, 24.0), (30.5, 32.5))
    for x0, x1 in folds:
        body = line(body, (x0, 22.0 + y0), (x1, 36.0 + y0), "K", inside_only=True)
        body = line(body, (x0 - 1, 22.0 + y0), (x1 - 1, 36.0 + y0), "P", inside_only=True)
    if not back:
        # A belt of black iron with a gold clasp across the inner robe; folds in the dark
        body = line(body, (19.0, 27.0 + y0), (28.5, 27.0 + y0), "D", inside_only=True)
        body = put(body, [(27 + y0, 23), (27 + y0, 24)], "Y")
        for x in (21.0, 26.0):
            body = line(body, (x, 29.0 + y0), (x + (x - 23.5) * 0.15, 36.0 + y0), "p", inside_only=True)
    body = fade_hem(body, y0)
    if back:
        return union(W, H, [(body, 0, 0)]), collar
    return union(W, H, [(fill(W, H, [(collar, 0, 0)]), 0, 0), (body, 0, 0)]), None


def robes_side(y0: int, k: int, sway_: int) -> Sprite:
    collar = polygon(W, H, at([(22.5, 17.0), (14.0, 8.5), (17.5, 11.5), (16.0, 4.0), (19.5, 9.5),
                               (21.0, 5.5), (23.0, 11.0), (24.5, 15.0)], y0), "P")
    collar = shade(collar, "P", "M", "p")
    collar = line(collar, (17.0, 7.0 + y0), (22.0, 15.0 + y0), "p", inside_only=True)
    robe = polygon(W, H, at([(19.0, 18.0), (29.0, 18.0), (31.0, 37.0), (11.5, 37.0), (14.0, 28.0)], y0), "p")
    front = polygon(W, H, at([(26.5, 18.0), (29.0, 18.0), (31.0, 37.0), (27.5, 37.0)], y0), "K")
    hem = tatters(12, 31, 37 + y0, k, sway_)
    body = shade(fill(W, H, [(robe, 0, 0), (front, 0, 0), (hem, 0, 0)]), "p", "P", "K")
    for x0, x1 in ((19.0, 15.0), (23.5, 21.0)):
        body = line(body, (x0, 22.0 + y0), (x1, 36.0 + y0), "K", inside_only=True)
        body = line(body, (x0 - 1, 22.0 + y0), (x1 - 1, 36.0 + y0), "P", inside_only=True)
    body = fade_hem(body, y0)
    return union(W, H, [(collar, 0, 0), (body, 0, 0)])


MANTLE_R = [(14.5, 21.0), (19.0, 14.0), (27.5, 13.5), (31.0, 19.0), (30.0, 22.5), (28.0, 20.5),
            (26.0, 25.0), (24.0, 21.0), (21.0, 26.0), (19.0, 21.5), (16.5, 25.0)]
MANTLE_U = [(9.5, 19.0), (16.0, 13.5), (32.0, 13.5), (38.5, 19.0), (38.5, 22.0), (36.0, 26.0),
            (34.0, 22.0), (31.0, 28.0), (28.5, 22.5), (26.0, 29.0), (24.0, 23.0), (21.5, 29.0),
            (19.0, 22.5), (16.5, 28.0), (14.0, 22.0), (12.0, 26.0), (9.5, 22.0)]

# ---------------------------------------------------------------------------------
# Pose
# ---------------------------------------------------------------------------------

# Rest positions per view: shoulders (staff side, casting side), the staff's x, the
# grip and the casting hand
REST = {
    "down": {"staff_x": 11, "grip": (12.0, 25.0), "free": (36.5, 31.0),
             "shoulders": ((13.0, 19.0), (35.0, 19.0))},
    "up": {"staff_x": 35, "grip": (36.0, 25.0), "free": (11.5, 31.0),
           "shoulders": ((35.0, 19.0), (13.0, 19.0))},
    "right": {"staff_x": 34, "grip": (33.0, 25.0), "free": (31.0, 30.0),
              "shoulders": ((25.0, 19.0), (22.0, 19.0))},
}


def pose(view: str, k: int = 0, dy: int = 0, sway_: int = 0, free=None, grip=None, staff_y: int = 0,
         gem: str = "", eyes: str = "", free_open: bool = True) -> Sprite:
    """The lich in view. k drifts the tatters; dy bobs it; free and grip place the casting
    hand and the staff hand (the staff moves with the grip's height change); gem and eyes
    recolour the soul-gem and the eye-lights."""
    rest = REST[view]
    y0 = LIFT + dy
    grip = grip or rest["grip"]
    free = free or rest["free"]
    staff_y += int(grip[1] - rest["grip"][1])
    sx = rest["staff_x"] + int(grip[0] - rest["grip"][0])
    s_staff, s_free = rest["shoulders"]
    gem_map = {"C": gem, "=": gem} if gem else {}
    eye_map = {"C": eyes, "I": eyes} if eyes else {}

    staff = fill(W, H, [(["GD"] * 27, 11 + y0 + staff_y, sx)])
    head = STAFF_HEAD if not gem else swap(STAFF_HEAD, {"C": gem})

    if view == "right":
        # Far arm (casting) first, behind; then the body; the near arm holds the staff
        out = stamp(blank(W, H), sleeve((s_free[0], s_free[1] + y0), (free[0] - 1, free[1] + y0 - 1), 4, 6, "p"), 0, 0)
        out = over(out, robes_side(y0, k, sway_))
        out = stamp(out, shade(polygon(W, H, at(MANTLE_R, y0), "P"), "P", "M", "p"), 0, 0)
        out = stamp(out, swap(RIBS_R, gem_map), 19 + y0, 26)
        out = stamp(out, HAND_OPEN if free_open else HAND_GRIP, int(free[1]) + y0 - 1, int(free[0]) - 2)
        out = stamp(out, staff, 0, 0)
        out = stamp(out, head, 4 + y0 + staff_y, sx - 3)
        out = stamp(out, sleeve((s_staff[0], s_staff[1] + y0), (grip[0] - 1, grip[1] + y0 - 1), 5, 6), 0, 0)
        out = stamp(out, HAND_GRIP, int(grip[1]) + y0, int(grip[0]) - 1)
        out = stamp(out, swap(SKULL_R, eye_map), 8 + y0, 22)
        out = stamp(out, CROWN_R, 4 + y0, 21)
        return out

    back = view == "up"
    robes, collar = robes_front(y0, k, sway_, back)
    out = robes
    mantle = MANTLE_U if back else MANTLE_D
    out = stamp(out, shade(polygon(W, H, at(mantle, y0), "P"), "P", "M", "p"), 0, 0)
    if back:
        out = stamp(out, swap(SKULL_U, eye_map), 8 + y0, 19)
        out = stamp(out, CROWN_U, 4 + y0, 19)
        out = over(out, union(W, H, [(collar, 0, 0)]))  # the collar stands in front of the skull
    else:
        out = stamp(out, swap(RIBS_D, gem_map), 18 + y0, 20)
    out = stamp(out, staff, 0, 0)
    out = stamp(out, head, 4 + y0 + staff_y, sx - 3)
    out = stamp(out, sleeve((s_staff[0], s_staff[1] + y0), (grip[0] + (1 if not back else -1), grip[1] + y0 - 1), 5, 7), 0, 0)
    out = stamp(out, HAND_GRIP if not back else hflip_part(HAND_GRIP), int(grip[1]) + y0, int(grip[0]) - 2)
    out = stamp(out, sleeve((s_free[0], s_free[1] + y0), (free[0], free[1] + y0 - 2), 5, 7), 0, 0)
    hand = HAND_OPEN if free_open else HAND_GRIP
    out = stamp(out, hand, int(free[1]) + y0 - 1, int(free[0]) - 2)
    if not back:
        out = stamp(out, swap(SKULL_D, eye_map), 8 + y0, 19)
        out = stamp(out, CROWN_D, 4 + y0, 19)
    return out


# ---------------------------------------------------------------------------------
# Magic
# ---------------------------------------------------------------------------------

ORB = spr("""
    .&P&.
    &PMP&
    PMIMP
    &PMP&
    .&P&.
""")
ORB_BIG = spr("""
    ..&P&..
    .&PMP&.
    &PMIMP&
    PMIWIMP
    &PMIMP&
    .&PMP&.
    ..&P&..
""")


def death_bolt_effect() -> list[Sprite]:
    """24 x 12, flying right: a teardrop of cold white light sheathed in violet, a tail of
    dark flame streaming and twisting behind it. Six frames that loop."""
    w, h = 24, 12
    cx, cy = 18.5, 6.0
    frames = []
    for k in range(6):
        r = rng(40 + k)
        grid = [["."] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                # The head: round in front, drawn out behind
                d = math.hypot(dx if dx > 0 else dx * 0.55, dy * 1.05)
                if d <= 1.2:
                    grid[y][x] = "W"
                elif d <= 2.1:
                    grid[y][x] = "I"
                elif d <= 3.1:
                    grid[y][x] = "M"
                elif d <= 4.1:
                    grid[y][x] = "P"
                elif dx < 0:
                    u = -dx / 18
                    half = 3.6 * (1 - u) + 0.7 * math.sin(x * 0.9 + k * 1.6)
                    off = 1.4 * math.sin(x * 0.45 - k * 1.1) * u
                    v = abs(dy - off)
                    if u < 1 and v < half:
                        if v > half - 1.2:
                            grid[y][x] = "&" if (x + y + k) % 2 else "p"
                        else:
                            grid[y][x] = "P" if v < half * 0.35 and u < 0.45 else "p"
                elif d <= 4.9 and (x + y + k) % 2 == 0:
                    grid[y][x] = "&"
        for _ in range(4):  # motes of dark light shed behind
            x, y = r.randrange(0, 12), r.randrange(1, h - 1)
            if grid[y][x] == ".":
                grid[y][x] = "M" if r.random() < 0.4 else "&"
        frames.append(["".join(row) for row in grid])
    return frames


def nova_ring(w: int, h: int, cx: float, cy: float, rx: float, k: int, fade: float = 0.0,
              flat: float = 2.0) -> Sprite:
    """A ring of dark energy on the floor (an ellipse half as tall as wide) with spikes
    bursting up from it."""
    ry = rx / flat
    out = blank(w, h)
    inner = ring(w, h, cx, cy, rx - 2, ry - 1, "&", thickness=2)
    out = over(out, [ "".join(ch if (x + y) % 2 == 0 else "." for x, ch in enumerate(row)) for y, row in enumerate(inner)])
    out = over(out, ring(w, h, cx, cy, rx, ry, "P", thickness=2))
    out = over(out, ring(w, h, cx, cy, rx, ry, "M", thickness=1))
    grid = [list(row) for row in out]
    n = max(6, int(rx))
    for i in range(n):
        ang = i / n * 2 * math.pi + k * 0.2
        x = int(cx + rx * math.cos(ang))
        y = int(cy + ry * math.sin(ang))
        tall = 2 + (i * 7 + k) % 4
        for t in range(tall):
            yy = y - t
            if 0 <= yy < h and 0 <= x < w:
                grid[yy][x] = "M" if t == tall - 1 else "p" if t == 0 else "P"
    out = ["".join(row) for row in grid]
    return dissolve(out, fade) if fade else out


def nova_effect() -> list[Sprite]:
    """64 x 40, its middle on the lich's shadow: the burst rolling out across the floor."""
    w, h = 64, 40
    sizes = [(6, 0.0), (12, 0.0), (18, 0.0), (23, 0.15), (27, 0.4), (29, 0.7)]
    return [nova_ring(w, h, 32, 22, rx, k, fade) for k, (rx, fade) in enumerate(sizes)]


def summon_circle(w: int, h: int, k: int, sweep: float = 360.0) -> Sprite:
    """A runic circle on the floor: two rings, runes turning between them, a glyph in the
    middle; sweep draws only that many degrees of it (it burning in)."""
    cx, cy = w / 2, h / 2
    rx, ry = w / 2 - 2, h / 2 - 2
    a1 = sweep if sweep < 360 else 360
    out = blank(w, h)
    glow = disc(w, h, cx, cy, rx - 1, ry - 1, "&")
    glow = ["".join(ch if (x + 2 * y + k) % 5 == 0 else "." for x, ch in enumerate(row)) for y, row in enumerate(glow)]
    if sweep >= 360:
        out = over(out, glow)
    bright = "M" if k % 2 == 0 else "I"
    out = over(out, ring(w, h, cx, cy, rx, ry, "P", thickness=1.5, a0=0, a1=a1))
    out = over(out, ring(w, h, cx, cy, rx, ry, bright if sweep >= 360 else "M", thickness=0.9, a0=0, a1=a1))
    out = over(out, ring(w, h, cx, cy, rx * 0.72, ry * 0.72, "P", thickness=1.0, a0=0, a1=a1))
    grid = [list(row) for row in out]
    runes = 10
    for i in range(runes):  # rune ticks between the rings, turning with k
        ang = (i / runes * 360 + k * 9) % 360
        if ang > a1:
            continue
        rad = math.radians(ang)
        x = cx + rx * 0.86 * math.cos(rad)
        y = cy - ry * 0.86 * math.sin(rad)
        for dx, dy, ch in ((0, 0, "M"), (1, 0, "P"), (0, -1, "P") if i % 2 else (0, 1, "P")):
            xx, yy = int(x + dx), int(y + dy)
            if 0 <= xx < w and 0 <= yy < h:
                grid[yy][xx] = ch
    if sweep >= 360:  # the glyph: a lozenge with a bar through it
        for dx, dy in ((0, -2), (-3, 0), (3, 0), (0, 2), (-1, -1), (1, -1), (-2, 0), (2, 0), (-1, 1), (1, 1)):
            grid[int(cy + dy)][int(cx + dx)] = "M"
        for dx in range(-5, 6):
            if abs(dx) > 3:
                grid[int(cy)][int(cx + dx)] = "P"
        grid[int(cy)][int(cx)] = bright
    return ["".join(row) for row in grid]


def summon_effect() -> list[Sprite]:
    """48 x 24, flat on the floor: the circle burns in round its rim, then turns and
    pulses. Eight frames; loop the last four while the dead keep rising."""
    return [summon_circle(48, 24, k, s) for k, s in enumerate([90, 180, 270, 360, 360, 360, 360, 360])]


def wisps(k: int, seed: int, n: int = 8, cx: float = 24, spread_: float = 16, low: float = 44,
          height: float = 30, letters: str = "&;") -> Sprite:
    r = rng(seed)
    grid = [["."] * W for _ in range(H)]
    for i in range(n):
        x0 = cx + r.uniform(-spread_, spread_)
        t = (r.uniform(0, 1) + k * 0.15) % 1.0
        x, y = int(x0 + math.sin(t * 5 + i)), int(low - t * height)
        if 0 <= y < H and 0 <= x < W:
            grid[y][x] = letters[i % len(letters)]
            if y + 1 < H and grid[y + 1][x] == ".":
                grid[y + 1][x] = letters[0]
    return ["".join(row) for row in grid]


def cracked(sprite: Sprite) -> Sprite:
    """Cracks through the skull and the soul-gem: dark lines over the bone and glass."""
    grid = [list(row) for row in sprite]
    for y in range(H):
        for x in range(W):
            if grid[y][x] in "CI" and (x + y) % 3 == 0:
                grid[y][x] = "K"
            elif grid[y][x] in "WL" and (x * 7 + y * 3) % 11 == 0:
                grid[y][x] = "D"
    return ["".join(row) for row in grid]


def floor_layer(sprite: Sprite, top: int, left: int) -> Sprite:
    return fill(W, H, [(sprite, top, left)])


# ---------------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------------


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "attack2": {}, "special": {}, "death": {},
    }
    hover = [0, -1, -1, 0]
    for view in ("down", "up", "right"):
        rest = REST[view]
        base = pose(view)
        fx, fy = rest["free"]
        gx, gy = rest["grip"]
        facing = {"down": (0, 1), "up": (0, -1), "right": (1, 0)}[view]
        side = -1 if view == "up" else 1  # which way the casting arm lifts outward

        # Idle: it hovers, the tatters drift, the soul-gem breathes light
        animations["idle"][view] = Anim(
            [pose(view, k, hover[k], gem="I" if k == 2 else "") for k in range(4)], fps=6,
        )

        # Walk: a glide. The body bobs, the hem streams back from the way it goes
        trail = -2 if view == "right" else 0
        glide = [0, -1, -1, -1, 0, 0, -1, 0]
        animations["walk"][view] = Anim(
            [pose(view, 2 * f, glide[f], sway_=trail + (0 if view == "right" else (1 if f < 4 else -1)))
             for f in range(8)],
            fps=8,
        )

        # Attack: the death bolt. Draw back the hand, a bolt swells in it, thrust, loose
        if view == "right":
            back, thrust, recoil = (27.0, 21.0), (39.0, 22.0), (35.0, 25.0)
        elif view == "down":
            back, thrust, recoil = (39.0, 20.0), (30.0, 30.0), (34.0, 28.0)
        else:
            back, thrust, recoil = (9.0, 20.0), (17.0, 14.0), (13.0, 22.0)

        def orb_at(sprite: Sprite, hand: tuple, dy: int = 0, push: int = 0) -> Sprite:
            ox = int(hand[0]) + facing[0] * (3 + push) - len(sprite[0]) // 2
            oy = int(hand[1]) + LIFT + dy + facing[1] * (2 + push) - len(sprite) // 2 - (1 if view == "right" else 0)
            return floor_layer(sprite, oy, ox)

        windup = pose(view, 0, -1, free=back, eyes="I")
        animations["attack"][view] = Anim(
            [
                pose(view, 0, -1, free=back),
                over(windup, orb_at(ORB, back, -1)),
                over(pose(view, 1, -1, free=back, eyes="I", gem="I"), orb_at(ORB_BIG, back, -1)),
                over(pose(view, 2, 0, free=thrust, eyes="I"), orb_at(ORB_BIG, thrust, 0, 1)),
                over(pose(view, 3, 0, free=thrust), orb_at(ORB, thrust, 0, 9)),
                pose(view, 0, 0, free=recoil),
                base,
            ],
            fps=10, loop=False,
        )

        # Attack 2: the nova. Rise, staff high and the free hand up, dark power gathers,
        # slam the staff down, the burst rolls out across the floor
        up_hand = (fx + side * 3, 14.0) if view != "right" else (28.0, 12.0)
        high = (gx, gy - 1)
        risen = pose(view, 1, -2, free=up_hand, grip=high, eyes="I")
        charged = over(risen, glow_edge(risen, "K", "&"))
        slam = pose(view, 2, 1, free=(fx, fy - 2), grip=(gx, gy + 2), gem="I")
        burst = [floor_layer(nova_ring(W, 14, 24, 7, rx, k, fade, flat=3.4), 33, 0)
                 for k, (rx, fade) in enumerate([(8, 0.0), (14, 0.0), (20, 0.35)])]
        animations["attack2"][view] = Anim(
            [
                pose(view, 0, -1, free=up_hand, grip=(gx, gy - 1)),
                risen,
                over(charged, wisps(1, 3, 10, cx=24, spread_=14, low=36, height=26, letters="&M")),
                over(slam, burst[0]),
                over(pose(view, 3, 1, free=(fx, fy - 2), grip=(gx, gy + 2)), burst[1]),
                over(pose(view, 0, 0, free=(fx, fy - 1), grip=(gx, gy + 1)), burst[2]),
                pose(view, 1, -1),
                base,
            ],
            fps=10, loop=False,
        )

        # Special, raise dead: staff lifted high, a circle burns into the floor, the dead
        # claw up out of it
        lifted = (gx, gy - 2)
        open_hand = (fx + side * 3, fy - 6) if view != "right" else (36.0, 24.0)

        def circle(k: int, sweep: float) -> Sprite:
            return floor_layer(summon_circle(44, 12, k, sweep), 36, 2)

        def hands_up(n: int) -> Sprite:
            # Bony hands clawing up at the circle's rim, n rows of them showing
            layer = blank(W, H)
            for x, y0 in ((1, 43), (42, 43), (8, 46), (35, 46)):
                part = BONE_HAND[:n]
                layer = over(layer, floor_layer(part, y0 - n, x))
            return layer

        def summoning(k: int, sweep: float, rising: int, staff: tuple = lifted) -> Sprite:
            f = pose(view, k, -1, free=open_hand, grip=staff, gem="I" if k % 2 else "", eyes="I")
            f = fill(W, H, [(circle(k, sweep), 0, 0), (f, 0, 0)])
            if k % 2:  # the staff's gem flares
                sx = rest["staff_x"] + int(staff[0] - gx)
                f = over(f, floor_layer(FLARE, 4 - 1 + int(staff[1] - gy), sx - 2))
            if rising:
                f = over(f, hands_up(rising))
            return over(f, wisps(k, 5, 6, cx=24, spread_=18, low=44, height=20))

        animations["special"][view] = Anim(
            [
                pose(view, 0, -1, free=(fx + side * 2, fy - 3), grip=(gx, gy - 1)),
                summoning(1, 120, 0),
                summoning(2, 240, 0),
                summoning(3, 360, 0),
                summoning(4, 360, 2),
                summoning(5, 360, 3),
                summoning(6, 360, 4),
                summoning(7, 360, 4),
                over(fill(W, H, [(dissolve(circle(0, 360), 0.5), 0, 0), (pose(view, 0, -1, grip=(gx, gy - 1)), 0, 0)]),
                     dissolve(hands_up(4), 0.5)),
                base,
            ],
            fps=8, loop=False,
        )

        # Death: the gem cracks, a cold flash, the robes collapse, the crown falls, fade
        crack = cracked(pose(view, 0, 0, eyes="D", gem="W"))
        flash = over(silhouette(base, "I"), only(glow_edge(base, "K", ";"), ";"))
        slump = squash(cracked(pose(view, 1, 3, eyes="D")), 9, 30)
        heap = union(W, H, [(HEAP, 37, 11)])
        crown = CROWN_R if view == "right" else CROWN_D if view == "down" else CROWN_U
        skull = SKULL_R if view == "right" else SKULL_D if view == "down" else SKULL_U
        lying = stamp(heap, swap(skull, {"C": "D", "I": "D"}), 38 - len(skull), 13)
        animations["death"][view] = Anim(
            [
                crack,
                flash,
                over(slump, wisps(0, 8, 6, cx=24, spread_=10, low=30, height=12, letters=";&")),
                over(stamp(lying, crown, 22, 30), wisps(1, 8, 8, cx=24, spread_=12, low=34, height=20, letters=";&")),
                over(stamp(lying, crown, 34, 28), wisps(2, 8, 8, cx=24, spread_=12, low=30, height=22, letters=";&")),
                stamp(dissolve(lying, 0.65), crown, 34, 28),
            ],
            fps=8, loop=False,
        )

    write_character(
        Character(
            name="lich",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="The final boss: a floating skeletal sorcerer-king in tattered purple robes, "
            "jagged gold crown, cold blue eye-lights, a soul-gem in its open ribcage and a "
            "horned staff. Attack: death bolt (fx death_bolt). Attack 2: staff-slam nova "
            "(fx nova). Special: raise dead (lifts the staff, a summoning circle burns into "
            "the floor and bony hands claw up; fx summon_circle).",
            shadow=22,
            effects=(
                Effect("death_bolt", death_bolt_effect(), fps=10, loop=True,
                       notes="24x12 bolt flying right (rotate to aim): a skull of cold light in a "
                       "purple aura with a tail of dark flame."),
                Effect("nova", nova_effect(), fps=10, loop=False,
                       notes="64x40, centre on the lich's shadow: a ring of dark energy rolling out "
                       "across the floor with spikes bursting up from it, then fading."),
                Effect("summon_circle", summon_effect(), fps=8, loop=False,
                       notes="48x24, flat on the floor under the summons: burns in round its rim "
                       "(frames 0-3), then turns and pulses (4-7; loop those while it holds)."),
            ),
        )
    )
