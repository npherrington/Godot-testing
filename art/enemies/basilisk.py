"""Basilisk: petrifying gaze.

A squat, heavy, six-legged lizard-serpent, low and long: olive-green scales with a
ribbed tan belly, a row of bony spikes down its spine, a crown of bone plates on a broad
flat head, and burning yellow eyes under heavy brows. Its tail drags and curls.
Attack: a lunging bite.
Special, "petrifying gaze": the eyes flare and a grey-stone beam goes out (Effect gaze).

Built like skeleton_warrior, scaled up: per view, a body (a hand-drawn silhouette mask,
shaded by _batch_b.shade, with belly and spines painted on), a head pasted on, and leg
sets for the gait; animations from those poses with the transforms; left mirrored from
right. _batch_b.place() seals the silhouette in K.
"""

from pixel import (
    Anim,
    ellipse,
    Character,
    Effect,
    Sprite,
    baseline,
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

from enemies._batch_b import place, shade

W, H = 48, 48

STONE = {
    "V": "G", "v": "D", "E": "L", "T": "L", "B": "G", "b": "D", "Y": "W", "O": "L",
    "F": "L", "r": "D", "R": "G", "W": "W", "L": "L", "G": "G", "D": "D",
}


def spines(body: Sprite, cols: list[tuple[int, int]], letter: str = "x") -> Sprite:
    """Bone spikes along the top edge of body: at each (column, size) a spike of size
    rows standing on the body's top pixel there."""
    out = body
    for c, n in cols:
        top = next(y for y, row in enumerate(body) if row[c] != ".")
        for k in range(n):
            y = top - n + k
            spike = "W" if k == 0 else ("WL" if k < n - 1 else "WLG")
            if k == n - 1 and n >= 3:
                spike = "LGG"
            out = paste(out, [spike[: k + 1]], y, c)
    return out


# ---------------------------------------------------------------------------------
# Right: profile, facing right. 48 wide. The hump is highest at the shoulders; the head
# hangs lower and forward on a thick neck; the tail tapers back and curls at its tip.
# ---------------------------------------------------------------------------------

RIGHT_MASK = [
    "................................................",
    "................................................",
    "...............xxxxxxxxxxxx.....................",
    "............xxxxxxxxxxxxxxxxxx..................",
    "..........xxxxxxxxxxxxxxxxxxxxxx................",
    "x.......xxxxxxxxxxxxxxxxxxxxxxxxxx..............",
    "xx....xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...........",
    ".xx..xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx..........",
    ".xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx..........",
    "..xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx..........",
    "...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx..........",
    ".....xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...........",
    "........xxxxxxxxxxxxxxxxxxxxxxxxxxxx............",
    "...........xxxxxxxxxxxxxxxxxxxxxxx..............",
]

# The head, its own drawing: a crown of bone plates, a heavy brow over the eye, the
# nostril at the snout's tip, the long mouth line and a pale jaw. 14 wide; the neck
# joins at its left.
HEAD_RIGHT = [
    "..W....W......",
    "..WL..WL.W....",
    ".WLG.WLGWL....",
    "WLGGWLGGLG....",
    "VLLLLGGGGGLv..",
    "VVVVVLLLLLGVv.",
    "VVVVKKOYYKVVVv",
    "VVVVVVKKKVVVVK",
    "vVVVVVVVVVVVVV",
    "vVVVKKKKKKKKKK",
    "vTTTTTTTTTTTTv",
    ".vBTTTTTTTTBv.",
    "..vvBBBBBBvv..",
]
# Jaws open for the bite: the lower jaw dropped, fangs top and bottom, a red throat
HEAD_RIGHT_BITE = [
    "..W....W......",
    "..WL..WL.W....",
    ".WLG.WLGWL....",
    "WLGGWLGGLG....",
    "VLLLLGGGGGLv..",
    "VVVVVLLLLLGVv.",
    "VVVVKKOYYKVVVv",
    "VVVVVVKKKVVVVK",
    "vVVVVVVVVVVVVV",
    "vVVKWKWKWKWKWK",
    "vVKrrrrrrrr...",
    "vVKrrFFFFr....",
    "vTKWKWKWKWKWK.",
    ".vTTTTTTTTTTv.",
    "..vvBBBBBBvv..",
]
# The gaze: eyes blazing white-gold under the brow
HEAD_RIGHT_GAZE = [r.replace("KKOYYK", "KYWWWY") for r in HEAD_RIGHT]

# Legs, near side: thigh, elbow out, forearm, splayed claws. Two stances for the gait
LEG_RIGHT = [
    ".VVVv..",
    "VVVVv..",
    ".vVVVv.",
    "..vVVv.",
    ".vVVv..",
    "WLWLW..",
]
LEG_RIGHT_FWD = [
    ".VVVv..",
    ".VVVVv.",
    "..vVVVv",
    "...vVVv",
    "...vVVv",
    "..WLWLW",
]
LEG_RIGHT_BACK = [
    ".VVVv..",
    "VVVVv..",
    "vVVv...",
    "vVv....",
    "vVv....",
    "WLWLW..",
]
LEGS_AT_RIGHT = (10, 19, 28)  # near legs' columns, back to front
HEAD_AT = 31  # the head's column on the neck

# ---------------------------------------------------------------------------------
# Down: facing the camera. The broad head low and in front, the hump of the body rising
# behind it with the spine's spikes, the legs stepping back up the screen in pairs
# (front, middle, back), the tail's curl showing past the hump.
# ---------------------------------------------------------------------------------

HEAD_DOWN = [
    ".........WW.........",
    "....W....WL....W....",
    "...WL...WLLG...LW...",
    "..WLG..WLGGGG..GLW..",
    ".WLGGLLGGGGGGLLGGLW.",
    "VLLLLGGGGGGGGGGLLLLv",
    "VVKOYKVVVVVVVVKYOKVv",
    "VVVKKVVVVVVVVVVKKVVv",
    "VVVVVVVEVVVVEVVVVVVv",
    "vVVVVVVVVVVVVVVVVVvv",
    ".vVVVVVKVVVVKVVVVVv.",
    ".vKKKKKKKKKKKKKKKKv.",
    "..vTTTTTTTTTTTTTTv..",
    "...vBBBBBBBBBBBBv...",
]
HEAD_DOWN_BITE = HEAD_DOWN[:11] + [
    ".vKWKWKWKWKWKWKWKWv.",
    ".vKrrrrrrrrrrrrrrKv.",
    ".vKrrrFFFFFFFFrrrKv.",
    ".vKKWKWKWKWKWKWKWKv.",
    "..vTTTTTTTTTTTTTTv..",
    "...vBBBBBBBBBBBBv...",
]
HEAD_DOWN_GAZE = [r.replace("VVKOYKVVVVVVVVKYOKVv", "VVYWWYVVVVVVVVYWWYVv") for r in HEAD_DOWN]

LEG_FRONT_DOWN = [
    "....VVVv",
    "...VVVVv",
    "..VVVvv.",
    ".VVVv...",
    ".vVVv...",
    "..vVv...",
    "..vVVv..",
    ".vVVVv..",
    "WLWLWL..",
]
LEG_MID_DOWN = [
    "...VVVv",
    "..VVVv.",
    ".VVVv..",
    ".vVv...",
    ".vVVv..",
    "WLWLW..",
]
LEG_BACK_DOWN = [
    "..VVv.",
    ".VVv..",
    ".vVv..",
    "vVVv..",
    "LWLW..",
]
TAIL_DOWN = [
    "......Vv",
    ".....VVv",
    "..vVVVv.",
    "vVVVVv..",
]

# ---------------------------------------------------------------------------------
# Up: the back. The head beyond the hump, its crown showing; the spine's spikes running
# down the middle; the tail curling toward us at the bottom.
# ---------------------------------------------------------------------------------

HEAD_UP = [
    ".........WW.........",
    "....W....WL....W....",
    "...WL...WLLG...LW...",
    "..WLG..WLGGGG..GLW..",
    ".WLGGLLGGGGGGLLGGLW.",
    "VLLLLGGGGGGGGGGLLLLv",
    "VVVVVVVVVVVVVVVVVVVv",
    ".VVVVVVVEVVVVVVVVVv.",
    "..vVVVVVVVVVVVVVVv..",
    "....vVVVVVVVVVVv....",
]
TAIL_UP = [
    "VVVVVVVv.......",
    ".VVVVVVVVv.....",
    "..vVVVVVVVv....",
    "....vVVVVVVv...",
    "......vVVVVVv..",
    "........vVVVVv.",
    ".........vVVVv.",
    "..........vVVv.",
    "...........vVv.",
    "...........vV..",
]

for _name, _sprite in list(globals().items()):
    if _name.isupper() and not _name.endswith("MASK") and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)


def _far(s: Sprite) -> Sprite:
    return recolour(s, {"V": "v", "E": "V", "W": "L", "L": "G", "T": "B"})


def _body_right() -> Sprite:
    body = shade(RIGHT_MASK, "V", "V", "v", speck="v")
    # the belly: tan plates under the flank
    grid = [list(r) for r in body]
    for y in range(9, len(grid)):
        for x in range(6, 36):
            if grid[y][x] != "." and (y + 1 >= len(grid) or grid[y + 1][x] == "." or y >= 11):
                grid[y][x] = "B" if x % 3 == 0 else "T"
    for x in range(8, 36):
        if grid[10][x] != ".":
            grid[10][x] = "v" if grid[10][x] in "Vv" else grid[10][x]
    body = ["".join(r) for r in grid]
    # glints on the lit back
    for x in range(14, 30, 5):
        top = next(y for y, row in enumerate(body) if row[x] != ".")
        body = paste(body, ["E"], top + 1, x)
    return spines(body, [(12, 2), (16, 3), (20, 4), (24, 4), (28, 3), (32, 2), (6, 1)])


BODY_RIGHT = _body_right()


# A bone spike of the spine, seen end-on
SPIKE = ["..W..", ".WLG.", "WLGGD"]


def _hump() -> Sprite:
    """The body seen end-on: a low, wide shaded hump, glints on its lit crown."""
    body = shade(ellipse(32, 12, "x"), "V", "V", "v", speck="v")
    for x in (9, 15, 21):
        body = paste(body, ["E"], 2 if x == 15 else 3, x)
    return body


HUMP = _hump()

# ---------------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------------

# Which legs lift for each gait: (left, right) for front, middle, back; -1 lifts a row
GAITS = {0: ((0, 0), (0, 0), (0, 0)), 1: ((-1, 0), (0, -1), (-1, 0)), 2: ((0, -1), (-1, 0), (0, -1))}


def pose_right(head: Sprite = HEAD_RIGHT, gait: int = 0, head_dx: int = 0, dx: int = 0,
               dy: int = 0) -> Sprite:
    """The profile: body, head on its neck, near and far legs in gait 0 (standing),
    1 or 2 (the two tripods of the walk)."""
    bh = len(BODY_RIGHT)
    canvas = blank(W, bh + 6)
    near = [LEG_RIGHT] * 3
    far = [LEG_RIGHT] * 3
    if gait == 1:
        near = [LEG_RIGHT_FWD, LEG_RIGHT_BACK, LEG_RIGHT_FWD]
        far = [LEG_RIGHT_BACK, LEG_RIGHT_FWD, LEG_RIGHT_BACK]
    elif gait == 2:
        near = [LEG_RIGHT_BACK, LEG_RIGHT_FWD, LEG_RIGHT_BACK]
        far = [LEG_RIGHT_FWD, LEG_RIGHT_BACK, LEG_RIGHT_FWD]
    for leg, c in zip(far, LEGS_AT_RIGHT):
        canvas = paste(canvas, _far(leg), bh - 3, c + 4)
    canvas = paste(canvas, BODY_RIGHT, 0, 0)
    canvas = paste(canvas, head, 4, HEAD_AT + head_dx)
    for leg, c in zip(near, LEGS_AT_RIGHT):
        canvas = paste(canvas, leg, bh - 1, c)
    return place(trim_bottom(canvas), W, H, dx=dx, dy=dy)


def pose_down(head: Sprite = HEAD_DOWN, gait: int = 0, head_dy: int = 0, dx: int = 0,
              dy: int = 0) -> Sprite:
    (fl, fr), (ml, mr), (bl, br) = GAITS[gait]
    canvas = blank(44, 24)
    canvas = paste(canvas, TAIL_DOWN, 1, 34)
    canvas = paste(canvas, LEG_BACK_DOWN, 7 + bl, 4)
    canvas = paste(canvas, flip(LEG_BACK_DOWN), 7 + br, 34)
    canvas = paste(canvas, LEG_MID_DOWN, 10 + ml, 1)
    canvas = paste(canvas, flip(LEG_MID_DOWN), 10 + mr, 36)
    canvas = paste(canvas, HUMP, 3, 6)
    canvas = paste(canvas, SPIKE, 1, 19)
    canvas = paste(canvas, SPIKE, 5, 19)
    canvas = paste(canvas, LEG_FRONT_DOWN, 13 + fl, 5)
    canvas = paste(canvas, flip(LEG_FRONT_DOWN), 13 + fr, 31)
    canvas = paste(canvas, head, 8 + head_dy, 12)
    return place(trim_bottom(canvas), W, H, dx=dx, dy=dy)


def pose_up(head: Sprite = HEAD_UP, gait: int = 0, head_dy: int = 0, dx: int = 0,
            dy: int = 0, tail_dx: int = 0) -> Sprite:
    (fl, fr), (ml, mr), (bl, br) = GAITS[gait]
    canvas = blank(44, 26)
    canvas = paste(canvas, head, 0 + head_dy, 12)
    canvas = paste(canvas, LEG_BACK_DOWN, 5 + fl, 5)
    canvas = paste(canvas, flip(LEG_BACK_DOWN), 5 + fr, 33)
    canvas = paste(canvas, LEG_MID_DOWN, 9 + ml, 1)
    canvas = paste(canvas, flip(LEG_MID_DOWN), 9 + mr, 36)
    canvas = paste(canvas, HUMP, 5, 6)
    for r in (5, 9, 13):
        canvas = paste(canvas, SPIKE, r, 19)
    canvas = paste(canvas, LEG_FRONT_DOWN, 14 + bl, 4)
    canvas = paste(canvas, flip(LEG_FRONT_DOWN), 14 + br, 32)
    canvas = paste(canvas, TAIL_UP, 14, 21 + tail_dx)
    return place(trim_bottom(canvas), W, H, dx=dx, dy=dy)


def find(f: Sprite, pattern: str) -> list[tuple[int, int]]:
    """(row, column) of every place pattern appears in f's rows."""
    return [(y, row.index(pattern, x)) for y, row in enumerate(f)
            for x in range(len(row)) if row.startswith(pattern, x)]


def trim_bottom(s: Sprite) -> Sprite:
    while s and not s[-1].strip("."):
        s = s[:-1]
    return s


POSES = {"down": pose_down, "up": pose_up, "right": pose_right}
HEADS = {
    "down": (HEAD_DOWN, HEAD_DOWN_BITE, HEAD_DOWN_GAZE),
    "up": (HEAD_UP, HEAD_UP, HEAD_UP),
    "right": (HEAD_RIGHT, HEAD_RIGHT_BITE, HEAD_RIGHT_GAZE),
}

# ---------------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------------


def _gaze_frame(n: int) -> Sprite:
    """The petrifying beam, flying right: a white core in grey-stone light, a ripple
    rolling along it and chips of stone flaking off."""
    w, h = 32, 12
    f = blank(w, h)
    for x in range(w):
        bulge = 1 if (x + 3 * n) % 8 in (0, 1) else 0
        for y in range(4 - bulge, 8 + bulge):
            d = abs(y - 5.5)
            f = paste(f, ["W" if d < 1 else ("L" if d < 2 else ":")], y, x)
    # stone ripples rolling along it
    for x0 in range(0, w, 8):
        x = (x0 + 3 * n + 1) % w
        for y in (2, 3, 8, 9):
            f = paste(f, ["G" if y in (2, 9) else "L"], y, x)
    # chips of stone flaking off
    for k, (fx, fy) in enumerate(((3, 0), (11, 10), (17, 1), (25, 10), (7, 10), (21, 0))):
        x = (fx + 4 * n + k) % w
        f = paste(f, ["GD" if k % 2 else "DG"], fy, x)
        f = paste(f, ["G"], fy + (1 if fy < 6 else -1), (x + 1) % w)
    return f


GAZE = [_gaze_frame(n) for n in range(4)]

STONE_DUST = [":.:..:", ".:::.:", "::.::."]

# ---------------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------------


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    floor = baseline(H)
    for view, pose in POSES.items():
        calm, bite, gaze = HEADS[view]
        base = pose()
        top = next(y for y, row in enumerate(base) if row.strip("."))
        mid = (top + floor) // 2

        # Idle: slow heavy breaths, then a flick of the forked tongue (from behind, a
        # twitch of the tail)
        breath = squash(base, 1, mid)
        if view == "right":
            flick = paste(base, ["F.F", ".FF", "F.."], floor - 10, HEAD_AT + len(calm[0]) - 1)
        elif view == "down":
            flick = paste(base, ["F", "F", "F.F"], floor - 1, 23)
        else:
            flick = pose(tail_dx=1)
        animations["idle"][view] = Anim([base, breath, breath, flick], fps=6)

        # Walk: the two tripods of six legs in turn; the body sways and the tail drags
        if view == "right":
            steps = [pose(gait=1), pose(gait=1, dy=-1), pose(), pose(dy=-1),
                     pose(gait=2), pose(gait=2, dy=-1), pose(), pose(dy=-1)]
        else:
            steps = [pose(gait=1, dx=-1), pose(gait=1, dx=-1, dy=-1), pose(), pose(dy=-1),
                     pose(gait=2, dx=1), pose(gait=2, dx=1, dy=-1), pose(), pose(dy=-1)]
        animations["walk"][view] = Anim(steps, fps=8)

        # Attack: draw back, jaws gape, lunge and bite, the snap, recover
        if view == "right":
            back = pose(bite, head_dx=-1)
            lunge = pose(bite, head_dx=1, dx=1)
            snap = paste(pose(calm, head_dx=1, dx=1), ["W.", ".W", "W."], floor - 12, W - 2)
        elif view == "down":
            back = pose(bite, head_dy=-2)
            lunge = pose(bite, head_dy=-1, dy=0)
            snap = paste(pose(calm, dy=0), [":W:W:W:"], floor - 1, 20)
        else:
            back = pose(head_dy=1)
            lunge = pose(head_dy=-2)
            snap = paste(pose(head_dy=-2), [":W:W:W:"], top - 2, 20)
        animations["attack"][view] = Anim([back, shift(back, 0, -1), lunge, snap, snap, base], fps=10,
                                          loop=False)

        # Special, petrifying gaze: it settles low, the eyes flare, a beam of grey stone
        # light goes out and stone ripples off it, then it fades
        low = squash(base, 1, mid)
        flare = pose(gaze)
        if view == "right":
            eye_r, eye_c = find(flare, "YWWWY")[0]
            glow = paste(flare, ["*.*", ".*.", "*.*"], eye_r - 1, eye_c + 1)
            beam = paste(flare, crop_beam(GAZE[0], W - eye_c - 4), eye_r - 5, eye_c + 4)
            beam2 = paste(flare, crop_beam(GAZE[1], W - eye_c - 4), eye_r - 5, eye_c + 4)
        elif view == "down":
            eyes = find(flare, "YWWY")
            glow = flare
            for r, c in eyes:
                glow = paste(glow, ["*..*", "....", "*..*"], r - 1, c)
            beam = underlay(glow, ripple(32, 8), floor - 6, 8)
            beam2 = underlay(glow, ripple(44, 10), floor - 8, 2)
        else:
            glow = paste(flare, ["*.*.*.*"], top + 4, 21)
            beam = underlay(flare, rotate_beam(GAZE[0], top + 2), 0, 18)
            beam2 = underlay(flare, rotate_beam(GAZE[1], top + 2), 0, 18)
        animations["special"][view] = Anim(
            [base, low, glow, beam, beam2, beam, glow, base],
            fps=8,
            loop=False,
        )

        # Death: a flash, it rears, slumps flat on its belly, turns to stone in its own
        # reflection, and crumbles
        rear = shear(base, -2, floor)
        flat = squash(base, 3, mid)
        stone = recolour(flat, STONE)
        cracked = underlay(dissolve(stone, 0.4), STONE_DUST, floor - 3, W // 2 - 3)
        animations["death"][view] = Anim(
            [silhouette(base, "W"), rear, flat, stone, cracked, dissolve(stone, 0.8)],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="basilisk",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Petrifying gaze: a squat six-legged crested lizard-serpent with olive "
            "scales, a bony crown and spine spikes, and burning yellow eyes. Attack is a "
            "lunging bite. Special: petrifying gaze (eyes flare, a grey-stone beam goes out).",
            shadow=34,
            effects=(
                Effect("gaze", GAZE, fps=10, loop=True,
                       notes="The petrifying beam: white core in grey-stone light with stone "
                       "chips, flying right; the game stretches or tiles it toward the target."),
            ),
        )
    )


def crop_beam(f: Sprite, w: int) -> Sprite:
    """The first w columns of a beam frame: its start, at the eye."""
    return [row[:w] for row in f]


def ripple(w: int, h: int) -> Sprite:
    """A ring of stone light spreading over the floor."""
    from enemies._batch_b import ring
    return ring(w, h, ":", rim="L", thickness=1.5)


def rotate_beam(f: Sprite, length: int) -> Sprite:
    """The beam turned to go up the screen, its foot at row length, the cell's height."""
    from pixel import rotate
    up = rotate(f, 3)
    up = up[-length:] if length < len(up) else up
    return [r for r in up] + ["." * len(up[0])] * (H - len(up))
