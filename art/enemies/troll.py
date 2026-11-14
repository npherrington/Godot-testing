"""Troll: regenerates.

A tall, gangly troll with a mossy grey-green hide, a hunched back knobbed along the
spine, arms so long its knuckles drag on the floor, a drooping hooked nose, stringy
hair, small mean yellow eyes and two stubby tusks.
Special, "regenerate": it hunches, glows green, motes of life rise off it, and it
straightens whole again.

How it's built:
- The head, torso and loincloth are FILLS per view. The arms and legs are drawn from
  joint positions (two-bone IK, limb()), so the long arms swing, reach and drag, and the
  knees bend under each step. union() outlines body and legs together; each near arm is
  outlined on its own so it reads in front of the body, and far limbs sit behind.
- The hide: green (V) shaded dark (v) with a grey (G) rim from the top-left light and
  grey moss patches.
- Death turns it to stone (an old troll weakness), cracks it and crumbles it.
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
    write_character,
)
from enemies._batch_d import (
    capsules,
    fill,
    glow_edge,
    hflip_part,
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
GROUND = 44.5


def hide(sprite: Sprite) -> Sprite:
    """Green hide lit grey from the top left, shaded dark green."""
    return shade(sprite, "V", "G", "v")


def limb(top, end, l1: float, l2: float, bend: int, r1: float, r2: float) -> Sprite:
    mid = ik(top, end, l1, l2, bend)
    return capsules(W, H, [(top[0], top[1], mid[0], mid[1], r1), (mid[0], mid[1], end[0], end[1], r2)], "V")


# Recolourings
GLOW = {"V": "E", "G": "E"}  # regenerating: the hide floods with life
STONE = {"V": "G", "v": "D", "G": "L", "E": "L", "b": "D", "B": "G", "Y": "D", "W": "L", "D": "D"}

# ---------------------------------------------------------------------------------
# Down: facing the camera
# ---------------------------------------------------------------------------------

HEAD_D = spr("""
    ...DDDDDD...
    ..DVVVVVVD..
    .DVVVVVVVVD.
    .DVKKVVKKVD.
    .DVYKVVKYVD.
    .DVVVvvVVVD.
    D.VVvVVvVV.D
    D.VVvVVvVV.D
    D.VvVVVVvV.D
    D..vVVVVv..D
    D..WvvvvW..D
    .D.vKKKKv.D.
    .D..vvvv..D.
    ..D......D..
""")
EAR_D = spr("""
    VV...
    VVVV.
    .VVVV
""")

TORSO_D = spr("""
    ..VG............GV..
    .VGGV..........VGGV.
    VVVGVVV......VVVGVVV
    VVVVVVVVVVVVVVVVVVVV
    .VVVVVvvVVVVvvVVVVV.
    ..VVVVVVVVVVVVVVVV..
    ...VVvVVVVVVVVvVV...
    ...VVVvVVVVVVvVVV...
    ...VvVVVVVVVVVVvV...
    ....VVvVVVVVVvVV....
    .....VVVVvvVVVV.....
    .....VVVVVVVVVV.....
    .....bBBBBBBBBb.....
    .....bBBbBBBbBB.....
    ......BBbBBbBB......
    ......bB.BB.Bb......
""")

HAND_D = spr("""
    .VVVV.
    VVVVVV
    VvVvVv
    V.V.V.
""")

# ---------------------------------------------------------------------------------
# Up: the back. Hair hangs in strings; the spine knobs run down the hump.
# ---------------------------------------------------------------------------------

HEAD_U = spr("""
    ...DDDDDD...
    ..DDDGDDDD..
    .DDDGDDDDDD.
    .DDGDDvDDDD.
    .DDDDDvDDvD.
    D.DvDDvDDv.D
    D.DvDDDDDv.D
    D..DDvDDD..D
    D..D.Dv.D..D
    .D.D.D..D.D.
    .D...D....D.
""")

TORSO_U = spr("""
    ..VG............GV..
    .VGGV..........VGGV.
    VVVGVVV......VVVGVVV
    VVVVVVVVVGGVVVVVVVVV
    .VVVvVVVVvvVVVVvVVV.
    ..VVvVVVVGGVVVVvVV..
    ...VVvVVVvvVVVvVV...
    ...VVVVVVGGVVVVVV...
    ...VVVVVVvvVVVVVV...
    ....VVVVVGGVVVVV....
    .....VVVVvvVVVV.....
    .....VVVVVVVVVV.....
    .....bBBBBBBBBb.....
    .....bBBBbBBBBb.....
    ......BbBBBBbB......
    ......bB.BB.Bb......
""")

# ---------------------------------------------------------------------------------
# Right: profile. Hunched hard: the hump is the highest point, the head juts forward
# below it, the nose hooks down over the tusks.
# ---------------------------------------------------------------------------------

HEAD_R = spr("""
    ..DDDD........
    .DVVVVVV......
    DVVVVVVVVV....
    DVVVVVVVVVV...
    DVVVVKKKVVV...
    DVVVVVYKVVVV..
    D.VVVVVVVVVVV.
    D.VVVVVVVvVVVV
    D..VVVVVvVVVVV
    D..VVKKVvVVVVV
    D...VWKKKVVVV.
    D...vvvvvKVVV.
    .....vvvv..VV.
""")
EAR_R = spr("""
    VV..
    VVV.
    .VVV
""")

TORSO_R = spr("""
    ....GGGG......
    ..GGVVVVVV....
    .GVVVVVVVVVV..
    GVVVVVVVVVVVVV
    GVVVVVVVVVVVVV
    VVVVVVVVVVVVV.
    VVVVVVVVVVVV..
    VVVVVVVVVVV...
    .VVVVVVVVVV...
    .VVVVVVVvVV...
    ..VVVVVVVvV...
    ..VVVVVVvV....
    ..VVVVVVvV....
    ..VVVVVVVV....
    ..bBBBBBBb....
    ..bBBbBBBBb...
    ..BBbBBBbBB...
    ...bB.BBb.Bb..
""")
SPINE_R = [(-1, 4), (-1, 6), (0, 2), (1, 1), (2, 0), (4, -1), (6, -1)]  # knobs along the hump

HAND_R = spr("""
    .VVV.
    VVVVV
    VVvVv
    .V.V.
""")
FOOT_R = spr("""
    VVVV..
    VVVVVV
""")


def _check_all() -> None:
    from pixel import check
    for name, value in list(globals().items()):
        if name.isupper() and isinstance(value, list) and value and isinstance(value[0], str):
            check(value, name)


_check_all()

# ---------------------------------------------------------------------------------
# Poses: joint targets in, a cell out
# ---------------------------------------------------------------------------------

# Where things are with the troll standing at rest, in cell coordinates (x, y)
REST = {
    "down": {
        "hands": ((9.5, 40.0), (38.5, 40.0)), "feet": ((19.5, 43.5), (28.5, 43.5)),
        "shoulders": ((14.5, 16.0), (33.5, 16.0)), "hips": ((21.5, 27.5), (26.5, 27.5)),
    },
    "up": {
        "hands": ((9.5, 40.0), (38.5, 40.0)), "feet": ((19.5, 43.5), (28.5, 43.5)),
        "shoulders": ((14.5, 16.0), (33.5, 16.0)), "hips": ((21.5, 27.5), (26.5, 27.5)),
    },
    "right": {
        "hands": ((27.0, 40.5), (23.0, 40.5)), "feet": ((21.0, 43.5), (16.0, 43.5)),
        "shoulders": ((21.0, 16.0), (18.0, 16.0)), "hips": ((19.0, 27.0), (17.0, 27.0)),
    },
}


def front_back(view: str, hands, feet, dy: int, hy: int, glow: bool) -> Sprite:
    rest = REST[view]
    sh = [(x, y + dy) for x, y in rest["shoulders"]]
    hips = [(x, y + dy) for x, y in rest["hips"]]
    legs = []
    for hip, foot, bend in zip(hips, feet, (1, -1)):
        legs.append((limb(hip, (foot[0], foot[1] - 1), 8.4, 8.4, bend, 1.8, 1.4), 0, 0))
        legs.append((capsules(W, H, [(foot[0] - 2.5, foot[1], foot[0] + 1.5, foot[1], 1.0)], "V")
                     if foot[0] < 24 else
                     capsules(W, H, [(foot[0] - 1.5, foot[1], foot[0] + 2.5, foot[1], 1.0)], "V"), 0, 0))
    torso = TORSO_D if view == "down" else TORSO_U
    out = hide(union(W, H, legs + [(torso, 12 + dy, 14)]))
    for side, (s, hand, bend) in enumerate(zip(sh, hands, (1, -1))):
        wrist = (hand[0], hand[1] - 1)
        hd = HAND_D if side == 0 else hflip_part(HAND_D)
        arm = fill(W, H, [(limb(s, wrist, 13, 13, bend, 1.7, 1.9), 0, 0),
                          (hd, int(hand[1]) - 1, int(hand[0]) - 3)])
        out = over(out, union(W, H, [(hide(arm), 0, 0)]))
    head = HEAD_D if view == "down" else HEAD_U
    out = stamp(out, hide(EAR_D), 8 + dy + hy, 14)
    out = stamp(out, hide(hflip_part(EAR_D)), 8 + dy + hy, 29)
    out = stamp(out, hide(head), 3 + dy + hy, 18)
    return swap(out, GLOW) if glow else out


def profile(hands, feet, dy: int, hy: int, hx: int, lean: int, glow: bool) -> Sprite:
    rest = REST["right"]
    sh = [(x, y + dy) for x, y in rest["shoulders"]]
    hips = [(x, y + dy) for x, y in rest["hips"]]
    # Far limbs: behind, a shade darker
    far = fill(W, H, [
        (limb(hips[1], (feet[1][0], feet[1][1] - 1), 9.5, 9.5, -1, 1.7, 1.3), 0, 0),
        (FOOT_R, int(feet[1][1]), int(feet[1][0]) - 1),
        (limb(sh[1], (hands[1][0], hands[1][1] - 1), 13, 13, 1, 1.6, 1.7), 0, 0),
        (HAND_R, int(hands[1][1]) - 2, int(hands[1][0]) - 2),
    ])
    far = shade(far, "V", "v", "v")
    out = union(W, H, [(far, 0, 0)])
    body = fill(W, H, [
        (limb(hips[0], (feet[0][0], feet[0][1] - 1), 9.5, 9.5, -1, 1.8, 1.4), 0, 0),
        (FOOT_R, int(feet[0][1]), int(feet[0][0]) - 1),
        (TORSO_R, 10 + dy, 13),
        (capsules(W, H, [(23.5, 15.0 + dy, 28.5 + lean, 18.0 + dy + hy, 2.4)], "V"), 0, 0),
    ])
    body = put(body, [(10 + dy + r, 13 + c) for r, c in SPINE_R], "V")
    if lean:
        body = shear(body, lean, 30 + dy)
    out = over(out, union(W, H, [(hide(body), 0, 0)]))
    out = stamp(out, hide(EAR_R), 13 + dy + hy, 24 + hx + lean)
    out = stamp(out, hide(HEAD_R), 12 + dy + hy, 26 + hx + lean)
    arm = fill(W, H, [
        (limb((sh[0][0] + lean, sh[0][1]), (hands[0][0], hands[0][1] - 1), 13, 13, 1, 1.8, 1.9), 0, 0),
        (HAND_R, int(hands[0][1]) - 2, int(hands[0][0]) - 2),
    ])
    out = over(out, union(W, H, [(hide(arm), 0, 0)]))
    return swap(out, GLOW) if glow else out


def pose(view: str, hands=None, feet=None, dy: int = 0, hy: int = 0, hx: int = 0, lean: int = 0,
         glow: bool = False) -> Sprite:
    rest = REST[view]
    hands = hands or rest["hands"]
    feet = feet or rest["feet"]
    if view == "right":
        return profile(hands, feet, dy, hy, hx, lean, glow)
    return front_back(view, hands, feet, dy, hy, glow)


# ---------------------------------------------------------------------------------
# Motes, smears, rubble
# ---------------------------------------------------------------------------------


def motes(k: int, seed: int = 7, n: int = 14, cx: float = 24, spread_: float = 14,
          bottom: float = 42, height: float = 34) -> Sprite:
    """Green motes of life rising and fading, frame k: each mote climbs from low on the
    body to above the head, bright (E) low, haze (%) as it thins."""
    r = rng(seed)
    grid = [["."] * W for _ in range(H)]
    for i in range(n):
        x0 = cx + r.uniform(-spread_, spread_)
        start = r.uniform(0, 1)
        t = (start + k * 0.14) % 1.0
        y = bottom - t * height
        x = x0 + 1.5 * math.sin(t * 6 + i)
        letter = "W" if t < 0.12 and i % 3 == 0 else "E" if t < 0.55 else "%"
        yy, xx = int(y), int(x)
        if 0 <= yy < H and 0 <= xx < W:
            grid[yy][xx] = letter
            if letter == "E" and 0 <= yy + 1 < H and grid[yy + 1][xx] == ".":
                grid[yy + 1][xx] = "%"
    return ["".join(row) for row in grid]


def regen_effect() -> list[Sprite]:
    """24 x 32: sparkles of green life rising, six frames that loop."""
    w, h = 24, 32
    frames = []
    for k in range(6):
        r = rng(11)
        grid = [["."] * w for _ in range(h)]
        for i in range(12):
            x0 = r.uniform(3, w - 3)
            t = (r.uniform(0, 1) + k / 6) % 1.0
            y = int(h - 2 - t * (h - 4))
            x = int(x0 + 1.5 * math.sin(t * 6.28 + i))
            if t < 0.6:
                grid[y][x] = "E"
                if y + 1 < h:
                    grid[y + 1][x] = "%"
                if (i + k) % 4 == 0:  # a twinkle: a little cross
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        if 0 <= y + dy < h and 0 <= x + dx < w:
                            grid[y + dy][x + dx] = "%" if grid[y + dy][x + dx] == "." else grid[y + dy][x + dx]
                    grid[y][x] = "W"
            else:
                grid[y][x] = "%"
        frames.append(["".join(row) for row in grid])
    return frames


def smear(w: int, h: int, cx: float, cy: float, rad: float, a0: float, a1: float) -> Sprite:
    from pixel import arc
    return arc(w, h, cx, cy, rad, a0, a1, ":", thickness=3, edge="W")


def cracks(sprite: Sprite, seed: int) -> Sprite:
    """Dark cracks zigzagging down through the drawn pixels."""
    r = rng(seed)
    grid = [list(row) for row in sprite]
    drawn = [(y, x) for y in range(H) for x in range(W) if sprite[y][x] not in ".K_"]
    for _ in range(7):
        y, x = r.choice(drawn)
        for _ in range(r.randint(3, 6)):
            if 0 <= y < H and 0 <= x < W and grid[y][x] not in ".":
                grid[y][x] = "K"
            y += 1
            x += r.choice((-1, 0, 1))
    return ["".join(row) for row in grid]


RUBBLE = spr("""
    ......LG..........
    ...GGLGDG...GL....
    .GLGDGGGDGGLGDG...
    GDGGDGDGGDGGDGGDG.
""")


def dust(n: int, seed: int, rise: int) -> Sprite:
    r = rng(seed)
    grid = [["."] * W for _ in range(H)]
    for _ in range(n):
        x, y = int(r.uniform(10, 38)), int(r.uniform(28, 44) - rise)
        if 0 <= y < H:
            grid[y][x] = r.choice(":~")
    return ["".join(row) for row in grid]


# ---------------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------------


def walk_frames(view: str) -> list[Sprite]:
    rest = REST[view]
    frames = []
    for f in range(8):
        t = f / 8 * 2 * math.pi
        dy = -1 if f in (2, 6) else 0
        if view == "right":
            nf, ff = rest["feet"]
            nh, fh = rest["hands"]
            near_foot = (nf[0] + 4 * math.cos(t) - 2, nf[1] - 3 * max(0.0, math.sin(t)))
            far_foot = (ff[0] + 4 * math.cos(t + math.pi) + 2, ff[1] - 3 * max(0.0, math.sin(t + math.pi)))
            near_hand = (nh[0] + 4 * math.cos(t + math.pi), nh[1] - 2.5 * max(0.0, math.sin(t + math.pi)))
            far_hand = (fh[0] + 4 * math.cos(t), fh[1] - 2.5 * max(0.0, math.sin(t)))
            frames.append(pose(view, (near_hand, far_hand), (near_foot, far_foot), dy=dy))
        else:
            (lf, rf), (lh, rh) = rest["feet"], rest["hands"]
            lift_l, lift_r = 3 * max(0.0, math.sin(t)), 3 * max(0.0, math.sin(t + math.pi))
            feet = ((lf[0], lf[1] - lift_l), (rf[0], rf[1] - lift_r))
            hands = ((lh[0] + 1.5 * math.cos(t), lh[1] - 2.5 * max(0.0, math.sin(t + math.pi))),
                     (rh[0] - 1.5 * math.cos(t), rh[1] - 2.5 * max(0.0, math.sin(t))))
            frames.append(pose(view, hands, feet, dy=dy))
    return frames


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    for view in ("down", "up", "right"):
        rest = REST[view]
        base = pose(view)
        h0, h1 = rest["hands"]

        # Idle: shoulders heave, the arms sway and the head bobs on its long neck
        animations["idle"][view] = Anim(
            [
                base,
                pose(view, ((h0[0] + 1, h0[1]), (h1[0] - 1, h1[1])), hy=1),
                pose(view, ((h0[0] + 1, h0[1]), (h1[0] - 1, h1[1])), dy=1, hy=1),
                pose(view, hy=1),
            ],
            fps=5,
        )
        animations["walk"][view] = Anim(walk_frames(view), fps=8)

        # Attack: the long arm swipe. Wind up high, sweep through a smear, follow through
        if view == "right":
            windup = pose(view, ((15.0, 10.0), h1), lean=-2, hy=-1)
            sweep = pose(view, ((43.5, 24.0), h1), lean=2, hx=1)
            sweep = over(sweep, smear(W, H, 26, 30, 19, 10, 75))
            follow = pose(view, ((41.0, 38.0), h1), lean=2, hx=1)
            follow = over(follow, smear(W, H, 26, 26, 17, -40, 5))
            settle = pose(view, ((36.0, 40.5), h1), lean=1)
        elif view == "down":
            windup = pose(view, ((7.0, 11.0), h1), hy=-1)
            sweep = pose(view, ((27.0, 38.0), h1), dy=1, hy=1)
            sweep = over(sweep, smear(W, H, 24, 18, 20, 195, 290))
            follow = pose(view, ((33.0, 41.0), h1), dy=1, hy=1)
            settle = pose(view, ((20.0, 41.0), h1))
        else:
            windup = pose(view, (h0, (41.0, 11.0)), hy=1)
            sweep = pose(view, (h0, (22.0, 4.0)), dy=-1, hy=-1)
            sweep = over(sweep, smear(W, H, 24, 20, 18, 40, 110))
            follow = pose(view, (h0, (14.0, 10.0)), dy=-1, hy=-1)
            settle = pose(view, (h0, (30.0, 30.0)))
        animations["attack"][view] = Anim(
            [windup, shift(windup, 0, -1), sweep, follow, settle, base], fps=10, loop=False,
        )

        # Special, regenerate: hunch, glow from within, motes rise, straighten whole
        tuck = (h0, h1) if view != "right" else ((h0[0] - 2, h0[1]), h1)
        hunch = pose(view, tuck, dy=2, hy=1)
        hunch2 = pose(view, tuck, dy=3, hy=2)
        lit = pose(view, tuck, dy=3, hy=2, glow=True)
        animations["special"][view] = Anim(
            [
                base,
                hunch,
                over(over(hunch2, glow_edge(hunch2, "K", "%")), motes(0)),
                over(lit, motes(1)),
                over(over(lit, glow_edge(lit, "K", "%")), motes(2)),
                over(pose(view, tuck, dy=1, hy=1, glow=True), motes(3)),
                over(pose(view, dy=-1), motes(4)),
                over(base, motes(5, n=6)),
            ],
            fps=8, loop=False,
        )

        # Death: flash, reel, sink to the knees, turn to stone, crack, crumble
        slump = pose(view, dy=5, hy=3)
        stone = swap(slump, STONE)
        cracked = cracks(stone, 3)
        rubble = union(W, H, [(RUBBLE, 41, 15)])
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                pose(view, dy=-1, hy=-1, lean=-2) if view == "right" else pose(view, dy=-1, hy=-1),
                slump,
                stone,
                over(cracked, dust(8, 1, 0)),
                over(over(rubble, dissolve(cracked, 0.55)), dust(12, 2, 6)),
            ],
            fps=8, loop=False,
        )

    write_character(
        Character(
            name="troll",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Tall, gangly troll: mossy grey-green hide, a knobbed hunched back, arms that "
            "drag its knuckles, a hooked nose and small yellow eyes; swipes with a long arm. "
            "Special: regenerate (hunches, glows green as motes of life rise, straightens "
            "healed; fx regen).",
            shadow=24,
            effects=(
                Effect(
                    "regen", regen_effect(), fps=8, loop=True,
                    notes="24x32 loop of green life motes rising; centre it on the troll while "
                    "it heals.",
                ),
            ),
        )
    )
