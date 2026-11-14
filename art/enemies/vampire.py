"""Vampire: life drain.

A gaunt noble with chalk-white skin, slicked black hair in a widow's peak, red eyes and
fangs, in a high-collared black cape lined with blood red, clawed hands at its edges.
Special, "life drain": it throws the cape open like bat wings and streams of blood mist
pour in to it from all round.

How it's built (the skeleton warrior's shape, with batch D's fills):
- Each view is a TORSO (head, collar, cape, suit; no legs) over a set of LEGS, drawn as
  fills and outlined together by union(). In front the cape is open, so the legs show
  through the gap; behind, only the shoes show under the hem.
- Hands and arms are parts stamped on with their own outline, so the claws read over
  the cape. The cape's hem sways a pixel with each step.
- The spread cape (the special) is a pose of its own per view, wings built from one
  half and a flip.
- Left is mirror()ed from right.
"""

import math

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    dissolve,
    mirror,
    shear,
    shift,
    silhouette,
    squash,
    write_character,
)
from enemies._batch_d import (
    fill,
    line,
    polygon,
    hflip_part,
    over,
    put,
    rng,
    shade,
    spr,
    stamp,
    sway,
    swap,
    union,
)

W, H = 32, 48
FOOT_ROW = 44  # the last row of fill; the outline below it stands on the baseline

# ---------------------------------------------------------------------------------
# Down: facing the camera. 22 wide; torso rows 0-27, the legs run from row 20.
# ---------------------------------------------------------------------------------

DOWN_TORSO = spr("""
    ........KKKKKK........
    .......KKDDKKKK.......
    ..p...KKDKKKKKKK...p..
    ..pp..KKKKKKKKKK..pp..
    ..pRp.KKWWKKWWKK.pRp..
    ..pRp.KWWWWWWWWK.pRp..
    ..pRRpKWWRWWRWWKpRRp..
    ..pRRp.WWWWWWWW.pRRp..
    ..prRp.LWWLLWWL.pRrp..
    ..prRp..WWrrWW..pRrp..
    ..prRRp.LLWWLL.pRRrp..
    ..prRRRp.LLLL.pRRRrp..
    .ppprRRpWWRRWWpRRrppp.
    pPpppppRWWWWWWRppppppp
    pPpppppRDWWWWDRppppppp
    pPpKpppRDDWWDDRppKpppp
    pppKpppRDDDDDDRppKpppp
    pppKppRrDDDDDDrRpKpppp
    pppKppRrDDDDDDrRpKpppp
    ppKpppRrKDDDDKrRppKppp
    ppKpppRr......rRppKppp
    ppKpppRr......rRppKppp
    pKppppRr......rRpppKpp
    pKppppRr......rRpppKpp
    pKpppRr........rRppKpp
    KppppRr........rRpppKp
    KpppRr..........rRppKp
    p.pRr............rRp.p
""")

DOWN_LEGS = spr("""
    ........DDDDDD........
    ........DDKKDD........
    ........DD..DD........
    ........DD..DD........
    ........DD..DD........
    ........DD..DD........
    ........DD..DD........
    ........DD..DD........
    ........DK..KD........
    ........DK..KD........
    .......GKK..KKG.......
    ......GKKK..KKKG......
""")
# Screen-left foot lifted, then screen-right
DOWN_LEGS_A = DOWN_LEGS[:8] + [
    ".......GKK..KD........",
    "......GKKK..KD........",
    "............KKG.......",
    "............KKKG......",
]
DOWN_LEGS_B = DOWN_LEGS[:8] + [
    "........DK..KKG.......",
    "........DK..KKKG......",
    ".......GKK............",
    "......GKKK............",
]

DOWN_HAND = spr("""
    WW.
    WLW
    LWL
    W.W
""")

# The striking arm (its right, screen left) out of the cape: raised, and raking across
ARM_UP_D = spr("""
    W.W.W
    WLWLW
    LWWWL
    .LWL.
    .DDD.
    .DDD.
    .DDD.
    ..DDD
    ..DDD
    ..DDD
""")
ARM_RAKE_D = spr("""
    DD.........
    DDD........
    .DDD.......
    ..DDD......
    ...DDD.....
    ....DDDL...
    .....DLWWW.
    ......WLWLW
    ......W.W.W
""")

# ---------------------------------------------------------------------------------
# Up: the back. The collar fans up round the head; the cape hides all but the shoes.
# ---------------------------------------------------------------------------------

UP_TORSO = spr("""
    ........KKKKKK........
    .......KGDKKKKK.......
    ..p...KGDKKKKKKK...p..
    ..pp..KDKKKDKKKK..pp..
    ..ppp.KKKKDKKKKK.ppp..
    ..pppp.KKKDKKKK.pppp..
    ..ppppp.KKDKKK.ppppp..
    ..pppppppppppppppppp..
    ..pPpppppppppppppppp..
    ..pPpppppppppppppppp..
    ...pppppppppppppppp...
    ...pppppppppppppppp...
    .pPpppppppppppppppppp.
    pPpppppppKppppKppppppp
    pPpppppppKppppKppppppp
    pPppppppKppppppKpppppp
    pppKppppKppppppKppppKp
    pppKppppKppppppKppppKp
    pppKpppKppppppppKpppKp
    ppKppppKppppppppKppppK
    ppKppppKppppppppKppppK
    ppKpppKppppppppppKpppK
    pKppppKppppppppppKpppK
    pKppppKppppppppppKpppK
    pKpppKppppppppppppKppp
    KppppKppppppppppppKppp
    pppppppppppppppppppppp
    p.ppp.ppp.pp.ppp.ppp.p
""")

UP_LEGS = spr("""
    ........DD..DD........
    ........DD..DD........
    ........DK..KD........
    .......GKK..KKG.......
    ......GKKK..KKKG......
""")
UP_LEGS_A = [
    "........DD..DD........",
    ".......GKK..DD........",
    "......GKKK..KD........",
    "............KKG.......",
    "............KKKG......",
]
UP_LEGS_B = [
    "........DD..DD........",
    "........DD..KKG.......",
    "........DK..KKKG......",
    ".......GKK............",
    "......GKKK............",
]

# ---------------------------------------------------------------------------------
# Right: profile. The cape hangs down the back (left); the suit shows in front.
# ---------------------------------------------------------------------------------

RIGHT_TORSO = spr("""
    ......KKKKKK........
    ....KKKKKDDKK.......
    ..pKKKKKKKKDDK......
    ..pKKKKKKKKKKWK.....
    ..pRKKKKKLKWWWWW....
    ..pRpKKKLWKWWWRW....
    ..pRp.KKKWWWWWWWW...
    ..pRp..KWWWWWWWL....
    ..prp...LWWWWrrL....
    ..prp...LLWWWWL.....
    ..prRp...LLLLL......
    ..prRp...LLW........
    .pprRRppWWRWW.......
    .pppprRpWWWWWW......
    pPpppppRDWWWWD......
    pPppppppRDWWDD......
    pPpppKppRDDDDD......
    pppppKppRDDDDD......
    pppppKppRDDDDD......
    ppppKpppRDDDDD......
    ppppKppppRDDDD......
    pppKpppppR..........
    pppKpppppR..........
    ppKppppppR..........
    ppKpppppppR.........
    pKppppppppR.........
    pKppppppppR.........
    p.ppp.pppp..........
""")

RIGHT_LEGS = spr("""
    .........DDDD.......
    .........DDDD.......
    .........DDDD.......
    .........DDDD.......
    .........DDKD.......
    .........DD.D.......
    .........DD.D.......
    .........DD.D.......
    .........DK.DK......
    .........DK.DK......
    ........GKKGKKKG....
    ........KKKKKKKKK...
""")
# Stride: back leg trailing, front leg reaching
RIGHT_LEGS_A = spr("""
    .........DDDD.......
    ........DDDDDD......
    ........DD..DD......
    .......DD....DD.....
    .......DD....DD.....
    ......DD......DD....
    ......DD......DD....
    .....DD........DD...
    .....DK........DK...
    ....DK.........DK...
    ...GKK.........GKKG.
    ...KKK.........KKKKK
""")
# Passing: the back foot lifted under the body
RIGHT_LEGS_B = spr("""
    .........DDDD.......
    .........DDDD.......
    .........DDDD.......
    .........DDDD.......
    ........DDKDD.......
    ........DD.DD.......
    ........DD.DD.......
    .......DD..DD.......
    ......GKK..DK.......
    ......KKK..DK.......
    ..........GKKKG.....
    ..........KKKKKK....
""")

ARM_HANG_R = spr("""
    .DD.
    .DD.
    .DD.
    .DD.
    .DD.
    .DD.
    .DDD
    .LW.
    LWWW
    WLW.
    W.W.
""")
# Raised high in front, claws spread
ARM_UP_R = spr("""
    ..W.W.
    ..WLWL
    ..LWWL
    ...LW.
    ...DD.
    ..DDD.
    ..DD..
    .DD...
    .DD...
    DD....
""")
# Thrust forward, claws out
ARM_FWD_R = spr("""
    DDDDDDLW.W.
    DDDDDDWLWLW
    ......LWWWL
    .......W.W.
""")


def _check_all() -> None:
    from pixel import check
    for name, value in list(globals().items()):
        if name.isupper() and isinstance(value, list) and value and isinstance(value[0], str):
            check(value, name)


_check_all()

# ---------------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------------

VIEWS = {
    "down": (DOWN_TORSO, (DOWN_LEGS, DOWN_LEGS_A, DOWN_LEGS_B), 20),
    "up": (UP_TORSO, (UP_LEGS, UP_LEGS_A, UP_LEGS_B), 27),
    "right": (RIGHT_TORSO, (RIGHT_LEGS, RIGHT_LEGS_A, RIGHT_LEGS_B), 20),
}


def body_box(view: str) -> tuple[int, int]:
    """The torso's top-left in the cell when standing."""
    torso, legs, leg_row = VIEWS[view]
    height = leg_row + len(legs[0])
    return FOOT_ROW + 1 - height, (W - len(torso[0])) // 2


def pose(view: str, step: int = 0, parts: list = (), dx: int = 0, dy: int = 0, hem: int = 0,
         torso: Sprite = None, recolour: dict = None) -> Sprite:
    """The view's torso over legs (step 0 stand, 1 and 2 the strides), the hem swung hem
    pixels, then each (sprite, row, col, behind) part stamped in torso coordinates."""
    base_torso, legs, leg_row = VIEWS[view]
    t = torso or base_torso
    t = sway(t, 18, hem)
    t = shade(t, "p", "p", "K")
    if recolour:
        t = swap(t, recolour)
    top, left = body_box(view)
    top, left = top + dy, left + dx
    out = union(W, H, [(legs[step], top + leg_row, left), (t, top, left)])
    for part in parts:
        sprite, r, c = part[:3]
        out = stamp(out, sprite, top + r, left + c, behind=len(part) > 3 and part[3])
    return out


def hands(view: str) -> list:
    if view == "down":
        return [(DOWN_HAND, 17, 5), (hflip_part(DOWN_HAND), 17, 14)]
    if view == "right":
        return [(ARM_HANG_R, 13, 9)]
    return []


# ---------------------------------------------------------------------------------
# The spread cape: arms up, the cape opened like bat wings, the red lining blazing
# ---------------------------------------------------------------------------------

def bat_wing(membrane: str, rib: str, edge: str, sheen: str = "") -> Sprite:
    """The left half of the spread cape, 11 x 21: the hand high at the outer corner, the
    shoulder at the inner edge, ribs fanning from the hand to a scalloped hem."""
    w, h = 11, 21
    hand, shoulder, body = (0.5, 0.5), (10.9, 6.0), (10.9, 20.0)
    tips = [(7.0, 20.8), (3.2, 18.5), (0.5, 14.5)]
    sags = [(8.8, 17.2), (5.0, 16.0), (1.8, 12.5)]
    pts = [hand, shoulder, body]
    for sag, tip in zip(sags, tips):
        pts += [sag, tip]
    s = polygon(w, h, pts, membrane)
    for tip in tips[:2]:
        if sheen:
            s = line(s, (1.0, 2.0), (tip[0] - 1.0, tip[1] - 1.0), sheen, inside_only=True)
        s = line(s, (1.5, 1.0), tip, rib, inside_only=True)
    s = line(s, (1.0, 0.5), (10.5, 5.6), edge, inside_only=True)  # the arm along the top
    s = line(s, (0.5, 1.0), (0.5, 14.0), edge, inside_only=True)  # the outer hem
    return put(s, [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)], "W")  # claws on the corner


WING_D = bat_wing("R", "r", "p", sheen="F")
WING_D_FLARE = bat_wing("R", "F", "p", sheen="W")
WING_U = bat_wing("p", "K", "P")
WING_U_FLARE = bat_wing("p", "r", "P")


def spread(view: str, flare: bool = False) -> Sprite:
    """The cape thrown open, arms high. flare makes the lining blaze."""
    top, left = body_box(view)
    torso, legs, leg_row = VIEWS[view]
    t = shade(torso, "p", "p", "K")
    if flare:
        t = swap(t, {"R": "F"} if view != "up" else {})
    if view == "down":
        core = [row[6:16] for row in t[:22]]  # head, collar and suit; wings replace the flaps
        wing = WING_D_FLARE if flare else WING_D
        body = fill(W, H, [
            (legs[0], top + leg_row, left),
            (core, top, left + 6),
            (wing, top + 4, 1), (hflip_part(wing), top + 4, W - 12),
        ])
    elif view == "up":
        core = [row[5:17] for row in t[:12]] + [row[6:16].center(12, ".") for row in t[12:26]]
        wing = WING_U_FLARE if flare else WING_U
        body = fill(W, H, [
            (legs[0], top + leg_row, left),
            (wing, top + 4, 1), (hflip_part(wing), top + 4, W - 12),
            (core, top, left + 5),
        ])
        return union(W, H, [(body, 0, 0)])
    else:
        # The cape opens behind it like one great wing, lining out; the near arm is high
        wing = WING_D_FLARE if flare else WING_D
        body = fill(W, H, [
            (wing, top + 2, left - 5),
            (legs[0], top + leg_row, left),
            (t, top, left),
        ])
        out = union(W, H, [(body, 0, 0)])
        return stamp(out, ARM_UP_R, top - 3, left + 8)
    return union(W, H, [(body, 0, 0)])


# ---------------------------------------------------------------------------------
# Blood mist: the streams the drain pulls in, and the fx stream
# ---------------------------------------------------------------------------------


def blood_streams(k: int, cx: float, cy: float, n: int = 7) -> Sprite:
    """Streaks of blood mist spiralling in to (cx, cy), frame k of 6: each a droplet (R)
    dragging a trail of mist (!), each arm a little ahead of the last."""
    grid = [["."] * W for _ in range(H)]
    for arm in range(n):
        base = arm * 2 * math.pi / n
        lag = 0.0
        while lag < 0.2:
            t = ((k + arm * 0.6) / 6 - lag) % 1.0  # 0 far out, 1 arrived
            rad = 18 * (1 - t) ** 0.9 + 1.5
            ang = base + 1.8 * (1 - t)
            x = int(cx + rad * math.cos(ang))
            y = int(cy + rad * math.sin(ang) * 0.85)
            letter = "F" if lag < 0.01 else "R" if lag < 0.03 else "!"
            if 0 <= y < H and 0 <= x < W and (grid[y][x] == "." or letter in "RF"):
                grid[y][x] = letter
            lag += 0.008
    return ["".join(r) for r in grid]


def drain_effect() -> list[Sprite]:
    """48 x 14: two strands of blood mist twisting round each other, flowing from the
    right edge (the victim) to the left (the vampire), droplets riding them. The wave and
    the droplets move 4 pixels a frame over a 24-pixel period, so the six frames loop."""
    w, h = 48, 14
    cy = h / 2 - 0.5
    frames = []
    for k in range(6):
        grid = [["."] * w for _ in range(h)]

        def y_at(x: int, phase: float) -> int:
            return int(round(cy + 3.4 * math.sin(2 * math.pi * (x + 4 * k) / 24 + phase)))

        for phase in (0.0, math.pi):
            for x in range(w):
                y = y_at(x, phase)
                grid[y][x] = "!"
                if (x + k) % 4 == 0 and 0 <= y + 1 < h and grid[y + 1][x] == ".":
                    grid[y + 1][x] = "!"
            for d in range(0, w + 12, 12):
                head = (d - 4 * k + (6 if phase else 0)) % (w + 12) - 6
                for i, letter in enumerate("FRRr"):
                    x = head + i
                    if 0 <= x < w:
                        grid[y_at(x, phase)][x] = letter
        frames.append(["".join(row) for row in grid])
    return frames


# Claw rake: three bright scratches through the air
def rake(w: int, h: int, flip: bool = False) -> Sprite:
    grid = [["."] * w for _ in range(h)]
    for k in range(3):
        for i in range(h):
            x = k * 3 + i * (w - 7) // max(1, h - 1)
            for xx, letter in ((x, "W"), (x - 1, ":")):
                if 0 <= xx < w:
                    grid[i][xx] = letter
    s = ["".join(r) for r in grid]
    return hflip_part(s) if flip else s


RAKE_D = rake(14, 9)
RAKE_R = rake(10, 8)

# A cape left on the floor with its collar standing up: the end of death
HEAP = spr("""
    ........pRRp..........
    ......ppRrrRpp........
    ....ppppKppppppp......
    ..pppKpppppppKpppp....
    .ppppppppKppppppppp...
    pRRrRRpppppppRRrRpppp.
    .pp.ppp.pp.ppp.pp.pp..
""")


def dust(n: int, seed: int, cx: int = 16, cy: int = 30, spread_: int = 9, rise: int = 0) -> Sprite:
    """Ash motes (:) and blood mist (!) drifting up."""
    r = rng(seed)
    grid = [["."] * W for _ in range(H)]
    for _ in range(n):
        x = int(cx + r.uniform(-spread_, spread_))
        y = int(cy + r.uniform(-spread_, spread_ * 0.6) - rise)
        if 0 <= x < W and 0 <= y < H:
            grid[y][x] = r.choice(":::!")
    return ["".join(row) for row in grid]


# ---------------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------------


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    for view in ("down", "up", "right"):
        rest = hands(view)
        base = pose(view, parts=rest)

        # Idle: a slow breath, the cape stirring
        top, left = body_box(view)
        breathe = squash(pose(view, parts=rest, hem=1 if view == "right" else 0), 1, top + 16)
        animations["idle"][view] = Anim([base, pose(view, parts=rest, hem=-1 if view == "right" else 0),
                                         breathe, breathe], fps=5)

        # Walk: step, settle, pass, rise on each leg; the hem swings against the stride
        swing = [1, 1, 0, -1, -1, -1, 0, 1] if view == "right" else [0, 1, 0, 0, 0, -1, 0, 0]
        steps = [1, 1, 0, 0, 2, 2, 0, 0]
        bob = [0, 1, 0, -1, 0, 1, 0, -1]
        animations["walk"][view] = Anim(
            [pose(view, steps[f], rest, dy=bob[f], hem=swing[f]) for f in range(8)], fps=8,
        )

        # Attack: claw rake. Cock the arm, lunge with the claws through a smear, recover
        if view == "down":
            other = [(hflip_part(DOWN_HAND), 17, 14)]
            windup = pose(view, parts=other + [(ARM_UP_D, -1, 0)])
            strike = pose(view, 1, other + [(ARM_RAKE_D, 12, 2)], dy=1)
            strike = over(strike, fill(W, H, [(RAKE_D, top + 17, left + 4)]))
            follow = pose(view, 1, other + [(ARM_RAKE_D, 12, 2)], dy=1)
        elif view == "up":
            windup = pose(view, parts=[(hflip_part(ARM_UP_D), -1, 17)])
            strike = pose(view, 1, [(hflip_part(ARM_RAKE_D), 8, 9, True)], dy=-1)
            strike = over(strike, fill(W, H, [(hflip_part(RAKE_D), top - 6, left + 6)]))
            follow = pose(view, 1, [(hflip_part(ARM_RAKE_D), 8, 9, True)], dy=-1)
        else:
            windup = shear(pose(view, parts=[(ARM_UP_R, -3, 8)]), -1, 40)
            strike = shear(pose(view, 1, [(ARM_FWD_R, 13, 9)], dx=1), 2, 40)
            strike = over(strike, fill(W, H, [(RAKE_R, top + 10, left + 15)]))
            follow = shear(pose(view, 1, [(ARM_FWD_R, 13, 9)], dx=1), 1, 40)
        animations["attack"][view] = Anim(
            [windup, shift(windup, 0, -1), strike, follow, follow, base], fps=10, loop=False,
        )

        # Special, life drain: the cape flies open, blood mist spirals in, it drinks
        open_ = spread(view)
        cy = top + 14
        drink = [over(spread(view, flare=k % 2 == 1), blood_streams(k, 16, cy)) for k in range(6)]
        if view == "up":
            drink = [over(spread(view, flare=k % 2 == 1), blood_streams(k, 16, cy - 6)) for k in range(6)]
        animations["special"][view] = Anim(
            [shift(open_, 0, -1), drink[0], drink[1], drink[2], drink[3], drink[4],
             drink[5], base],
            fps=8, loop=False,
        )

        # Death: flash, reel, the flesh greys to ash, collapse, the empty cape, mist
        ashen = {"W": "L", "L": "G", "R": "r", "F": "r"}
        reel = shear(pose(view, parts=rest, dy=-1), -2, 40)
        crumble = dissolve(swap(pose(view, parts=rest), ashen), 0.35)
        heap = fill(W, H, [(HEAP, FOOT_ROW - 6, 5)])
        heap = union(W, H, [(heap, 0, 0)])
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                reel,
                over(crumble, dust(14, 1, cy=top + 10)),
                over(squash(dissolve(crumble, 0.3), 12, 30), dust(18, 2, cy=top + 14, rise=2)),
                over(heap, dust(16, 3, cy=top + 16, rise=5)),
                over(dissolve(heap, 0.6), dust(8, 4, cy=top + 12, rise=8)),
            ],
            fps=8, loop=False,
        )

    write_character(
        Character(
            name="vampire",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Gaunt pale noble: slicked black hair, red eyes and fangs, a high-collared black "
            "cape lined in red; rakes with its claws. Special: life drain (throws the cape open "
            "like bat wings and pulls in streams of blood mist; fx drain).",
            shadow=14,
            effects=(
                Effect(
                    "drain", drain_effect(), fps=10, loop=True,
                    notes="48x14 loop: blood mist flowing from the right edge (the victim) to the "
                    "left (the vampire); stretch or chain it along the line between them.",
                ),
            ),
        )
    )
