"""Goblin: a small, sneering rock-thrower.

A runt about 20 pixels tall with green skin, huge pointed ears with pink insides, a long
hooked nose, a fanged grin and yellow eyes, in a ragged leather jerkin with a rope belt.
It carries a fist-sized rock in its throwing hand.
Attack: winds up over its shoulder and hurls the rock (the Effect "rock" is the
spinning projectile). Attack2: a quick stab with a chipped shiv.
Special, "taunt": a cocky hop with its arms flung up and its tongue out.

How it's built, following skeleton_warrior.py:
- Each view (down, up, right) is a TORSO (head and body, without the throwing arm) on a
  set of LEGS, fill only. pose() stacks them, outlines the lot with _batch_a.ol(), and
  pastes outlined arm parts on in pose coordinates.
- The throwing arm is a separate part per position (hang, raised, thrown, stab).
- Animations come from those poses with squash, shift, shear, rotate and dissolve.
- Left is mirror()ed from right.
"""

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    blank,
    check,
    dissolve,
    mirror,
    outline,
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

from enemies._batch_a import edge_shade, ol, stand

W, H = 32, 48  # the cell

# ---------------------------------------------------------------------------------
# Down: facing the camera. 22 wide, fill only. Head rows 0-9 (ears out to both sides),
# body 10-15, legs 16-19. The throwing arm is the one on screen left.
# ---------------------------------------------------------------------------------

DOWN_TORSO = [
    "........EEEVVV........",
    "E......EEEVVVVV......v",
    "EE....EEVVVVVVVv....vv",
    ".EFE..EVVVVVVVVv..vFv.",
    "..EFFEEvvVVVVvvvvFFv..",
    "...EFVVYKVVVVKYvVFv...",
    "....VVVVVVEVVVVvvv....",
    "......VVVVvvVVVv......",
    "......VKWKKKKWKv......",
    ".......VVVVVVvv.......",
    "......VTTBBBBBBbVv....",
    "......VTBBbBBBBbVv....",
    "......VbTBBBBBBbVv....",
    ".......bYbbbbbbbVv....",
    ".......TBBTBBTBb.VV...",
    ".......B.bB.Bb.B......",
]

DOWN_LEGS = [
    "........VV..vV........",
    "........Vv..Vv........",
    ".......EVv..VVv.......",
    ".......VVv..VVv.......",
]
# Screen-left foot lifted
DOWN_LEGS_A = [
    "........VV..vV........",
    ".......EVv..Vv........",
    ".......VVv..VVv.......",
    "............VVv.......",
]
# Screen-right foot lifted
DOWN_LEGS_B = [
    "........VV..vV........",
    "........Vv..VVv.......",
    ".......EVv..VVv.......",
    ".......VVv............",
]

# The throwing arm, screen left, each with the rock in its fist where it has one
ARM_HANG_DOWN = [
    ".EV",
    "EVv",
    "EV.",
    "EVv",
    "VV.",
    "LGG",
    "GGD",
]
ARM_RAISED_DOWN = [
    ".LG.",
    "LGGD",
    ".GD.",
    ".EV.",
    ".EVv",
    ".EVv",
    "EVv.",
]
ARM_THROWN_DOWN = [
    "EVv..",
    ".EVv.",
    "..EVv",
    "..VVV",
    "..V.V",
]
ARM_STAB_DOWN = [
    "EVv...",
    ".EVv..",
    "..EVv.",
    "..VVVv",
    "...bB.",
    "...LG.",
    "...LG.",
    "...W..",
]

# ---------------------------------------------------------------------------------
# Up: the back. Ears from behind, the jerkin's back; the throwing arm is screen right.
# ---------------------------------------------------------------------------------

UP_TORSO = [
    "........EEEVVV........",
    "E......EEEVVVVV......v",
    "EE....EEVVVVVVVv....vv",
    ".EVE..EVVVVVVVVv..vVv.",
    "..EVVEEVVVVVVVVvvVVv..",
    "...EVVVVVVVVVVVvVVv...",
    "....VVVVVVVVVVVvvv....",
    "......VVVVVVVVvv......",
    "......vVVVVVVvvv......",
    ".......vvvvvvvv.......",
    "....vVTTBBBBBBbV......",
    "....vVTBBBBBBBbV......",
    "....vVTBBBBBBBbV......",
    "....vV.bbbbbbbbb......",
    "...VV.TBBTBBTBb.......",
    "......B.bB.Bb.B.......",
]


def _mirror_part(part: Sprite, row: int, col: int, width: int = 22) -> tuple[Sprite, int, int]:
    """A down-view arm placed at the same height on the other side, flipped."""
    return [r[::-1] for r in part], row, width - col - len(part[0])


# ---------------------------------------------------------------------------------
# Right: profile, facing right. 19 wide. The ear sweeps back, the nose juts forward;
# the throwing arm is the near one.
# ---------------------------------------------------------------------------------

RIGHT_TORSO = [
    ".........EEEV......",
    "E......EEEVVVVv....",
    ".EE...EEVVVVVVVv...",
    "..EEFEEEVVVVVVVVv..",
    "...EFFEEVVVVvvvYKv.",
    ".....VFVVVVVVVVVEEv",
    "......VVVVVVVVVVVvv",
    "......VVVVVVVVKKWv.",
    ".......VVVVVVVVVv..",
    "......TBBBBBBVv....",
    ".....TTBBBBBBBb....",
    ".....TBBBBBBBBb....",
    ".....bBBBBBBBbb....",
    ".....bbYbbbbbb.....",
    ".....TBBTBBTBb.....",
    ".....B.bB.BB.b.....",
]

RIGHT_LEGS = [
    ".......VV.vV.......",
    ".......Vv.Vv.......",
    ".......Vv.Vv.......",
    "......VVv.VVVv.....",
]
# Stride: back leg trailing, front leg reaching
RIGHT_LEGS_A = [
    ".......VV.vV.......",
    "......Vv...Vv......",
    ".....Vv.....Vv.....",
    "....VVv.....VVVv...",
]
# Passing: the back foot lifted under the body
RIGHT_LEGS_B = [
    ".......VVvV........",
    ".......VvVv........",
    "........VVVVv......",
    "........VVVv.......",
]

ARM_HANG_RIGHT = [
    "EV..",
    "EVv.",
    ".EV.",
    ".EVv",
    ".VVv",
    ".LGG",
    ".GGD",
]
ARM_RAISED_RIGHT = [
    ".LG.....",
    "LGGD....",
    ".GDVv...",
    "...EVv..",
    "....EVv.",
    ".....EVv",
    "......EV",
]
ARM_THROWN_RIGHT = [
    "EVv.....",
    ".EVVVVv.",
    "..vvvVVV",
    "......V.",
]
ARM_STAB_RIGHT = [
    "EVv..........",
    ".EVVVVvbBLLLW",
    "..vvvVVbGGG..",
]

# Flat on its back, seen from above: head to the left (it fell backward), ears splayed,
# eyes shut, tongue lolling, one arm flung up and one down, feet to the right
DEAD = [
    "...E......VV...........",
    "...EE.....EVv..........",
    "...EFE....EVv..........",
    "..EVVVVE.TBBBBBb.......",
    ".EVKVVVVTTBBBBBBbVVVVv.",
    ".EVVVKFVbTBBbBBBBb.....",
    ".EVKVVVVTBBBBBBBBbVVVVv",
    "..VVVVVv..bbYbbbbb.....",
    "...vFv.....Vv..........",
    "...vv.......VV.........",
    "...v...................",
]

for _name, _sprite in list(globals().items()):
    if _name.isupper() and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)

# ---------------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------------

DOWN_PARTS = {
    "hang": (ARM_HANG_DOWN, 10, 4),
    "raised": (ARM_RAISED_DOWN, 4, 3),
    "thrown": (ARM_THROWN_DOWN, 10, 4),
    "stab": (ARM_STAB_DOWN, 10, 4),
}
UP_PARTS = {k: _mirror_part(*v) for k, v in DOWN_PARTS.items()}
RIGHT_PARTS = {
    "hang": (ARM_HANG_RIGHT, 10, 8),
    "raised": (ARM_RAISED_RIGHT, 4, 0),
    "thrown": (ARM_THROWN_RIGHT, 10, 9),
    "stab": (ARM_STAB_RIGHT, 10, 8),
}
VIEWS = {
    "down": (DOWN_TORSO, DOWN_LEGS, DOWN_LEGS_A, DOWN_LEGS_B, DOWN_PARTS),
    "up": (UP_TORSO, DOWN_LEGS, DOWN_LEGS_A, DOWN_LEGS_B, UP_PARTS),
    "right": (RIGHT_TORSO, RIGHT_LEGS, RIGHT_LEGS_A, RIGHT_LEGS_B, RIGHT_PARTS),
}
# Arm positions that go behind the body in a view
BEHIND = {("right", "raised"), ("up", "thrown"), ("up", "stab")}

# The tongue stuck out for the taunt, where it goes on each view's torso
TONGUE = {"down": (["FF", "rF"], 9, 10), "right": (["FF", ".F"], 8, 15)}


def pose(
    view: str, arm: str = "hang", legs: Sprite = (), dx: int = 0, dy: int = 0, tongue: bool = False,
) -> Sprite:
    """The view's torso on legs, outlined, with the throwing arm in position arm, on the
    cell; tongue sticks its tongue out."""
    torso, stand_legs, _, _, parts = VIEWS[view]
    body = torso + list(legs or stand_legs)
    if tongue and view in TONGUE:
        t, r, c = TONGUE[view]
        body = paste(body, t, r, c)
    out = ol(body)
    part, r, c = parts[arm]
    out_full = stand(out, W, H, dx, dy)
    bw, bh = size(body)
    left, top = (W - bw - 2) // 2 + dx + 1, H - 2 - bh + dy  # the fill's top-left on the cell
    out_full = (underlay if (view, arm) in BEHIND else paste)(out_full, ol(part), top + r - 1, left + c - 1)
    return out_full


# ---------------------------------------------------------------------------------
# The rock: an irregular lump that tumbles, its crack turning while the light stays put
# ---------------------------------------------------------------------------------

ROCK = [
    ".XXXX.",
    "XXXXXX",
    "XXXcXX",
    "XXcXXX",
    ".XXXX.",
]


def rock_frames() -> list[Sprite]:
    frames = []
    for n in range(4):
        r = rotate(ROCK, n)
        shaded = edge_shade(r, "L", "G", "D", keep="c")
        shaded = [row.replace("c", "D") for row in shaded]
        f = outline(paste(blank(8, 8), shaded, (8 - len(r)) // 2, (8 - len(r[0])) // 2))
        frames.append(f)
    return frames


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "attack2": {}, "special": {}, "death": {},
    }
    for view, (torso, stand_legs, legs_a, legs_b, parts) in VIEWS.items():
        side = view == "right"
        base = pose(view)
        a = pose(view, legs=legs_a)
        b = pose(view, legs=legs_b)
        mid = H - 12  # a row in the belly, to squash for breath

        # Idle: a twitchy breath, shoulders hunching
        animations["idle"][view] = Anim([base, squash(base, 1, mid), squash(base, 1, mid), base], fps=6)

        # Walk: a scurrying step on each foot, dipping on the plant, rising on the pass
        animations["walk"][view] = Anim(
            [a, squash(a, 1, mid), base, shift(base, 0, -1), b, squash(b, 1, mid), base, shift(base, 0, -1)],
            fps=10,
        )

        # Attack: wind the rock back over the shoulder, lean into the throw, release,
        # follow through, recover. The game launches fx rock on the release frame (3).
        windup = pose(view, "raised", dx=-1 if side else 0)
        throw = pose(view, "thrown", dx=1 if side else 0, dy=1 if view == "down" else 0)
        if side:
            windup = shear(windup, -2, H - 6)
            throw = shear(throw, 2, H - 6)
        animations["attack"][view] = Anim(
            [windup, squash(windup, 1, mid), throw, throw, pose(view, "thrown"), base],
            fps=10,
            loop=False,
        )

        # Attack2: a quick stab with a shiv, darting forward
        stab = pose(view, "stab", dx=2 if side else 0, dy=1 if view == "down" else (-1 if view == "up" else 0))
        animations["attack2"][view] = Anim(
            [squash(pose(view, "raised"), 1, mid), stab, stab, pose(view, "hang"), base],
            fps=10,
            loop=False,
        )

        # Special, taunt: crouch, hop with its arms flung up and its tongue out, land
        crouch = squash(base, 2, mid)
        hop = pose(view, "raised", legs=legs_b, tongue=True)
        animations["special"][view] = Anim(
            [
                crouch,
                shift(hop, 0, -4),
                shift(hop, 0, -6),
                shift(hop, 0, -3),
                squash(pose(view, tongue=True), 2, mid),
                pose(view, tongue=True),
                base,
            ],
            fps=10,
            loop=False,
        )

        # Death: flash, reel back, buckle and fall backward, lie flat, fade
        dead = stand(ol(DEAD), W, H)
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                shear(base, -2, H - 4),
                squash(shear(base, -5, H - 4), 6, mid),
                dead,
                dissolve(dead, 0.45),
                dissolve(dead, 0.8),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="goblin",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="A runty green goblin with huge ears, a hooked nose and yellow eyes, in ragged "
            "leather, throwing rocks (fx rock). Special: taunt (a cocky hop, arms up, tongue out).",
            shadow=12,
            effects=(
                Effect("rock", rock_frames(), fps=12, loop=True, notes="The thrown rock, tumbling."),
            ),
        )
    )
