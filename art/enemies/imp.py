"""Imp: fireball caster.

A little red devil, about 19 pixels tall: ivory horns, a pot belly in orange, a wide
toothy grin and big yellow eyes, purple bat wings and a spade-tipped tail. It hovers
over its shadow on beating wings. attack hurls a fireball (Effect "fireball", a
4-frame projectile in the fire ramp with a heat-haze trail). Special, "blink": it
vanishes in a puff of smoke and pops back out of another.

How it's built: a body fill per view (down, up, right), wings as separate fills in
three beats (up, mid, down) tucked behind the body, the throwing arm as a part, and
the tail as a part; everything is outlined by ol() and composed on the cell.
"""

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    blank,
    dissolve,
    erase,
    flip,
    mirror,
    paste,
    recolour,
    shear,
    silhouette,
    size,
    squash,
    underlay,
    write_character,
)
from enemies._batch_c import check_sprites, dots, ol, puff, sym

W, H = 32, 48
HOVER = 6  # rows between the hooves and the baseline
SKIN_SHADE = {"F": "R", "L": "G"}

# ---------------------------------------------------------------------------------
# Down: facing the camera. 14 wide, 19 tall.
# ---------------------------------------------------------------------------------

DOWN_HALF = [
    # 0123456
    ".W.....",  # 0 horn tips curl out
    ".WL....",
    "..LL...",  # horn roots
    "..FFRRR",
    "FFRRRRR",  # ear tips
    ".FRYYRR",  # 5 big eyes
    ".RRYKRR",
    ".rRRRRR",
    "..RWKWK",  # the grin
    "..rRWWW",
    "...rRRR",  # 10 chin
    "...RRFO",
    "..FrROO",  # arm, pot belly
    "..RrROO",
    "..W.ROO",  # claws
    "....RRO",  # 15
    "....RR.",
    "....Rr.",
    "...rKr.",  # hooves
]

# The throwing arm (screen left): its box in the body, rows 11-14, columns 2-3
ARM_BOX = (11, 2, 4, 2)

# Raised overhead with the fireball cupped; at (2, 0)
ARM_UP_DOWN = [
    "W.",
    "RW",
    "FR",
    "FR",
    "Fr",
    "Rr",
    "RR",
    ".R",
    ".R",
    ".R",
]

# Flung forward at the camera; at (11, 1)
ARM_THROW_DOWN = [
    "FRR..",
    ".FrR.",
    "..RRW",
    "..W.W",
]

# ---------------------------------------------------------------------------------
# Up: the back. Horns and ears frame the back of the head; the tail hangs down.
# ---------------------------------------------------------------------------------

UP_HALF = [
    ".W.....",
    ".WL....",
    "..LL...",
    "..FFRRR",
    "FFRRRRR",
    ".FRRRRR",  # 5
    ".RRRRRR",
    ".rRRRRR",
    "..rRRRR",
    "..rrRRR",
    "...rrRR",  # 10 nape
    "...RRFr",
    "..FrRRr",  # the spine
    "..RrRRr",
    "..W.RRr",
    "....RRr",  # 15
    "....RR.",
    "....Rr.",
    "...rKr.",
]

# ---------------------------------------------------------------------------------
# Right: profile. A hooked nose, a pointed ear swept back, the belly out front.
# ---------------------------------------------------------------------------------

RIGHT_BODY = [
    # 0123456789AB
    "W...........",  # 0 horn curls back
    "WL..........",
    ".LL.........",
    "..LFFRR.....",
    "FFRRRRRR....",  # ear swept back
    ".FRRRRYYR...",  # 5 eye
    ".rRRRRYKRR..",
    "..rRRRRRRRR.",  # hooked nose
    "..rRRRWKWKr.",  # grin
    "...rRRRWWW..",
    "....rRRRR...",  # 10 chin
    "....RRRFO...",
    "...FRRROOO..",  # belly out front
    "...RrRROOO..",
    "....rRRROO..",
    ".....RRRR...",  # 15
    ".....RR.RR..",
    "....RR...RR.",
    "....rK...rK.",  # hooves
]

# The near arm hanging, at (11, 5); raised behind the head, at (1, 3); flung out
# in front, at (10, 7)
ARM_HANG_RIGHT = [
    "FR",
    "Rr",
    "Rr",
    "WW",
]
ARM_UP_RIGHT = [
    "W..",
    "RW.",
    "FR.",
    "FR.",
    "Rr.",
    ".Rr",
    ".RR",
    ".FR",
    ".RR",
    "..R",
]
ARM_THROW_RIGHT = [
    "FRR....",
    ".rRRRRW",
    "...rRWW",
]

# ---------------------------------------------------------------------------------
# Wings, drawn as the screen-left wing seen from the front; the shoulder joint is the
# bottom-right corner. Bones in dark red along the leading edge, membrane purple.
# ---------------------------------------------------------------------------------

WING_UP = [
    "r......",
    "rP.....",
    "rPP....",
    ".rPp...",
    ".rPPp..",
    "..rPPp.",
    "..rpPPr",
    "...p.Pr",
    "......r",
]
WING_MID = [
    "rr.......",
    "PPrr.....",
    "pPPPrr...",
    ".pPPPPrr.",
    "..pPpPPPr",
    "...p.p.pr",
]
WING_DOWN = [
    "......r",
    "....rrP",
    "..rrPPp",
    "rrPPPp.",
    "PPpPp..",
    "pp.p...",
]

# The tail: from the rump down and out to the side, ending in a spade
TAIL_DOWN = [
    "r.....",
    "r.....",
    ".r....",
    ".r..R.",
    "..rRRR",
    "...rR.",
]
TAIL_RIGHT = [
    "...r.",
    "..r..",
    "..r..",
    "...r.",
    "R..r.",
    "RRr..",
    "RR...",
]

check_sprites(globals())

DOWN_FULL = sym(DOWN_HALF, SKIN_SHADE)
UP_FULL = sym(UP_HALF, SKIN_SHADE)

# Where things attach, in body-fill coordinates: the wing joint (row, col) for the
# screen-left wing, and the tail root
DOWN_WING_JOINT = (12, 3)
RIGHT_WING_JOINT = (12, 3)
WINGS = {"up": WING_UP, "mid": WING_MID, "down": WING_DOWN}


def _erase(sprite: Sprite, box: tuple[int, int, int, int]) -> Sprite:
    return erase(sprite, *box)


def imp(view: str, wing: str = "mid", arm: str = "hang", dx: int = 0, dy: int = 0,
        fire: Sprite | None = None) -> Sprite:
    """The imp hovering in the cell: its body for the view, wings at a beat, the throwing
    arm in a position, and optionally a fireball sprite in the raised hand."""
    w = WINGS[wing]
    if view in ("down", "up"):
        full = DOWN_FULL if view == "down" else UP_FULL
        body = full
        if arm != "hang" and view == "down":
            body = _erase(body, ARM_BOX)
        if arm != "hang" and view == "up":
            body = _erase(body, (ARM_BOX[0], 14 - ARM_BOX[1] - ARM_BOX[3], ARM_BOX[2], ARM_BOX[3]))
        b = ol(body)
        bw, bh = size(b)
        left = (W - bw) // 2 + dx
        top = H - 2 - HOVER - bh + dy
        out = paste(blank(W, H), b, top, left)
        jr, jc = DOWN_WING_JOINT
        lw, rw = ol(w), ol(recolour(flip(w), {"P": "p"} if view == "down" else {}))
        if view == "down":
            out = underlay(out, lw, top + 1 + jr - len(w), left + 1 + jc - len(w[0]))
            out = underlay(out, rw, top + 1 + jr - len(w), left + 1 + (bw - 2 - 1 - jc))
        else:
            # from behind, the wings grow out of the shoulder blades over the back
            jr, jc = 13, 4
            out = paste(out, lw, top + 1 + jr - len(w), left + 1 + jc - len(w[0]))
            out = paste(out, ol(flip(w)), top + 1 + jr - len(w), left + 1 + (bw - 2 - 1 - jc))
        tail = ol(TAIL_DOWN if view == "down" else flip(TAIL_DOWN))
        if view == "down":
            out = underlay(out, tail, top + 14, left + 7)
        else:
            out = paste(out, ol(TAIL_DOWN), top + 14, left + 6)
        if view == "down":
            if arm == "up":
                out = paste(out, ol(ARM_UP_DOWN), top - 1, left + 0)
                hand = (top + 1, left + 1)
            elif arm == "throw":
                out = paste(out, ol(ARM_THROW_DOWN), top + 11, left + 1)
                hand = (top + 19, left + 7)  # the fireball leaves toward the camera
            else:
                hand = None
        else:
            if arm == "up":
                out = paste(out, ol(flip(ARM_UP_DOWN)), top - 1, left + bw - 4)
                hand = (top + 1, left + bw - 2)
            elif arm == "throw":
                out = underlay(out, ol(flip(ARM_THROW_DOWN)), top + 11, left + bw - 8)
                hand = (top - 3, left + bw // 2 + 2)  # away up the screen
            else:
                hand = None
    else:
        b = ol(RIGHT_BODY)
        bw, bh = size(b)
        left = (W - bw) // 2 + dx
        top = H - 2 - HOVER - bh + dy
        out = paste(blank(W, H), b, top, left)
        jr, jc = RIGHT_WING_JOINT
        # the far wing peeks over the shoulder, the near one spreads behind the back
        out = underlay(out, ol(recolour(w, {"P": "p"})), top + 1 + jr - len(w) - 2, left + 1 + jc - len(w[0]) + 3)
        out = underlay(out, ol(w), top + 1 + jr - len(w), left + 1 + jc - len(w[0]))
        out = underlay(out, ol(flip(TAIL_RIGHT)), top + 13, left - 4)
        parts = {"hang": (ARM_HANG_RIGHT, 11, 5), "up": (ARM_UP_RIGHT, 1, 3), "throw": (ARM_THROW_RIGHT, 10, 7)}
        a, r, c = parts[arm]
        if arm == "up":
            out = underlay(out, ol(a), top + r, left + c)
        else:
            out = paste(out, ol(a), top + r, left + c)
        hand = {"up": (top + 1, left + c + 1), "throw": (top + 11, left + c + 11)}.get(arm)
    if fire is not None and hand is not None:
        fw, fh = size(fire)
        out = paste(out, fire, hand[0] - fh // 2, hand[1] - fw // 2)
    return out


# ---------------------------------------------------------------------------------
# Fire and smoke
# ---------------------------------------------------------------------------------

SPARK = ["^Y^", "YWY", "^Y^"]
SPARK_TRAIL = ["*.^", ".*.", "^.*"]
FLAME = [
    ".^O^.",
    "^ORO^",
    "ORYRO",
    "^OYO^",
    ".^R^.",
]


def fireball_frames() -> list[Sprite]:
    """A fireball flying right: a hot core in the fire ramp with a flickering tail of
    heat haze. 16x12, four frames, looping."""
    cores = [
        [
            "......^^OO....",
            "....^^ORRYO...",
            "..^^^ORYYWYO..",
            "^^^^ORYWWWYR..",
            "..^^^ORYYWYO..",
            "....^^ORRYO...",
            "......^^OO....",
        ],
        [
            ".......^OO....",
            "..^^^^ORYYO...",
            "....^ORYWWYR..",
            ".^^^^ORYWWWYO.",
            "...^^ORYYWYR..",
            "..^^^^ORRYO...",
            ".......^OO....",
        ],
        [
            "......^^OO....",
            "...^^^ORYRO...",
            "^^^^^ORYWWYO..",
            "..^^^ORYWWWYR.",
            "^^^^^ORYYWYO..",
            "...^^^ORRYO...",
            "......^^OO....",
        ],
        [
            ".......^OO....",
            ".^^^^^ORRYO...",
            "...^^ORYYWYR..",
            "^^^^^ORYWWWYO.",
            "..^^^ORYYWYR..",
            ".^^^^^ORYYO...",
            ".......^OO....",
        ],
    ]
    out = []
    for n, core in enumerate(cores):
        f = blank(16, 12)
        f = paste(f, core, 2, 1)
        if n % 2:
            f = paste(f, dots(16, 12, [(1, 9, "*"), (10, 6, "*")]), 0, 0)
        else:
            f = paste(f, dots(16, 12, [(2, 4, "*"), (9, 10, "*")]), 0, 0)
        out.append(f)
    return out


def smoke(r: int, seed: int = 0) -> Sprite:
    """A puff of grey smoke about 2r across."""
    return puff(r, seed, "L", "W", "G", "~")


def _on(frame: Sprite, sprite: Sprite, cy: int, cx: int) -> Sprite:
    """sprite centred on (cy, cx) of frame."""
    w, h = size(sprite)
    return paste(frame, sprite, cy - h // 2, cx - w // 2)


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {"idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {}}
    centre = (H - 2 - HOVER - 10, W // 2)  # the imp's middle, for smoke
    for view in ("down", "up", "right"):
        base = imp(view)

        # Idle: wings beat, the body bobs against them
        animations["idle"][view] = Anim(
            [imp(view, "up", dy=1), imp(view, "mid"), imp(view, "down", dy=-1), imp(view, "mid")], fps=8
        )

        # Walk: it flits along, two wingbeats per cycle with a skip in the bob
        beats = ["up", "mid", "down", "mid", "up", "mid", "down", "mid"]
        bob = [1, 0, -1, -1, 1, 0, -1, 0]
        lean = 1 if view == "right" else 0
        animations["walk"][view] = Anim(
            [shear(imp(view, w, dy=d), lean, 40) if lean else imp(view, w, dy=d) for w, d in zip(beats, bob)],
            fps=10,
        )

        # Attack: conjure a spark, grow it to a fireball overhead, fling it, follow through
        throw_lean = (2 if view == "right" else 0)
        animations["attack"][view] = Anim(
            [
                imp(view, "mid", "up", fire=SPARK),
                imp(view, "up", "up", dy=-1, fire=FLAME),
                imp(view, "up", "up", dy=-2, fire=FLAME),
                shear(imp(view, "down", "throw", dx=1 if view == "right" else 0, dy=1, fire=FLAME), throw_lean, 40),
                imp(view, "mid", "throw", fire=SPARK_TRAIL),
                base,
            ],
            fps=10,
            loop=False,
        )

        # Special, blink: a gleeful crouch, a puff of smoke swallows it, gone, a puff
        # somewhere else and it pops back out
        cy, cx = centre
        p1, p2, p3 = smoke(6, 0), smoke(8, 1), smoke(9, 0)
        animations["special"][view] = Anim(
            [
                squash(imp(view, "up", dy=2), 2, 36),
                _on(dissolve(base, 0.3), p1, cy, cx),
                _on(dissolve(base, 0.7), p2, cy, cx),
                _on(blank(W, H), dissolve(p3, 0.3), cy - 2, cx),
                _on(blank(W, H), dissolve(p3, 0.7), cy - 4, cx),
                blank(W, H),
                _on(dissolve(imp(view, "down"), 0.6), p2, cy, cx),
                _on(dissolve(imp(view, "up"), 0.2), dissolve(p1, 0.5), cy - 2, cx),
                imp(view, "up", dy=-1),
                base,
            ],
            fps=10,
            loop=False,
        )

        # Death: flash, knocked back with wings crumpled, drops to the floor, bursts
        # into smoke and embers
        fallen = imp(view, "down", dy=HOVER)
        embers = dots(W, H, [(30, 10, "*"), (27, 20, "*"), (33, 15, "Y"), (24, 13, "*"), (29, 22, "O")])
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                shear(imp(view, "down", dy=2), -2 if view != "right" else -3, 40),
                squash(fallen, 3, 40),
                _on(paste(dissolve(squash(fallen, 3, 40), 0.5), embers, 0, 0), smoke(8, 0), H - 10, W // 2),
                _on(paste(blank(W, H), dissolve(embers, 0.4), 0, 0), dissolve(smoke(9, 1), 0.5), H - 12, W // 2),
                _on(blank(W, H), dissolve(smoke(10, 0), 0.8), H - 14, W // 2),
            ],
            fps=9,
            loop=False,
        )

    write_character(
        Character(
            name="imp",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Fireball caster: a small red devil with ivory horns, purple bat wings, a spade tail and "
            "a wide grin, hovering. attack: hurls a fireball (fx fireball). Special: blink (vanishes "
            "in a puff of smoke and reappears).",
            shadow=10,
            effects=(
                Effect("fireball", fireball_frames(), fps=10, loop=True,
                       notes="Projectile flying right; rotate to the throw direction. Fire ramp with heat haze."),
            ),
        )
    )
