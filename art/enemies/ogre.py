"""Ogre: a huge, hunched brute that hits very hard.

A mountain of ruddy tan flesh: a hump of shoulders, a great round belly, stumpy legs
and a tiny head sunk between the shoulders, with a heavy brow, piggy yellow eyes, a
fleshy nose and two up-jutting tusks. It wears a grey pelt loincloth on a belt with a
bone buckle and carries a crude studded club over its shoulder.
Attack: an overhead club smash, the club coming down in a smear and hitting the floor.
Special, "slam": it hops and drives the club and its fist into the floor, sending out an
expanding ring of dust (Effect "shockwave").

How it's built: the body is drawn, not typed, from _batch_a's shaded shapes: orbs for the
hump, back and belly, tubes for the legs, arms and club, and only the head and loincloth
as letter matrices. pose() places them per view from a few joint positions, outlines the
body in K and inlays the arms and club with dark-brown inner lines. Left is mirror()ed
from right.
"""

from __future__ import annotations

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    arc,
    blank,
    check,
    dissolve,
    mirror,
    outline,
    paste,
    shear,
    shift,
    silhouette,
    squash,
    underlay,
    write_character,
)

from enemies._batch_a import Canvas, inlay, orb, ring, tube

S = 48  # the cell, square
SKIN = ("S", "T", "B")  # light, mid, shade
WOOD = ("T", "B", "b")

# ---------------------------------------------------------------------------------
# The head and loincloth, fill only
# ---------------------------------------------------------------------------------

HEAD_DOWN = [
    "..SSSTTT..",
    ".SSTTTTTB.",
    "SSbbTTbbTB",
    "STYbTTbYBB",
    "STTTSFTTTB",
    "STTSFFBTTB",
    "SWTbbbbTWB",
    "SWBBBBBBWB",
    ".TBBBBBBB.",
]
HEAD_UP = [
    "..SSSTTT..",
    ".SSTTTTTB.",
    "SSTTTTTTTB",
    "STTTTTTTBB",
    "STTTTTTTTB",
    "STTTTTTTBB",
    "STTTTTTBBB",
    ".TBBBBBBB.",
    "..BBBBBB..",
]
HEAD_RIGHT = [
    "..SSTT...",
    ".SSTTTT..",
    "SSTTbbbT.",
    "STTTTbYT.",
    "STTTTTTSF",
    "STTTTTTFB",
    "BTTTTbbW.",
    "BBTTTTBW.",
    ".BBBBBB..",
]
LOIN_DOWN = [
    "bbbbbbbbbbLWLbbbbbbbbb",
    "DGGLGGGGGGGLGGGGGGGGGD",
    ".DGGGGGGGGGGGGGGGGGGD.",
    "..DDGGGGGGGGGGGGGGDD..",
    "......DLGGGGGGGD......",
    ".......DGGGGGGD.......",
    ".......DGDGGDGD.......",
    "........D.DD.D........",
]
LOIN_UP = [
    "bbbbbbbbbbbbbbbbbbbbbb",
    "DGGLGGGGGGGGGGGGGGGGGD",
    ".DGGGGGGGGGGGGGGGGGGD.",
    "..DDGGGGGGGGGGGGGGDD..",
    "......DLGGGGGGGD......",
    ".......DGGDGGGGD......",
    ".......D.DGGD.D.......",
    ".........D..D.........",
]
LOIN_RIGHT = [
    "bbbbbbbbbLWLb",
    "DGLGGGGGGGGGD",
    ".DGGGGGGGGGGD",
    "..DGGGGGGGGD.",
    "...DGGDGGGD..",
    "....D..DGD...",
]

for _name, _sprite in list(globals().items()):
    if _name.isupper() and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)

# ---------------------------------------------------------------------------------
# Geometry: joint positions in cell coordinates at rest
# ---------------------------------------------------------------------------------

# Arms: (shoulder, elbow, wrist, fist centre, club grip, club tip) per arm pose and view,
# the club arm on screen left in down, screen right in up, the near arm in profile
CLUB_ARM = {
    "down": {
        "hang": ((10.5, 15), (8, 25), (11, 21), (12, 19), (12, 19), (7, 7)),
        "raised": ((10.5, 15), (6, 10), (12, 7), (13, 6), (13, 6), (33, 6)),
        "smash": ((10.5, 15), (12, 25), (18, 32), (19, 34), (19, 34), (27, 44)),
    },
    "right": {
        "hang": ((19, 18), (18, 29), (24, 28), (25, 26), (25, 26), (7, 7)),
        "raised": ((20, 17), (19, 10), (25, 7), (26, 7), (26, 7), (6, 9)),
        "smash": ((21, 18), (31, 22), (37, 27), (38, 29), (38, 30), (42, 44)),
    },
}
OFF_ARM = {
    "down": {
        "hang": ((37.5, 15), (40, 24), (39, 31), (39.5, 34)),
        "smash": ((37.5, 15), (36, 25), (30, 32), (29, 34)),
        "raised": ((37.5, 15), (42, 10), (36, 7), (35, 6)),
    },
    "right": {
        "hang": ((25, 17), (30, 26), (34, 31), (35, 33)),
        "smash": ((25, 17), (33, 21), (40, 26), (41, 28)),
        "raised": ((25, 17), (25, 10), (30, 7), (31, 6)),
    },
}


def flip_x(p):
    return (S - p[0], p[1])


def arm_joints(view: str, which: str, name: str):
    """The joints of an arm pose; the up view is the down view mirrored."""
    table = CLUB_ARM if which == "club" else OFF_ARM
    if view == "up":
        return tuple(flip_x(p) for p in table["down"][name])
    return table[view][name]


def moved(p, d):
    return (p[0] + d[0], p[1] + d[1])


# ---------------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------------


def club(grip, tip) -> Sprite:
    """The club on its own cell: a tapering tube of wood from grip to tip, a leather
    wrap at the grip and iron studs round the head."""
    c = tube(S, S, [grip, tip], [1.4, 3.3], *WOOD)
    can = Canvas(S, S, c)
    gx, gy = grip
    tx, ty = tip
    for t, side in ((0.62, 1), (0.74, -1), (0.86, 1), (0.95, -1), (0.8, 0)):
        x, y = gx + (tx - gx) * t, gy + (ty - gy) * t
        # across the club
        length = max(1e-6, ((tx - gx) ** 2 + (ty - gy) ** 2) ** 0.5)
        px, py = -(ty - gy) / length, (tx - gx) / length
        r = 1.4 + 1.9 * t
        sx, sy = x + px * side * (r - 0.8), y + py * side * (r - 0.8)
        if can.get(round(sx - 0.5), round(sy - 0.5)) != ".":
            can.set(sx - 0.5, sy - 0.5, "L")
    for t in (0.1, 0.18):
        x, y = gx + (tx - gx) * t, gy + (ty - gy) * t
        for dx in (-1, 0, 1):
            if can.get(round(x - 0.5 + dx), round(y - 0.5)) != ".":
                can.set(x - 0.5 + dx, y - 0.5, "b")
    return can.rows()


def arm(joints) -> tuple[Sprite, Sprite]:
    """An arm: (the upper arm and forearm tube, the fist), each on its own cell."""
    shoulder, elbow, wrist, fist = joints[:4]
    limb = tube(S, S, [shoulder, elbow, wrist], [4.6, 3.7, 3.2], *SKIN)
    hand = orb(9, 8, *SKIN)
    knuckles = paste(hand, ["b.b.b"], 5, 2)
    return limb, paste(blank(S, S), knuckles, round(fist[1] - 4), round(fist[0] - 4.5))


def legs(view: str, body, lift=(0, 0), stride=(0, 0), kneel: float = 0.0) -> Sprite:
    """Both legs and feet on one cell: hips move with the body, feet stay planted unless
    lifted (lift raises each foot) or striding (stride slides each foot, profile)."""
    if view == "right":
        hips, ankles = [(23, 36), (31, 36)], [(22, 42), (33, 42)]
        toe = 2
    else:
        hips, ankles = [(18, 35), (29, 35)], [(17, 42), (30, 42)]
        toe = 0
    out = blank(S, S)
    for n, (hip, ankle) in enumerate(zip(hips, ankles)):
        hip = moved(hip, (body[0], body[1] + kneel * 8))
        ankle = (ankle[0] + stride[n], ankle[1] - lift[n])
        if kneel < 0.9:
            out = paste(out, tube(S, S, [hip, ankle], [4.6, 3.6], *SKIN), 0, 0)
        foot = orb(11 if view == "right" else 10, 5, *SKIN)
        foot = paste(foot, ["b.b"] if view != "right" else ["..b.b"], 3, 3)
        out = paste(out, foot, round(ankle[1]) - 1, round(ankle[0]) - 5 + toe)
    return out


def pose(
    view: str, club_arm: str = "hang", off_arm: str = "hang", body=(0, 0), lift=(0, 0), stride=(0, 0),
    kneel: float = 0.0, slump: int = 0,
) -> Sprite:
    """The ogre in view. body moves everything above the hips (dx, dy); lift and stride
    move the feet; kneel folds the legs away; slump drops the head and shoulders."""
    bx, by = body
    by += round(kneel * 8)
    fill = blank(S, S)
    sh = (bx, by + slump)

    def at(sprite, top, left, d=(bx, by)):
        nonlocal fill
        fill = paste(fill, sprite, top + d[1], left + d[0])

    lower = legs(view, (bx, by), lift, stride, kneel)
    if view == "down":
        fill = paste(fill, lower, 0, 0)
        at(orb(34, 14, *SKIN), 11, 7, sh)
        at(HEAD_DOWN, 10 + slump * 2, 19, sh)
        belly = paste(orb(26, 20, *SKIN), ["B", "B"], 11, 12)
        belly = paste(belly, ["..BBBB..."], 16, 9)
        at(belly, 17, 11)
        at(LOIN_DOWN, 32, 13)
    elif view == "up":
        fill = paste(fill, lower, 0, 0)
        at(HEAD_UP, 7 + slump * 2, 19, sh)
        back = orb(34, 22, *SKIN)
        for y in range(4, 17):
            back = paste(back, ["B"], y, 17)
        at(back, 11, 7, sh)
        at(LOIN_UP, 31, 13)
    else:
        fill = paste(fill, lower, 0, 0)
        at(orb(24, 18, *SKIN), 9, 7, sh)
        belly = paste(orb(24, 21, *SKIN), ["B"], 12, 18)
        at(belly, 18, 18)
        at(HEAD_RIGHT, 13 + slump * 2, 32, sh)
        at(LOIN_RIGHT, 34, 19)
    out = outline(fill)

    # The off arm, then the club and the club arm over it
    behind_off = view == "right"
    j = [moved(p, sh) for p in arm_joints(view, "off", off_arm)]
    limb, fist = arm(j)
    out = inlay(out, limb, 0, 0, "b", behind=behind_off)
    out = inlay(out, fist, 0, 0, "b", behind=behind_off)

    j = [moved(p, sh) for p in arm_joints(view, "club", club_arm)]
    club_behind = (view, club_arm) in {("up", "smash"), ("up", "hang")}
    out = inlay(out, club(j[4], j[5]), 0, 0, "b", behind=club_behind)
    limb, fist = arm(j[:4])
    arm_behind = (view, club_arm) == ("up", "smash")
    out = inlay(out, limb, 0, 0, "b", behind=arm_behind)
    out = inlay(out, fist, 0, 0, "b", behind=arm_behind or (view, club_arm) == ("up", "hang"))
    return out


# ---------------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------------

DUST = [
    "..:~:..",
    ".:~:~:.",
    ":~:::~:",
    ".:::::.",
]


def dust(f: Sprite, x: int, y: int, front: bool = False) -> Sprite:
    """A puff of dust centred on (x, y), behind the ogre, or over it when front."""
    return (paste if front else underlay)(f, DUST, y - 3, x - 3)


def shockwave(n: int) -> Sprite:
    """Frame n of the slam's ring of dust, 64x32: it widens, thins and fades, with grit
    thrown along it."""
    w, h = 64, 32
    rx = 8 + n * 4.6
    ry = rx * 0.42
    f = ring(w, h, 31.5, 15.5, rx, ry, ":", thickness=4.2 - n * 0.4, edge="L")
    inner = ring(w, h, 31.5, 15.5, max(1, rx - 3.5), max(1, ry - 1.6), "~", thickness=2.2)
    f = underlay(f, inner, 0, 0)
    import math

    c = Canvas(w, h, f)
    for k in range(10):
        a = math.radians(k * 36 + 15)
        c.set(31.5 + (rx + 1) * math.cos(a), 15.5 - (ry + 1) * math.sin(a), "G" if k % 2 else "D")
    f = c.rows()
    return dissolve(f, [0, 0, 0.1, 0.3, 0.5, 0.75][n])


# The club's path in the smash: a bright smear down through the air
SMEAR_DOWN = arc(18, 34, 18, 17, 16, 95, 265, ":", thickness=3, edge="W")
SMEAR_RIGHT = arc(30, 34, 6, 30, 28, -20, 95, ":", thickness=3, edge="W")


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    for view in ("down", "up", "right"):
        side = view == "right"
        base = pose(view)
        belly_row = 28

        # Idle: a slow heave of the belly and shoulders
        animations["idle"][view] = Anim(
            [base, squash(base, 1, belly_row), pose(view, body=(0, 1)), squash(base, 1, belly_row)], fps=4
        )

        # Walk: a heavy stomp. Front and back: the weight rolls onto the planted foot
        # while the other lifts, dipping on each plant. Profile: the legs stride.
        if side:
            strides = [(-3, 3), (-2, 2), (0, 0), (2, -2), (3, -3), (2, -2), (0, 0), (-2, 2)]
            lifts = [(0, 0), (0, 0), (0, 3), (0, 0), (0, 0), (0, 0), (3, 0), (0, 0)]
            dips = [1, 0, -1, 0, 1, 0, -1, 0]
            walk = [pose(view, body=(0, dips[n]), stride=strides[n], lift=lifts[n]) for n in range(8)]
        else:
            lifts = [(0, 0), (3, 0), (4, 0), (1, 0), (0, 0), (0, 3), (0, 4), (0, 1)]
            sway = [0, 1, 1, 0, 0, -1, -1, 0]
            dips = [1, 0, -1, 0, 1, 0, -1, 0]
            walk = [pose(view, body=(sway[n], dips[n]), lift=lifts[n]) for n in range(8)]
        animations["walk"][view] = Anim(walk, fps=8)

        # Attack: heave the club overhead, hold, bring it down in a smear, hit the floor
        # in a puff of dust, hold, haul it back
        raised = pose(view, "raised", body=(-1 if side else 0, 0))
        hit = pose(view, "smash", body=(0, 2))
        if view == "down":
            swing = paste(pose(view, "smash", body=(0, 1)), SMEAR_DOWN, 4, 2)
            hit = dust(hit, 27, 44, front=True)
        elif side:
            swing = paste(pose(view, "smash", body=(0, 1)), SMEAR_RIGHT, 2, 16)
            hit = dust(hit, 42, 44, front=True)
        else:
            swing = pose(view, "smash", body=(0, 1))
            hit = dust(dust(hit, 5, 42), 43, 42)
        animations["attack"][view] = Anim(
            [pose(view, "raised"), raised, swing, hit, hit, pose(view, body=(0, 1)), base],
            fps=10,
            loop=False,
        )

        # Special, slam: crouch, hop with both arms up, drive the club and fist into the
        # floor, the ground shakes (fx shockwave starts on frame 4), rise
        crouch = pose(view, body=(0, 3), kneel=0.15)
        up = pose(view, "raised", "raised")
        slam = pose(view, "smash", "smash", body=(0, 3), kneel=0.2)
        floor = {"down": [(28, 45), (4, 43), (44, 43)], "up": [(4, 42), (44, 42)], "right": [(42, 44), (5, 44)]}[view]
        slammed = slam
        for x, y in floor:
            slammed = dust(slammed, x, y)
        animations["special"][view] = Anim(
            [
                crouch,
                up,
                pose(view, "raised", "raised", lift=(2, 2)),
                slam,
                slammed,
                shift(slammed, 1, 0),
                shift(slammed, -1, 0),
                pose(view, body=(0, 1)),
                base,
            ],
            fps=10,
            loop=False,
        )

        # Death: flash, reel, the knees give, it slumps forward, fades
        slumped = shear(squash(base, 13, 24), 3 if side else 0, S - 4)
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                shear(base, -2, S - 6),
                squash(base, 6, 32),
                slumped,
                dissolve(slumped, 0.45),
                dissolve(slumped, 0.8),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="ogre",
            kind="enemies",
            size=(S, S),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="A huge hunched ogre: tan hide, pot belly, tiny tusked head, pelt loincloth, "
            "a studded club on its shoulder; overhead smash. Special: slam (drives the club into the "
            "floor and sends out fx shockwave, a ring of dust).",
            shadow=30,
            effects=(
                Effect("shockwave", [shockwave(n) for n in range(6)], fps=12, loop=False,
                       notes="The slam's expanding ring of dust, centred on the ogre's feet."),
            ),
        )
    )
