"""Dark Mage: caster.

A hooded sorcerer in layered purple robes: a pointed hood whose tail hangs down its back,
a mantle with a gold clasp, bell sleeves, a gold belt and a ragged hem. Its face is lost
in the hood's shadow but for two burning yellow eyes. Bony hands grip a knotted staff
whose iron claw holds a glowing lilac orb.
Attack: it raises the staff (the sleeve falls back off a bony forearm), the orb flares,
and it looses a shadow bolt (Effect).
Special, "blink": it dissolves into a puff of magic haze and reforms.

Built like skeleton_warrior: a torso on a set of robe-hem "legs" per view, the staff and
its arm pasted per frame, animations from those poses, left mirrored from right. Bodies
are drawn as fills; _batch_b.place() seals the finished silhouette in K and lays glows
underneath it.
"""

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    blank,
    check,
    dissolve,
    flip,
    mirror,
    paste,
    recolour,
    shear,
    shift,
    silhouette,
    squash,
    underlay,
    write_character,
)

from enemies._batch_b import centred, disc, line, outlined, place, puff, ring

W, H = 32, 48

# ---------------------------------------------------------------------------------
# Down: facing the camera. 20 wide; torso rows 0-22, robe hem 23-32. The staff hand is
# screen left; the staff stands just outside the sleeve.
# ---------------------------------------------------------------------------------

DOWN_TORSO = [
    ".........MP.........",
    "........MPPp........",
    ".......MPPPPp.......",
    "......MMPPPPPp......",
    ".....MMPPPPPPPp.....",
    ".....MPPPPPPPPp.....",
    "....MPPPppppPPPp....",
    "....MPPpKKKKpPPp....",
    "....MPpKKKKKKpPp....",
    "....MPpKYKKYKpPp....",
    "....MPpKKKKKKpPp....",
    "....MPPpKKKKpPPp....",
    "...MPPPPppppPPPPp...",
    "..MMPPPPPYOPPPPPPp..",
    ".MMPPPPPPOOPPPPPPpp.",
    ".MPPPPPPPPPPPPPPPpp.",
    "MPpPPpPPpPPpPPpPPpPp",
    "pMPpppMPPPpPPPppMPpp",
    "MMPPp.MPPPpPPPp.MPPp",
    "MPPPp.MPPPpPPPp.MPPp",
    "MPPPp.OYYYYYYYO.MPPp",
    "MPPPPpMPPPpPPPppPPPp",
    "pKKKp.MPPPpPPPp.pKKp",
]

# The same with the staff arm (screen left) lifted away: the robe's side shows
DOWN_TORSO_RAISED = DOWN_TORSO[:17] + [
    "....ppMPPPpPPPppMPpp",
    "......MPPPpPPPp.MPPp",
    "......MPPPpPPPp.MPPp",
    "......OYYYYYYYO.MPPp",
    "......MPPPpPPPppPPPp",
    "......MPPPpPPPp.pKKp",
]

DOWN_HEM = [
    "......MPPPpPPPp.....",
    ".....MMPPPpPPPPp....",
    ".....MPPPPpPPPPp....",
    "....MMPPPPpPPPPPp...",
    "....MPPPPPpPPPPPp...",
    "...MMPPPPPpPPPPPpp..",
    "...MPPPPPPpPPPPPpp..",
    "..MPPpPPPPpPPPPpPpp.",
    "..pPpPpPPpppPPpPpPp.",
    "..p.p.pDDp.pDDp.p.p.",
]

# Stepping: the hem swings to one side over the striding foot
DOWN_HEM_A = DOWN_HEM[:7] + [
    ".MPPpPPPPpPPPPpPpp..",
    ".pPpPpPPpppPPpPpPp..",
    ".pDDDp.p.pp.p.p.p...",
]
DOWN_HEM_B = DOWN_HEM[:7] + [
    "...MPPpPPPPpPPPPpPpp",
    "...pPpPpPPpppPPpPpPp",
    "...p.p.p.pp.p.pDDDp.",
]

# ---------------------------------------------------------------------------------
# Up: the back. A seam down the hood, the mantle over the shoulders.
# ---------------------------------------------------------------------------------

UP_TORSO = [
    ".........MP.........",
    "........MPPp........",
    ".......MPPPPp.......",
    "......MMPPpPPp......",
    ".....MMPPPpPPPp.....",
    ".....MPPPPpPPPp.....",
    "....MPPPPPpPPPPp....",
    "....MPPPPPpPPPPp....",
    "....MPPPPPpPPPPp....",
    "....MPPPPPpPPPPp....",
    "....MPPPPPpPPPPp....",
    "....MPPPPPpPPPPp....",
    "...MPPPPPPpPPPPPp...",
    "..MMPPPPPPpPPPPPPp..",
    ".MMPPPPPPPpPPPPPPpp.",
    ".MPPPPPPPPpPPPPPPpp.",
    "MPpPPpPPpPPpPPpPPpPp",
    "pMPpppMPPPPPPPppMPpp",
    "MMPPp.MPPPPPPPp.MPPp",
    "MPPPp.MPPPPPPPp.MPPp",
    "MPPPp.OOOOOOOOO.MPPp",
    "MPPPPpMPPPPPPPppPPPp",
    "pKKKp.MPPPPPPPp.pKKp",
]

# The staff arm (screen right) lifted away
UP_TORSO_RAISED = UP_TORSO[:17] + [
    "pMPpppMPPPPPPPpp....",
    "MMPPp.MPPPPPPPp.....",
    "MPPPp.MPPPPPPPp.....",
    "MPPPp.OOOOOOOOO.....",
    "MPPPPpMPPPPPPPpp....",
    "pKKKp.MPPPPPPPp.....",
]

UP_HEM = [
    "......MPPPPPPPp.....",
    ".....MMPPPPPPPPp....",
    ".....MPPPPPPPPPp....",
    "....MMPPPPPPPPPPp...",
    "....MPPPPPPPPPPPp...",
    "...MMPPPPPPPPPPPpp..",
    "...MPPPPPPPPPPPPpp..",
    "..MPPpPPPPPPPPPpPpp.",
    "..pPpPpPPpPpPPpPpPp.",
    "..p.p.pDDp.pDDp.p.p.",
]
UP_HEM_A = UP_HEM[:7] + [
    ".MPPpPPPPPPPPPpPpp..",
    ".pPpPpPPpPpPPpPpPp..",
    ".pDDDp.p.pp.p.p.p...",
]
UP_HEM_B = UP_HEM[:7] + [
    "...MPPpPPPPPPPPPpPpp",
    "...pPpPpPPpPpPPpPpPp",
    "...p.p.p.pp.p.pDDDp.",
]

# ---------------------------------------------------------------------------------
# Right: profile, facing right. 18 wide. The hood's brim juts over a dark face with one
# eye, its tail hanging down the back; the near sleeve reaches forward to the staff.
# ---------------------------------------------------------------------------------

RIGHT_TORSO = [
    ".....MMPp.........",
    "...MMPPPPpp.......",
    "..MPPPPPPPPp......",
    ".MPPPPPPPPPPp.....",
    ".MPpMPPPPPPPPp....",
    ".MPpMPPPPPPPPPp...",
    ".MPpMPPPPPPPPPPPp.",
    ".Mp.MPPPPPPPpKKKp.",
    ".Mp.MPPPPPPpKKKK..",
    "..p.MPPPPPPpKKYK..",
    "....MPPPPPPpKKKK..",
    "....MPPPPPPPpKKp..",
    "....MMPPPPPPPpp...",
    "...MMPPPPPPPPPPp..",
    "...MPPPPPPPPPPPpp.",
    "...MPPPPPMMPPPPPp.",
    "...MPPPPPpMMPPPPpp",
    "...MPPPPPPpMMPPPpp",
    "...MPPPPPPPpMPPpKp",
    "...pOYYYYYOppppp..",
    "...MPPPPPPpPPPp...",
    "...MPPPPPPpPPPp...",
    "..MMPPPPPPpPPPp...",
]

# The near arm lifted away
RIGHT_TORSO_RAISED = RIGHT_TORSO[:14] + [
    "...MPPPPPPPPPPp...",
    "...MPPPPPPPPPPp...",
    "...MPPPPPPPpPPp...",
    "...MPPPPPPPpPPp...",
    "...MPPPPPPPpPPp...",
    "...pOYYYYYOpppp...",
] + RIGHT_TORSO[20:]

RIGHT_HEM = [
    "..MPPPPPPPpPPPp...",
    "..MPPPPPPPPpPPPp..",
    ".MMPPPPPPPPpPPPp..",
    ".MPPPPPPPPPpPPPp..",
    "MMPPpPPPPPPpPPPpp.",
    "MPPpPPPPPPPPpPPpp.",
    "MPPpPPPPPPPPpPPpp.",
    "MPpPPPPPPPPPPpPpp.",
    "pPpPpPpPPpPpPpPpp.",
    "p.p.p.pDDDp.pDDDp.",
]
# Stride: the hem kicked forward by the front foot, the back foot trailing
RIGHT_HEM_A = RIGHT_HEM[:5] + [
    "MPPpPPPPPPPPpPPPp.",
    "MPPpPPPPPPPPPpPPpp",
    "MPpPPPPPPPPPPPpPpp",
    "pPpPpPpPPpPpPpPpPp",
    "pDDDp.p.p.p.p.DDDD",
]
# Passing: feet together under a narrowed hem
RIGHT_HEM_B = RIGHT_HEM[:5] + [
    "MPPpPPPPPPPpPPpp..",
    ".MPpPPPPPPPpPPpp..",
    ".MpPPPPPPPPPpPpp..",
    ".pPpPpPPpPpPpPp...",
    ".p.p.p.DDDDp.p....",
]

# Raised staff arms: the sleeve fallen back to the elbow off a bony forearm, the hand
# round the staff. Down (screen left); up is its mirror on screen right.
ARM_RAISED_DOWN = [
    ".WLW...",
    ".LLG...",
    "..LG...",
    "..LG...",
    ".MPPp..",
    "MPPPPp.",
    "MPPPPPp",
    "pMPPPPp",
    "ppMPPPp",
    ".pppMPp",
]
ARM_RAISED_RIGHT = [
    "...........WLW",
    "...........LLG",
    "...........LG.",
    "...........LG.",
    "..........MPPp",
    ".MMMPPPPPPPPPp",
    "MPPPPPPPPPPPp.",
    ".pPPPPPPPPpp..",
    "..ppppppp.....",
]

# The empty robe, crumpled on the floor, the hood flopped over at one end
HEAP = [
    ".......MPPp.............",
    ".....MMPPPPp............",
    "....MPPKKKPPp...........",
    "...MPPKKKKKPPpp.........",
    "..MMPPPKKKPPPPPpp.......",
    ".MPPPPPPPPPPpPPPPPp.....",
    "MPPPpPPPPPPPPPpPPPPpp...",
    "MPPPPPPpOYYOPPPPpPPPPPp.",
    "pPpPPpPPPPPPPPPpPPpPpPp.",
    "pp.ppppppppppppppppp.pp.",
]

# The staff dropped flat beside it, the orb gone dark
FALLEN_STAFF = [
    ".......................PPP.",
    "..TBBBbBBBBBBBTBBBBBbBDPMPp",
    ".......................Ppp.",
]

for _name, _sprite in list(globals().items()):
    if _name.isupper() and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)

# ---------------------------------------------------------------------------------
# The staff: a knotted shaft and a two-pronged iron claw holding the orb
# ---------------------------------------------------------------------------------

HEAD = [
    "..MMM..",
    ".MWWMP.",
    "GMWMMPD",
    "GMMMPPD",
    ".GPPpD.",
    "..GDD..",
]
HEAD_FLARE = [
    "..WWW..",
    ".WWWWM.",
    "GWWWWMD",
    "GMWWMMD",
    ".GMMMD.",
    "..GDD..",
]
HEAD_DARK = [
    "..PPP..",
    ".PMPPp.",
    "GPMPPpD",
    "GPPPppD",
    ".GpppD.",
    "..GDD..",
]


def staff(head: Sprite = HEAD, length: int = 36) -> Sprite:
    """The staff standing upright, outlined: head on a knotted shaft, its last row the
    shaft's foot. 9 wide, the shaft in column 4."""
    rows = list(head)
    for n in range(length - len(head)):
        ch = "b" if n % 8 == 5 else ("T" if n in (1, 9, 17) else "B")
        rows.append("..." + ch + "...")
    return outlined(rows)


STAFF = staff()
STAFF_FLARE = staff(HEAD_FLARE)
STAFF_DARK = staff(HEAD_DARK)
SHAFT = 4  # the shaft's column in a staff sprite
ORB_ROW, ORB_COL = 3, 4  # the orb's centre in a staff sprite


def sparkle(d: int, spots: list[tuple[int, int]]) -> Sprite:
    """A haze disc d across with glints at spots."""
    s = disc(d, "&")
    for r, c in spots:
        s = paste(s, ["*"], r, c)
    return s


# Glows round the orb, centred on it: a soft halo, a flare in two flickers, a burst
HALO = disc(9, "&")
FLARE = sparkle(13, [(1, 3), (2, 10), (10, 1), (11, 9)])
FLARE_2 = sparkle(15, [(0, 7), (4, 14), (7, 0), (14, 7), (3, 2), (12, 12)])
BURST = ring(17, 17, "&", rim="M", thickness=2.0)
for _r, _c in ((0, 8), (8, 0), (8, 16), (16, 8)):
    BURST = paste(BURST, ["W"], _r, _c)


def slanted_staff(head: Sprite = HEAD_FLARE) -> tuple[Sprite, int, int]:
    """The staff thrust forward and up at a slant (profile), outlined; returns it and the
    (row, column) of the orb's centre."""
    w, h = 18, 30
    grid = [list(r) for r in line(w, h, 2, h - 1, 14, 6, "B")]
    grid[20][7] = "b"
    grid[12][11] = "T"
    canvas = paste(["".join(r) for r in grid], head, 0, 11)
    return outlined(canvas), 4, 15


SLANTED, SLANT_ORB_R, SLANT_ORB_C = slanted_staff()

# ---------------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------------

VIEWS = {
    "down": (DOWN_TORSO, DOWN_HEM, DOWN_HEM_A, DOWN_HEM_B),
    "up": (UP_TORSO, UP_HEM, UP_HEM_A, UP_HEM_B),
    "right": (RIGHT_TORSO, RIGHT_HEM, RIGHT_HEM_A, RIGHT_HEM_B),
}

# Per view: the staff's shaft column, the staff hand (sprite, row, column) and the free
# hand, all in body coordinates
GRIP = {
    "down": (-1, (["WLL", "LGD"], 22, -2), (["LW", "GL"], 22, 17)),
    "up": (20, (["LLW", "DGL"], 22, 19), None),
    "right": (17, (["WLW", "LGL"], 18, 16), None),
}

# Per view, the staff held high: the torso with that arm away, the raised arm (sprite,
# row, column), and the shaft column
RAISED = {
    "down": (DOWN_TORSO_RAISED, (ARM_RAISED_DOWN, 10, -3), -1),
    "up": (UP_TORSO_RAISED, (flip(ARM_RAISED_DOWN), 10, 16), 20),
    "right": (RIGHT_TORSO_RAISED, (ARM_RAISED_RIGHT, 6, 6), 18),
}
RAISE = 6  # rows the staff lifts


def mage(view: str, hem: Sprite = None, stf: Sprite = None, glow: Sprite = None,
         raised: bool = False, dx: int = 0, dy: int = 0) -> Sprite:
    """The view's pose holding the staff (stf, or the plain one), low or raised, with
    glow, if given, centred on its orb."""
    torso, stand, _, _ = VIEWS[view]
    stf = stf or STAFF
    shaft, hand, free = GRIP[view]
    lift_by = 0
    if raised:
        torso, hand, shaft = RAISED[view]
        lift_by = RAISE
    body = torso + (hem or stand)
    top = len(body) - len(stf) + 1 - lift_by
    left = shaft - SHAFT
    front = [(stf, top, left), hand]
    if free:
        front.append(free)
    haze = []
    if glow:
        gh, gw = len(glow), len(glow[0])
        haze.append((glow, top + ORB_ROW - gh // 2, left + ORB_COL - gw // 2))
    back = []
    if view == "up":  # seen from behind, the staff is beyond the body
        back, front = [front[0]], front[1:]
    return place(body, W, H, front=front, back=back, haze=haze, dx=dx, dy=dy)


def casting(view: str) -> Sprite:
    """The release: in profile the staff thrust forward at a slant; from front and back
    the staff brought down with the orb bursting."""
    if view != "right":
        return mage(view, stf=STAFF_FLARE, glow=BURST, dy=0)
    body = RIGHT_TORSO_RAISED + RIGHT_HEM
    top, left = 2, 4
    gh, gw = len(BURST), len(BURST[0])
    arm = [
        "........WLW",
        ".MMMPPPPLGL",
        "MPPPPPPPpp.",
        ".pPPPPPpp..",
        "..ppppp....",
    ]
    return place(
        body, W, H,
        front=[(SLANTED, top, left), (arm, 12, 4)],
        haze=[(BURST, top + SLANT_ORB_R - gh // 2, left + SLANT_ORB_C - gw // 2)],
    )


# ---------------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------------

# Shadow bolt: a knot of darkness with a lilac rim and a white-hot nose, trailing haze
# that writhes frame to frame. Flies right; the game turns it.
SHADOW_BOLT_CORE = [
    "....pPPM....",
    "..pKKKpPMW..",
    ".pKKKKKpMWW.",
    ".pKKKKKpMWW.",
    "..pKKKpPMW..",
    "....pPPM....",
]
# The trail, writhing: one per frame
_TRAILS = [
    [
        "......&&..&.",
        "..&&&&&&&...",
        "&&&&.&&&&&..",
        ".&&&&&&&&&..",
        "...&&&&&&...",
        ".....&&..&..",
    ],
    [
        "....&..&&...",
        ".&&&.&&&&&..",
        "&&&&&&&&&&..",
        "&&.&&&&&&&..",
        "..&&&&&&&...",
        "......&&....",
    ],
    [
        ".......&....",
        "..&.&&&&&&..",
        ".&&&&&&&&&..",
        "&&&&&&&&&&..",
        ".&&&.&&&&...",
        "...&&...&...",
    ],
    [
        ".....&&&.&..",
        "&&.&&&&&&...",
        ".&&&&&&&&&..",
        "..&&&&&&&&..",
        "&&&&&&&&&...",
        ".&...&&.....",
    ],
]


def _bolt(n: int) -> Sprite:
    """A knot of darkness with a lilac rim and a white-hot nose, its haze trail writhing
    behind. Flies right; the game turns it."""
    f = blank(20, 10)
    f = paste(f, ["." * 12 for _ in range(2)], 0, 0)
    f = underlay(paste(f, SHADOW_BOLT_CORE, 2, 8), _TRAILS[n], 2, 0)
    for r, c in ((1, 6 + n), (8, 9 - n), (0, 12 + n % 2)):
        f = underlay(f, ["&"], r, c)
    return f


SHADOW_BOLT = [_bolt(n) for n in range(4)]


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    for view, (torso, stand, hem_a, hem_b) in VIEWS.items():
        base = mage(view)
        lit = mage(view, glow=HALO)
        a = mage(view, hem_a)
        b = mage(view, hem_b)

        # Idle: a slow breath while the orb pulses in its claw
        breathe = squash(lit, 1, 30)
        animations["idle"][view] = Anim([base, lit, breathe, lit], fps=5)

        # Walk: a gliding step on each foot, the hem swinging over it
        animations["walk"][view] = Anim(
            [a, shift(a, 0, -1), base, shift(base, 0, -1), b, shift(b, 0, -1), base, shift(base, 0, -1)],
            fps=8,
        )

        # Attack: raise the staff, the orb gathers light and flares, release, recover
        animations["attack"][view] = Anim(
            [
                mage(view, raised=True, glow=HALO),
                mage(view, raised=True, stf=STAFF_FLARE, glow=FLARE),
                mage(view, raised=True, stf=STAFF_FLARE, glow=FLARE_2),
                casting(view),
                lit,
                base,
            ],
            fps=10,
            loop=False,
        )

        # Special, blink: the robe lights up, dissolves into haze, gone, reforms
        bright = recolour(lit, {"p": "P", "P": "M", "M": "W"})
        cloud = [puff(24, 30, "&", 1.0, core="M", core_amount=0.12, ox=n, oy=2 * n) for n in range(4)]
        wisp = puff(14, 14, "&", 0.8, ox=1, oy=2)
        empty = blank(W, H)
        animations["special"][view] = Anim(
            [
                lit,
                bright,
                underlay(dissolve(bright, 0.4), cloud[0], 15, 4),
                underlay(dissolve(bright, 0.75), cloud[1], 15, 4),
                centred(empty, cloud[2], 15),
                centred(empty, wisp, 26),
                underlay(dissolve(bright, 0.75), cloud[3], 15, 4),
                underlay(dissolve(bright, 0.4), wisp, 26, 9),
                bright,
                lit,
            ],
            fps=10,
            loop=False,
        )

        # Death: a flash as it reels, the orb dark; it sinks to its knees, the robe
        # caves in, the empty robe lies in a heap, and its magic drifts off as it fades
        dark = mage(view, stf=STAFF_DARK)
        reel = shear(squash(dark, 3, 34), -2, 40)
        kneel = squash(dark, 8, 32)
        cave = shear(squash(dark, 16, 26), 2, 40)
        heap = place(HEAP if view != "up" else flip(HEAP), W, H,
                     front=[(outlined(FALLEN_STAFF), 6, -3)])
        spirit = puff(12, 14, "&", 0.8)
        animations["death"][view] = Anim(
            [
                silhouette(reel, "W"),
                kneel,
                cave,
                heap,
                underlay(dissolve(heap, 0.45), spirit, 22, 10),
                dissolve(underlay(heap, spirit, 16, 10), 0.8),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="dark_mage",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Caster: a hooded sorcerer in purple robes, yellow eyes in a shadowed hood, "
            "a staff with a glowing orb. Attack raises the staff and throws a shadow bolt. "
            "Special: blink (dissolves into magic haze and reforms).",
            shadow=16,
            effects=(
                Effect("shadow_bolt", SHADOW_BOLT, fps=10, loop=True,
                       notes="Projectile: a knot of shadow with a lilac rim, flying right."),
            ),
        )
    )
