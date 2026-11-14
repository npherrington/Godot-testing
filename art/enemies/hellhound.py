"""Hellhound: fire breath.

A lean, high-shouldered hound with a charcoal hide split by glowing ember cracks, a
mane and tail of live flame and burning yellow eyes.
Special, "fire breath": it rears, sucks in, and pours a cone of flame from its jaws.

How it's built:
- Every view is a set of FILLS (colour only) pasted together and outlined as one
  silhouette by union(). The head is stamped on with its own outline so the ears and
  jaw read against the mane. Light from the top left comes from shade().
- The legs are drawn from joint positions (two-bone IK, see leg_r), so the walk is a
  real diagonal trot: near-front with far-hind, far-front with near-hind.
- Mane and tail flames have three flicker variants that cycle through every animation.
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
    shear,
    silhouette,
    squash,
    write_character,
)
from enemies._batch_d import (
    behind,
    capsules,
    disc,
    fill,
    flames,
    ik,
    over,
    put,
    rng,
    shade,
    spr,
    stamp,
    swap,
    union,
)

W, H = 48, 48
GROUND = 43.5  # the paws' centre line: their fill ends on row 44, the outline on the baseline

# Embers going out: what death and the dying flames recolour to
COOL = {"Y": "O", "O": "R", "R": "r", "W": "Y"}
ASH = {"Y": "r", "O": "r", "R": "D", "W": "O", "G": "D"}
HOT = {"R": "O", "O": "Y", "r": "R"}  # flames flaring as it draws breath

# ---------------------------------------------------------------------------------
# Right: profile, facing right
# ---------------------------------------------------------------------------------

HEAD_R = spr("""
    .DD.............
    .DDD............
    DDDDD...........
    .DDDDDDDDD......
    .DDDDDDKKDDD....
    DDDDDDOYYDDDDDD.
    DDDDDDDDDDDDDDDK
    DDDDDDDDDDDDDDDK
    DDDDDDDrrrKKKKK.
    rDDDDDDDDWDDDW..
    .rrDDDDDDrrrr...
    ...rrrrr........
""")

HEAD_R_OPEN = spr("""
    .DD.............
    .DDD............
    DDDDD...........
    .DDDDDDDDD......
    .DDDDDDKKDDD....
    DDDDDDOYYDDDDDD.
    DDDDDDDDDDDDDDDK
    DDDDDDDDDWrWrWDK
    DDDDDDrOOYYYO...
    rDDDDrOYYYO.....
    .rDDDDrWrWrW....
    ..rrDDDDDDDDr...
    ....rrrrrrr.....
""")

# Jaws at their widest: the breath
HEAD_R_ROAR = spr("""
    .DD.............
    .DDD............
    DDDDD...........
    .DDDDDDDDD......
    .DDDDDDKKDDD....
    DDDDDDOYYDDDDDD.
    DDDDDDDDDDDDDDDK
    DDDDDDDDDWrWrWDK
    DDDDDDrOYYYYO...
    rDDDDrOYYWWYY...
    .rDDDrOYYYYYO...
    ..rDDDrWrWrW....
    ...rrDDDDDDDr...
    .....rrrrrr.....
""")

BODY_R = spr("""
    .......................DD......
    ....................DDDDDDD....
    ..................DDDDDDDDDDD..
    ................DDDDDDDDDDDDDD.
    .............DDDDDDDDDDDDDDDDD.
    ...DDDDD..DDDDDDDDDDDDDDDDDDDDD
    .DDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
    DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
    DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
    DDDDDDDDDDDDDDDDDDDDDDDDDDDDDD.
    DDDDDDDDDDDDDDDDDDDDDDDDDDDDD..
    DDDDDDDDDDrrrDDDDDDDDDDDDDDDr..
    DDDDDDDDr....rDDDDDDDDDDDDDr...
    rDDDDDDr......rDDDDDDDDDDDr....
    .rDDDDr........rDDDDDDDDDr.....
    ..rDDr..........rDDDDDDDr......
    ...rr............rrrrrrr.......
""")

# Belly shading (r) and ember cracks (O, Y at the hottest points), in BODY_R coordinates
BODY_R_SHADE = [(11, 9), (11, 10), (10, 13), (11, 14), (12, 15), (12, 14)]
BODY_R_CRACKS = [(6, 3), (7, 4), (8, 4), (9, 5), (10, 5), (11, 4),
                 (7, 13), (8, 14), (9, 14), (8, 17), (9, 18), (10, 18), (11, 19),
                 (5, 23), (6, 24), (7, 24), (8, 25), (9, 25), (10, 24), (7, 20), (6, 19)]
BODY_R_HOT = [(8, 4), (9, 18), (7, 24), (8, 25)]

MANES_R = [
    spr("""
        ......R.........
        .....RR....R....
        R...RRO...RR....
        RR..ROR..ROR..R.
        .RR.ROOR.ROR.RR.
        .ROR.ROORROOR.R.
        ..ROROYOROYORROR
        ..ROOYYOOOYYOOR.
        ...OYYYYYYYYYYOR
        ....OYYYYYYYYYO.
    """),
    spr("""
        ................
        ....R......R....
        R...RR....RR....
        RR..ROR...ROR...
        .RR.ROOR.RROR.R.
        .ROR.ROORROOR.RR
        ..RORYYOROYOROR.
        ..ROOYYOOOYYOOR.
        ...OYYYYYYYYYYOR
        ....OYYYYYYYYYO.
    """),
    spr("""
        .......R........
        ......RR...R....
        .R...ROR...RR...
        RR..ROR...ROR..R
        .RR.ROR..ROOR.RR
        ..RORORRROOR.RR.
        ..ROROYOROYORROR
        ..ROOYYOOYYYOOR.
        ...OYYYYYYYYYYOR
        ....OYYYYYYYYYO.
    """),
]

# The tail curls up from the croup; its last third is on fire
TAILS_R = [
    spr("""
        ..R.....
        .RR.R...
        .RORR...
        RROYOR..
        ROYYOR..
        .OYYOR..
        .ROYO...
        ..DDD...
        ..DDD...
        ...DDD..
        ....DDD.
        .....DDD
        ......DD
    """),
    spr("""
        ...R....
        ..RR....
        .ROR.R..
        RROYRR..
        ROYYOR..
        .OYYOR..
        .ROYO...
        ..DDD...
        ..DDD...
        ...DDD..
        ....DDD.
        .....DDD
        ......DD
    """),
    spr("""
        .R......
        .RR..R..
        RORR.R..
        ROYOOR..
        ROYYOR..
        .OYYOR..
        .ROYO...
        ..DDD...
        ..DDD...
        ...DDD..
        ....DDD.
        .....DDD
        ......DD
    """),
]

BODY_TOP, BODY_LEFT = 16, 8
HEAD_AT = (17, 29)  # the head's top-left with the body at rest
ELBOW = (30.0, 30.5)  # where the near front leg leaves the chest
STIFLE = (11.5, 30.0)  # where the near hind leg leaves the haunch


def body_r() -> Sprite:
    b = put(BODY_R, BODY_R_SHADE, "r")
    b = put(b, BODY_R_CRACKS, "O")
    return put(b, BODY_R_HOT, "Y")


def leg_r(top: tuple[float, float], paw: tuple[float, float], l1: float, l2: float, bend: int) -> Sprite:
    """A profile leg from top to paw, the middle joint bent to bend's side; the front
    leg's wrist glows like the cracks."""
    joint = ik(top, paw, l1, l2, bend)
    px, py = paw
    segs = [
        (top[0], top[1], joint[0], joint[1], 1.4),
        (joint[0], joint[1], px, py - 0.5, 1.0),
        (px - 0.5, py, px + 1.8, py, 1.0),
    ]
    s = capsules(W, H, segs, "D")
    return put(s, [(int(joint[1]), int(joint[0]))], "O") if bend < 0 else s


def trot(anchor_x: float, t: float, stride: float = 4.0, lift: float = 4.0) -> tuple[float, float]:
    """The paw's position at phase t: on the ground sliding back for the first half,
    lifted and swinging forward for the second."""
    t %= 1.0
    if t < 0.5:
        return anchor_x + stride - 4 * stride * t, GROUND
    u = (t - 0.5) / 0.5
    return anchor_x - stride + 2 * stride * u, GROUND - lift * math.sin(math.pi * u)


def stand_paws(dx: int = 0) -> dict[str, tuple[float, float]]:
    return {
        "near_front": (ELBOW[0] + dx + 1, GROUND), "far_front": (ELBOW[0] + dx - 3, GROUND),
        "near_hind": (STIFLE[0] + dx - 2, GROUND), "far_hind": (STIFLE[0] + dx + 2, GROUND),
    }


def trot_paws(phase: float) -> dict[str, tuple[float, float]]:
    return {
        "near_front": trot(ELBOW[0], phase), "far_hind": trot(STIFLE[0] + 1, phase),
        "far_front": trot(ELBOW[0] - 3, phase + 0.5), "near_hind": trot(STIFLE[0] - 2, phase + 0.5),
    }


def right_pose(paws: dict, bx: int = 0, by: int = 0, head: Sprite = HEAD_R, hx: int = 0,
               hy: int = 0, flicker: int = 0, lean: int = 0, flames_map: dict = None) -> Sprite:
    """The profile: body moved (bx, by), head moved (hx, hy) more, lean shears the body
    (negative rears back), paws placed where given."""
    ex, ey = ELBOW[0] + bx, ELBOW[1] + by
    sx, sy = STIFLE[0] + bx, STIFLE[1] + by
    far = fill(W, H, [
        (shade(leg_r((ex - 3, ey), paws["far_front"], 7.5, 7.0, -1), "D", "D", "r"), 0, 0),
        (shade(leg_r((sx + 3, sy), paws["far_hind"], 8.0, 8.0, 1), "D", "D", "r"), 0, 0),
    ])
    near = fill(W, H, [
        (leg_r((ex, ey), paws["near_front"], 7.5, 7.0, -1), 0, 0),
        (leg_r((sx, sy), paws["near_hind"], 8.0, 8.0, 1), 0, 0),
    ])
    mane, tail = MANES_R[flicker % 3], TAILS_R[flicker % 3]
    if flames_map:
        mane, tail = swap(mane, flames_map), swap(tail, flames_map)
    upper = fill(W, H, [
        (tail, BODY_TOP - 7 + by, max(2 + bx, 1 - lean)),  # the tail never leaves the cell
        (body_r(), BODY_TOP + by, BODY_LEFT + bx),
        (mane, BODY_TOP - 7 + by, 21 + bx),
    ])
    if lean:
        upper = shear(upper, lean, 32 + by)
    body = shade(over(upper, near), "D", "G", "r")
    out = over(union(W, H, [(far, 0, 0)]), union(W, H, [(body, 0, 0)]))
    return stamp(out, shade(head, "D", "G", "r"), HEAD_AT[0] + by + hy, HEAD_AT[1] + bx + hx)


# ---------------------------------------------------------------------------------
# Down: facing the camera. The head is nearest and biggest; a crest of flame rises
# from the shoulders behind it, the haunches show either side of the chest.
# ---------------------------------------------------------------------------------

HEAD_D = spr("""
    .D..............D.
    .DD............DD.
    DDDD..........DDDD
    DrDDD........DDDrD
    DrrDDDDDDDDDDDDrrD
    .DDDDDDDDDDDDDDDD.
    .DDKDDDDDDDDDDKDD.
    .DDDKKDDDDDDKKDDD.
    .DDOYYDDDDDDYYODD.
    ..DDDDDDDDDDDDDD..
    ...DDDDDDDDDDDD...
    ....DDDDKKDDDD....
    ....rDDDKKDDDr....
    ....rWDrrrrDWr....
    .....rWrrrrWr.....
    ......rrrrrr......
""")

HEAD_D_OPEN = spr("""
    .D..............D.
    .DD............DD.
    DDDD..........DDDD
    DrDDD........DDDrD
    DrrDDDDDDDDDDDDrrD
    .DDDDDDDDDDDDDDDD.
    .DDKDDDDDDDDDDKDD.
    .DDDKKDDDDDDKKDDD.
    .DDOYYDDDDDDYYODD.
    ..DDDDDDDDDDDDDD..
    ...DDDDDKKDDDDD...
    ...rDWrrrrrrWDr...
    ...rOOYYYYYYOOr...
    ...rOYYYWWYYYOr...
    ...rrOOYYYYOOrr...
    ....rWrrrrrrWr....
    .....rrDDDDrr.....
    .......rrrr.......
""")

CHEST_D = spr("""
    ...DDDDDDDDDD...
    .DDDDDDDDDDDDDD.
    DDDDDDDDDDDDDDDD
    DDDDDDDDDDDDDDDD
    DDDDDDDDDDDDDDDD
    .DDDDDDDDDDDDDD.
    .DDDDDDDDDDDDDD.
    ..DDDDDrrDDDDD..
    ...DDDr..rDDD...
""")
CHEST_D_CRACKS = [(2, 2), (3, 3), (4, 3), (2, 13), (3, 12), (4, 12), (5, 7), (6, 8)]

HAUNCH_D = disc(7, 10, 3.5, 5, 3.5, 5, "D")

# The crest of flame behind the head, three flickers
CRESTS_D = [
    flames(28, 14, [(2.5, 8, 3), (6, 12, 3.5), (10.5, 14, 3.5), (14, 10, 3), (17.5, 14, 3.5),
                    (22, 11, 3.5), (25.5, 8, 3)]),
    flames(28, 14, [(2, 9, 3), (6.5, 13, 3.5), (10, 11, 3), (14, 14, 3.5), (18, 12, 3.5),
                    (21.5, 14, 3.5), (26, 7, 3)]),
    flames(28, 14, [(3, 7, 3), (6, 14, 3.5), (10.5, 12, 3.5), (14.5, 13, 3), (18, 10, 3),
                    (22, 13, 3.5), (25.5, 9, 3)]),
]

FRONT_X = (20.0, 28.0)  # the front legs' x, seen from in front or behind
HIND_X = (14.5, 33.5)  # the hind legs', further out


def leg_v(x: float, top: float, paw_y: float, near: bool) -> Sprite:
    """A leg seen from in front or behind: straight down, a paw at the bottom."""
    segs = [
        (x, top, x, paw_y - 1.0, 1.4 if near else 1.1),
        (x - 1.3, paw_y, x + 1.3, paw_y, 1.0),
    ]
    s = capsules(W, H, segs, "D")
    knee = int((top + paw_y) / 2)
    return put(s, [(knee, int(x))], "O") if near else s


def lift_of(t: float, lift: float = 3.0) -> float:
    t %= 1.0
    return 0.0 if t < 0.5 else lift * math.sin(math.pi * (t - 0.5) / 0.5)


def trot_lifts(phase) -> list[float]:
    """Paw lifts for (near left, near right, far left, far right): diagonals together."""
    if phase is None:
        return [0.0] * 4
    return [lift_of(phase), lift_of(phase + 0.5), lift_of(phase + 0.5), lift_of(phase)]


def down_pose(phase: float = None, by: int = 0, head: Sprite = HEAD_D, hy: int = 0,
              flicker: int = 0, flames_map: dict = None, extra: list = ()) -> Sprite:
    """Facing the camera. phase None stands; otherwise the trot's phase."""
    lifts = trot_lifts(phase)
    hind = fill(W, H, [
        (HAUNCH_D, 24 + by, 11), (HAUNCH_D, 24 + by, 30),
        (leg_v(HIND_X[0], 30 + by, 40.5 - lifts[2], False), 0, 0),
        (leg_v(HIND_X[1], 30 + by, 40.5 - lifts[3], False), 0, 0),
    ])
    hind = put(shade(hind, "D", "D", "r"), [(27 + by, 13), (28 + by, 13), (27 + by, 34), (28 + by, 34)], "O")
    crest = CRESTS_D[flicker % 3]
    if flames_map:
        crest = swap(crest, flames_map)
    upper = fill(W, H, [
        (crest, 8 + by, 10),
        (put(CHEST_D, CHEST_D_CRACKS, "O"), 27 + by, 16),
        (leg_v(FRONT_X[0], 32 + by, GROUND - lifts[0], True), 0, 0),
        (leg_v(FRONT_X[1], 32 + by, GROUND - lifts[1], True), 0, 0),
    ])
    body = shade(upper, "D", "G", "r")
    out = over(union(W, H, [(hind, 0, 0)]), union(W, H, [(body, 0, 0)]))
    out = stamp(out, shade(head, "D", "G", "r"), 14 + by + hy, 15)
    for part, top, left in extra:
        out = over(out, fill(W, H, [(part, top, left)]))
    return out


# ---------------------------------------------------------------------------------
# Up: from behind. The rump is nearest; the tail sweeps up to the right; the head is
# at the far end inside its crest of flame.
# ---------------------------------------------------------------------------------

HEAD_U = spr("""
    .D..............D.
    .DD............DD.
    DDDD..........DDDD
    DDrDD........DDrDD
    DDrrDDDDDDDDDDrrDD
    .DDDDDDDDDDDDDDDD.
    .DDDDDDDDDDDDDDDD.
    ..DDDDDDDDDDDDDD..
    ...DDDDDDDDDDDD...
    ....DDDDDDDDDD....
""")

BACK_U = spr("""
    .....DDDDDDDD.....
    ...DDDDDDDDDDDD...
    ..DDDDDDDDDDDDDD..
    ..DDDDDDDDDDDDDD..
    ..DDDDDDDDDDDDDD..
    ...DDDDDDDDDDDD...
    ...DDDDDDDDDDDD...
    ....DDDDDDDDDD....
    ...DDDDDDDDDDDD...
    ..DDDDDDDDDDDDDD..
    .DDDDDDDDDDDDDDDD.
    DDDDDDDDDDDDDDDDDD
    DDDDDDDDDDDDDDDDDD
    DDDDDDDDrrDDDDDDDD
    DDDDDDDr..rDDDDDDD
    .DDDDDr....rDDDDD.
    ..rrrr......rrrr..
""")
# The spine's crack down the middle, and the haunches'
BACK_U_CRACKS = [(1, 8), (2, 9), (3, 8), (4, 9), (5, 8), (6, 9), (7, 8), (8, 9),
                 (10, 3), (11, 3), (12, 4), (10, 14), (11, 14), (12, 13)]
BACK_U_HOT = [(3, 8), (6, 9)]

# The tail from the rump, sweeping up and out to the right, burning at the end
TAILS_U = [
    spr("""
        ...R....
        ..RR.R..
        ..RORR..
        .ROYOR..
        .RYYOR..
        .OYYO...
        DDOO....
        DDD.....
        DD......
        DD......
    """),
    spr("""
        ....R...
        ...RR...
        .R.ROR..
        .RROYR..
        .RYYOR..
        .OYYO...
        DDOO....
        DDD.....
        DD......
        DD......
    """),
    spr("""
        ..R.....
        ..RR.R..
        .RORRR..
        .ROYOR..
        .RYYOR..
        .OYYO...
        DDOO....
        DDD.....
        DD......
        DD......
    """),
]
TAIL_STEM_U = spr("""
    .....DD
    ....DD.
    ...DD..
    ..DD...
    DDD....
""")


def up_pose(phase: float = None, by: int = 0, hy: int = 0, flicker: int = 0,
            flames_map: dict = None, extra: list = ()) -> Sprite:
    lifts = trot_lifts(phase)  # near = hind (bottom of screen), far = front
    far = fill(W, H, [
        (leg_v(HIND_X[0] + 2, 30 + by, 40.5 - lifts[2], False), 0, 0),
        (leg_v(HIND_X[1] - 2, 30 + by, 40.5 - lifts[3], False), 0, 0),
    ])
    far = shade(far, "D", "D", "r")
    crest = CRESTS_D[(flicker + 1) % 3]
    tail = TAILS_U[flicker % 3]
    if flames_map:
        crest, tail = swap(crest, flames_map), swap(tail, flames_map)
    back = put(put(BACK_U, BACK_U_CRACKS, "O"), BACK_U_HOT, "Y")
    upper = fill(W, H, [
        (crest, 9 + by, 10),
        (back, 21 + by, 15),
        (leg_v(19.0, 34 + by, GROUND - lifts[0], True), 0, 0),
        (leg_v(29.0, 34 + by, GROUND - lifts[1], True), 0, 0),
    ])
    out = over(union(W, H, [(far, 0, 0)]), union(W, H, [(shade(upper, "D", "G", "r"), 0, 0)]))
    out = stamp(out, shade(HEAD_U, "D", "G", "r"), 13 + by + hy, 15)
    out = stamp(out, shade(fill(18, 16, [(TAIL_STEM_U, 11, 0), (tail, 2, 5)]), "D", "G", "r"), 22 + by, 24)
    for part, top, left in extra:
        out = over(out, fill(W, H, [(part, top, left)]))
    return out


# ---------------------------------------------------------------------------------
# Fire: the breath cone (the Effect) and the gouts drawn in the hound's own cell
# ---------------------------------------------------------------------------------


def flame_cone(w: int, h: int, length: float, spread: float, seed: int, fade: float = 0.0) -> Sprite:
    """A plume of fire pouring right from the middle of the left edge: white-hot at the
    jaws, banded Y O R r outward, its edge billowing, its end rounded, haze round it."""
    r = rng(seed)
    ph = [r.uniform(0, 6.28) for _ in range(6)]
    cy = h / 2
    knee = 0.78
    rows = []
    for y in range(h):
        line = []
        for x in range(w):
            u = (x + 0.5) / max(length, 1)
            if u > 1.08:
                line.append(".")
                continue
            if u <= knee:
                half = 1.0 + spread * math.sqrt(u / knee)
            else:
                k = (u - knee) / (1.08 - knee)
                half = (1.0 + spread) * math.sqrt(max(0.0, 1 - k * k))
            half *= 1 + 0.16 * math.sin(x * 0.75 + ph[0]) + 0.08 * math.sin(x * 1.4 + ph[1] + y * 0.3)
            drift = 0.9 * math.sin(x * 0.28 + ph[2]) * min(1.0, u * 2)
            v = abs(y + 0.5 - cy - drift) / max(half, 0.4)
            heat = (1.08 - 0.75 * v - 0.45 * u + 0.11 * math.sin(x * 0.9 + y * 0.8 + ph[3])
                    + 0.07 * math.sin(x * 1.7 - y * 1.1 + ph[4]) - fade)
            if v > 1.0:
                ch = "^" if v < 1.3 and (x + y) % 2 == 0 and fade < 0.5 else "."
            elif heat > 0.86:
                ch = "W"
            elif heat > 0.66:
                ch = "Y"
            elif heat > 0.44:
                ch = "O"
            elif heat > 0.2:
                ch = "R"
            else:
                ch = "r"
            line.append(ch)
        rows.append("".join(line))
    grid = [list(row) for row in rows]
    lo = int(length * 0.4)
    for _ in range(max(1, int(length / 6))):  # sparks thrown clear
        x, y = r.randrange(lo, max(lo + 1, min(w, int(length * 1.05)))), r.randrange(h)
        if grid[y][x] in ".^":
            grid[y][x] = "*"
    return ["".join(row) for row in grid]


def fire_breath_effect() -> list[Sprite]:
    """40 x 24, pointing right from its left edge's middle: ignite, roll out, roar
    three frames, gutter out in smoke."""
    w, h = 40, 24
    frames = [
        flame_cone(w, h, 12, 4, 1),
        flame_cone(w, h, 26, 7, 2),
        flame_cone(w, h, 38, 10, 3),
        flame_cone(w, h, 39, 10.5, 4),
        flame_cone(w, h, 38, 10, 5),
    ]
    last = flame_cone(w, h, 39, 11, 6, fade=0.35)
    smoke = [(4, 30), (5, 33), (3, 35), (6, 36), (18, 31), (19, 34), (20, 36),
             (2, 38), (21, 38), (11, 39), (8, 37), (15, 37)]
    frames.append(put(last, smoke, "~"))
    return frames


def rot_down(sprite: Sprite) -> Sprite:
    """Turned a quarter clockwise: a cone pointing right now points down."""
    return ["".join(sprite[len(sprite) - 1 - c][r] for c in range(len(sprite))) for r in range(len(sprite[0]))]


def rot_up(sprite: Sprite) -> Sprite:
    return list(reversed(rot_down(sprite)))


# The gout in the hound's own cell, while the fx cone carries the reach
GOUT_R = [flame_cone(9, 16, 9, 6.5, 10 + k) for k in range(3)]
GOUT_DN = [rot_down(flame_cone(15, 18, 15, 8, 20 + k)) for k in range(3)]
GOUT_UP = [rot_up(flame_cone(13, 16, 13, 7, 30 + k)) for k in range(3)]


# Snap marks: the bite's hit, two rows of teeth closing
BITE_R = spr("""
    .W..W.
    W.WW.W
    ......
    W.WW.W
    .W..W.
""")
BITE_D = spr("""
    .W....W.
    W.W..W.W
    ........
    W.W..W.W
    .W....W.
""")


def smoke_puffs(n: int) -> list[tuple[Sprite, int, int]]:
    """Wisps of smoke for death and the breath's end, drifting up with n."""
    puff = put(blank(3, 3), [(0, 1), (1, 0), (1, 2), (2, 1)], "~")
    return [(puff, 18 - n * 2, 14 + n), (puff, 14 - n * 2, 26 - n), (puff, 22 - n * 2, 33 + n)]


# ---------------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------------


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    bob = [0, 0, 1, 0, 0, 0, 1, 0]

    # --- Right ---
    stand = stand_paws()
    base_r = right_pose(stand)
    animations["idle"]["right"] = Anim(
        [right_pose(stand, flicker=0), right_pose(stand, flicker=1, hy=1),
         squash(right_pose(stand, flicker=2, hy=1), 1, 31), right_pose(stand, flicker=1)],
        fps=6,
    )
    animations["walk"]["right"] = Anim(
        [right_pose(trot_paws(f / 8), by=bob[f], flicker=f) for f in range(8)], fps=10,
    )
    crouch_paws = {k: (x - 1, y) for k, (x, y) in stand_paws(-2).items()}
    lunge_paws = {
        "near_front": (ELBOW[0] + 7, GROUND - 2), "far_front": (ELBOW[0] + 4, GROUND - 1),
        "near_hind": (STIFLE[0] - 5, GROUND), "far_hind": (STIFLE[0] - 3, GROUND),
    }
    bite = right_pose(lunge_paws, bx=2, head=HEAD_R, hx=1, hy=1, flicker=2)
    animations["attack"]["right"] = Anim(
        [
            right_pose(crouch_paws, bx=-2, by=1, hy=1, flicker=0),
            right_pose(crouch_paws, bx=-2, by=2, head=HEAD_R_OPEN, hy=1, flicker=1),
            right_pose(lunge_paws, bx=2, head=HEAD_R_OPEN, hx=1, flicker=2),
            over(bite, fill(W, H, [(BITE_R, 22, 41)])),
            right_pose(lunge_paws, bx=1, head=HEAD_R, hx=1, hy=1, flicker=0),
            right_pose(stand, flicker=1),
        ],
        fps=10, loop=False,
    )

    def breathing(k: int) -> Sprite:
        f = right_pose(stand_paws(-3), bx=-3, head=HEAD_R_ROAR, hy=1, flicker=k, flames_map=HOT)
        return over(f, fill(W, H, [(GOUT_R[k % 3], 19, 38)]))

    animations["special"]["right"] = Anim(
        [
            right_pose(stand_paws(-1), bx=-1, hx=-1, hy=-2, lean=-1, flicker=0),
            right_pose(stand_paws(-2), bx=-2, hx=-2, hy=-4, lean=-2, flicker=1, flames_map=HOT),
            squash(right_pose(stand_paws(-2), bx=-2, hx=-2, hy=-4, lean=-2, flicker=2, flames_map=HOT), 1, 31),
            breathing(0), breathing(1), breathing(2), breathing(0),
            over(right_pose(stand_paws(-1), bx=-1, head=HEAD_R_OPEN, hy=1, flicker=1),
                 fill(W, H, [(p, t + 6, l + 8) for p, t, l in smoke_puffs(0)[:1]])),
        ],
        fps=10, loop=False,
    )
    lying = squash(right_pose(stand, hy=4, flicker=2, flames_map=COOL), 10, 32)
    animations["death"]["right"] = Anim(
        [
            silhouette(base_r, "W"),
            right_pose(stand, hx=-1, hy=-3, lean=-3, flicker=1),
            squash(right_pose(stand, hy=2, flicker=1, flames_map=COOL), 5, 33),
            lying,
            over(swap(lying, ASH), fill(W, H, smoke_puffs(1))),
            over(dissolve(swap(lying, ASH), 0.6), fill(W, H, smoke_puffs(2))),
        ],
        fps=8, loop=False,
    )

    # --- Down ---
    base_d = down_pose()
    animations["idle"]["down"] = Anim(
        [down_pose(flicker=0), down_pose(flicker=1, hy=1), squash(down_pose(flicker=2, hy=1), 1, 33),
         down_pose(flicker=1)],
        fps=6,
    )
    animations["walk"]["down"] = Anim(
        [down_pose(f / 8, by=bob[f], flicker=f) for f in range(8)], fps=10,
    )
    animations["attack"]["down"] = Anim(
        [
            down_pose(by=-1, hy=-1, flicker=0),
            down_pose(by=-1, head=HEAD_D_OPEN, hy=-2, flicker=1),
            down_pose(by=1, head=HEAD_D_OPEN, hy=2, flicker=2),
            down_pose(by=1, hy=3, flicker=0, extra=[(BITE_D, 33, 20)]),
            down_pose(by=1, hy=2, flicker=1),
            down_pose(flicker=2),
        ],
        fps=10, loop=False,
    )

    def breathing_d(k: int) -> Sprite:
        return down_pose(head=HEAD_D_OPEN, hy=1, flicker=k, flames_map=HOT,
                         extra=[(GOUT_DN[k % 3], 28, 15)])

    animations["special"]["down"] = Anim(
        [
            down_pose(hy=-2, flicker=0),
            down_pose(by=-1, hy=-4, flicker=1, flames_map=HOT),
            squash(down_pose(by=-1, hy=-4, flicker=2, flames_map=HOT), 1, 33),
            breathing_d(0), breathing_d(1), breathing_d(2), breathing_d(0),
            down_pose(head=HEAD_D_OPEN, hy=1, flicker=1,
                      extra=[(p, t + 16, l + 6) for p, t, l in smoke_puffs(0)[:1]]),
        ],
        fps=10, loop=False,
    )
    lying_d = squash(down_pose(hy=3, flicker=2, flames_map=COOL), 8, 34)
    animations["death"]["down"] = Anim(
        [
            silhouette(base_d, "W"),
            down_pose(by=-1, hy=-3, flicker=1),
            squash(down_pose(hy=2, flicker=1, flames_map=COOL), 4, 34),
            lying_d,
            over(swap(lying_d, ASH), fill(W, H, smoke_puffs(1))),
            over(dissolve(swap(lying_d, ASH), 0.6), fill(W, H, smoke_puffs(2))),
        ],
        fps=8, loop=False,
    )

    # --- Up ---
    base_u = up_pose()
    animations["idle"]["up"] = Anim(
        [up_pose(flicker=0), up_pose(flicker=1, hy=1), squash(up_pose(flicker=2, hy=1), 1, 33),
         up_pose(flicker=1)],
        fps=6,
    )
    animations["walk"]["up"] = Anim(
        [up_pose(f / 8, by=bob[f], flicker=f) for f in range(8)], fps=10,
    )
    animations["attack"]["up"] = Anim(
        [
            up_pose(by=1, hy=1, flicker=0),
            up_pose(by=1, hy=2, flicker=1),
            up_pose(by=-1, hy=-3, flicker=2),
            up_pose(by=-1, hy=-3, flicker=0, extra=[(BITE_D, 8, 20)]),
            up_pose(by=-1, hy=-2, flicker=1),
            up_pose(flicker=2),
        ],
        fps=10, loop=False,
    )

    def breathing_u(k: int) -> Sprite:
        f = up_pose(hy=-1, flicker=k, flames_map=HOT)
        return behind(f, fill(W, H, [(GOUT_UP[k % 3], 1, 16)]))

    animations["special"]["up"] = Anim(
        [
            up_pose(hy=1, flicker=0),
            up_pose(by=1, hy=2, flicker=1, flames_map=HOT),
            squash(up_pose(by=1, hy=2, flicker=2, flames_map=HOT), 1, 33),
            breathing_u(0), breathing_u(1), breathing_u(2), breathing_u(0),
            up_pose(hy=-1, flicker=1),
        ],
        fps=10, loop=False,
    )
    lying_u = squash(up_pose(hy=2, flicker=2, flames_map=COOL), 8, 34)
    animations["death"]["up"] = Anim(
        [
            silhouette(base_u, "W"),
            up_pose(by=-1, hy=-2, flicker=1),
            squash(up_pose(hy=2, flicker=1, flames_map=COOL), 4, 34),
            lying_u,
            over(swap(lying_u, ASH), fill(W, H, smoke_puffs(1))),
            over(dissolve(swap(lying_u, ASH), 0.6), fill(W, H, smoke_puffs(2))),
        ],
        fps=8, loop=False,
    )

    write_character(
        Character(
            name="hellhound",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Lean charcoal hound split by glowing ember cracks, with a flaming mane and tail "
            "and burning eyes; bites with a lunge. Special: fire breath (rears back and pours a "
            "cone of flame from its jaws; fx fire_breath).",
            shadow=30,
            effects=(
                Effect(
                    "fire_breath", fire_breath_effect(), fps=10, loop=False,
                    notes="40x24 cone pointing right from the left edge's middle (put that on the "
                    "jaws, rotate to aim): ignite, roll out, three frames of roar, gutter out.",
                ),
            ),
        )
    )
