"""Medusa: her stare turns you to stone.

A gorgon: a woman's torso in a gold band and gold armbands, rising from a coiled green
snake tail, with a crown of writhing hair-snakes and glowing green eyes. Walk is a
slither: the coils ripple under her. attack is a tail lash: the tip rears up behind and
cracks forward with a smear. Special, "stone stare": the hair-snakes rear and hiss,
her eyes flash white and gold, and a pale ring-wave rolls out (Effect "stare"). She
dies the way her victims do: turned to stone, cracking and crumbling.

How it's built:
- The torso is drawn by hand per view (down and up as symmetric halves).
- The tail is a 3D path (a 1.35-turn helix ending in a tapering tip) drawn by tube()
  from _batch_c for each view, so the coils overlap correctly from every side. The
  ripple and the lash are changes to that path.
- The hair-snakes are tiny tubes too, rooted round the scalp; a phase writhes them and
  rear straightens them up.
"""

import math
import random

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    blank,
    dissolve,
    mirror,
    nearest_in,
    paste,
    recolour,
    shift,
    silhouette,
    underlay,
    write_character,
)
from enemies._batch_c import check_sprites, compose, dots, ol, project, ring, scales, sym, tube

W, H = 48, 48
SKIN = {"S": "T", "T": "B", "Y": "O"}

# ---------------------------------------------------------------------------------
# Torsos: hair mass, face, gold band, armbands, hands. Down and up are 18 wide.
# ---------------------------------------------------------------------------------

DOWN_HALF = [
    # 012345678
    "......VVV",  # 0 scalp, the snakes' roots
    ".....VVVV",
    "....VVSSS",  # hairline
    "....VSBSS",  # brows
    "....VKESS",  # eyes, lined dark
    "....vSSSS",  # 5
    ".....SSST",
    ".....TSFr",  # lips
    "......TSS",
    ".......TS",  # neck
    "....SSSSS",  # 10 shoulders
    "..SSSSSSS",
    ".SSSTYYYY",  # the gold band
    ".SSTYOYYO",
    ".YYSTTYYY",  # armbands
    ".OOSSTSSS",  # 15
    ".SSTSSSSS",
    ".STSSSSSS",
    ".ST.TSSSS",
    ".ST..VVVV",  # scales from the hips
    ".SS..VEVV",  # 20
    "STS..VVVV",  # hands
    "W.W......",  # nails
]

UP_HALF = [
    "......VVV",
    ".....VVVV",
    "....VVVVV",
    "....VEVVV",
    "....VVVVV",
    "....vVVEV",  # 5
    ".....vVVV",
    ".....vVVV",
    "......vVV",
    ".......TS",  # neck
    "....SSSSS",  # 10
    "..SSSSSST",
    ".SSSTYYYY",  # the band's clasp at the back
    ".SSTSSSST",
    ".YYSTSSST",
    ".OOSSSSST",  # 15
    ".SSTSSSST",
    ".STSSSSST",
    ".ST.TSSST",
    ".ST..VVVV",
    ".SS..VVVV",  # 20
    "STS..VVVV",
    "W.W......",
]

RIGHT_TORSO = [
    # 0123456789ABC
    "...VVVVV.....",  # 0
    "..VVVVVVV....",
    "..VVVVSSS....",
    "..VVVSSBSS...",
    "..VVVSSKES...",  # eye, lined dark
    "..vVVSSSSSS..",  # 5 nose
    "..vVVTSSSS...",
    "..vVvTSSFr...",  # lips
    "...vv.TSSS...",
    "......TSS....",  # neck
    "....SSSSSS...",  # 10
    "...SSSSSSSS..",
    "..TSSSYYYYYY.",  # the gold band over the bust
    "..TSSSYOYYYO.",
    "..TSSSSSSSS..",
    "..TTSSSSSS...",  # 15
    "...TSSSSSS...",
    "...TSSSSSS...",
    "...VVVVVVV...",  # scales from the hips
    "...VVEVVVV...",
    "...VVVVVVV...",  # 20
]

# The near arm in profile, hanging with its armband; at (10, 5)
ARM_RIGHT = [
    "SS..",
    "STS.",
    "YYO.",
    "STS.",
    "STT.",
    ".ST.",
    ".ST.",
    ".ST.",
    ".SS.",
    ".STS",
    "..WW",
]

check_sprites(globals())

DOWN_TORSO = sym(DOWN_HALF, SKIN)
UP_TORSO = sym(UP_HALF, SKIN)
TORSO = {"down": DOWN_TORSO, "up": UP_TORSO, "right": RIGHT_TORSO}

# Where each view's eyes are in the torso fill, for the stare's flash
EYES = {"down": [(5, 6), (5, 11)], "up": [], "right": [(4, 8)]}

# ---------------------------------------------------------------------------------
# The tail
# ---------------------------------------------------------------------------------


def _smooth(a: float, b: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _tip(kind: str, u: float, ax: float) -> tuple[float, float, float]:
    """The lashing tip's curve, u from its root (0) to its point (1)."""
    if kind == "raise":  # reared up behind her
        return ax + u * 4, 4 + u * 22 + 3 * math.sin(u * 3), -4 - u * 10 + 6 * u * u
    return ax - u * 6, 3 + u * 6, -2 + u * 22  # strike: flung out forward and low


def tail_path(phase: float = 0.0, ripple: float = 0.8, lash: float = 0.0, n: int = 170) -> list:
    """The tail in creature space (x to her left, y up, z forward): it leaves the hips,
    winds down and out 1.35 turns and ends in a tip that curls up off the floor. ripple
    runs a wave through the coils. lash poses the tip: 0 at rest, 1 reared up behind,
    2 cracked out forward, blending between."""
    ytop = 16.0
    pts = []
    tip_from = 0.74
    ax = 1.5 + 11.5 * _smooth(0, 0.5, tip_from)
    for i in range(n):
        s = i / (n - 1)
        r = 3.4 - 0.6 * s if s < 0.78 else 2.93 - 2.0 * (s - 0.78) / 0.22
        theta = math.radians(-60) + 2 * math.pi * 1.35 * s
        rad = 1.5 + 11.5 * _smooth(0, 0.5, s) + (s > 0.82) * (s - 0.82) * 25
        rad += ripple * math.sin(phase + s * 14)
        y = r + (ytop - r) * max(0.0, 1 - s / 0.55) ** 1.4 + ripple * 0.4 * max(0.0, math.sin(phase + s * 9))
        if s > 0.9:
            y += (s - 0.9) * 30
        x, z = rad * math.cos(theta), rad * math.sin(theta)
        if lash and s > tip_from:
            u = (s - tip_from) / (1 - tip_from)
            rest = (x, y, z)
            raised = _tip("raise", u, ax)
            struck = _tip("strike", u, ax)
            a, b, k = (rest, raised, lash) if lash <= 1 else (raised, struck, lash - 1)
            # the blend eases in from the root so the tip leaves the coil smoothly
            k = k * _smooth(0, 0.25, u) if lash <= 1 else k
            x, y, z = (a[j] + (b[j] - a[j]) * k for j in range(3))
        pts.append((x, y, z, r))
    return pts


TAIL_SHADE = scales("V", "E", "v", "T")


def tail(view: str, phase: float = 0.0, ripple: float = 0.8, lash: float = 0.0) -> tuple[Sprite, list]:
    return tube(W, H, project(tail_path(phase, ripple, lash), view, W / 2, 40), TAIL_SHADE)


# ---------------------------------------------------------------------------------
# The hair-snakes
# ---------------------------------------------------------------------------------

# Roots round the scalp, per view: (x, y in torso fill, angle out in degrees, length).
ROOTS = {
    "down": [(4, 4, 200, 8), (4, 1, 160, 7), (6, 0, 125, 7), (9, 0, 95, 6), (12, 0, 60, 7),
             (14, 1, 25, 7), (14, 4, -20, 8)],
    "up": [(4, 4, 200, 8), (4, 1, 160, 7), (6, 0, 125, 7), (9, 0, 95, 6), (12, 0, 60, 7),
           (14, 1, 25, 7), (14, 4, -20, 8), (7, 4, 230, 6), (11, 4, -50, 6)],
    "right": [(2, 4, 210, 8), (2, 1, 170, 8), (3, 0, 135, 7), (5, 0, 105, 6), (7, 0, 75, 6),
              (3, 6, 235, 7)],
}
HAIR_SHADE = scales("V", "E", "v", rings=20)


def hair(view: str, phase: float = 0.0, rear: float = 0.0) -> tuple[list, list[tuple[float, float]]]:
    """Screen samples for the hair-snakes in torso-fill coordinates, and each head's
    centre. rear 0 lets them curl and writhe; 1 stands them up straight and tall."""
    samples = []
    heads = []
    for k, (x0, y0, angle, length) in enumerate(ROOTS[view]):
        a = math.radians(angle)
        # rearing swings each snake up towards the vertical and lengthens it
        up = math.radians(90)
        a = a + (up - a) * 0.35 * rear
        length = length * (1 + 0.35 * rear)
        m = 14
        px, py = x0 + 0.5, y0 + 0.5
        curl = 1.2 * (1 - rear) * (1 if k % 2 else -1)
        for i in range(m):
            u = i / (m - 1)
            bend = a + curl * u + 0.5 * (1 - 0.6 * rear) * math.sin(phase + k * 1.7 + u * 4)
            step = length / (m - 1)
            if i:
                px += step * math.cos(bend)
                py -= step * math.sin(bend)
            r = 1.05 if u < 0.85 else 1.45
            samples.append((px, py, 0.0, r, k + u * 0.05))
        heads.append((px, py))
    return samples, heads


def head_details(view: str, heads: list[tuple[float, float]], rear: float) -> list[tuple[int, int, str]]:
    """Eye and, when rearing, tongue pixels for each snake head."""
    out = []
    for hx, hy in heads:
        out.append((int(hy), int(hx), "Y"))
        if rear > 0.5:
            out.append((int(hy) - 2, int(hx), "R"))
    return out


# ---------------------------------------------------------------------------------
# Composing a pose
# ---------------------------------------------------------------------------------

TORSO_AT = {"down": (5, 15), "up": (5, 15), "right": (6, 17)}  # fill (row, col) of the torso's top left


def medusa(view: str, phase: float = 0.0, ripple: float = 0.8, lash: float = 0.0, rear: float = 0.0,
           dx: int = 0, dy: int = 0, eyes: str = "") -> Sprite:
    """Medusa in the cell: the tail behind and below, the torso on it, the hair round her
    head; eyes, if given, overrides the eye letter (the stare's flash)."""
    coil, zs = tail(view, phase, ripple, lash)
    torso = TORSO[view]
    if eyes:
        torso = [list(r) for r in torso]
        for r, c in EYES[view]:
            torso[r][c] = eyes
        torso = ["".join(r) for r in torso]
    r0, c0 = TORSO_AT[view]
    # the torso's own outline, with its hips sunk into the coil's top
    t_out = ol(torso)
    hs, heads = hair(view, phase, rear)
    hs = [(sx + c0, sy + r0, d, r, t) for sx, sy, d, r, t in hs]
    hair_sprite, _ = tube(W, H, hs, HAIR_SHADE)
    hair_sprite = paste(hair_sprite, dots(W, H, head_details(view, [(x + c0, y + r0) for x, y in heads], rear)), 0, 0)
    out = coil
    out = paste(out, t_out, r0 - 1, c0 - 1)
    if view == "right":
        out = paste(out, ol(ARM_RIGHT), r0 + 10 - 1, c0 + 5 - 1)
    # the hair goes behind the head, and the coil's nearest loop in front of the hands
    out = underlay(out, hair_sprite, 0, 0)
    front = [[ch if zs[y][x] is not None and zs[y][x] > 6 else "." for x, ch in enumerate(row)]
             for y, row in enumerate(coil)]
    out = paste(out, ["".join(r) for r in front], 0, 0)
    out = shift(out, dx, dy + 5)
    return out


def smear(view: str, a: float, b: float, steps: int = 9) -> Sprite:
    """The trail the tail tip cuts between lash poses a and b: a band of mist with a
    bright leading rim."""
    pts = []
    for k in range(steps):
        lash = a + (b - a) * k / (steps - 1)
        x, y, z, _ = tail_path(0.0, 0.8, lash)[-4]
        sx, sy, *_ = project([(x, y, z, 1.0)], view, W / 2, 40)[0]
        pts.append((sx, sy + 5))
    out = blank(W, H)
    for k, (sx, sy) in enumerate(pts):
        for oy, ox in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
            yy, xx = int(sy) + oy, int(sx) + ox
            if 0 <= yy < H and 0 <= xx < W:
                letter = "W" if k == steps - 1 or (k > steps // 2 and (oy, ox) == (0, 0)) else ":"
                if out[yy][xx] != "W":
                    out = paste(out, [letter], yy, xx)
    return out


def stare_rings(cy: int, cx: int, r: float, letter: str = "W") -> tuple[Sprite, Sprite]:
    """A pale ring-wave round her head, flattened to the floor plane: (the far half,
    which goes behind her, the near half, which goes in front)."""
    halves = []
    for a0, a1 in ((0, 180), (180, 360)):
        halves.append(compose(W, H, [
            (ring(W, H, cx, cy, r, r * 0.6, ":", 2.0, letter, a0, a1), 0, 0),
            (dissolve(ring(W, H, cx, cy, r - 3, (r - 3) * 0.6, ":", 1.0, "L", a0, a1), 0.4), 0, 0),
        ]))
    return halves[0], halves[1]


def with_rings(body: Sprite, rings: tuple[Sprite, Sprite], fade: float = 0.0) -> Sprite:
    back, front = (dissolve(r, fade) for r in rings)
    return paste(underlay(body, back, 0, 0), front, 0, 0)


def stare_effect() -> list[Sprite]:
    """The stone stare's ring-wave rolling out: pale rings that widen and thin, with
    glints of gold. Centre it on her eyes."""
    frames = []
    for n in range(6):
        r = 6 + 6 * n
        f = compose(80, 48, [
            (ring(80, 48, 40, 24, r, r * 0.6, ":", 2.5, "W"), 0, 0),
            (ring(80, 48, 40, 24, max(2, r - 6), max(2, r - 6) * 0.6, ":", 1.0, "L"), 0, 0),
        ])
        f = dissolve(f, min(0.75, 0.13 * n), n, 0)
        glints = [(24 + round(r * 0.6 * math.sin(a)), 40 + round(r * math.cos(a)), "*")
                  for a in (0.5 + n * 0.3, 2.2 + n * 0.3, 3.9 + n * 0.3, 5.3 + n * 0.3)]
        frames.append(paste(f, dots(80, 48, glints), 0, 0))
    return frames


STONE = nearest_in("KDGLW")


def petrify(sprite: Sprite, from_row: int) -> Sprite:
    """Rows from from_row down turned to grey stone."""
    return sprite[:from_row] + recolour(sprite[from_row:], STONE)


def cracks(sprite: Sprite, seed: int) -> Sprite:
    """Dark crack lines across the stone where it is solid."""
    rnd = random.Random(seed)
    grid = [list(r) for r in sprite]
    for _ in range(7):
        y, x = rnd.randrange(8, 44), rnd.randrange(12, 36)
        for _ in range(6):
            if 0 <= y < H and 0 <= x < W and grid[y][x] in "DGLW":
                grid[y][x] = "D" if grid[y][x] in "LW" else "K"
            y += rnd.choice((1, 1, 0))
            x += rnd.choice((-1, 1))
    return ["".join(r) for r in grid]


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {"idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {}}
    for view in ("down", "up", "right"):
        base = medusa(view)

        # Idle: the hair writhes and the coils breathe
        animations["idle"][view] = Anim(
            [medusa(view, phase=k * math.pi / 2, ripple=0.4) for k in range(4)], fps=6
        )

        # Walk: a slither, a wave running round the coils as she sways over them
        animations["walk"][view] = Anim(
            [medusa(view, phase=k * math.pi / 4, ripple=1.3, dx=round(1.4 * math.sin(k * math.pi / 4)))
             for k in range(8)],
            fps=9,
        )

        # Attack, tail lash: the tip rears up behind her, hangs, cracks forward with a
        # smear, and slides back into the coil
        strike = paste(medusa(view, lash=2.0), smear(view, 1.0, 2.0), 0, 0)
        animations["attack"][view] = Anim(
            [
                medusa(view, lash=0.5),
                medusa(view, lash=1.0),
                medusa(view, lash=1.0, rear=0.3, dy=-1),
                strike,
                medusa(view, lash=2.0),
                medusa(view, lash=0.6),
                base,
            ],
            fps=10,
            loop=False,
        )

        # Special, stone stare: the hair rears and hisses, the eyes flash white and gold,
        # a pale ring-wave rolls out from her gaze
        r0, c0 = TORSO_AT[view]
        cy, cx = r0 + 4 + 5, c0 + (8 if view == "right" else 9)
        glare = medusa(view, rear=1.0, eyes="W")
        glow = dots(W, H, [(cy - 1, cx - 3, "*"), (cy - 1, cx + 2, "*"), (cy, cx - 4, "*"), (cy, cx + 3, "*"),
                           (cy + 1, cx - 3, "*"), (cy + 1, cx + 2, "*")]) if view != "up" else blank(W, H)
        animations["special"][view] = Anim(
            [
                medusa(view, rear=0.5, ripple=0.2),
                medusa(view, rear=1.0, eyes="Y", dy=-1),
                paste(glare, glow, 0, 0),
                with_rings(paste(glare, glow, 0, 0), stare_rings(cy, cx, 6)),
                with_rings(glare, stare_rings(cy + 2, cx, 11)),
                with_rings(medusa(view, rear=1.0, eyes="Y"), stare_rings(cy + 4, cx, 16)),
                with_rings(medusa(view, rear=0.7), stare_rings(cy + 6, cx, 21), 0.5),
                base,
            ],
            fps=8,
            loop=False,
        )

        # Death: struck, then her own curse takes her: stone creeps up from the tail,
        # cracks, and she crumbles to dust
        stone = recolour(base, STONE)
        cracked = cracks(stone, 3)
        rubble = shift(dissolve(cracked, 0.45, 1, 2), 0, 2)
        dust = dots(W, H, [(40, 14, ":"), (42, 20, ":"), (38, 30, ":"), (43, 34, ":"), (36, 24, ":")])
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                petrify(base, 34),
                petrify(base, 20),
                cracked,
                paste(rubble, dust, 0, 0),
                paste(dissolve(shift(cracked, 0, 4), 0.8, 2, 1), dust, 0, 0),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="medusa",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="A gorgon: a woman's torso with gold bands on a coiled green snake tail, a crown of hair-snakes "
            "and glowing green eyes. Slithers. attack: tail lash. Special: stone stare (hair-snakes rear, eyes "
            "flash, a pale ring-wave rolls out and petrifies).",
            shadow=28,
            effects=(
                Effect("stare", stare_effect(), fps=10, loop=False,
                       notes="Expanding pale rings on the floor plane; centre on Medusa's eyes."),
            ),
        )
    )
