"""The player: a young adventurer with a steel sword, a round shield and a red scarf.

8 directions. down, down_right, right, up_right and up are drawn; the left-hand three
are mirrored. Each view is a BODY (head and torso, no arms) on LEGS, with the sword
arm and the shield pasted on as parts, so a frame only names which arm position and
which legs it uses. The states (injured, frozen, poisoned) are recoloured from
normal by pixel.STATES.
"""

from typing import NamedTuple

from pixel import (
    Anim,
    Character,
    Sprite,
    arc,
    baseline,
    cell,
    check,
    ellipse,
    flip,
    mirror,
    outline,
    paste,
    shear,
    shift,
    size,
    squash,
    underlay,
    write_character,
)

W, H = 32, 48

# ---------------------------------------------------------------------------------
# Generated parts: the sword and the shield
# ---------------------------------------------------------------------------------

STEPS = {
    "up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1),
    "up_right": (-1, 1), "down_right": (1, 1), "up_left": (-1, -1), "down_left": (1, -1),
}


def sword(direction: str, length: int = 8) -> tuple[Sprite, int, int]:
    """A steel sword with a gold guard pointing direction, and its grip's (row, column)."""
    dr, dc = STEPS[direction]
    pr, pc = -dc, dr
    px: dict[tuple[int, int], str] = {(0, 0): "B", (-dr, -dc): "Y"}
    for k in (-1, 0, 1):
        px[(dr + k * pr, dc + k * pc)] = "Y" if k == 0 else "O"
    for i in range(2, length + 2):
        px[(dr * i, dc * i)] = "W"
        if dr and dc:
            px.setdefault((dr * i + 1, dc * i), "L")
        elif dr:  # vertical: a shaded edge on the right
            px.setdefault((dr * i, 1), "L")
        else:  # horizontal: shaded underside
            px.setdefault((1, dc * i), "L")
    r0 = min(r for r, _ in px) - 1
    c0 = min(c for _, c in px) - 1
    h = max(r for r, _ in px) - r0 + 2
    w = max(c for _, c in px) - c0 + 2
    grid = [["."] * w for _ in range(h)]
    for (r, c), letter in px.items():
        grid[r - r0][c - c0] = letter
    return outline(["".join(row) for row in grid]), -r0, -c0


def shield(w: int, h: int, back: bool = False) -> Sprite:
    """A round wooden shield w x h (narrow when seen at an angle): iron rim, planks,
    a gold boss; lit from the top left. back: the inside, dark planks and a strap."""
    body = ellipse(w, h, "B")
    rows = [list(r) for r in body]
    cy, cx = (h - 1) / 2, (w - 1) / 2
    for y in range(h):
        for x in range(w):
            if rows[y][x] == ".":
                continue
            edge = any(
                not (0 <= y + dy < h and 0 <= x + dx < w) or body[y + dy][x + dx] == "."
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if edge:
                rows[y][x] = "L" if (y < cy and x <= cx + 1) else "G"
            elif back:
                rows[y][x] = "T" if abs(y - cy) < 1 else ("b" if x % 2 else "B")
            elif (x - round(cx)) % 3 == 0:
                rows[y][x] = "b"
            elif y < cy - 1 and x < cx:
                rows[y][x] = "T"
    if back:
        return outline(["".join(r) for r in rows])
    by, bx = round(cy - 0.5), round(cx - 0.5)
    for y, x, letter in ((by, bx, "Y"), (by, bx + 1, "Y"), (by + 1, bx, "Y"), (by + 1, bx + 1, "O")):
        if 0 <= y < h and 0 <= x + (1 if w < 6 else 0) < w and w >= 4:
            rows[y][min(x, w - 2)] = letter
    return outline(["".join(r) for r in rows])


# ---------------------------------------------------------------------------------
# Down: facing the camera. Body 14 wide: head rows 0-12, torso 13-20, legs 21-27.
# Sword arm on screen left, shield on screen right.
# ---------------------------------------------------------------------------------

DOWN_BODY = [
    ".....KK.KK....",
    "...KKTBKBTKK..",
    "..KBTTBBBTTBK.",
    ".KBTBBBBBBBTBK",
    ".KBBBBBBBBBBBK",
    "KUUUUUUUUUUUuK",
    "KBBSSSSSSSSBBK",
    "KBSSSSSSSSSSBK",
    "KBSSKSSSSKSSBK",
    "KBSSKSSSSKSSBK",
    ".KSSSSSSSSSTK.",
    "..KTSSSSSSTK..",
    "...KKKKKKKK...",
    "...KRRRRRRK...",
    "..KRRRRRRrRK..",
    "..KUrRUUCUuK..",
    "..KUrRUUCUuK..",
    "..KBBBYYBBbK..",
    "..KUUUUUUUuK..",
    "..KUUUUUUUuK..",
    "..KKKKKKKKKK..",
]

DOWN_LEGS = [
    "...KTTKKTTK...",
    "...KTTKKTTK...",
    "...KTbKKTbK...",
    "...KBBKKBBK...",
    "..KBBBKKBBBK..",
    "..KbbbKKbbbK..",
    "..KKKKKKKKKK..",
]

# Screen-left leg lifted two rows
DOWN_LEGS_A = [
    "...KTTKKTTK...",
    "...KBBKKTTK...",
    "..KBBBKKTbK...",
    "..KbbbKKBBK...",
    "..KKKKKKBBBK..",
    ".......KbbbK..",
    ".......KKKKK..",
]
DOWN_LEGS_B = flip(DOWN_LEGS_A)

ARM_DOWN = {
    # name: (sprite, row, column) in body coordinates
    "rest": ([
        ".KKK",
        "KUUK",
        "KUuK",
        "KBBK",
        "KSSK",
        "KSSK",
        ".KK.",
    ], 13, 0),
    "raised": ([
        ".KK.",
        "KSSK",
        "KSSK",
        "KBBK",
        "KUUK",
        "KUuK",
        "KUUK",
    ], 7, 0),
    "forward": ([
        ".KKK...",
        "KUUUK..",
        "KUuUUK.",
        ".KKBBSK",
        "...KSSK",
        "....KK.",
    ], 13, 1),
}
FIST_DOWN = {"rest": ((18, 1), "down_left", 6), "raised": ((8, 1), "up", 8), "forward": ((16, 5), "down_left", 8)}

SHIELD_REST_DOWN = (shield(5, 11), 13, 11)
SHIELD_UP_DOWN = (shield(11, 12), 12, 2)

SMEAR_DOWN = arc(18, 20, 17, 19, 16, 100, 175, ":", thickness=3, edge="W")


# ---------------------------------------------------------------------------------
# Right: profile, facing right. Body 15 wide: the headband's tails fly off the back
# (columns 0-1). The sword arm is the near one; the shield is on the far arm, so at
# rest only its rim shows past the chest.
# ---------------------------------------------------------------------------------

RIGHT_BODY = [
    "......KK.KK....",
    "....KKTBKBTKK..",
    "...KBTTBBBTTBK.",
    "..KBBBBBBBBBTBK",
    "..KBBBBBBBBBBBK",
    ".KKuUUUUUUUUUUK",
    "KUUKBBBBSSSSSSK",
    ".KuKBBBSSSSSSSK",
    "..KBBBBSSSSKSSK",
    "..KBBBSSSSSKSSK",
    "...KBBSSSSSSSSK",
    "....KBTSSSSSTK.",
    ".....KKKKKKKK..",
    ".KK...KRRRRK...",
    "KRrK.KRRRRrRK..",
    ".KRRKKUURRUuK..",
    "..KKKKUUUCUuK..",
    ".....KUUUCUuK..",
    ".....KBBBBYbK..",
    ".....KUUUUUuK..",
    ".....KUUUUUuK..",
    ".....KKKKKKKK..",
]

RIGHT_LEGS = [
    "......KTTTTK...",
    "......KTTbTK...",
    "......KTbKTK...",
    "......KBBKBK...",
    "......KBBKBBK..",
    "......KbbKbbbK.",
    "......KKKKKKKK.",
]

# Stride: back leg trailing, front leg reaching
RIGHT_LEGS_A = [
    "......KTTTTK...",
    ".....KTTbKTTK..",
    ".....KTbK.KTTK.",
    "....KBBK...KBBK",
    "...KBBK....KBBK",
    "...KbbK....KbbbK"[:15],
    "...KKKK....KKKK",
]

# Passing: the far leg lifted under the body
RIGHT_LEGS_B = [
    "......KTTTTK...",
    "......KTTbTK...",
    "......KTKBBK...",
    "......KBKBBBK..",
    "......KBKbbbK..",
    "......KbbKKKK..",
    "......KKKK.....",
]

ARM_RIGHT = {
    "rest": ([
        ".KKK",
        "KUUK",
        "KUuK",
        "KBBK",
        "KSSK",
        "KSSK",
        ".KK.",
    ], 13, 6),
    "raised": ([
        ".KK.",
        "KSSK",
        "KSSK",
        "KBBK",
        "KUUK",
        "KUuK",
        "KUUK",
        "KUUK",
    ], 6, 6),
    "forward": ([
        ".KKK.....",
        "KUUUKKKK.",
        "KUuUBBSSK",
        ".KKKKKSSK",
        "......KK.",
    ], 13, 6),
}
FIST_RIGHT = {
    "rest": ((18, 7), "down_right", 6),
    "raised": ((7, 7), "up_left", 8),
    "forward": ((15, 13), "right", 8),
}
SHIELD_REST_RIGHT = (shield(4, 11), 13, 11)
SHIELD_UP_RIGHT = (shield(6, 13), 12, 11)
SMEAR_RIGHT = arc(18, 20, 1, 19, 17, 5, 85, ":", thickness=3, edge="W")

# ---------------------------------------------------------------------------------
# Down-right: three-quarters front. The face has turned right; more of the shield
# shows, and the sword arm sits further back on screen left.
# ---------------------------------------------------------------------------------

DOWN_RIGHT_BODY = [
    ".....KK.KK....",
    "...KKTBKBTKK..",
    "..KBTTBBBTTBK.",
    ".KBTBBBBBBBTBK",
    ".KBBBBBBBBBBBK",
    "KuUUUUUUUUUUUK",
    "KBBBBSSSSSSSBK",
    "KBBBSSSSSSSSSK",
    "KBBSSSKSSSKSSK",
    "KBBSSSKSSSKSSK",
    ".KBSSSSSSSSSTK",
    "..KTSSSSSSSTK.",
    "...KKKKKKKKK..",
    "...KRRRRRRK...",
    "..KRRRRRrRRK..",
    "..KUUrRUUCuK..",
    "..KUUrRUUCuK..",
    "..KBBBBBYYbK..",
    "..KUUUUUUUuK..",
    "..KUUUUUUUuK..",
    "..KKKKKKKKKK..",
]

ARM_DOWN_RIGHT = {
    "rest": (ARM_DOWN["rest"][0], 13, 0),
    "raised": (ARM_DOWN["raised"][0], 7, 0),
    "forward": ([
        ".KKK....",
        "KUUUK...",
        "KUuUUKK.",
        ".KKKBBSK",
        "....KSSK",
        ".....KK.",
    ], 13, 1),
}
FIST_DOWN_RIGHT = {
    "rest": ((18, 1), "down_left", 6),
    "raised": ((8, 1), "up", 8),
    "forward": ((16, 6), "down_right", 8),
}
SHIELD_REST_DOWN_RIGHT = (shield(7, 11), 13, 10)
SHIELD_UP_DOWN_RIGHT = (shield(10, 12), 12, 5)
SMEAR_DOWN_RIGHT = arc(20, 22, 2, 2, 19, 280, 355, ":", thickness=3, edge="W")

# ---------------------------------------------------------------------------------
# Up-right: three-quarters back. The back of the head, a cheek and ear on the
# right; the sword arm on screen right, the shield's back on screen left.
# ---------------------------------------------------------------------------------

UP_RIGHT_BODY = [
    "....KK.KK.....",
    "..KKTBKBTKK...",
    ".KBTTBBBTTBK..",
    "KBTBBBBBBBTBK.",
    "KBBBBBBBBBBBK.",
    "KUUUUUUUUUuUK.",
    "KBBBBBBBBBBSK.",
    "KBBBBBBBBBBSSK",
    "KBBBBBBBBBTSSK",
    "KBBBBBBBBBTSK.",
    ".KBBBBBBBBBTK.",
    "..KBBBBBBBTK..",
    "...KKKKKKKK...",
    "...KRRRRRRK...",
    "..KRRRRRRRrK..",
    "..KUURRrUUuK..",
    "..KUURRrUUuK..",
    "..KBBRRrBBbK..",
    "..KUUKRrUUuK..",
    "..KUUUKKUUuK..",
    "..KKKKKKKKKK..",
]

# ---------------------------------------------------------------------------------
# Up: the back. Hair, the headband's knot and tails, the scarf hanging down the back.
# ---------------------------------------------------------------------------------

UP_BODY = [
    ".....KK.KK....",
    "...KKTBKBTKK..",
    "..KBTTBBBTTBK.",
    ".KBTBTBBTBBTBK",
    ".KBBTBBBBTBBBK",
    "KUUUUUUUUUUUuK",
    "KBTBBBBBBBTBBK",
    "KBTBbBBBBBTbBK",
    "KBBBbBBBBBBbBK",
    "KBBBBBBBBBBbBK",
    ".KBBbBBBBBbBK.",
    "..KbBBBBBBbK..",
    "...KKKKKKKK...",
    "...KRRRRRRK...",
    "..KRRRRRRRrK..",
    "..KUUURRrUuK..",
    "..KUUURRrUuK..",
    "..KBBBRRrBbK..",
    "..KUUUKRrUuK..",
    "..KUUUUKKUuK..",
    "..KKKKKKKKKK..",
]

UP_LEGS = [
    "...KTTKKTTK...",
    "...KTTKKTTK...",
    "...KTbKKTbK...",
    "...KBBKKBBK...",
    "...KBBKKBBK...",
    "..KbbbKKbbbK..",
    "..KKKKKKKKKK..",
]
UP_LEGS_A = [
    "...KTTKKTTK...",
    "...KBBKKTTK...",
    "...KBBKKTbK...",
    "..KbbbKKBBK...",
    "..KKKKKKBBK...",
    ".......KbbbK..",
    ".......KKKKK..",
]
UP_LEGS_B = flip(UP_LEGS_A)


def _mirror_arm(arm: dict, width: int = 14) -> dict:
    """The down view's arm positions on the other side of the body, flipped."""
    return {k: (flip(s), r, width - c - len(s[0])) for k, (s, r, c) in arm.items()}


ARM_UP = _mirror_arm(ARM_DOWN)
FIST_UP = {
    "rest": ((18, 12), "down_right", 6),
    "raised": ((8, 12), "up", 8),
    "forward": ((4, 9), "up", 9),
}
SHIELD_REST_UP = (shield(5, 11, back=True), 13, -2)
SHIELD_UP_UP = (shield(18, 14), 11, -2)
SMEAR_UP = arc(22, 16, 20, 15, 15, 90, 175, ":", thickness=3, edge="W")

ARM_UP_RIGHT = _mirror_arm(ARM_DOWN)
FIST_UP_RIGHT = {
    "rest": ((18, 12), "down_right", 6),
    "raised": ((8, 12), "up", 8),
    "forward": ((6, 11), "up_right", 9),
}
SHIELD_REST_UP_RIGHT = (shield(5, 11, back=True), 13, -1)
SHIELD_UP_UP_RIGHT = (shield(16, 13), 12, -3)
SMEAR_UP_RIGHT = arc(20, 18, 2, 17, 16, 20, 100, ":", thickness=3, edge="W")

# ---------------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------------


class View(NamedTuple):
    body: Sprite  # head and torso, no arms
    legs: tuple[Sprite, Sprite, Sprite]  # standing, step A, step B
    arm: dict[str, tuple[Sprite, int, int]]  # sword arm per position
    fist: dict[str, tuple[tuple[int, int], str, int]]  # grip position, blade direction, blade length
    shield_rest: tuple[Sprite, int, int]
    shield_up: tuple[Sprite, int, int]
    smear: tuple[Sprite, int, int]
    behind: frozenset = frozenset()  # parts drawn under the body: "shield", "arm:<position>"
    chest: int = 16  # the body row squashed to breathe


VIEWS: dict[str, View] = {
    "down": View(
        DOWN_BODY, (DOWN_LEGS, DOWN_LEGS_A, DOWN_LEGS_B), ARM_DOWN, FIST_DOWN,
        SHIELD_REST_DOWN, SHIELD_UP_DOWN, (SMEAR_DOWN, 0, -5),
    ),
    "down_right": View(
        DOWN_RIGHT_BODY, (DOWN_LEGS, DOWN_LEGS_A, DOWN_LEGS_B), ARM_DOWN_RIGHT, FIST_DOWN_RIGHT,
        SHIELD_REST_DOWN_RIGHT, SHIELD_UP_DOWN_RIGHT, (SMEAR_DOWN_RIGHT, 2, -2),
    ),
    "right": View(
        RIGHT_BODY, (RIGHT_LEGS, RIGHT_LEGS_A, RIGHT_LEGS_B), ARM_RIGHT, FIST_RIGHT,
        SHIELD_REST_RIGHT, SHIELD_UP_RIGHT, (SMEAR_RIGHT, -2, 7),
        behind=frozenset({"shield", "arm:raised"}),
    ),
    "up_right": View(
        UP_RIGHT_BODY, (UP_LEGS, UP_LEGS_A, UP_LEGS_B), ARM_UP_RIGHT, FIST_UP_RIGHT,
        SHIELD_REST_UP_RIGHT, SHIELD_UP_UP_RIGHT, (SMEAR_UP_RIGHT, -4, 6),
        behind=frozenset({"arm:forward", "guard"}),
    ),
    "up": View(
        UP_BODY, (UP_LEGS, UP_LEGS_A, UP_LEGS_B), ARM_UP, FIST_UP,
        SHIELD_REST_UP, SHIELD_UP_UP, (SMEAR_UP, -4, -4),
        behind=frozenset({"arm:forward", "guard"}),
    ),
}


def pose(view: str, arm: str = "rest", legs: int = 0, guard: bool = False, dx: int = 0, dy: int = 0) -> Sprite:
    """One frame: the view's body on its legs, the sword arm in position arm holding the
    sword, and the shield at rest or raised (guard)."""
    v = VIEWS[view]
    body = v.body + v.legs[legs]
    bw, bh = size(body)
    left, top = (W - bw) // 2 + dx, baseline(H) - bh + dy
    out = cell(body, W, H, dx, dy)

    def put(sprite: Sprite, r: int, c: int, behind: bool) -> None:
        nonlocal out
        out = (underlay if behind else paste)(out, sprite, top + r, left + c)

    sh, sr, sc = v.shield_up if guard else v.shield_rest
    shield_behind = ("guard" if guard else "shield") in v.behind
    arm_sprite, ar, ac = v.arm[arm]
    (fr, fc), direction, length = v.fist[arm]
    blade, gr, gc = sword(direction, length)
    arm_behind = f"arm:{arm}" in v.behind
    put(blade, fr - gr, fc - gc, arm_behind)
    put(arm_sprite, ar, ac, arm_behind)
    put(sh, sr, sc, shield_behind)
    return out


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {"idle": {}, "walk": {}, "attack": {}, "defend": {}}
    for name, v in VIEWS.items():
        base = pose(name)
        a, b = pose(name, legs=1), pose(name, legs=2)
        chest = baseline(H) - len(v.body) - len(v.legs[0]) + v.chest
        animations["idle"][name] = Anim([base, base, squash(base, 1, chest), squash(base, 1, chest)], fps=5)
        animations["walk"][name] = Anim(
            [a, shift(a, 0, 1), base, shift(base, 0, -1), b, shift(b, 0, 1), base, shift(base, 0, -1)], fps=10
        )
        smear, sr, sc = v.smear
        top = baseline(H) - len(v.body) - len(v.legs[0])
        left = (W - len(v.body[0])) // 2
        windup = pose(name, "raised")
        swing = paste(pose(name, "forward"), smear, top + sr, left + sc)
        hit = squash(pose(name, "forward", dy=1), 1, chest)
        animations["attack"][name] = Anim([windup, shift(windup, 0, -1), swing, hit, pose(name, "forward"), base], fps=10, loop=False)
        guard = pose(name, guard=True)
        animations["defend"][name] = Anim([guard, squash(guard, 1, chest)], fps=6, loop=False)
    write_character(
        Character(
            name="player",
            kind="player",
            size=(W, H),
            animations={k: mirror(v) for k, v in animations.items()},
            notes="The adventurer: steel sword, round shield, red scarf. States recolour the "
            "normal sheet: injured, frozen, poisoned.",
            shadow=14,
            states=("normal", "injured", "frozen", "poisoned"),
        )
    )


def DRAFT() -> list[list[Sprite]]:
    """Each view's poses in a row, for looking at while drawing."""
    return [
        [pose(n), pose(n, legs=1), pose(n, legs=2), pose(n, "raised"), pose(n, "forward"), pose(n, guard=True)]
        for n in VIEWS
    ]


for _name, _sprite in list(globals().items()):
    if _name.isupper() and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)
