"""Ghost: a drifting spirit that floats through walls.

A pale shroud of a spirit with a long wailing mouth, black eye hollows lit by a
pinpoint each, ragged sleeves ending in long bony fingers, and no legs: below the waist
it thins into a translucent veil tail that streams and curls behind it. It hovers a few
rows above its shadow.
Special, "phase": its body turns to veil, dissolves until only the two eye-lights are
left, and dissolves back in, as when it passes through a wall.

How it's built, following skeleton_warrior.py:
- Each view is a BODY (head, shroud and tail, fill only) and two arm parts per pose
  (hang, raised, reach), each with where it goes in body coordinates.
- pose() outlines the opaque body in K (the translucent tail gets none, so it fades),
  pastes the outlined arms on, and hovers the result over the baseline.
- The tail is swayed with _batch_a.sway(), and veil() turns a frame translucent for the
  phase and death, keeping the eye-lights.
- Left is mirror()ed from right.
"""

from pixel import (
    Anim,
    Character,
    Sprite,
    blank,
    check,
    dissolve,
    dither,
    mirror,
    outline,
    paste,
    recolour,
    shift,
    silhouette,
    size,
    stretch,
    underlay,
    write_character,
)

from enemies._batch_a import Canvas, ol, sway

W, H = 32, 48  # the cell
HOVER = 4  # rows between the tail's tip and the baseline
TAIL = 18  # body row where the shroud starts thinning into the tail

# ---------------------------------------------------------------------------------
# Down: facing the camera. 22 wide, fill only (pose() outlines it). Rows 0-12 head and
# mouth, 13-21 the shroud, 17 on the veil tail.
# ---------------------------------------------------------------------------------

DOWN_BODY = [
    ".........WWII.........",
    ".......WWIIIIIC.......",
    "......WIIIIIIIIC......",
    ".....WIIIIIIIIIIC.....",
    ".....WIIIIIIIIIIC.....",
    ".....WIIKKIIKKIIC.....",
    ".....WIKWKIIKWKIC.....",
    ".....WIKKIIIIKKIC.....",
    ".....WIIIIKKIIIIC.....",
    ".....WIIIKuuKIIIC.....",
    "....WIIIIKuuKIIIIC....",
    "...WIIIIIKuuKIIIICC...",
    "...WIIIIIIKKIIIIICC...",
    "..WIIICIIIIIIIICIICC..",
    "..WIICIIIIIIIIIICICC..",
    "..;IICIIIIIIIIIICIC;..",
    "...;ICIIIIIIIIIICI;...",
    "...;;IICIIIIIICIC;;...",
    "....;IICIIIIIICIC;....",
    "....;;ICIIIIIICI;;....",
    ".....;IICIIIICIC;.....",
    ".....;;ICIIIICI;;.....",
    "......;;IIIIIC;;......",
    ".......;;IIIC;;.......",
    ".......;;;IIC;........",
    "........;;;I;;........",
    "........;;;;;;........",
    ".........;;;;;;.......",
    "..........;;;;;.......",
    "...........;;;;.......",
    "............;;;.......",
    "...........;;;........",
    "..........;;..........",
]

# Arms: the screen-left ones, fill only; the right one is the mirror. Hanging, the
# hands are held up in front with the fingers drooping.
ARM_HANG = [
    "..WIC",
    ".WIIC",
    "WIIIC",
    "IIII.",
    "I.I..",
    "I.I..",
    "..I..",
]
ARM_RAISED = [
    "I.I..",
    "I.I.I",
    "IIII.",
    "WIIC.",
    ".WIIC",
    "..WIC",
    "...WI",
]
ARM_SWIPE = [
    "WI......",
    "WIIC....",
    ".WIIC...",
    "..WIIC..",
    "...WIIII",
    "....I.I.",
    "....I.I.",
    "......I.",
]

# ---------------------------------------------------------------------------------
# Up: the back of the shroud. No face; a seam runs down the hood.
# ---------------------------------------------------------------------------------

UP_BODY = [
    row if n > 12 else row.replace("K", "I").replace("u", "I")
    for n, row in enumerate(DOWN_BODY)
]
UP_BODY = UP_BODY[:3] + [
    ".....WIIIIIIIIIIC.....",
    ".....WIIIIIIIIIIC.....",
    ".....WIIIIICIIIIC.....",
    ".....WIIIIICIIIIC.....",
    ".....WIIIIICIIIIC.....",
    ".....WIIIIIICIIIC.....",
    ".....WIIIIIICIIIC.....",
    "....WIIIIIIICIIIIC....",
    "...WIIIIIIIICIIIICC...",
    "...WIIIIIIIIIIIIICC...",
] + UP_BODY[13:]

# ---------------------------------------------------------------------------------
# Right: profile, facing right. 22 wide. The eye hollow and the long open mouth are on
# the front of the head; the tail streams back to the left.
# ---------------------------------------------------------------------------------

RIGHT_BODY = [
    "..........WWII........",
    "........WWIIIIIC......",
    ".......WIIIIIIIIC.....",
    "......WIIIIIIIIIIC....",
    "......WIIIIIIIIIIIC...",
    "......WIIIIIIIKKIIC...",
    "......WIIIIIIKWKIIIC..",
    "......WIIIIIIIKKIIIC..",
    "......WIIIIIIIIIIIIC..",
    "......WIIIIIIIIKKIIC..",
    ".....WIIIIIIIIKuuKIC..",
    ".....WIIIIIIIIKuuKIC..",
    ".....WIIIIIIIIKuuKIC..",
    ".....WIIIIIIIIIKKIIC..",
    "....WIICIIIIIIIIIICC..",
    "....WICIIIIIIIIIICC...",
    "....;ICIIIIIIIICIC....",
    "...;;ICIIIIIIICIC.....",
    "...;;IICIIIIICIC......",
    "..;;;IICIIIICIC;......",
    "..;;;ICIIIICIC;.......",
    ".;;;;ICIIIICC;........",
    ".;;;;;CIIICC;.........",
    ";;;;;;;III;;..........",
    ";;;;;;;;;;;...........",
    ";;;;;;;;;.............",
    ".;;;;;................",
    "..;;;.................",
    "...;;.................",
    "....;;................",
    ".....;................",
    "......................",
    "......................",
    "......................",
]

ARM_HANG_RIGHT = [
    ".WIIC...",
    "..WIIC..",
    "...WIIC.",
    "....WIII",
    "....IIII",
    "....I.I.",
    "....I.I.",
    "......I.",
]
# Wound back behind the body, the claws showing past its back
ARM_BACK_RIGHT = [
    "I.I.......",
    ".IIIIC....",
    "I.IIIIIIC.",
    "....WIIIIC",
    "......WIIC",
]
ARM_REACH_RIGHT = [
    ".WIIC.........",
    "..WIIIIIIIIII.",
    "...WIIIIIIIIII",
    "....CCCCCCI.I.",
    "..........I.I.",
]

for _name, _sprite in list(globals().items()):
    if _name.isupper() and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)


def flip(s: Sprite) -> Sprite:
    return [r[::-1] for r in s]


# Each view's arm parts: arm -> [(sprite, row, column, behind)], fill only, in body
# coordinates. Arms behind the body show only round it.
PARTS = {
    "down": {
        "hang": [(ARM_HANG, 11, 0, False), (flip(ARM_HANG), 11, 17, False)],
        "raised": [(ARM_RAISED, 4, 0, False), (flip(ARM_RAISED), 4, 17, False)],
        "swipe": [(ARM_SWIPE, 10, 2, False), (flip(ARM_SWIPE), 10, 12, False)],
    },
    "up": {
        "hang": [(ARM_HANG, 11, 0, True), (flip(ARM_HANG), 11, 17, True)],
        "raised": [(ARM_RAISED, 4, 0, True), (flip(ARM_RAISED), 4, 17, True)],
        "swipe": [(ARM_SWIPE, 10, 2, True), (flip(ARM_SWIPE), 10, 12, True)],
    },
    "right": {
        "hang": [(ARM_HANG_RIGHT, 14, 11, False)],
        "raised": [(ARM_BACK_RIGHT, 8, 0, True)],
        "swipe": [(ARM_REACH_RIGHT, 14, 9, False)],
    },
}
BODIES = {"down": DOWN_BODY, "up": UP_BODY, "right": RIGHT_BODY}


def pose(view: str, arms: str = "hang", tail: int = 0, dx: int = 0, dy: int = 0) -> Sprite:
    """The ghost in view with its arms in position arms, its tail swayed tail pixels,
    hovering HOVER rows over the baseline and moved dx, dy. The lower shroud is dithered
    to veil so it reads as see-through."""
    body = BODIES[view]
    body = body[: TAIL - 4] + dither(body[TAIL - 4 : TAIL], "I", ";", 0.25) + dither(body[TAIL:], "I", ";", 0.5)
    body = sway(body, tail, TAIL)
    bw, bh = size(body)
    left = (W - bw) // 2 + dx
    top = H - 2 - HOVER - bh + dy
    out = paste(blank(W, H), ol(body), top - 1, left - 1)
    for part, r, c, behind in PARTS[view][arms]:
        out = (underlay if behind else paste)(out, ol(part), top + r - 1, left + c - 1)
    return out


def rake(w: int, h: int, slant: int) -> Sprite:
    """Three claw marks, bright with a frost haze beside each: the hit."""
    c = Canvas(w, h)
    for i in range(3):
        x0 = 1 + i * 3
        c.line(x0, 0, x0 + slant, h - 1, "W")
    rows = c.rows()
    return outline(rows, "=")


# A puff of frost where the claws land, in profile
FROST_BURST = [
    "...=...",
    ".=.I.=.",
    "..=W=..",
    "=IWWWI=",
    "..=W=..",
    ".=.I.=.",
    "...=...",
]

VEIL = {"W": ";", "I": ";", "C": "=", "U": "=", "u": "=", "K": "="}


def veil(f: Sprite, eyes: bool = True) -> Sprite:
    """The frame turned to translucent veil, keeping the eye-lights (each W with K on
    all four sides) when eyes, i.e. when the face is showing."""
    lights = [] if not eyes else [
        (y, x)
        for y in range(1, H - 1)
        for x in range(1, W - 1)
        if f[y][x] == "W" and f[y - 1][x] == f[y + 1][x] == f[y][x - 1] == f[y][x + 1] == "K"
    ]
    out = recolour(f, VEIL)
    for y, x in lights:
        out = paste(out, ["W"], y, x)
    return out


def lights_only(f: Sprite, eyes: bool = True) -> Sprite:
    """Just the eye-lights of a frame, each with a faint haze round it; nothing when the
    face isn't showing."""
    out = blank(W, H)
    if not eyes:
        return out
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if f[y][x] == "W" and f[y - 1][x] == f[y + 1][x] == f[y][x - 1] == f[y][x + 1] == "K":
                out = paste(out, [".;.", ";W;", ".;."], y - 1, x - 1)
    return out


def wisps(f: Sprite, puffs: list[tuple[int, int]]) -> Sprite:
    """Small detached puffs of veil at (row, column) on the cell, behind the ghost."""
    for y, x in puffs:
        f = underlay(f, [";;", ".;"], y, x)
    return f


# Walk: a slow bob (rows), the tail swinging (pixels) and loose wisps drifting off
BOB = [0, -1, -2, -2, -1, 0, 1, 1]
SWING = [0, 1, 2, 1, 0, -1, -2, -1]
TRAIL_RIGHT = [-3, -3, -2, -2, -3, -4, -4, -3]


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    for view in ("down", "up", "right"):
        side = view == "right"
        base = pose(view, tail=-2 if side else 0)

        # Idle: hover up and down, the tail lazily swaying
        animations["idle"][view] = Anim(
            [
                pose(view, tail=-2 if side else 1),
                pose(view, tail=-3 if side else 0, dy=-1),
                pose(view, tail=-2 if side else -1, dy=-1),
                pose(view, tail=-1 if side else 0),
            ],
            fps=5,
        )

        # Walk: drift with a bob; the tail streams and swings, puffs of veil peel off
        walk = []
        for n in range(8):
            tail = TRAIL_RIGHT[n] if side else SWING[n]
            f = pose(view, tail=tail, dy=BOB[n])
            age = n % 4
            if side:
                f = wisps(f, [(36 + BOB[n] + age // 2, 6 - age * 2), (40 - age, 10 - age * 2)])
            else:
                f = wisps(f, [(41 - age, 12 - age), (39 - age // 2, 19 + age)])
            walk.append(dissolve(f, 0.0))
        animations["walk"][view] = Anim(walk, fps=8)

        # Attack: rear up with the arms raised and the mouth agape, swoop in and rake
        # with the claws in a burst of frost, drift back
        push = {"down": (0, 2), "up": (0, -2), "right": (2, 0)}[view]
        px, py = push
        raised = pose(view, "raised", dy=-2, dx=-px // 3)
        swipe = pose(view, "swipe", dx=px, dy=py)
        if side:
            swipe_fx = paste(swipe, FROST_BURST, 21, 25)
        elif view == "down":
            swipe_fx = paste(swipe, rake(11, 8, 3), 32 + py, 10)
        else:
            swipe_fx = underlay(swipe, rake(11, 8, 3), 28 + py, 10)
        animations["attack"][view] = Anim(
            [
                pose(view, "raised", dy=-1),
                raised,
                shift(raised, px // 2, py // 2),
                swipe_fx,
                swipe,
                pose(view, dx=px // 2, dy=py // 2),
                base,
            ],
            fps=10,
            loop=False,
        )

        # Special, phase: the body goes to veil, dissolves to the two eye-lights, and
        # comes back
        face = view != "up"
        v = veil(base, face)
        animations["special"][view] = Anim(
            [
                base,
                v,
                dissolve(v, 0.4),
                paste(dissolve(v, 0.75), lights_only(base, face), 0, 0),
                lights_only(base, face),
                paste(dissolve(v, 0.75), lights_only(base, face), 0, 0),
                dissolve(v, 0.4),
                v,
                base,
            ],
            fps=8,
            loop=False,
        )

        # Death: flash, a stretched wail, then it rises as veil and comes apart
        wail = stretch(base, 3, 20)
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                wail,
                shift(veil(wail, face), 0, -2),
                shift(dissolve(veil(wail, face), 0.45), 0, -4),
                shift(dissolve(veil(wail, face), 0.7), 0, -6),
                shift(dissolve(veil(wail, face), 0.9), 0, -8),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="ghost",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="A pale wailing spirit with black eye hollows, long-fingered sleeves and a veil "
            "tail; hovers and drifts through walls. Special: phase (turns to veil and fades to "
            "two eye-lights, then fades back in).",
            shadow=12,
        )
    )
