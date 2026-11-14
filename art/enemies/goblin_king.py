"""Goblin King: elite fighter, boss of the goblins.

A big, broad goblin twice the plain goblin's bulk: green skin, long ears, red eyes
under a heavy brow, a hooked nose and an underbite with tusks. A lopsided gold crown,
an ermine-trimmed red cape, mismatched scrap armour (a riveted breastplate gone to
rust in places, a heavy pauldron, iron boots) and a big cleaver with a hole in its
blade. attack is a cleaver chop; attack2 is a shoulder bash. Special, "war cry": he
thrusts the cleaver up and roars, and a gold aura pulses out to rally his goblins
(Effect "war_cry").

How it's built: the skeleton_warrior shape, drawn as fills that ol() outlines. Down
and up are symmetric halves with a hand-lit face and the crown pasted on; right is a
profile. The cleaver arm is a part per position, and the cleaver is one sprite turned
to each heading with its grip tracked, so it can be put in any fist.
"""

import math

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    arc,
    baseline,
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
    size,
    squash,
    underlay,
    write_character,
)
from enemies._batch_c import SHADE, check_sprites, compose, dots, fill_pose, lift, ol, puff, ring, sym

W, H = 48, 48
KING_SHADE = {k: v for k, v in SHADE.items() if k not in "RY"} | {"W": "L"}

# ---------------------------------------------------------------------------------
# Down: facing the camera. 30 wide, 40 tall (crown included).
# ---------------------------------------------------------------------------------

DOWN_HALF = [
    # 012345678901234
    "...............",  # 0  the crown goes here
    "...............",
    "...............",
    "...............",
    "........EEEEEEE",  # 4 head
    ".......EEEEEEEE",
    "E......EEEEEEEE",  # ear tips
    "EEE...EEEEEEEEE",
    ".EEEE.EEEEEEEEE",
    "..EEEEEEEEEEEEE",
    "...vvvVEEEEEEEE",  # 10
    "......VEEEEEEEE",
    "......VEEEEEEEE",
    "......vVEEEEEEE",
    ".......vVEEEEEE",
    "..L.WWWWWLWWWWW",  # 15 a spike on the pauldron; ermine collar
    ".GLLWDWWWWWDWWL",
    "GLLLLWWLWWLWWLL",  # pauldrons
    "GLWLLGLGLLLLLLL",
    "GLLLGGDGLLWLLGL",
    "DGGGGDDRGLLLLGL",  # 20
    "RrEEVVrRGLLGLGG",  # upper arms; the cape between arm and body
    "RrEVVVrRDGLLGGG",
    "RrEVVVrRDGGLGOG",  # rust
    "RrGLGGrRDGGGGGG",  # bracers
    "RrGGGDrRDDGGGGD",  # 25
    "RrEVVVrRBBBBBBB",  # fists; belt
    "RrVVVvrRBTBBBYY",  # buckle
    "RrVvvvrRbBBBBBB",
    "RrrRRRRRbBTBBTB",  # tassets
    "RrRRRRRRbBBbBBb",  # 30
    "RrRRRRRRbBB.BBb",
    "RrRRRRRRR.VVVV.",  # legs
    "RrRrRRRRR.EVVV.",
    "RrRRRrRRR.GLGG.",  # knee guards
    "RrRRRRrRR.VVVv.",  # 35
    "RrRrRRRRR.VVVv.",
    ".rRRrRRrR.DGGGD",  # iron boots
    "..rR.rR.RDGLGGD",  # the cape's ragged hem
    ".........DDDDDD",
]

# The face, lit from the left, over the symmetric head at (4, 7)
FACE_DOWN = [
    "..EEEEEEEEEEVV..",
    ".EEEEEEEEEEVVVV.",
    "EEEEEEEEEEVVVVVV",
    "EEvvvvEEVvvvvVVV",  # heavy brows
    "EVvKRREEVVRRKvVV",  # red eyes
    "EVVvvEEEEVvvVVVV",
    "EEVVVVEEEVVVVVVV",
    "VEVVVEEEEEVVVVVv",  # nose
    "VVVVvEEEEEvVVVVv",
    "VVVVVvvvvvvVVVVv",  # nostrils
    "VVKKKKKKKKKKKKVv",  # mouth
    "VVWKKKKKKKKKKWVv",  # tusks
    ".vVWVVVVVVVVWVv.",
    "..vVVVVVVVVVVv..",  # underbite jaw
]

# Mouth open, roaring
FACE_ROAR_DOWN = FACE_DOWN[:9] + [
    "VVVVKKKKKKKKVVVv",
    "VVKKrrrrrrrrKKVv",
    "VVWKrrFFFFrrKWVv",
    ".vVWKKKKKKKKWVv.",
    "..vVVVVVVVVVVv..",
]

# Lopsided: tipped down to his left (screen right)
CROWN = [
    "Y..........",
    "YY...Y.....",
    "YWY.YYY..Y.",
    "YYYYYYYY.YY",
    "WYRYYYRYYYY",
    "YYYYYYYYYYO",
    "OOOOYYYYYYO",
    "....OOOOOOO",
]

# The cleaver arm (screen left): its box in the body, rows 21-28, columns 2-6
ARM_BOX = (21, 1, 8, 6)

ARM_RAISED_DOWN = [
    "EVVV.",  # the fist high over the head
    "VVVv.",
    "GLGG.",
    "GGGD.",
    "EVVV.",
    "EVVV.",
    "EVVV.",
    "EVVv.",
    ".EVVv",
    ".EVVv",
]
ARM_FORWARD_DOWN = [
    "EVVv....",
    "EVVVv...",
    ".EVVVv..",
    "..GLGGD.",
    "..GGGGD.",
    "...EVVVv",
    "...VVVvv",
]

# ---------------------------------------------------------------------------------
# Up: the back. The cape covers him from collar to hem; ears, crown and boots show.
# ---------------------------------------------------------------------------------

UP_HALF = [
    "...............",
    "...............",
    "...............",
    "...............",
    "........EEEEEEE",  # 4 the back of the head
    ".......EEVVVVVV",
    "E......EVVVVVVV",
    "EEE...EVVVVVVVV",
    ".EEEE.EVVVVVVVV",
    "..EEEEVVVVVVVVV",
    "...vvvVVVVVVVVV",  # 10
    "......vVVVVVVVV",
    "......vVVVVVVVV",
    "......vvVVVVVVV",
    ".......vvVVVVVV",
    "..L.WWWWWLWWWWW",  # 15 ermine collar
    ".GLLWDWWWWWDWWL",
    "GLLLLWWLWWLWWLW",
    "GLWLRRRRRRRRRRR",  # the cape
    "GLLLRRRRRRRRRRR",
    "DGGGRRrRRRRRrRR",  # 20
    "RrVVRRrRRRRRrRR",
    "RrVVRRrRRRRRrRR",
    "RrVVRRrRRRRRrRR",
    "RrGGRRrRRRRRrRR",
    "RrGGRRrRRRRRrRR",  # 25
    "RrVVRRrRRRRRrRR",
    "RrVVRRrRRRRRrRR",
    "RrVvRRrRRRRRrRR",
    "RrrRRRrRRRRRrRR",
    "RrRRRRrRRRRRrRR",  # 30
    "RrRRRRrRRRRRrRR",
    "RrRRRRrRRRRRrRR",
    "RrRRRRrRRRRRrRR",
    "RrRRRRrRRRRRrRR",
    "RrRRRRrRRRRRrRR",  # 35
    "RrRRRRrRRRRRrRR",
    ".rRRRRrRRRRRrRR",
    "..rR.rR.RrR.rRR",  # ragged hem
    ".........DDDDDD",  # boot heels
]
UP_ARM_BOX = (21, 23, 8, 6)

# ---------------------------------------------------------------------------------
# Right: profile. The cape falls behind him; the near arm swings the cleaver.
# ---------------------------------------------------------------------------------

RIGHT_BODY = [
    # 0123456789012345678901234567
    "............................",  # 0  crown
    "............................",
    "............................",
    "............................",
    ".........EEEEEEE............",  # 4 head
    "........EEEEEEEEE...........",
    "EEE.....EEEEEEEEEE..........",  # the ear swept back
    ".EEEE..EEEEEEEEEEEE.........",
    "..EEEEEEEEEEvvvvEEE.........",  # brow
    "...vvEEEEEEEvKRvEEEE........",  # eye
    "......VEEEEEEvvEEEEEE.......",  # 10 nose
    "......VVEEEEEEEEEEEEEE......",
    "......VVVEEEEEEEVVVVEv......",
    ".......VVVEEEEKKKKKKv.......",  # mouth
    ".......vVVVEEEWKKKKWv.......",  # tusk
    "....WWWWWLVVEVVVVVVv........",  # 15 collar, jaw
    "...WLWWDWWWWLWVVVv..........",
    "..RWWLWWLWWWWLWW............",
    ".RRRRGLLLLLLLLGLL...........",  # breastplate
    ".RrRRGLLWLLLLLLGLL..........",
    "RRrRRGGLLLLLLLLGLL..........",  # 20
    "RRrRRDGGLLLLLLGGL...........",
    "RrRRRDGGGLLLGGOGL...........",  # rust
    "RrRRrDGGGGGGGGGG............",
    "RrRRrDDGGGGGGGGD............",
    "RrRRrBBBBBBBBBBB............",  # 25 belt
    "RrRRrBBBBBBYYBBB............",
    "rRRRrbBBBBBBBBBB............",
    "rRRrRbBTBBTBBTB.............",  # tassets
    "rRRrRbBBbBBbBBb.............",
    "rRrRRRbB..VVVV..............",  # 30
    "rRrRRRRVVVVVVVV.............",
    "rRRrRRRVVV.EVVV.............",
    "rRRrRRRGLG.GLGG.............",
    "rRrRRRRVVV.VVVv.............",
    ".rRRrRRVVV.VVVv.............",  # 35
    ".rRrRRRVVv.VVVv.............",
    "..rRrRDGGGDGGGGDD...........",  # boots
    "...rRRDGGGDGLGGGDD..........",
    "......DDDDDDDDDDDD..........",
]

# Rows 30-39 of the profile, swapped in for the walk: a stride and a passing step
RIGHT_LEGS_A = [
    "rRrRRRbB..VVVV..............",
    "rRrRRRRVVV.VVVVV............",
    "rRRrRRVVV...EVVVV...........",
    "rRRrRRGLG....GLGG...........",
    "rRrRRVVV......VVVv..........",
    ".rRRrVVV.......VVVv.........",
    ".rRrRVVv.......VVVv.........",
    "..rRDGGGD.......DGGGGDD.....",
    "...DGGGGD.......DGLGGGDD....",
    "...DDDDDD.......DDDDDDDD....",
]
RIGHT_LEGS_B = [
    "rRrRRRbB..VVVV..............",
    "rRrRRRRVVVVVVVV.............",
    "rRRrRRRVVVEVVVV.............",
    "rRRrRRRGLGGLGG..............",
    "rRrRRRRVVVVVVv..............",
    ".rRRrRRVVVDGGGGDD...........",
    ".rRrRRRVVvDGLGGGDD..........",
    "..rRrRDGGGDDDDDDDD..........",
    "...rRRDGGGD.................",
    "......DDDDD.................",
]

ARM_HANG_RIGHT = [
    "GLLG..",  # the pauldron
    "GLWLG.",
    "DGGGD.",
    ".EVVv.",
    ".EVVv.",
    ".EVVv.",
    ".GLGG.",
    ".GGGD.",
    ".EVVV.",
    ".VVVv.",
    ".vvvv.",
]
ARM_RAISED_RIGHT = [
    "...EVVv",
    "...VVVv",
    "..GLGGD",
    "..GGGD.",
    "..EVVv.",
    ".EVVv..",
    ".EVVv..",
    "GLLG...",
    "GLWLG..",
    "DGGGD..",
]
ARM_FORWARD_RIGHT = [
    "GLLG.......",
    "GLWLG......",
    "DGGGDVVVGLG",
    ".EVVVVVVGGD",
    ".vVVvvvvEVV",
    "........VVv",
]

check_sprites(globals())

# ---------------------------------------------------------------------------------
# The cleaver: drawn blade-up, turned to each heading; "?" marks the grip
# ---------------------------------------------------------------------------------

CLEAVER_UP = [
    ".DGGGLLW",  # a heavy square-ended blade: spine, flat, bright edge
    "DDGLLLLW",
    "DGLLLLLW",
    "DGLLGLLW",
    "DGLLLLLW",
    "DGLOLLLW",  # rust
    "DGLLLLLW",
    "DGLLLLLW",
    "DGGLLLLW",
    "DDDDDDDD",
    "...bB...",
    "...?B...",
    "...bB...",
    "...bB...",
    "...OO...",
]


def cleaver(heading: str) -> tuple[Sprite, int, int]:
    """The cleaver with its blade towards heading (up, right, down, left), outlined,
    and the (row, column) of its grip."""
    turns = {"up": 0, "right": 1, "down": 2, "left": 3}[heading]
    s = rotate(CLEAVER_UP, turns)
    if heading == "left":
        s = [r for r in s[::-1]]  # keep the edge facing down when held out to the left
    s = ol(s)  # "?" is not a palette letter, so the outline leaves the grip alone
    for r, row in enumerate(s):
        if "?" in row:
            c = row.index("?")
            s[r] = row.replace("?", "b")
            return s, r, c
    raise AssertionError("cleaver has no grip")


def held(heading: str, fist: tuple[int, int]) -> tuple[Sprite, int, int]:
    s, gr, gc = cleaver(heading)
    return s, fist[0] - gr, fist[1] - gc


# ---------------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------------

DOWN_TOP = paste(sym(DOWN_HALF, KING_SHADE), FACE_DOWN, 4, 7)
DOWN_ROAR = paste(sym(DOWN_HALF, KING_SHADE), FACE_ROAR_DOWN, 4, 7)
UP_TOP = sym(UP_HALF, {"E": "V", "W": "L"})
ARM_HANG_DOWN = crop(DOWN_TOP, *ARM_BOX)
ARM_HANG_UP = crop(UP_TOP, *UP_ARM_BOX)

# (arm part, row, col), (fist row, col), cleaver heading, and whether the cleaver goes
# behind the body
DOWN_ARMS = {
    "overhead": ((ARM_RAISED_DOWN, 7, 1), (8, 2), "up", False),
    "hang": ((ARM_HANG_DOWN, 21, 1), (27, 3), "down", False),
    "raised": ((ARM_RAISED_DOWN, 7, 1), (8, 2), "up", False),
    "forward": ((ARM_FORWARD_DOWN, 19, 2), (24, 7), "down", False),
}
UP_ARMS = {
    "overhead": ((flip(ARM_RAISED_DOWN), 7, 24), (8, 27), "up", False),
    "hang": ((ARM_HANG_UP, 21, 23), (27, 26), "down", False),
    "raised": ((flip(ARM_RAISED_DOWN), 7, 24), (8, 27), "up", False),
    "forward": ((flip(ARM_FORWARD_DOWN), 19, 20), (24, 22), "up", True),
}
RIGHT_ARMS = {
    "hang": ((ARM_HANG_RIGHT, 17, 9), (26, 11), "down", False),
    "raised": ((ARM_RAISED_RIGHT, 7, 9), (8, 13), "left", False),
    "overhead": ((ARM_RAISED_RIGHT, 7, 9), (8, 11), "up", True),
    "forward": ((ARM_FORWARD_RIGHT, 17, 9), (21, 18), "down", False),
}
CROWN_AT = {"down": (-2, 10), "up": (-2, 9), "right": (-2, 9)}


def _cape_behind(sprite: Sprite, box: tuple[int, int, int, int]) -> Sprite:
    """The arm's box filled with the cape that hangs behind it."""
    r0, c0, h, w = box
    patch = [("RRrRRR" * w)[:w] for k in range(h)]
    return paste(erase(sprite, *box), patch, r0, c0)


def _step(sprite: Sprite, side: int) -> Sprite:
    """A front or back view with one leg's boot lifted two rows: side 0 the screen-left
    leg, 1 the right."""
    c0 = 9 if side == 0 else 15
    block = crop(sprite, 32, c0, 8, 6)
    return paste(erase(sprite, 32, c0, 8, 6), lift(block, 2, 3), 32, c0)


def king(view: str, arm: str = "hang", face: str = "", dx: int = 0, dy: int = 1, crown: bool = True,
         legs: str = "") -> Sprite:
    """The king in the cell, the cleaver arm in a position, optionally mid-step (legs a
    or b)."""
    if view == "down":
        top, arms, box = (DOWN_ROAR if face == "roar" else DOWN_TOP), DOWN_ARMS, ARM_BOX
    elif view == "up":
        top, arms, box = UP_TOP, UP_ARMS, UP_ARM_BOX
    else:
        top, arms, box = RIGHT_BODY, RIGHT_ARMS, None
    if legs and view != "right":
        top = _step(top, 0 if legs == "a" else 1)
    elif legs:
        top = top[:30] + (RIGHT_LEGS_A if legs == "a" else RIGHT_LEGS_B)
    (part, fist, heading, behind) = arms[arm]
    fill = _cape_behind(top, box) if box else top
    blade = held(heading, fist)
    cr, cc = CROWN_AT[view]
    crown_part = [(CROWN if view != "up" else flip(CROWN), cr, cc)] if crown else []
    # the cleaver is already outlined, so it goes on after fill_pose
    body = fill_pose(W, H, fill, crown_part + ([] if behind else [part]), dx, dy)
    bw, bh = size(ol(fill))
    left, top_row = (W - bw) // 2 + dx, baseline(H) - bh + dy
    s, r, c = blade
    p, pr, pc = part
    if behind:
        out = underlay(body, s, top_row + 1 + r, left + 1 + c)
        return underlay(out, ol(p), top_row + pr, left + pc)
    out = paste(body, s, top_row + 1 + r, left + 1 + c)
    # the fist closes over the handle again
    return paste(out, ol(p), top_row + pr, left + pc)


# A chop's smear: where the blade fell
SMEAR_DOWN = arc(22, 26, 21, 25, 22, 95, 170, ":", 3, "W")
SMEAR_RIGHT = arc(20, 26, 2, 24, 20, 5, 85, ":", 3, "W")
SPARKS = ["*.Y.*", ".*W*.", "YW.WY", ".*W*.", "*.Y.*"]


def aura(cy: int, cx: int, r: float, seed: int) -> Sprite:
    """The war cry's gold aura: a pulsing ring of glow with sparks thrown off it."""
    out = compose(W, H, [
        (ring(W, H, cx, cy, r, r * 0.55, "*", 2.0, "Y", gaps=10, gap_width=0.25, spin=seed * 9), 0, 0),
        (dissolve(ring(W, H, cx, cy, r - 4, (r - 4) * 0.55, "*", 1.0), 0.5, seed), 0, 0),
    ])
    pts = [(round(cy - (r + 3) * 0.55 * math.sin(a)), round(cx + (r + 3) * math.cos(a)), "Y")
           for a in [seed * 0.7 + k * 1.3 for k in range(5)]]
    return paste(out, dots(W, H, pts), 0, 0)


def war_cry_effect() -> list[Sprite]:
    """The rallying pulse that spreads to nearby goblins: a gold ring rolling out,
    sparks riding it, fading as it goes."""
    frames = []
    for n in range(6):
        r = 6 + 6 * n
        f = compose(80, 48, [
            (ring(80, 48, 40, 24, r, r * 0.55, "*", 3.0, "Y", gaps=12, gap_width=0.2, spin=n * 7), 0, 0),
            (ring(80, 48, 40, 24, max(2, r - 5), max(2, r - 5) * 0.55, "*", 1.0), 0, 0),
        ])
        f = dissolve(f, min(0.7, 0.12 * n), n, 1)
        pts = [(round(24 - (r + 2) * 0.55 * math.sin(a)), round(40 + (r + 2) * math.cos(a)), "W")
               for a in [n * 0.5 + k * 1.57 for k in range(4)]]
        frames.append(paste(f, dots(80, 48, pts), 0, 0))
    return frames


def fallen(view: str) -> Sprite:
    """The king face down on the floor, crown gone."""
    fill = {"down": _cape_behind(DOWN_TOP, ARM_BOX), "up": _cape_behind(UP_TOP, UP_ARM_BOX), "right": RIGHT_BODY}[view]
    body = ol(fill[2:])
    lying = rotate(body, 3 if view == "right" else 1)
    return cell(lying, W, H, 0, 1)


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "attack2": {}, "special": {}, "death": {},
    }
    for view in ("down", "up", "right"):
        base = king(view)
        a, b = king(view, legs="a"), king(view, legs="b")

        # Idle: a slow, heavy breath that lifts the pauldrons
        animations["idle"][view] = Anim([base, squash(base, 1, 30), squash(base, 2, 30), squash(base, 1, 30)], fps=5)

        # Walk: a heavy royal stomp
        animations["walk"][view] = Anim(
            [a, shift(a, 0, 1), base, shift(base, 0, -1), b, shift(b, 0, 1), base, shift(base, 0, -1)], fps=8
        )

        # Attack, cleaver chop: heave it up, hold, bring it down with a smear, bite into
        # the floor with sparks, wrench it free
        windup = king(view, "raised") if view == "right" else king(view, "overhead")
        if view == "right":
            chop = paste(shear(king(view, "forward", dx=2), 2, 40), SMEAR_RIGHT, 10, 26)
            hit = paste(shear(king(view, "forward", dx=2, dy=2), 3, 40), SPARKS, 40, 36)
        elif view == "down":
            chop = paste(king(view, "forward", dy=2), SMEAR_DOWN, 8, 0)
            hit = paste(squash(king(view, "forward", dy=2), 2, 34), SPARKS, 40, 8)
        else:
            chop = king(view, "forward", dy=0)
            hit = paste(squash(king(view, "forward", dy=0), 2, 34), SPARKS, 22, 30)
        animations["attack"][view] = Anim(
            [windup, shift(windup, 0, -1), chop, hit, hit, base], fps=10, loop=False
        )

        # Attack 2, shoulder bash: hunker behind the pauldron, drive in, impact, back off
        if view == "right":
            hunker = shear(squash(base, 2, 30), -2, 40)
            bash = shear(king(view, dx=5), 4, 40)
            impact = paste(bash, SPARKS, 16, 38)
            dust = puff(4, 1, "L", "W", "G", ":")
            bash_dust = paste(impact, dust, 34, 2)
            back = king(view, dx=2)
        elif view == "down":
            hunker = squash(base, 3, 30)
            bash = king(view, dy=3)
            bash_dust = paste(bash, SPARKS, 22, 5)
            back = king(view, dy=2)
        else:
            hunker = squash(base, 3, 30)
            bash = king(view, dy=-3)
            bash_dust = paste(bash, puff(4, 1, "L", "W", "G", ":"), 34, 18)
            back = king(view, dy=-1)
        animations["attack2"][view] = Anim([hunker, hunker, bash_dust, bash, back, base], fps=10, loop=False)

        # Special, war cry: cleaver thrust to the ceiling, a roar, the gold aura pulses
        # out twice
        cry = king(view, "overhead", "roar")
        cy = 24
        animations["special"][view] = Anim(
            [
                king(view, "overhead"),
                cry,
                paste(cry, aura(cy, 24, 10, 0), 0, 0),
                paste(shift(cry, 0, -1), aura(cy, 24, 15, 1), 0, 0),
                paste(cry, dissolve(aura(cy, 24, 20, 2), 0.4), 0, 0),
                paste(cry, aura(cy, 24, 11, 3), 0, 0),
                paste(shift(cry, 0, -1), aura(cy, 24, 16, 4), 0, 0),
                paste(cry, dissolve(aura(cy, 24, 21, 5), 0.5), 0, 0),
                base,
            ],
            fps=9,
            loop=False,
        )

        # Death: flash, stagger, down on one knee, topple; the crown bounces off and
        # rolls away, the last thing to fade
        knee = squash(king(view, crown=False), 6, 36)
        lying = fallen(view)
        crown = ol(CROWN)
        roll = rotate(crown, 1)
        sign = -1 if view == "right" else 1
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                paste(shear(knee, -2 * sign, 44), crown, 2, 18),
                paste(shear(knee, 5 * sign, 44), crown, 6, 18 + 6 * sign),
                paste(lying, roll, 30, 24 + 12 * sign),
                paste(dissolve(lying, 0.5), crown, 37, 24 + 15 * sign),
                paste(dissolve(lying, 0.85), dissolve(crown, 0.4), 37, 24 + 15 * sign),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="goblin_king",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Elite goblin boss: big and broad, a lopsided gold crown, an ermine-trimmed red cape, scrap "
            "armour and a heavy cleaver. attack: cleaver chop; attack2: shoulder bash. Special: war cry "
            "(raises the cleaver and roars; a gold aura pulses out and buffs nearby goblins).",
            shadow=26,
            effects=(
                Effect("war_cry", war_cry_effect(), fps=10, loop=False,
                       notes="Gold rally pulse rolling out across the floor; centre on the king's feet."),
            ),
        )
    )
