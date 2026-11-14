"""Spider: a giant cave spider that lays web traps.

Wide and low: a fat dark abdomen with a bone-pale chevron pattern, a smaller head with a
black face plate holding eight red eyes, pale curved fangs, and eight long jointed legs
whose knees rise above the body before they step down to the floor.
Attack: rears up on its back legs, then lunges and bites.
Special, "web": rears, its pattern flares, and it spits a ball of silk (Effect
"web_shot") that lands as a sticky floor web (Effect "web", the trap).

How it's built: the body is two shaded ovals (_batch_a.orb) with the face, fangs and
markings pasted on; the legs are drawn, not typed. Each view has a table of legs, each
a body joint, a knee and a foot, and a draw order back to front. pose() offsets those
points (the gait, a rear-up, a lunge, a death curl), draws every leg as a femur and a
shin with its own outline, and stacks the parts. Left is mirror()ed from right.
"""

from __future__ import annotations

import math

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    blank,
    check,
    dissolve,
    mirror,
    outline,
    paste,
    recolour,
    silhouette,
    write_character,
)

from enemies._batch_a import Canvas, ol, orb

S = 48  # the cell, square

# ---------------------------------------------------------------------------------
# The parts
# ---------------------------------------------------------------------------------

# A black face plate with eight red eyes: two big ones lit from the top left, the rest
# small round them
FACE_DOWN = [
    "..KKKKKK..",
    ".RKKKKKKR.",
    "RKFRKKFRKR",
    ".KRRKKRRK.",
    "..KKKKKK..",
]
FACE_RIGHT = [
    ".KKRK.",
    "KRKKFK",
    "KKKFRR",
    ".KKRRK",
    "..KKK.",
]
# Fangs: the bases and the curved tips, fill only
FANGS_DOWN_SHUT = [
    ".GDDGDD.",
    ".GDDGDD.",
    "..LWWL..",
    "...WW...",
]
FANGS_DOWN_OPEN = [
    "GDD..GDD",
    "GDD..GDD",
    "LW....WL",
    "W......W",
]
FANGS_RIGHT_SHUT = [
    "GDD.",
    "GDD.",
    ".LW.",
    "..W.",
]
FANGS_RIGHT_OPEN = [
    "GDD..",
    "GDDD.",
    "..LWW",
    "....W",
]
# The abdomen's pattern: bone-pale chevrons pointing at the head
CHEVRONS_DOWN = [
    "W.......W",
    ".L.....L.",
    "..L...L..",
    "...LLL...",
    "L.......L",
    ".L.....L.",
    "..LLLLL..",
]
CHEVRONS_UP = CHEVRONS_DOWN[::-1]
CHEVRONS_RIGHT = [
    "W..W..W..",
    ".L..L..L.",
    "..L..L..L",
]

for _name, _sprite in list(globals().items()):
    if _name.isupper() and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)

ABDOMEN = {"down": orb(20, 14, "G", "D", "p", "L"), "up": orb(20, 15, "G", "D", "p", "L"),
           "right": orb(20, 15, "G", "D", "p", "L")}
HEAD = {"down": orb(14, 11, "G", "D", "p"), "up": orb(14, 11, "G", "D", "p"), "right": orb(14, 10, "G", "D", "p")}


def mirror_x(p: tuple[int, int]) -> tuple[int, int]:
    return S - 1 - p[0], p[1]


class Leg:
    """One leg: where it joins the body, its knee and its foot, in cell coordinates at
    rest, which gait group it steps with, and whether it's on the far side."""

    def __init__(self, joint, knee, foot, group, far=False, palp=False):
        self.joint, self.knee, self.foot = joint, knee, foot
        self.group, self.far, self.palp = group, far, palp


def pair(right: tuple, group: int) -> tuple[Leg, Leg]:
    """A right leg and its mirror on the left, which steps with the other group."""
    j, k, f = right
    return Leg(mirror_x(j), mirror_x(k), mirror_x(f), 1 - group), Leg(j, k, f, group)


# Each view: the body parts' places (top, left) and the legs, then the draw order
DOWN_LEGS = {
    1: pair(((28, 37), (36, 29), (39, 45)), 1),
    2: pair(((29, 35), (39, 24), (44, 40)), 0),
    3: pair(((29, 33), (40, 20), (45, 33)), 1),
    4: pair(((28, 31), (37, 16), (42, 25)), 0),
    0: pair(((26, 38), (29, 40), (28, 43)), 0),  # palps
}
UP_LEGS = {
    1: pair(((28, 21), (35, 11), (39, 19)), 1),
    2: pair(((29, 23), (39, 14), (44, 28)), 0),
    3: pair(((29, 25), (41, 20), (45, 36)), 1),
    4: pair(((28, 28), (38, 25), (42, 45)), 0),
}
RIGHT_NEAR = {
    1: Leg((32, 36), (40, 25), (43, 45), 0),
    2: Leg((30, 36), (34, 22), (37, 45), 1),
    3: Leg((28, 36), (24, 21), (21, 45), 0),
    4: Leg((26, 35), (14, 19), (6, 45), 1),
}
RIGHT_FAR = {
    n: Leg((leg.joint[0] + 1, leg.joint[1] - 2), (leg.knee[0] + 2, leg.knee[1] - 2), (leg.foot[0] + 1, leg.foot[1] - 2),
           1 - leg.group, far=True)
    for n, leg in RIGHT_NEAR.items()
}

FORWARD = {"down": (0, 1), "up": (0, -1), "right": (1, 0)}


def legs_of(view: str) -> list[tuple[str, Leg]]:
    """(key, leg) for every leg in a view; key is e.g. L1, R3, N2, F4, P (palp)."""
    if view == "right":
        return [(f"N{n}", leg) for n, leg in RIGHT_NEAR.items()] + [(f"F{n}", leg) for n, leg in RIGHT_FAR.items()]
    table = DOWN_LEGS if view == "down" else UP_LEGS
    out = []
    for n, (left, right) in table.items():
        out += [(f"L{n}" if n else "PL", left), (f"R{n}" if n else "PR", right)]
    return out


ORDER = {
    "down": ["L4", "R4", "abdomen", "L3", "R3", "L2", "R2", "L1", "R1", "head", "PL", "PR"],
    "up": ["L1", "R1", "head", "L2", "R2", "L3", "R3", "L4", "R4", "abdomen"],
    "right": ["F4", "F3", "F2", "F1", "abdomen", "N4", "N3", "N2", "N1", "head"],
}
PLACE = {  # (top, left) of each body part per view
    "down": {"abdomen": (18, 14), "head": (29, 17)},
    "up": {"head": (18, 17), "abdomen": (26, 14)},
    "right": {"abdomen": (21, 4), "head": (29, 24)},
}


def draw_leg(joint, knee, foot, far: bool, palp: bool) -> Sprite:
    """A leg on its own cell: a thick femur up to the knee and a thin shin down to the
    foot, lit on top, outlined."""
    c = Canvas(S, S)
    if palp:
        c.line(*joint, *knee, "G")
        c.line(*knee, *foot, "D")
        return outline(c.rows())
    c.line(*joint, *knee, "D" if far else "G")
    c.line(joint[0], joint[1] + 1, knee[0], knee[1] + 1, "D")
    c.line(*knee, *foot, "D")
    c.set(*knee, "G" if far else "L")
    return outline(c.rows())


def lerp(a, b, t):
    return (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t))


def add(a, b):
    return (round(a[0] + b[0]), round(a[1] + b[1]))


def pose(
    view: str, step: int | None = None, body: tuple[int, int] = (0, 0), rear: float = 0.0, reach: int = 0,
    curl: float = 0.0, crouch: int = 0, fangs: str = "shut", glow: bool = False,
) -> Sprite:
    """The spider in view. step (0-7) is the gait frame, None standing. body moves the
    body (dx, dy). rear lifts the front legs off the floor (0-1); reach pushes their feet
    forward. curl folds every leg in toward the body (death). crouch lowers the knees.
    fangs is "shut" or "open"; glow brightens the pattern."""
    fx, fy = FORWARD[view]
    out = blank(S, S)
    legs = dict(legs_of(view))
    for item in ORDER[view]:
        if item in ("abdomen", "head"):
            top, left = PLACE[view][item]
            part = (ABDOMEN if item == "abdomen" else HEAD)[view]
            part = decorate(view, item, part, fangs, glow)
            out = paste(out, ol(part), top - 1 + body[1], left - 1 + body[0])
            if item == "head":
                out = face(view, out, body, fangs)
            continue
        leg = legs[item]
        joint, knee, foot = add(leg.joint, body), leg.knee, leg.foot
        knee = add(knee, (body[0] * 0.6, body[1] * 0.6))
        if step is not None and not leg.palp and item not in ("PL", "PR"):
            theta = 2 * math.pi * step / 8 + math.pi * leg.group
            s, swing = math.sin(theta), math.cos(theta) > 0
            foot = add(foot, (fx * 2 * s, fy * 2 * s - (2 if swing else 0)))
            knee = add(knee, (fx * s, fy * s - (1 if swing else 0)))
        # Feet stay on the floor and inside the cell, outline and all
        foot = (min(max(foot[0], 1), S - 2), min(foot[1], S - 3))
        if crouch:
            knee = add(knee, (0, crouch))
        front = item[1:] == "1"
        if rear and front:
            out_x = (1 if leg.knee[0] > S // 2 else -1) if view != "right" else 0
            knee = add(knee, (fx * 2 * rear + out_x * 2 * rear, -9 * rear))
            foot = add(foot, (fx * (3 * rear + reach) + out_x * 5 * rear, -15 * rear))
        elif reach and front:
            foot = add(foot, (fx * reach, fy * reach))
        if curl:
            knee = lerp(knee, add(joint, ((knee[0] - joint[0]) * 0.3, -3)), curl)
            foot = lerp(foot, add(joint, ((foot[0] - joint[0]) * 0.25, 2)), curl)
        out = paste(out, draw_leg(joint, knee, foot, leg.far, item in ("PL", "PR")), 0, 0)
    return out


def decorate(view: str, item: str, part: Sprite, fangs: str, glow: bool) -> Sprite:
    """The abdomen's chevrons (brighter when glowing) and spinnerets, the rear eyes."""
    if item == "abdomen":
        marks = {"down": (CHEVRONS_DOWN, 3, 5), "up": (CHEVRONS_UP, 4, 5), "right": (CHEVRONS_RIGHT, 3, 4)}[view]
        m, r, c = marks
        if glow:
            m = recolour(m, {"L": "W", "W": "Y"})
        return paste(part, m, r, c)
    if view == "up":  # the rear eyes on top of the head, glinting
        return paste(part, ["R.KK.R", "K....K"], 2, 4)
    return part


def face(view: str, out: Sprite, body: tuple[int, int], fangs: str) -> Sprite:
    """The face plate and fangs on the head, in cell coordinates."""
    bx, by = body
    if view == "down":
        f = FANGS_DOWN_OPEN if fangs == "open" else FANGS_DOWN_SHUT
        out = paste(out, ol(f), 37 + by, 19 + bx)
        return paste(out, FACE_DOWN, 31 + by, 19 + bx)
    if view == "right":
        f = FANGS_RIGHT_OPEN if fangs == "open" else FANGS_RIGHT_SHUT
        out = paste(out, ol(f), 36 + by, 34 + bx)
        return paste(out, FACE_RIGHT, 30 + by, 32 + bx)
    return out


# ---------------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------------


def web_ball(turn: float) -> Sprite:
    """A 12x12 ball of silk, its strands turned by turn degrees."""
    c = Canvas(12, 12)
    cx, cy = 5.5, 5.5
    for k in range(6):
        a = math.radians(turn + k * 60)
        c.line(round(cx), round(cy), round(cx + 5 * math.cos(a)), round(cy - 5 * math.sin(a)), "L")
    for k in range(12):
        a = math.radians(turn + k * 30)
        c.set(cx + 3 * math.cos(a), cy - 3 * math.sin(a), "W")
    c.set(cx, cy, "W")
    c.set(cx + 1, cy, "W")
    rows = c.rows()
    return outline(rows, ":")


def web_trap(glint: int) -> Sprite:
    """The sticky web left on the floor, 32x32: eight uneven spokes, rings strung between
    them, dew glinting on one ring (glint picks which spoke it's on)."""
    c = Canvas(32, 32)
    cx, cy = 15.5, 15.5
    angles = [5, 52, 88, 133, 178, 222, 272, 318]
    reach = [15, 13, 15, 14, 15, 13, 15, 14]
    for a, r in zip(angles, reach):
        t = math.radians(a)
        c.line(round(cx), round(cy), round(cx + r * math.cos(t)), round(cy - r * math.sin(t)), "L")
    for ring, letter in ((4, "L"), (7.5, "L"), (11, ":"), (14, ":")):
        pts = []
        for a, r in zip(angles, reach):
            t = math.radians(a)
            rr = min(ring, r)
            pts.append((cx + rr * math.cos(t), cy - rr * math.sin(t)))
        for p, q in zip(pts, pts[1:] + pts[:1]):
            c.line(*p, *q, letter, under=True)
    # Dew: bright drops along the middle ring
    for k in range(3):
        a = math.radians(angles[(glint + k * 3) % 8])
        c.set(cx + 7.5 * math.cos(a), cy - 7.5 * math.sin(a), "W")
    c.set(cx, cy, "W")
    return c.rows()


def strand(out: Sprite, start: tuple[int, int], end: tuple[int, int]) -> Sprite:
    """A taut strand of silk from start to end over the frame."""
    c = Canvas(S, S, out)
    c.line(*start, *end, "W")
    c.line(start[0], start[1] + 1, end[0], end[1] + 1, ":", under=True)
    return c.rows()


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    for view in ("down", "up", "right"):
        fx, fy = FORWARD[view]
        base = pose(view)

        # Idle: the body sinks and lifts on its knees, the palps twitch
        animations["idle"][view] = Anim(
            [base, pose(view, crouch=1, body=(0, 1)), pose(view, crouch=1, body=(0, 1)), base], fps=5
        )

        # Walk: alternating tetrapod gait (L1 R2 L3 R4 against R1 L2 R3 L4), body steady
        animations["walk"][view] = Anim(
            [pose(view, step=n, body=(0, -1 if n in (1, 5) else 0)) for n in range(8)], fps=10
        )

        # Attack: rear up with the front legs raised and fangs open, hold, lunge and
        # bite, hold the bite, settle back
        back = (-fx * 2, -2 - fy * 1)
        lunge = (fx * 3, fy * 2)
        bite = pose(view, body=lunge, reach=3, fangs="shut")
        if view == "down":
            bite = paste(bite, ["W.W.W", ".:.:.", "W.:.W"], 43, 22)
        elif view == "right":
            bite = paste(bite, ["W..", ".:W", "W:."], 38, 38)
        animations["attack"][view] = Anim(
            [
                pose(view, rear=0.6, body=(back[0] // 2, -1), fangs="open"),
                pose(view, rear=1.0, body=back, fangs="open"),
                pose(view, body=lunge, reach=4, fangs="open"),
                bite,
                pose(view, body=(fx, fy), reach=1),
                base,
            ],
            fps=10,
            loop=False,
        )

        # Special, web: crouch, rear, the pattern flares, spit the silk, recover
        reared = pose(view, rear=0.8, body=back, fangs="open", glow=True)
        spit_body = (fx * 2, fy)
        spit = pose(view, body=spit_body, reach=2, fangs="open", glow=True)
        ball = web_ball(0)
        if view == "down":
            spit = paste(spit, ball, 36, 18)
        elif view == "right":
            spit = paste(strand(spit, (37, 40), (44, 38)), ball, 32, 36)
        else:
            spit = paste(spit, ball, 8, 18)
        animations["special"][view] = Anim(
            [
                pose(view, crouch=2, body=(0, 1)),
                pose(view, rear=0.5, body=(back[0] // 2, -1), fangs="open"),
                reared,
                pose(view, rear=0.8, body=back, fangs="open"),
                spit,
                pose(view, body=spit_body, reach=2),
                base,
            ],
            fps=10,
            loop=False,
        )

        # Death: flash, the legs curl in under it, it sinks to the floor, fades
        curled = pose(view, curl=1.0, body=(0, 3))
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                pose(view, curl=0.45, body=(0, 1), fangs="open"),
                pose(view, curl=0.8, body=(0, 2)),
                curled,
                dissolve(curled, 0.45),
                dissolve(curled, 0.8),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="spider",
            kind="enemies",
            size=(S, S),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="A giant cave spider: dark bulbous abdomen with pale chevrons, eight red eyes, "
            "pale fangs, long high-kneed legs; bites. Special: web (spits fx web_shot, which "
            "leaves fx web on the floor as a trap).",
            shadow=30,
            effects=(
                Effect("web_shot", [web_ball(a) for a in (0, 20, 40)], fps=10, loop=True,
                       notes="The silk ball it spits, spinning in flight."),
                Effect("web", [web_trap(g) for g in (0, 1, 2)], fps=4, loop=True,
                       notes="The sticky floor web it leaves: a trap tile, 32x32, dew glinting."),
            ),
        )
    )
