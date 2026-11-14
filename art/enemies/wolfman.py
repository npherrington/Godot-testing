"""Wolfman: pack hunter.

A hunched grey werewolf in torn brown trousers, yellow eyes, long clawed arms and
digitigrade legs. attack is a claw swipe with three claw-streaks; attack2 is a lunging
bite. Special, "howl": it throws its head back and howls, sound rings rolling off the
muzzle to call the pack (Effect "howl").

How it's built (the skeleton_warrior shape, drawn as fills that ol() outlines):
- down and up are symmetric halves (sym) with a hand-lit face pasted on; right is a
  profile. Each view is a torso on a set of legs.
- The attacking arm (screen left in down, screen right in up, the near arm in profile)
  is a separate part per position: hang, raised, swipe, low.
- Bite and howl swap the head for an open-jawed or thrown-back one.
"""

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    arc,
    blank,
    cell,
    crop,
    dissolve,
    erase,
    flip,
    mirror,
    paste,
    rotate,
    shear,
    shift,
    silhouette,
    squash,
    stretch,
    write_character,
)
from enemies._batch_c import (
    SHADE,
    check_sprites,
    compose,
    fill_pose,
    halves,
    join,
    lift,
    ol,
    ring,
    sym,
)

W, H = 32, 48
FUR_SHADE = {k: v for k, v in SHADE.items() if k not in "YF"}

# ---------------------------------------------------------------------------------
# Down: facing the camera. The back hump rises behind the head; long arms hang clear
# of a narrow waist. 26 wide; torso rows 0-24, legs 25-31.
# ---------------------------------------------------------------------------------

DOWN_HALF = [
    # 0123456789ABC
    ".......L.....",  # 0 ear tips
    ".......LL....",
    ".....LLLFL...",  # the back hump rises behind the head
    "....LLGLFGLLL",
    "...LLGDLLLLLL",
    "..LLGGDLLLLLL",  # 5
    ".LLGGGDLDDLLL",
    ".LGGGGDLYYDLW",
    "LGGGGDDLLDLWW",
    "GLGGGDGLLLWWK",
    "GLLGDGDGKWKKK",  # 10
    "GLGDGGGDLKLLL",
    "GLGDDGGGDDLLL",
    "GLG.DLGGLLLWL",
    "GLG.DLLGLLLLL",
    "GLG..DGLGLLLL",  # 15
    "GGD..DGGGDLLL",
    "GLG...DGGGLLL",
    "GLG...DGGGGLL",
    "GLG...TTTTTTT",  # rope belt
    "GGD...BBBBBBB",  # 20
    "LWLL..BBBBBbB",
    "W.W.W.BBGBbB.",  # claws; a hole in the trousers
    "......BBBbBB.",
    "......Bb.bBb.",  # torn hems
]

LEGS_HALF = [
    ".......GLG...",
    ".......GLGG..",
    "........LGG..",
    "........GLG..",
    ".......GLGG..",
    "......LLGGG..",
    "......W.W.W..",
]

# The face, lit from the left, pasted over the symmetric head at (4, 7)
FACE_DOWN = [
    "LLLLLLLLLLLG",
    "LDDLLLLLLDDG",  # brows
    "LYYDLWWLDYYG",  # eyes
    "GLLLLWWLLLGD",
    "GGLLWWWWLLDD",  # snout
    "GDLLWKKWLGDD",  # nose
    "GDGLWLLWLDDD",  # lip
    "GGDWDDDDWDDD",  # fangs
    "GGDDGGGGDDGG",  # jaw
]

# Jaws wide for the bite
FACE_BITE_DOWN = [
    "LLLLLLLLLLLG",
    "LDDLLLLLLDDG",
    "LYYDLWWLDYYG",
    "GLLLWWWWLLGD",
    "GDLWKKKKWLDD",  # nose
    "GDKWWKKWWKDD",  # upper fangs
    "GDKrrFFrrKDD",  # throat, tongue
    "GDKWrrrrWKDD",
    "GGDKWWWWKDDD",  # lower fangs
]

# Head thrown back for the howl: eyes shut, snout up, mouth an O
FACE_HOWL_DOWN = [
    "....LWWL....",
    "...LWKKWG...",  # nose, pointing up
    "LLLLLWWLLLLG",
    "LDDDLWWLDDDG",  # eyes squeezed shut
    "GLLLWKKWLLGD",
    "GGLWKrrKWLDD",  # mouth open
    "GDLWKFFKWGDD",
    "GDGLWKKWLDDD",
    "GGDDLWWLDDDD",  # chin
    "GGDDGLLGDDGG",
]

DOWN_TOP = paste(sym(DOWN_HALF, FUR_SHADE), FACE_DOWN, 4, 7)
DOWN_BITE_TOP = paste(sym(DOWN_HALF, FUR_SHADE), FACE_BITE_DOWN, 4, 7)
DOWN_HOWL_TOP = paste(sym(DOWN_HALF, FUR_SHADE), FACE_HOWL_DOWN, 2, 7)
DOWN_LEGS = sym(LEGS_HALF, FUR_SHADE)
_LL, _LR = halves(DOWN_LEGS, 13)
DOWN_LEGS_A = join(lift(_LL, 2, 2), _LR)  # screen-left paw up
DOWN_LEGS_B = join(_LL, lift(_LR, 2, 2))  # screen-right paw up

# The attacking (screen-left) arm's box in the torso: rows 13-22, columns 0-4
ARM_BOX = (13, 0, 10, 5)
ARM_HANG_DOWN = crop(DOWN_TOP, *ARM_BOX)

ARM_RAISED_DOWN = [
    "W.W.W.",  # claws up by the ear
    "LWLWL.",
    "LLGGD.",
    ".LLGD.",
    ".LGGD.",
    ".LGGD.",
    ".LGGD.",
    "..LGGD",
    "..LGGD",
    "..LGGD",
]

# Swept across the belly, claws to the lower right
ARM_SWIPE_DOWN = [
    "LGD........",
    "LGGD.......",
    ".LGGD......",
    "..LGGD.....",
    "...LGGD....",
    "....LGGDW..",
    ".....LLWLW.",
    "......W.W.W",
]

# Driven forward at the camera, claws spread
ARM_LOW_DOWN = [
    "LGD....",
    "LGGD...",
    "LGGD...",
    ".LGGD..",
    ".LGGD..",
    "..LLWL.",
    ".WLWLW.",
    ".W.W.W.",
]

# ---------------------------------------------------------------------------------
# Up: the back. Only the ears and the crown of the head clear the hump; the tail
# hangs between the legs.
# ---------------------------------------------------------------------------------

UP_HALF = [
    # 0123456789ABC
    ".......L.....",  # 0 ears from behind
    ".......LL.L..",  # a tuft of mane
    ".....L.LGLLL.",
    "....LLLLGGLLL",  # the crown of the head between the ears
    "..L.LGGLLGDGL",
    "..LLLGGGDDGLD",  # 5 the hump, mane bristling along the spine
    ".LLGGGDGGGLGD",
    ".LGGGDGGGLGGD",
    "LGGGDGGGLGGDD",
    "GLGGGGGLGGDGD",
    "GLLGDGLGGDGGD",  # 10 fur flowing down and out from the spine
    "GLGDGLGGDGGDD",
    "GLGDGGGDGGDGD",
    "GLG.DGDGGDGGD",
    "GLG.DGGGDGGDD",
    "GLG..DGDGGDGD",  # 15
    "GGD..DGGGGGLL",  # tail root
    "GLG...DGGGLLL",
    "GLG...TTTLLLL",
    "GLG...TTTGLLG",
    "GGD...BBBGLLG",  # 20
    "LWLL..BBBGLLG",
    "W.W.W.BBBBGLG",
    "......BBBbGLL",
    "......Bb.bBGL",
]

UP_LEGS_HALF = [
    ".......GLG..L",  # tail tip
    ".......GLGG..",
    "........LGG..",
    "........GLG..",
    ".......GLGG..",
    "......LLGGG..",
    "......GLGLG..",  # heels
]

HOWL_UP = [
    "...LLGG...",  # the snout's tip up over the hump
    "..LLLGGG..",
    "..LLLGGD..",
    "L.LLLGGD.G",  # ears laid back
    "LLLLLGGGGD",
    ".LLLGGGGD.",
    ".LLGGGGGD.",
    "..LGGGGD..",
]

UP_TOP = sym(UP_HALF, FUR_SHADE)
UP_LEGS = sym(UP_LEGS_HALF, FUR_SHADE)
_UL, _UR = halves(UP_LEGS, 13)
UP_LEGS_A = join(lift(_UL, 2, 2), _UR)
UP_LEGS_B = join(_UL, lift(_UR, 2, 2))

# The attacking arm is on screen right from behind: the down arm box, flipped
UP_ARM_BOX = (13, 21, 10, 5)
ARM_HANG_UP = crop(UP_TOP, *UP_ARM_BOX)

# ---------------------------------------------------------------------------------
# Right: profile. The hump of the back is the highest point, the head juts forward
# below it, the tail hangs off the rump and the legs fold back at the hock. 24 wide.
# ---------------------------------------------------------------------------------

RIGHT_TORSO = [
    # 012345678901234567890123
    "............L...........",  # 0 ear tip
    ".....LLLL...LL..........",
    "...LLLLLLLL.LFL.........",
    "..LLLGGGGGLLLLFL........",
    ".LLGGGGDGGGLLLLLL.......",  # skull
    ".LGGGDGGGGDLLLDDLL......",  # 5 brow
    "LGGGDGGGDGDLLLYDLLLL....",  # eye
    "LGGDGGGDGGDLLLLLLLLLLL..",  # snout top
    "GGGGGGDGGDGLLLGGGGGGGLK.",  # nose
    "GGGDGGGGGDGGDDKWKKKWKKK.",  # mouth, fangs
    "GGDGGGDGGDGGGDDDDDDDD...",  # 10 jaw
    "DGGGGDGGGDGGGGDDLL......",  # throat ruff
    ".DGGGGGGGDGGGGGLLL......",
    "..DGGDGGGGDGGGLLLL......",
    "..DGGGGGGGDGGGLLLL......",
    ".LDDGGGGGGDGGGLLL.......",  # 15
    "LLGDDGGGGGGDGGLLL.......",  # the tail leaves the rump
    "LGGGDDGGGGGDGLL.........",
    "LGGG.TTTTTTTTTT.........",  # belt
    "GGG..BBBBBBBBBBB........",
    "GGD..BBBBBBBBBBBB.......",  # 20
    ".GD...bBBBBBBBBBBB......",
    "..D....bBBBBBBBBBB......",
    ".........bBBbBBbBB......",
    "..........B.b..B.b......",  # torn hems
]

# Knee forward in the trousers, shin back to the hock, long foot forward to the claws
RIGHT_LEGS = [
    # 012345678901234567890123
    ".........DGG...GLLG.....",
    "........DGG...GLLG......",
    ".......DGG...GLLG.......",
    ".......DGGD..GLLGG......",
    "........DDGD..GGLLG.....",
    ".........DDGD..GGLLG....",
    ".........DDDDW.GGLLLLW..",
]

# Stride: near paw reaching, far paw pushing off behind
RIGHT_LEGS_A = [
    "........DGG.....GLLG....",
    ".......DGG.....GLLG.....",
    "......DGG.....GLLGG.....",
    ".....DGGD.....GGLLG.....",
    ".....DDGD......GGLLG....",
    "....DDGD........GGLLG...",
    "....DDDDW.......GGLLLLW.",
]

# Passing: near paw lifted under the body, far paw planted
RIGHT_LEGS_B = [
    "..........DGGGLLG.......",
    ".........DGG.GLLG.......",
    "........DGG.GLLGG.......",
    "........DGGD.GGLLG......",
    ".........DDGD.GGLLLW....",
    "..........DDGD..........",
    "..........DDDDW.........",
]

# The near arm, hanging from the shoulder in front of the chest; at (9, 10)
ARM_HANG_RIGHT = [
    "LLG..",
    "LGGD.",
    "LGGD.",
    ".LGD.",
    ".LGD.",
    ".LGGD",
    ".LGGD",
    "..LGD",
    "..LGD",
    "..LGD",
    ".LLGD",
    ".LWLW",
    ".W.W.",
]

# Raised back over the hump, claws high; at (-3, 6)
ARM_RAISED_RIGHT = [
    "W.W....",
    "WLW....",
    "LLGW...",
    ".LGG...",
    ".LGGD..",
    "..LGD..",
    "..LGGD.",
    "...LGD.",
    "...LGGD",
    "....LGD",
    "....LGG",
    ".....LG",
]

# Flung forward and down, claws out; at (9, 10)
ARM_SWIPE_RIGHT = [
    "LLG.........",
    "LGGGD.......",
    ".LGGGGD.....",
    "...LGGGGD...",
    ".....LGGGLW.",
    ".......LLWLW",
    "........W.W.",
]

# Follow-through, low and forward; at (9, 10)
ARM_LOW_RIGHT = [
    "LLG.....",
    "LGGD....",
    ".LGGD...",
    "..LGGD..",
    "...LGGD.",
    "....LGGD",
    ".....LWW",
    "....W.W.",
]

# Jaws open for the bite: rows 6-12 of the head, at (6, 10)
BITE_RIGHT = [
    "DLLLYDLLLLLLK.",
    "DLLLLLLLLWKWK.",
    "GLLLGGGGW.W...",
    "GGDDrrr.......",
    "GGGDrFF.W.W...",
    "GGGGDLLLWLWL..",
    "GGGGDDDDDD....",
]

# Head thrown back, snout to the ceiling; at (-5, 10) once the head is cleared
HOWL_RIGHT = [
    # 0123456789AB
    "........LK..",
    ".......LLK..",
    "......LLWK..",
    "......LLW.K.",
    ".....LLLW.rK",
    ".L..LLLLWrrK",
    ".LL.LLLLWrK.",
    ".LFLLDYLLWK.",
    "..LFLLLLLLK.",
    "..LLLLLLLL..",
    "...LLLLLLL..",
    "...LLLLLLL..",
    "...GLLLLL...",
    "...GGLLLL...",
    "....GGLLL...",
    "....GGGLL...",
    ".....GGGL...",
]

check_sprites(globals())

# ---------------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------------

DOWN_PARTS = {
    "hang": (ARM_HANG_DOWN, 13, 0),
    "raised": (ARM_RAISED_DOWN, -2, -1),
    "swipe": (ARM_SWIPE_DOWN, 9, 0),
    "low": (ARM_LOW_DOWN, 10, 0),
}
UP_PARTS = {
    k: (flip(a), r, 26 - c - len(a[0])) for k, (a, r, c) in DOWN_PARTS.items()
}
UP_PARTS["hang"] = (ARM_HANG_UP, 13, 21)
RIGHT_PARTS = {
    "hang": (ARM_HANG_RIGHT, 9, 10),
    "raised": (ARM_RAISED_RIGHT, -3, 6),
    "swipe": (ARM_SWIPE_RIGHT, 9, 10),
    "low": (ARM_LOW_RIGHT, 9, 10),
}

# Arm positions that pass behind the body: swinging away from the viewer from behind
BEHIND = {("up", "swipe"), ("up", "low")}


def _armless(view: str, top: Sprite) -> Sprite:
    if view == "down":
        return erase(top, *ARM_BOX)
    if view == "up":
        return erase(top, *UP_ARM_BOX)
    return top


def body(view: str, top: str = "stand", legs: str = "stand", arm: str = "hang", dx: int = 0, dy: int = 1) -> Sprite:
    """The view's pose: a head variant (stand, bite, howl), a leg set (stand, a, b) and
    the attacking arm in a position."""
    tops = {
        "down": {"stand": DOWN_TOP, "bite": DOWN_BITE_TOP, "howl": DOWN_HOWL_TOP},
        "up": {"stand": UP_TOP, "bite": UP_TOP, "howl": UP_TOP},
        "right": {
            "stand": RIGHT_TORSO,
            "bite": paste(RIGHT_TORSO, BITE_RIGHT, 6, 10),
            "howl": erase(RIGHT_TORSO, 0, 11, 12, 13),
        },
    }[view][top]
    leg_sets = {
        "down": {"stand": DOWN_LEGS, "a": DOWN_LEGS_A, "b": DOWN_LEGS_B},
        "up": {"stand": UP_LEGS, "a": UP_LEGS_A, "b": UP_LEGS_B},
        "right": {"stand": RIGHT_LEGS, "a": RIGHT_LEGS_A, "b": RIGHT_LEGS_B},
    }[view][legs]
    parts_by_view = {"down": DOWN_PARTS, "up": UP_PARTS, "right": RIGHT_PARTS}[view]
    fill = _armless(view, tops) + leg_sets
    part = parts_by_view[arm]
    extra = []
    if top == "howl" and view == "right":
        extra = [(HOWL_RIGHT, -5, 10)]
    if top == "howl" and view == "up":
        extra = [(HOWL_UP, -4, 8)]
    if (view, arm) in BEHIND:
        return fill_pose(W, H, fill, extra, dx, dy, under=[part])
    return fill_pose(W, H, fill, extra + [part], dx, dy)


# Three claw-streaks where the swipe passed
CLAWS_DOWN = compose(20, 20, [
    (arc(20, 20, 18, 2, 16, 190, 260, ":", 1.2, "W"), 0, 0),
    (arc(20, 20, 18, 2, 13, 195, 255, ":", 1.2, "W"), 0, 0),
    (arc(20, 20, 18, 2, 10, 200, 250, ":", 1.2, "W"), 0, 0),
])
CLAWS_RIGHT = compose(14, 18, [
    (arc(14, 18, 0, 2, 13, 290, 350, ":", 1.2, "W"), 0, 0),
    (arc(14, 18, 0, 2, 10, 285, 350, ":", 1.2, "W"), 0, 0),
    (arc(14, 18, 0, 2, 7, 280, 350, ":", 1.2, "W"), 0, 0),
])


def _rings_from(cx: float, cy: float, r: float, up: bool = True) -> Sprite:
    """Small sound arcs off the muzzle in the cell, for the howl frames."""
    a0, a1 = (20, 160) if up else (-60, 60)
    return compose(W, H, [
        (ring(W, H, cx, cy, r, r * 0.8, ":", 1, "W", a0, a1), 0, 0),
        (ring(W, H, cx, cy, r + 3, (r + 3) * 0.8, ":", 1, "L", a0 + 10, a1 - 10), 0, 0),
    ])


def howl_effect() -> list[Sprite]:
    """Sound rings rolling out from the muzzle and thinning as they go."""
    frames = []
    for n in range(6):
        layers = []
        for k in range(3):
            r = 3 + 3 * n - 5 * k
            if r < 2:
                continue
            fade = min(0.7, 0.08 * n + 0.15 * k)
            band = ring(40, 32, 20, 16, r, r * 0.75, ":", 1.6, "W" if k == 0 else "L",
                        gaps=8, gap_width=0.18, spin=n * 6)
            layers.append((dissolve(band, fade, n, k), 0, 0))
        frames.append(compose(40, 32, layers) if layers else blank(40, 32))
    return frames


def _fallen(view: str) -> Sprite:
    """The body toppled onto its side, lying on the baseline."""
    fill = {"down": DOWN_TOP + DOWN_LEGS[-3:], "up": UP_TOP + UP_LEGS[-3:],
            "right": RIGHT_TORSO + RIGHT_LEGS[-3:]}[view]
    lying = rotate(ol(fill), 3 if view == "right" else 1)
    return cell(lying, W, H, 0, 1)


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "attack2": {}, "special": {}, "death": {},
    }
    for view in ("down", "up", "right"):
        base = body(view)
        a = body(view, legs="a")
        b = body(view, legs="b")

        # Idle: the shoulders heave with each breath
        animations["idle"][view] = Anim(
            [base, squash(base, 1, 26), squash(base, 2, 26), squash(base, 1, 26)], fps=5
        )

        # Walk: a prowling lope, step-settle-pass-rise on each paw
        animations["walk"][view] = Anim(
            [a, shift(a, 0, 1), base, shift(base, 0, -1), b, shift(b, 0, 1), base, shift(base, 0, -1)],
            fps=9,
        )

        # Attack: claws raised, hold, swipe with streaks, follow-through, recover
        windup = body(view, arm="raised")
        if view == "right":
            swipe = paste(body(view, arm="swipe", dx=1), CLAWS_RIGHT, 20, 22)
            hit = shear(body(view, arm="low", dx=1), 2, 40)
        elif view == "down":
            swipe = paste(body(view, arm="swipe", dy=2), CLAWS_DOWN, 21, 3)
            hit = squash(body(view, arm="low", dy=2), 1, 30)
        else:
            swipe = paste(body(view, arm="swipe", dy=0), flip(CLAWS_DOWN), 9, 8)
            hit = squash(body(view, arm="low", dy=0), 1, 30)
        animations["attack"][view] = Anim(
            [windup, shift(windup, 0, -1), swipe, hit, hit, base], fps=10, loop=False
        )

        # Attack 2, the lunging bite: crouch, spring with jaws wide, snap shut, back off
        crouch = squash(base, 2, 30)
        if view == "right":
            spring = shear(body(view, "bite", dx=4), 3, 40)
            snap = shear(body(view, dx=5), 2, 40)
            back = body(view, dx=2)
        elif view == "down":
            spring = body(view, "bite", dy=3)
            snap = body(view, dy=3)
            back = body(view, dy=2)
        else:
            spring = body(view, dy=-2)
            snap = squash(body(view, dy=-2), 1, 30)
            back = body(view, dy=-1)
        animations["attack2"][view] = Anim(
            [crouch, spring, spring, snap, back, base], fps=10, loop=False
        )

        # Special, howl: head back, chest swells, rings roll off the muzzle
        howl = stretch(body(view, "howl"), 1, 30)
        if view == "right":
            rings = [_rings_from(24, 9, r, up=True) for r in (3, 5, 7)]
        elif view == "down":
            rings = [_rings_from(16, 12, r) for r in (4, 6, 8)]
        else:
            rings = [_rings_from(16, 8, r) for r in (4, 6, 8)]
        animations["special"][view] = Anim(
            [
                crouch,
                body(view, "howl"),
                howl,
                compose(W, H, [(howl, 0, 0), (rings[0], 0, 0)]),
                compose(W, H, [(shift(howl, 0, -1), 0, 0), (rings[1], 0, 0)]),
                compose(W, H, [(howl, 0, 0), (rings[2], 0, 0)]),
                compose(W, H, [(howl, 0, 0), (dissolve(rings[2], 0.5), 0, 0)]),
                base,
            ],
            fps=8,
            loop=False,
        )

        # Death: flash, rear back, buckle to the knees, topple, fade
        knees = squash(base, 7, 36)
        lying = _fallen(view)
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                knees,
                shear(knees, -6 if view == "right" else 6, 44),
                lying,
                dissolve(lying, 0.5),
                dissolve(lying, 0.8),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="wolfman",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Pack hunter: a hunched grey werewolf in torn trousers with yellow eyes and long claws. "
            "attack: claw swipe; attack2: lunging bite. Special: howl (head thrown back, sound rings "
            "call the pack to it).",
            shadow=18,
            effects=(
                Effect("howl", howl_effect(), fps=10, loop=False,
                       notes="Sound rings rolling out from the muzzle; centre on the wolfman's head."),
            ),
        )
    )
