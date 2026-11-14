"""Skeleton Warrior: melee fighter. The reference character module; copy its shape.

A rattling skeleton in a dented iron half-helm and one pauldron, a tattered red
loincloth, eyes glowing red, swinging a rusty short sword.
Special, "reassemble": it falls into a heap of bones and pulls itself back together.

How it's built, which any character can follow:
- Each view (down, up, right) is a TORSO (head and body, no sword arm) on top of a
  set of LEGS, all at natural size. A walk pose is the same torso on other legs.
- The sword arm is a separate sprite per position (hanging, raised, forward), and the
  sword comes from sword(direction), placed by its grip at the arm's fist. pose()
  puts the torso and legs on the cell and pastes the parts on in pose coordinates.
- Animations are built from those poses with the pixel transforms: squash to
  breathe, shift to bob, shear to lean, silhouette to flash, dissolve to fade.
- Left is mirror()ed from right.
"""

from pixel import (
    Anim,
    Character,
    Sprite,
    arc,
    baseline,
    cell,
    check,
    dissolve,
    frame,
    mirror,
    outline,
    paste,
    shear,
    shift,
    silhouette,
    size,
    underlay,
    squash,
    write_character,
)

W, H = 32, 48  # the cell

# ---------------------------------------------------------------------------------
# Down: facing the camera. 22 wide; torso rows 0-23, legs 24-30. The sword arm is
# the one on screen left.
# ---------------------------------------------------------------------------------

DOWN_TORSO = [
    "........KKKKKK........",
    "......KKGLLGGGKK......",
    ".....KGLLGGGGGGDK.....",
    ".....KGLGGGGGGODK.....",
    "....KDDDDDDDDDDDDK....",
    ".....KWWWWWWWWWLK.....",
    ".....KWKKWWWWKKLK.....",
    ".....KWKRWWWWRKLK.....",
    ".....KWWWWKKWWWLK.....",
    "......KWKWKWKWLK......",
    ".......KWWWWWLK.......",
    "........KKKKKK........",
    ".........KLLK...KKKK..",
    "..KKK.KKKKLLKKKKGLLGK.",
    ".KWWWKWWWWLLWWWKLGGDK.",
    "..KKKKDDDKLLKDDKKDDK..",
    "....KWWWWWLLWWWWKWK...",
    ".....KDDDKLLKDDKKWK...",
    ".....KWWWWLLWWWK.KWK..",
    "......KDDKLLKDK..KLK..",
    ".......KKWLLWK...KWK..",
    "......KrRRRRRRK..KWK..",
    "......KWRRRRRWK.KWWWK.",
    ".......KRrRRrK..KWKWK.",
]

DOWN_LEGS = [
    ".......KWKRrKWK.......",
    ".......KWKrRKWK.......",
    ".......KLK.KKLK.......",
    "......KWWK..KWWK......",
    ".......KLK..KLK.......",
    ".......KWK..KWK.......",
    "......KWWWK.KWWWK.....",
]

# Screen-left leg lifted: shorter by two rows, foot off the ground
DOWN_LEGS_A = DOWN_LEGS[:4] + [
    "......KWWWK.KLK.......",
    ".......KKK..KWK.......",
    "............KWWWK.....",
]

# Screen-right leg lifted
DOWN_LEGS_B = DOWN_LEGS[:4] + [
    ".......KLK.KWWWK......",
    ".......KWK..KKK.......",
    "......KWWWK...........",
]

# The sword arm's positions, each with where its top-left goes (row, column) in pose
# coordinates and where its fist holds the grip
ARM_HANG_DOWN = [
    ".KWLK",
    ".KWK.",
    ".KWK.",
    ".KLK.",
    ".KWK.",
    ".KWK.",
    ".KLK.",
    "KWWWK",
    "KWKWK",
]
ARM_RAISED_DOWN = [
    "KWWWK",
    "KWKWK",
    ".KWK.",
    ".KWK.",
    ".KLK.",
    ".KWK.",
    ".KWK.",
    ".KLK.",
    ".KWK.",
]
ARM_FORWARD_DOWN = [
    "KWLK.....",
    ".KWWK....",
    "..KWWK...",
    "...KWWK..",
    "...KWWWK.",
    "...KWKWK.",
]

# ---------------------------------------------------------------------------------
# Up: the back. The spine and shoulder blades show; the sword arm is on screen right.
# ---------------------------------------------------------------------------------

UP_TORSO = [
    "........KKKKKK........",
    "......KKGGGLLGKK......",
    ".....KDGGGGGLLGK......",
    ".....KDGOGGGGLGK......",
    "....KDDDDDDDDDDDDK....",
    ".....KLWWWWWWWWWK.....",
    ".....KLWWWWWWWWWK.....",
    ".....KLWWWWWWWWWK.....",
    ".....KLLWWWWWWWLK.....",
    "......KLLWWWWWLK......",
    ".......KLLWWWLK.......",
    "........KKKKKK........",
    "..KKKK...KLLK.........",
    ".KGLLGKKKKLLKKKK.KKK..",
    ".KDGGLKWWWKKWWWWKWWWK.",
    "..KDDKWLLLKWKLLLWKKKK.",
    "...KWKWKKKWLKKKKWK....",
    "...KWKDKWWLWKWWWK.....",
    "..KWK.KDKKKLKKKDK.....",
    "..KLK..KDWWLWWDK......",
    "..KWK...KKKLKKK.......",
    "..KWK..KrrrrrrRK......",
    ".KWWWK.KrRRRRRRK......",
    ".KWKWK..KrRRrRK.......",
]

UP_LEGS = DOWN_LEGS
UP_LEGS_A = DOWN_LEGS_A
UP_LEGS_B = DOWN_LEGS_B


def _mirror_part(part: Sprite, row: int, col: int, width: int = 22) -> tuple[Sprite, int, int]:
    """A down-view arm placed at the same height on the other side, flipped."""
    return [r[::-1] for r in part], row, width - col - len(part[0])


# ---------------------------------------------------------------------------------
# Right: profile, facing right. 20 wide. The spine is at the back (left), the ribs
# curve forward, the sword arm is the near one.
# ---------------------------------------------------------------------------------

RIGHT_TORSO = [
    "......KKKKKK........",
    "....KKGLLLGGKK......",
    "...KGLLGGGGGGDK.....",
    "...KGLGGGGOGGDK.....",
    "..KDDDDDDDDDDDDK....",
    "...KLWWWWWWWWWK.....",
    "...KLWWWWWKKWWK.....",
    "...KLWWWWWKRWWWK....",
    "...KLLWWWWWWWKKK....",
    "....KLLWWWWWKWKWK...",
    ".....KKLLWWWWWWK....",
    ".......KKKKKKKK.....",
    ".......KLLK.........",
    "......KLLKKKK.......",
    ".....KLLKWWWWK......",
    ".....KLLKDDDDWK.....",
    ".....KLLKWWWWWK.....",
    ".....KLLKDDDDWK.....",
    ".....KLLKWWWWK......",
    "......KLLKKKKK......",
    "......KLLK..........",
    "......KrRRRRRK......",
    "......KrRRRRRRK.....",
    "......KrRRRrRK......",
]

RIGHT_LEGS = [
    ".......KrRKRrK......",
    ".......KWKKKWK......",
    ".......KLK.KLK......",
    "......KWWK.KWWK.....",
    ".......KLK..KLK.....",
    ".......KWK..KWK.....",
    ".......KWWWKKWWWK...",
]

# Stride: back leg trailing, front leg reaching
RIGHT_LEGS_A = [
    ".......KrRKRrK......",
    "......KWKK.KWK......",
    ".....KLK....KLK.....",
    ".....KWWK...KWWK....",
    "....KLK......KLK....",
    "....KWK......KWK....",
    "...KWWWK.....KWWWK..",
]

# Passing: legs crossing under the body
RIGHT_LEGS_B = [
    ".......KrRKRrK......",
    "........KWKWK.......",
    "........KLKLK.......",
    ".......KWWKWWK......",
    "........KLKLK.......",
    "........KWKWK.......",
    "........KWWWWWK.....",
]

ARM_HANG_RIGHT = [
    ".KK..",
    "KWWK.",
    "KWLK.",
    ".KWK.",
    ".KWK.",
    ".KLK.",
    ".KWK.",
    ".KWK.",
    "KWWWK",
    "KWKWK",
]
ARM_RAISED_RIGHT = [
    "KWWWK",
    "KWKWK",
    ".KWK.",
    ".KWK.",
    ".KLK.",
    ".KWK.",
    ".KWK.",
    ".KLK.",
    ".KWK.",
    ".KWK.",
    ".KLK.",
    ".KWK.",
    ".KWK.",
    "KWWK.",
    "KWLK.",
]
ARM_FORWARD_RIGHT = [
    ".KK.....KKK.",
    "KWWKKKKKWWWK",
    "KWLWWLWWWKWK",
    ".KKKKKKKWWWK",
    "........KKK.",
]
ARM_LOW_RIGHT = [
    ".KK.....",
    "KWWK....",
    "KWLWK...",
    ".KKWWK..",
    "...KWWK.",
    "...KWWWK",
    "...KWKWK",
]

# A heap of bones with the helm on top: the end of death, the start of reassemble
PILE = [
    "..........KKKKKK..........",
    "........KKGLLGGGKK........",
    ".......KDDDDDDDDDDK.......",
    "....KK..KWKKWWKKWK..KK....",
    "...KWWK.KWKRWWRKWK.KWWK...",
    "....KWWKKKWWKKWWKKKWWK....",
    ".KK..KWWKWKWKWKWKWWWK..KK.",
    "KWWKKKWWWLLKrRRrKKWWKKKWWK",
    ".KWWWWKKWWKRRrRRKWWKWWWWK.",
    "..KKKWWWKKLWWKKWWLKKWWKK..",
    "....KKKKKKKKKKKKKKKKKKKK..",
]

for _name, _sprite in list(globals().items()):
    if _name.isupper() and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)

# ---------------------------------------------------------------------------------
# The sword
# ---------------------------------------------------------------------------------

STEPS = {
    "up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1),
    "up_right": (-1, 1), "down_right": (1, 1), "up_left": (-1, -1), "down_left": (1, -1),
}


def sword(direction: str, length: int = 7) -> tuple[Sprite, int, int]:
    """A rusty short sword pointing direction, outlined, and the (row, column) of its
    grip in the sprite: put that on the fist."""
    dr, dc = STEPS[direction]
    pr, pc = -dc, dr  # across the blade
    px: dict[tuple[int, int], str] = {(0, 0): "b", (-dr, -dc): "O"}
    for k in (-1, 0, 1):
        px[(dr + k * pr, dc + k * pc)] = "D"
    for i in range(2, length + 2):
        px[(dr * i, dc * i)] = "O" if i == length // 2 + 1 else "W"
        if dr and dc:  # a diagonal: fill under each step so the blade reads solid
            px.setdefault((dr * i + 1, dc * i), "L")
    r0 = min(r for r, _ in px) - 1
    c0 = min(c for _, c in px) - 1
    h = max(r for r, _ in px) - r0 + 2
    w = max(c for _, c in px) - c0 + 2
    grid = [["."] * w for _ in range(h)]
    for (r, c), letter in px.items():
        grid[r - r0][c - c0] = letter
    return outline(["".join(row) for row in grid]), -r0, -c0


def held(direction: str, fist: tuple[int, int], length: int = 7) -> tuple[Sprite, int, int]:
    """The sword as a part, its grip on fist (row, column)."""
    s, gr, gc = sword(direction, length)
    return s, fist[0] - gr, fist[1] - gc


def pose(
    torso: Sprite, legs: Sprite, parts: list[tuple[Sprite, int, int]] = (),
    dx: int = 0, dy: int = 0, behind: bool = False,
) -> Sprite:
    """The torso on the legs, standing in the cell, with each (sprite, row, column) part
    pasted over it in turn, in the pose's own coordinates; with behind, the parts go
    under the body instead and show only around it."""
    body = torso + legs
    bw, bh = size(body)
    left, top = (W - bw) // 2 + dx, baseline(H) - bh + dy
    out = cell(body, W, H, dx, dy)
    for sprite, r, c in parts:
        out = (underlay if behind else paste)(out, sprite, top + r, left + c)
    return out


# Each view's parts: (arm sprite, row, column) per arm position, and the fist each
# arm's grip goes on. The sword goes on before the arm, so the fist closes over it.
DOWN_PARTS = {
    "hang": ((ARM_HANG_DOWN, 15, 0), (23, 2), "down"),
    "raised": ((ARM_RAISED_DOWN, 5, 0), (5, 2), "up"),
    "forward": ((ARM_FORWARD_DOWN, 15, 1), (20, 5), "down_left"),
}
UP_PARTS = {
    k: (_mirror_part(*arm), (fist[0], 21 - fist[1]), d) for k, (arm, fist, d) in DOWN_PARTS.items()
}
RIGHT_PARTS = {
    "hang": ((ARM_HANG_RIGHT, 13, 7), (21, 9), "up_right"),
    "raised": ((ARM_RAISED_RIGHT, -2, 7), (-2, 9), "up_left"),
    "forward": ((ARM_FORWARD_RIGHT, 13, 7), (15, 17), "right"),
    "low": ((ARM_LOW_RIGHT, 13, 7), (18, 12), "down_right"),
}
VIEWS = {
    "down": (DOWN_TORSO, DOWN_LEGS, DOWN_LEGS_A, DOWN_LEGS_B, DOWN_PARTS),
    "up": (UP_TORSO, UP_LEGS, UP_LEGS_A, UP_LEGS_B, UP_PARTS),
    "right": (RIGHT_TORSO, RIGHT_LEGS, RIGHT_LEGS_A, RIGHT_LEGS_B, RIGHT_PARTS),
}


# Arm positions that pass behind the body in a view: the raised arm behind the head in
# profile, the swinging arm in front of the chest seen from the back
BEHIND = {("right", "raised"), ("up", "forward")}


def armed(view: str, arm: str, legs: Sprite = (), dx: int = 0, dy: int = 0) -> Sprite:
    """The view's pose holding the sword in the arm position arm."""
    torso, stand, _, _, parts = VIEWS[view]
    arm_part, fist, direction = parts[arm]
    blade = held(direction, fist)
    return pose(torso, legs or stand, [blade, arm_part], dx, dy, behind=(view, arm) in BEHIND)


# A slash smear: a bright arc where the blade passed
SMEAR_DOWN = arc(16, 22, 15, 21, 15, 95, 175, ":", thickness=3, edge="W")
SMEAR_RIGHT = arc(16, 20, 2, 16, 14, 0, 80, ":", thickness=3, edge="W")


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    pile = cell(PILE, W, H)
    for view, (torso, stand, legs_a, legs_b, parts) in VIEWS.items():
        base = armed(view, "hang")
        a = armed(view, "hang", legs_a)
        b = armed(view, "hang", legs_b)

        # Idle: shoulders sink a pixel and rise, the jaw-rattle of a breath it hasn't got
        animations["idle"][view] = Anim([base, squash(base, 1, 34), squash(base, 1, 34), base], fps=5)

        # Walk: step, settle, pass, rise, on each leg
        animations["walk"][view] = Anim(
            [a, shift(a, 0, 1), base, shift(base, 0, -1), b, shift(b, 0, 1), base, shift(base, 0, -1)],
            fps=8,
        )

        # Attack: wind up, hold, swing with a smear, hit leaning in, recover
        windup = armed(view, "raised")
        if view == "right":
            swing = paste(armed(view, "forward"), SMEAR_RIGHT, 14, 16)
            hit = shear(armed(view, "low"), 2, 40)
        elif view == "down":
            swing = paste(armed(view, "forward"), SMEAR_DOWN, 8, 2)
            hit = squash(armed(view, "forward", dy=1), 1, 30)
        else:
            swing = paste(armed(view, "forward"), [r[::-1] for r in SMEAR_DOWN], 8, 14)
            hit = squash(armed(view, "forward", dy=1), 1, 30)
        animations["attack"][view] = Anim(
            [windup, shift(windup, 0, -1), swing, hit, hit, base], fps=10, loop=False
        )

        # Special, reassemble: crumple into the pile, rattle, pull back together
        crumple = squash(base, 10, 30)
        animations["special"][view] = Anim(
            [
                base,
                crumple,
                pile,
                shift(pile, -1, 0),
                shift(pile, 1, 0),
                frame(W, H, [(dissolve(base, 0.6), 0, H), (pile, 0, H)]),
                frame(W, H, [(pile, 0, H), (dissolve(base, 0.3), 0, H)]),
                base,
            ],
            fps=8,
            loop=False,
        )

        # Death: flash, stagger, crumple, collapse, fade
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                shear(squash(base, 3, 32), -2, 40),
                crumple,
                pile,
                dissolve(pile, 0.5),
                dissolve(pile, 0.8),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="skeleton_warrior",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Melee fighter: a rusty short sword and a dented helm. Special: reassemble "
            "(collapses into bones and rises again).",
            shadow=14,
        )
    )
