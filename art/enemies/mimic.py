"""Mimic: disguised as treasure.

Shut, it is the game's treasure chest to the pixel (environment._chest.CHEST_CLOSED):
iron bands and a gold lock. Open, the lid is a jaw: a row of fangs along its edge, a
black-red maw, a fat pink tongue, and two yellow eyes glowing in the dark inside.
Idle: perfectly still but for one twitch of the lid.
Walk: it hops, the lid flapping to show teeth and tongue.
Attack: a wide chomp.
Special, "reveal": the lid creaks, eyes open in the dark gap, then the mouth gapes.

The front (down) view is the chest itself, split at the seam into lid and box, with the
mouth drawn between. The back (up) and side (right) are drawn to match it: the same
planks, bands, rim and outline; the side lid tilts open on its hinge.
"""

from pixel import (
    Anim,
    Character,
    Sprite,
    baseline,
    blank,
    check,
    dissolve,
    mirror,
    paste,
    shear,
    shift,
    silhouette,
    squash,
    write_character,
)

from environment._chest import CHEST_CLOSED, CHEST_OPEN

from enemies._batch_b import vshear

W, H = 32, 48
CW = len(CHEST_CLOSED[0])  # 24

# ---------------------------------------------------------------------------------
# The chest, split: the lid (top and front, with the lock's upper half), the seam row
# (the box's top edge, carrying the hasp) and the box front
# ---------------------------------------------------------------------------------

LID = CHEST_CLOSED[:8]
SEAM = CHEST_CLOSED[8]
BOX = CHEST_CLOSED[9:]
LID_INSIDE = CHEST_OPEN[:6]  # the lid thrown back, its shaded inside facing us
RIM = CHEST_OPEN[10]  # the box's lit top edge, seen when the lid is up

# The back: the same lid top, planks and bands, no lock; two hinges across the seam
BACK = [
    "..KKKKKKKKKKKKKKKKKKKK..",
    ".KSSTLLTTTTTTTTTTTTLLTTK",
    "KSSTTLGTTTTTTTTTTTTLGTTK",
    "KSTTTLGTTTTTTTTTTTTLGTBK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KTBGLLGBBBBBBBBBBGLLGBbK",
    "KKKGDDDKKKKKKKKKKGDDDKKK",
    "KTBGLLGBBBBBBBBBBGLLGBbK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KTBBbLGBBBBBBBBBBBBLGBbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KTBBBLGBBBbBBBBBBBBLGBbK",
    "KBBBBLGBBBBBBBBBbBBLGbbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    ".KKKKKKKKKKKKKKKKKKKKKK.",
]
BACK_LID, BACK_SEAM, BACK_BOX = BACK[:8], BACK[8], BACK[9:]

# The side, front to the right: the lid's top and side, plank seams in line with the
# front's, a corner post at each end, and an iron ring handle
SIDE = [
    "..KKKKKKKKKKKKK.",
    ".KSSTTTTTTTTTTTK",
    "KSSTTTTTTTTTTTTK",
    "KSTTTTTTTTTTTTBK",
    "KTLBBBBBBBBBBLbK",
    "KbDbbbbbbbbbbDbK",
    "KTLBBBBBBBBBBLbK",
    "KTLBBBBBBBBBBLbK",
    "KKDKKKKKKKKKKDKK",
    "KTLBBBBBBBBBBLbK",
    "KTLBBBGDDGBBBLbK",
    "KTLBBGBBBBDBBLbK",
    "KbDbbDbbbbDbbDbK",
    "KTLBBBDDDDBBBLbK",
    "KTLBBBBBBBbBBLbK",
    "KBLBBBBBBBBBBLbK",
    "KbDbbbbbbbbbbDbK",
    ".KKKKKKKKKKKKKK.",
]
SIDE_LID, SIDE_SEAM, SIDE_BOX = SIDE[:8], SIDE[8], SIDE[9:]

TONGUE = [
    "FFF.",
    "FFFr",
    ".FFr",
    ".Fr.",
]
TONGUE_LONG = [
    "FFF..",
    "FFFr.",
    ".FFFr",
    "..FFr",
    "..FFr",
    "...r.",
]

for _name, _sprite in list(globals().items()):
    if _name.isupper() and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)


# ---------------------------------------------------------------------------------
# The mouth
# ---------------------------------------------------------------------------------


# Fangs along the lid's edge and the box's, uneven: bases, then long (W) and short (L)
# tips; lower ones point up
UPPER = ["KWWKWWWKWWKKKKWWKWWWKWWK", "KLKKKWKKKLKKKKKLKKWKKKLK"]
LOWER = ["KKLKKKWKKKKLKKLKKWKKKLKK", "KWWKKWWWKKWWKWWKWWWKKWWK"]


def maw(n: int, eyes: str = "", tongue: bool = False) -> Sprite:
    """The open mouth between lid and box, n rows tall: a dark slit (1), darkness (2),
    fangs (3 and up) round a black-red throat with the tongue on its floor; eyes peer out
    of the dark ("O" opening, "Y" open)."""
    rows = [list("K" * CW) for _ in range(n)]
    if n >= 4:
        for y in range(2, n - 2):
            for x in range(3, CW - 3):
                rows[y][x] = "r" if y >= n // 2 or 7 < x < CW - 8 else "K"
        if tongue:
            for y in range(max(2, n - 4), n - 2):
                for x in range(8, 16):
                    rows[y][x] = "F" if x < 14 else "r"
    if n >= 3:
        rows[0] = list(UPPER[0])
        rows[-1] = list(LOWER[1])
    if n >= 4:
        rows[1] = list(UPPER[1])
        rows[-2] = list(LOWER[0])
    if eyes:
        ey = {1: 0, 2: 0, 3: 1, 4: 1}.get(n, 2)
        for x in (6, CW - 8):
            if eyes == "O":
                rows[ey][x + (x > CW // 2)] = "O"
            else:
                rows[ey][x], rows[ey][x + 1] = ("Y", "W") if x < CW // 2 else ("W", "Y")
    return ["".join(r) for r in rows]


def front(n: int = 0, *, wide: bool = False, eyes: str = "", tongue: bool = False,
          glint: bool = False) -> Sprite:
    """The chest front with the lid lifted n rows over the mouth; wide throws the lid
    right back, so its inside shows above a gaping maw."""
    if n <= 0:
        return list(CHEST_CLOSED)
    if wide:
        top = LID_INSIDE
    else:
        top = LID
    mouth = maw(n, eyes=eyes, tongue=tongue)
    if n == 1 and glint:
        mouth = [mouth[0][:16] + "W" + mouth[0][17:]]
    out = list(top) + mouth + ([RIM] if wide else []) + [SEAM] + list(BOX)
    if tongue and n >= 4:
        t = TONGUE_LONG if wide else TONGUE
        out = paste(out, t, len(top) + n - 2, 14)
    return out


def back(n: int = 0) -> Sprite:
    """The chest from behind, the lid lifted n rows: from here only a dark gap and the
    tips of the fangs show."""
    if n <= 0:
        return list(BACK)
    gap = n if n < 4 else (n + 1) // 2 + 1
    mouth = ["K" * CW for _ in range(gap)]
    if gap >= 2:
        mouth[-1] = "K" + "".join("L" if (x - 2) % 3 == 0 else "K" for x in range(1, CW - 1)) + "K"
    return list(BACK_LID) + mouth + [BACK_SEAM] + list(BACK_BOX)


def side(n: int = 0, *, eyes: str = "", tongue: bool = False) -> Sprite:
    """The chest from the side, front to the right, the lid tilted open on its hinge
    at the back so the front edge rises n rows: a wedge of a mouth."""
    sw = len(SIDE[0])
    if n <= 0:
        return list(SIDE)
    lid_h = len(SIDE_LID)
    canvas = blank(sw, lid_h + n + 1 + len(SIDE_BOX))
    box = [SIDE_SEAM] + list(SIDE_BOX)
    canvas = paste(canvas, box, lid_h + n, 0)
    # the mouth's wedge: from the hinge (no gap) to the front (n rows)
    for x in range(sw):
        gap = round(n * x / (sw - 1))
        for k in range(gap):
            y = lid_h + n - gap + k
            if x in (0, sw - 1):
                ch = "K"
            elif k == 0 and x % 3 != 0 and gap >= 2:
                ch = "W"
            elif k == gap - 1 and x % 3 != 1 and gap >= 3:
                ch = "W"
            elif tongue and k >= gap - 3 and 7 <= x <= 12 and gap >= 4:
                ch = "F"
            else:
                ch = "r" if k >= gap // 2 and gap >= 4 else "K"
            canvas = paste(canvas, [ch], y, x)
    canvas = paste(canvas, vshear(list(SIDE_LID), n, 0), n, 0)
    if eyes:
        gap = round(n * 11 / (sw - 1))
        if gap >= 2:
            ey = lid_h + n - gap + (1 if gap >= 3 else 0)
            canvas = paste(canvas, [eyes + ("W" if eyes == "Y" else eyes)], ey, 10)
    if tongue and n >= 4:
        canvas = paste(canvas, ["FF.", "FFr", ".Fr", ".r."], lid_h + n - 1, sw - 3)
    return canvas


# ---------------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------------


def stand(chest: Sprite, dx: int = 0, dy: int = 0) -> Sprite:
    """The chest on the cell, its bottom on the baseline, moved (dx, dy)."""
    cw, ch = len(chest[0]), len(chest)
    return paste(blank(W, H), chest, baseline(H) - ch + dy, (W - cw) // 2 + dx)


VIEW = {
    "down": lambda n=0, **k: front(n, **k),
    "up": lambda n=0, **k: back(n),
    "right": lambda n=0, wide=False, glint=False, **k: side(n + (2 if wide else 0), **k),
}


def mimic(view: str, n: int = 0, dx: int = 0, dy: int = 0, **kw) -> Sprite:
    return stand(VIEW[view](n, **kw), dx, dy)


def crouch(f: Sprite) -> Sprite:
    """Squashed a row at the box's middle: gathering for a hop, or landing."""
    return squash(f, 1, baseline(H) - 5)


def thud(f: Sprite) -> Sprite:
    """Impact ticks either side of the chest's foot."""
    f = paste(f, [":W", "W."], baseline(H) - 4, 1)
    return paste(f, ["W:", ".W"], baseline(H) - 4, W - 3)


# ---------------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------------


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    for view in VIEW:
        closed = mimic(view)

        # Idle: dead still, a chest like any other, but for one twitch of the lid
        animations["idle"][view] = Anim(
            [closed, closed, closed, mimic(view, 1, glint=True)], fps=6
        )

        # Walk: two hops, gathering, the lid flapping open on the way up and shutting as
        # it lands
        animations["walk"][view] = Anim(
            [
                crouch(closed),
                mimic(view, 3, dy=-3),
                mimic(view, 5, dy=-5, tongue=True),
                mimic(view, 2, dy=-2),
                crouch(closed),
                mimic(view, 2, dy=-3),
                mimic(view, 4, dy=-4, tongue=True),
                mimic(view, 1, dy=-1),
            ],
            fps=10,
        )

        # Attack: jaws wide, lunge, SNAP, worry, settle
        lunge_dx = 3 if view == "right" else 0
        animations["attack"][view] = Anim(
            [
                mimic(view, 4, dy=-1),
                mimic(view, 8, wide=True, tongue=True, eyes="Y", dy=-3),
                mimic(view, 9, wide=True, tongue=True, eyes="Y", dy=-2, dx=lunge_dx),
                thud(mimic(view, dx=lunge_dx)),
                mimic(view, 1, dx=lunge_dx + 1),
                closed,
            ],
            fps=10,
            loop=False,
        )

        # Special, reveal: the lid creaks, settles, lifts on darkness, eyes open in it,
        # look about, then the mouth gapes
        cw = len(VIEW[view]()[0])
        seam = baseline(H) - len(CHEST_CLOSED) + len(LID)
        creak = paste(mimic(view, 1), [":.", ".:"], seam - 2, (W - cw) // 2 - 2)
        creak = paste(creak, [".:", ":."], seam - 2, (W + cw) // 2)
        animations["special"][view] = Anim(
            [
                closed,
                creak,
                closed,
                mimic(view, 2),
                mimic(view, 2, eyes="O"),
                mimic(view, 2, eyes="Y"),
                mimic(view, 3, eyes="Y"),
                mimic(view, 5, eyes="Y", tongue=False),
                mimic(view, 8, wide=True, eyes="Y", tongue=True, dy=-1),
                mimic(view, 8, wide=True, eyes="Y", tongue=True),
            ],
            fps=8,
            loop=False,
        )

        # Death: a flash, the jaw flops open with the tongue lolling, the chest sags and
        # splits, and it fades
        limp = mimic(view, 6, wide=True, tongue=True)
        sag = shear(squash(limp, 3, baseline(H) - 6), 2, baseline(H))
        animations["death"][view] = Anim(
            [
                silhouette(mimic(view, 4), "W"),
                limp,
                sag,
                shift(squash(sag, 3, baseline(H) - 6), 0, 0),
                dissolve(sag, 0.5),
                dissolve(sag, 0.85),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="mimic",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Disguised as treasure: the game's chest, until its lid opens on fangs, a "
            "tongue and glowing eyes. Walks by hopping. Attack is a wide chomp. Special: "
            "reveal (the lid creaks, eyes open in the gap, then the mouth gapes).",
            shadow=22,
        )
    )
