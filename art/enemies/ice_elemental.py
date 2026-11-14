"""Ice Elemental: freezes the player.

A floating figure built of jagged ice crystals round a glowing white core: a crested
crystal head with white eyes, spiked shoulders, detached crystal fists, and a body
that tapers to drifting shards above its shadow. Small shards orbit it and frost haze
hangs round it. attack hurls an ice shard (Effect "ice_shard"). Special, "frost nova":
it draws its shards in to the core, then a ring of frost bursts out across the floor
(Effect "frost_nova"). It dies by its core guttering out and the body shattering.

How it's built: a torso per view (down and up as symmetric halves, drawn as fills
that ol() outlines), fists and trailing shards as parts that drift on their own, and
orbiting shards placed round an ellipse each frame, in front or behind by depth.
"""

import math

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    blank,
    dissolve,
    flip,
    mirror,
    paste,
    recolour,
    rotate,
    shear,
    silhouette,
    size,
    underlay,
    write_character,
)
from enemies._batch_c import check_sprites, compose, dots, ol, puff, ring, shatter, sym

W, H = 48, 48
HOVER = 5
ICE_SHADE = {"I": "C", "C": "U"}

# ---------------------------------------------------------------------------------
# Down: facing the camera. 22 wide, 19 tall torso; fists and tail shards are parts.
# ---------------------------------------------------------------------------------

DOWN_HALF = [
    # 01234567890123
    ".............I",  # 0 the crest
    ".........I...I",
    ".........IC.IC",
    "..I......ICIIC",  # shoulder spikes
    "..IC....ICCICC",
    "..ICI...ICCCCC",  # 5 head
    "I.ICC...CuuWWu",  # eyes in dark sockets
    "IIICCU..ICCCCU",
    ".ICICCU..UCCUu",
    "ICCCICUU..uUuu",  # the shoulder cluster; neck
    "ICCCCCUu.ICCCI",  # 10 chest plates
    ".UCCCUu.ICCCCC",
    "..uUUu.ICCCCUI",  # the core
    "......ICCCCUIW",
    "......UCCCUIWW",
    "......uUCCCUIW",  # 15
    ".......UCCCCUI",
    ".......uUCCCCC",
    "........uUCCCU",  # the body tapers
    ".........uUCCU",
    "..........uUCU",  # 20
    "...........uUU",
    "............uU",
]

UP_HALF = [
    ".............I",
    ".........I...I",
    ".........IC.IC",
    "..I......ICIIC",
    "..IC....ICCICC",
    "..ICI...ICCCCC",  # 5
    "I.ICC...CCCUCC",
    "IIICCU..ICCUCU",
    ".ICICCU..UCUUu",
    "ICCCICUU..uUuu",
    "ICCCCCUu.ICCUC",  # 10
    ".UCCCUu.ICCUCC",
    "..uUUu.ICCCUCC",
    "......ICCCUCCI",  # the core glowing through
    "......UCCCUCII",
    "......uUCCUCCI",  # 15
    ".......UCCUCCC",
    ".......uUCUCCC",
    "........uUUCCU",
    ".........uUCCU",
    "..........uUCU",  # 20
    "...........uUU",
    "............uU",
]

FIST_DOWN = [
    "..I...",
    ".ICI..",
    "ICCCU.",
    "ICCUu.",  # a forearm shard
    ".UCu..",
    "..I...",
    ".ICCI.",
    "ICICCU",  # the fist cluster
    "ICCCUu",
    ".UCUu.",
    "..u...",
]

# Thrust at the camera: the fist big and bright, frost on its knuckles
FIST_PUNCH_DOWN = [
    "..IWI..",
    ".ICWCI.",
    "ICCICCU",
    "ICICCUu",
    ".UCCUu.",
    "..uUu..",
]

# ---------------------------------------------------------------------------------
# Right: profile. The crest sweeps back, the core shows on the chest, a cluster of
# spikes sits on the shoulder.
# ---------------------------------------------------------------------------------

RIGHT_BODY = [
    # 01234567890123456789
    "....I...............",  # 0 the crest swept back
    "....IC..I...........",
    ".....ICIC...........",
    "......ICCII.........",
    ".I....ICCCCC........",  # head; a shoulder spike
    ".IC...ICCCCCI.......",  # 5
    ".ICI..CCCuWWU.......",  # the eye in its socket
    "IICCI.CCCCCCU.......",
    "ICICCU.UCCCU........",  # jaw
    "ICCCCUU.uUu.........",  # neck
    ".UCCCCUICCCCI.......",  # 10 shoulder cluster; chest
    "..uUCUICCCCCCI......",
    "....ICCCCCCUIC......",  # the core, on the chest
    "....UCCCCCUIWI......",
    "....uUCCCCUIWW......",
    ".....UCCCCCUIC......",  # 15
    ".....uUCCCCCU.......",
    "......uUCCCCU.......",
    ".......uUCCCU.......",
    "........uUCCU.......",
    ".........uUCU.......",  # 20
    "..........uUU.......",
    "...........uU.......",
]

FIST_RIGHT = [
    "..I...",
    ".ICI..",
    "ICCCU.",
    ".UCUu.",
    ".ICI..",
    "ICICU.",
    "ICCCUu",
    ".UCUu.",
]

# A fist drawn back and crackling with frost, and thrust out
FIST_BACK_RIGHT = [
    "..IC..",
    ".ICCU.",
    "ICCCUu",
    "ICICU.",
    ".UCUu.",
    "..u...",
]
FIST_PUNCH_RIGHT = [
    "....ICI.",
    "IIICCCWI",
    "UCCCCCIC",
    ".uUUCCUU",
    "....uUu.",
]

# Trailing shards under the body, largest first
SHARDS = [
    [".I..", "ICCU", "ICUu", ".CU.", ".u.."],
    [".I.", "ICU", "CUu", ".u."],
    ["I.", "CU", ".u"],
]
ORBITER = [".I", "IC", "Cu"]

check_sprites(globals())

DOWN_TORSO = sym(DOWN_HALF, ICE_SHADE)
UP_TORSO = sym(UP_HALF, ICE_SHADE)  # the core glows through the back as I

TORSO = {"down": DOWN_TORSO, "up": UP_TORSO, "right": RIGHT_BODY}
CORE = {"down": [(13, 13), (13, 14), (14, 12), (14, 13), (14, 14), (14, 15), (15, 13), (15, 14)],
        "up": [], "right": [(13, 12), (14, 12), (14, 13)]}


def elemental(view: str, phase: float = 0.0, dy: int = 0, dx: int = 0, fists: str = "hang",
              orbit: float = 1.0, core: str = "W", haze: bool = True, tail: float = 0.0,
              squat: int = 0) -> Sprite:
    """The elemental hovering in the cell. phase drives the bob of its parts and the
    orbit of the small shards (orbit scales the orbit's radius: 0 pulls them into the
    core). fists: hang, back (drawn back to throw), punch, spread. core is the core's
    letter (W lit, I dim, u dead). tail trails the lower shards back (walking)."""
    torso = [list(r) for r in TORSO[view]]
    for r, c in CORE[view]:
        torso[r][c] = core if torso[r][c] in "WI" else torso[r][c]
    torso = ["".join(r) for r in torso]
    t = ol(torso)
    tw, th = size(t)
    left = (W - tw) // 2 + dx
    top = H - 2 - HOVER - 8 - th + dy + squat
    out = blank(W, H)
    cx, cy = left + tw / 2, top + 15

    # tail shards, drifting apart and together
    below = top + th - 1
    for k, shard in enumerate(SHARDS):
        drift = round(math.sin(phase + k * 1.3))
        sx = round(cx - len(shard[0]) / 2 - 1 + drift - tail * (k + 1) * (1 if view == "right" else 0))
        out = paste(out, ol(shard), below + k * 3 + (k > 0), sx)
    out = paste(out, t, top, left)

    # fists float beside the body
    bob = round(math.sin(phase + 1.0))
    if view in ("down", "up"):
        f = ol(FIST_DOWN)
        lf, rf = f, ol(flip(recolour(FIST_DOWN, ICE_SHADE)))
        ly = top + 12 + bob
        if fists == "spread":
            out = paste(out, lf, ly - 6, left - 5)
            out = paste(out, rf, ly - 6, left + tw - 1)
        elif fists == "back":
            # the throwing fist cocked high by the shoulder spikes
            out = paste(out, lf, top - 2, left - 4)
            out = paste(out, rf, ly, left + tw - 3)
        elif fists == "punch":
            if view == "down":
                out = paste(out, ol(FIST_PUNCH_DOWN), top + 17, left + tw // 2 - 6)
            else:
                out = underlay(out, lf, top + 8, left + tw // 2 - 6)
            out = paste(out, rf, ly, left + tw - 3)
        else:
            out = paste(out, lf, ly, left - 3)
            out = paste(out, rf, ly - bob * 2, left + tw - 3)
    else:
        if fists == "back":
            out = paste(out, ol(FIST_BACK_RIGHT), top + 9 + bob, left - 3)
        elif fists == "punch":
            out = paste(out, ol(FIST_PUNCH_RIGHT), top + 10, left + tw - 4)
        elif fists == "spread":
            out = paste(out, ol(FIST_RIGHT), top + 3, left + tw - 4)
            out = underlay(out, ol(FIST_RIGHT), top + 3, left - 3)
        else:
            out = underlay(out, ol(FIST_RIGHT), top + 11 - bob, left - 2)
            out = paste(out, ol(FIST_RIGHT), top + 12 + bob, left + tw - 6)

    # orbiting shards: in front when on the near side of the ellipse
    o = ol(ORBITER)
    for k in range(3):
        a = phase + k * 2 * math.pi / 3
        rx, ry = 15 * orbit, 5 * orbit
        ox, oy = round(cx + rx * math.cos(a)) - 2, round(cy + 2 + ry * math.sin(a)) - 2
        out = (paste if math.sin(a) > 0 else underlay)(out, o, oy, ox)

    if haze:
        mist = dots(W, H, [(top + 8 + round(1.5 * math.sin(phase + k)), round(cx - 13 + k * 3), "=") for k in range(9)]
                    + [(below + 9 + (k % 2), round(cx - 4 + k * 2), "=") for k in range(5)])
        out = underlay(out, mist, 0, 0)
    return out


def ice_shard_frames() -> list[Sprite]:
    """An ice shard flying right, glinting as it turns, frost haze streaming off it.
    16x10, four frames, looping."""
    shards = [
        ["....UCCII.....", "=..uUCCCIIW...", "==uUUCCCCIIWW.", "=..uUUCCCIIC..", "....uUUCC....."],
        ["....UCCIW.....", "...uUCCCIIW...", "=uUUCCCCIWWWW.", "==.uUUCCCIC...", "....uUUCC....."],
        ["....UCCII.....", "==.uUCCCIIW...", "=.uUUCCCCIIWW.", "...uUUCCCIIC..", "....uUUCC....."],
        ["....UCCII.....", "=..uUCCCIWW...", "==uUUCCCCIIWW.", "=..uUUCCCIIC..", "....uUUCC....."],
    ]
    return [paste(blank(16, 10), ol(s), 1, 0) for s in shards]


def nova_ring(w: int, h: int, cx: float, cy: float, r: float, seed: int, flat: float = 0.5) -> Sprite:
    """A ring of frost on the floor: a bright rim, haze inside it, and ice spikes
    jutting up off the rim."""
    out = compose(w, h, [
        (ring(w, h, cx, cy, r, r * flat, "=", 3.0, "I"), 0, 0),
        (ring(w, h, cx, cy, max(1, r - 3), max(1, r - 3) * flat, ";", 1.0), 0, 0),
    ])
    spikes = []
    for k in range(10):
        a = seed * 0.4 + k * 2 * math.pi / 10
        x, y = round(cx + r * math.cos(a)), round(cy - r * flat * math.sin(a))
        spikes += [(y - 1, x, "W"), (y - 2, x, "I")]
    return paste(out, dots(w, h, spikes), 0, 0)


def frost_nova_frames() -> list[Sprite]:
    """The frost nova bursting out across the floor and melting away. 80x48, six
    frames; centre it on the elemental's shadow."""
    frames = []
    for n in range(6):
        r = 5 + 7 * n
        f = nova_ring(80, 48, 40, 24, r, n)
        if n < 2:
            f = paste(f, puff(4 + 2 * n, n, "I", "W", "C", "="), 24 - (6 + 2 * n), 40 - (6 + 2 * n))
        frames.append(dissolve(f, min(0.7, 0.12 * n), n, 2))
    return frames


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {"idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {}}
    for view in ("down", "up", "right"):
        tau = 2 * math.pi
        base = elemental(view)

        # Idle: it bobs, the shards turn round it, the core pulses
        animations["idle"][view] = Anim(
            [elemental(view, phase=k * tau / 4, dy=round(math.sin(k * tau / 4)), core="WWIW"[k]) for k in range(4)],
            fps=6,
        )

        # Walk: it glides, leaning into the drift, its tail of shards trailing
        lean = 2 if view == "right" else 0
        walk = []
        for k in range(8):
            p = k * tau / 8
            f = elemental(view, phase=p * 2, dy=round(1.2 * math.sin(p * 2)), tail=1.0)
            walk.append(shear(f, lean, 40) if lean else f)
        animations["walk"][view] = Anim(walk, fps=9)

        # Attack: a fist drawn back, frost gathering on it; thrown forward; the shard
        # leaves; it settles
        charge = elemental(view, fists="back", dx=-1 if view == "right" else 0)
        sparkle = dots(W, H, [(7, 6, "="), (5, 8, "I"), (9, 10, "="), (4, 12, "="), (11, 5, "I")])
        if view == "right":
            sparkle = dots(W, H, [(19, 12, "="), (21, 11, "I"), (17, 13, "=")])
        throw = elemental(view, fists="punch", dx=2 if view == "right" else 0, dy=1 if view == "down" else 0)
        shard = ice_shard_frames()[0]
        if view == "right":
            thrown = paste(throw, shard, 23, 34)
        elif view == "down":
            thrown = paste(throw, rotate(shard, 1), 34, 15)  # flying at the camera
        else:
            thrown = underlay(throw, rotate(shard, 3), -2, 17)  # away up the screen
        animations["attack"][view] = Anim(
            [charge, underlay(charge, sparkle, 0, 0), paste(charge, sparkle, 0, 0), thrown, throw, base],
            fps=10,
            loop=False,
        )

        # Special, frost nova: shards drawn in, the core flares, a ring of frost bursts
        # out across the floor
        cy, cx = H - 7, W // 2
        gather = []
        for k, (ph, o, sq) in enumerate(((0, 0.7, 1), (0.6, 0.4, 2), (1.2, 0.15, 2))):
            body = elemental(view, phase=ph, orbit=o, core="W", squat=sq)
            pull = 14 - 5 * k
            inward = dots(W, H, [(26 + sq + round(pull * 0.5 * math.sin(a)), round(24 + pull * math.cos(a)), "=" if j % 2 else "I")
                                 for j, a in enumerate([k * 0.4 + i * math.pi / 4 for i in range(8)])])
            gather.append(paste(body, inward, 0, 0))
        flare = elemental(view, phase=1.5, orbit=1.3, fists="spread", dy=-2)
        animations["special"][view] = Anim(
            gather + [
                underlay(silhouette(gather[-1], "I"), nova_ring(W, H, cx, cy, 5, 0, 0.42), 0, 0),
                underlay(flare, nova_ring(W, H, cx, cy, 9, 1, 0.42), 0, 0),
                underlay(flare, nova_ring(W, H, cx, cy, 13, 2, 0.42), 0, 0),
                underlay(elemental(view, phase=2, orbit=1.2, fists="spread", dy=-1), dissolve(nova_ring(W, H, cx, cy, 17, 3, 0.42), 0.4), 0, 0),
                elemental(view, phase=2.5, orbit=1.1),
                base,
            ],
            fps=10,
            loop=False,
        )

        # Death: the core gutters and dies, cracks run through it, it bursts apart and
        # the pieces fall and melt away
        dead = elemental(view, core="u", haze=False, orbit=0.6, dy=2)
        ccx, ccy = W / 2, 22
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                dead,
                shatter(dead, ccy, ccx, 0.3, chunk=6, fall=8, floor=45),
                shatter(dead, ccy, ccx, 0.7, chunk=6, fall=26, floor=45),
                dissolve(shatter(dead, ccy, ccx, 1.0, chunk=6, fall=40, floor=45), 0.35),
                dissolve(shatter(dead, ccy, ccx, 1.1, chunk=6, fall=40, floor=45), 0.7),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="ice_elemental",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="A floating figure of jagged ice round a glowing core, shards orbiting it, hovering over its "
            "shadow. attack: hurls an ice shard (fx ice_shard). Special: frost nova (draws its shards in, "
            "then a ring of frost bursts out across the floor and freezes; fx frost_nova).",
            shadow=20,
            effects=(
                Effect("ice_shard", ice_shard_frames(), fps=10, loop=True,
                       notes="Projectile flying right; rotate to the throw direction."),
                Effect("frost_nova", frost_nova_frames(), fps=10, loop=False,
                       notes="Ring of frost spreading over the floor; centre on the elemental's shadow."),
            ),
        )
    )
