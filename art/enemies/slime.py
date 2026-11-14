"""Slime: a low lime blob that splits in two when hit.

A gumdrop of green ooze, lit from the top left with a wet glint, white eyes, and a
half-digested skull and a few bubbles floating inside it.
Special, "split": it stretches wide, pinches at the waist and divides into two halves
that slide apart; the game then swaps it for two slime_small.

How it's built: the body is drawn, not typed. _batch_a.slime(w, h, view, mood) makes a
lit dome of any size with the face and the skull pasted in, so squash and stretch are
just other sizes. Every frame is a list of (width, height, lift, lean, mood) shapes.
Left is mirror()ed from right.
"""

from pixel import Anim, Character, Sprite, blank, dissolve, mirror, paste, silhouette, write_character

from enemies._batch_a import GUT_BONE, GUT_SKULL, ol, slime, stand

W, H = 32, 48  # the cell
BASE = (24, 16)  # the resting blob, fill only

# The skull it leaves in the puddle when it dies
SKULL = ol(GUT_SKULL)


def body(
    w: int, h: int, view: str, mood: str = "calm", lean: float = 0.0, lift: int = 0, dx: int = 0,
    dy: int = 0, gut: Sprite | None = GUT_SKULL,
) -> Sprite:
    """The slime w x h (fill size) on the cell, lifted lift rows off the ground."""
    return stand(ol(slime(w, h, view, mood, lean, gut)), W, H, dx, dy - lift)


def view_lean(view: str, lean: float) -> float:
    """Profile faces right, so it leans that way at rest; the other views stand straight."""
    return lean + 1.5 if view == "right" else 0.0


def twins(halves: list[tuple[int, int, int, str, bool]], view: str) -> Sprite:
    """Two blobs, each (w, h, centre offset, mood, has the bone), on one cell."""
    out = blank(W, H)
    lean = 1.0 if view == "right" else 0.0
    for w, h, off, mood, bone in halves:
        s = ol(slime(w, h, view, mood, lean, GUT_BONE if bone else None))
        out = paste(out, s, H - 2 - len(s) + 1, W // 2 + off - len(s[0]) // 2)
    return out


def peanut(w: int, h: int, apart: int, view: str) -> Sprite:
    """Two domes w x h overlapping, their centres apart pixels apart, under one outline:
    the pinch before the split. Each half already has its own squinting eyes."""
    out = blank(w + apart, h)
    out = paste(out, slime(w, h, view, "none", 0.0, None, bubbles=False), 0, 0)
    out = paste(out, slime(w, h, view, "none", 0.0, GUT_SKULL, bubbles=False), 0, apart)
    if view != "up":
        for c in (w // 2, apart + w // 2):
            out = paste(out, ["KK.KK"], h // 3, c - 2 + (1 if view == "right" else 0))
    # The waist: a dark crease down the middle where it's pulling apart
    mid = (w + apart) // 2
    for y in range(h):
        if out[y][mid] != ".":
            out = paste(out, ["v"], y, mid)
    return stand(ol(out), W, H)


# Hop: (w, h, lift, lean): gather, spring, fly, land, settle
HOP = [
    (24, 16, 0, 0.0),
    (27, 13, 0, -1.0),
    (20, 19, 1, 2.0),
    (21, 18, 5, 1.0),
    (22, 17, 7, 0.0),
    (21, 18, 4, -1.0),
    (28, 12, 0, 0.0),
    (25, 15, 0, 0.0),
]


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    for view in ("down", "up", "right"):
        lean = lambda n: view_lean(view, n)  # noqa: E731
        base = body(*BASE, view, lean=lean(0))

        # Idle: a slow wobble, settling and swelling
        animations["idle"][view] = Anim(
            [base, body(25, 15, view, lean=lean(0)), base, body(23, 17, view, lean=lean(0.5))], fps=5
        )

        # Walk: one full hop per cycle; the shadow stays on the floor
        animations["walk"][view] = Anim(
            [body(w, h, view, lean=lean(n), lift=lift) for w, h, lift, n in HOP], fps=9
        )

        # Attack: gather, rear up with the maw open, lunge, engulf, chomp, pull back.
        # From the front and back it lunges by swelling; in profile it throws itself forward.
        if view == "right":
            attack = [
                body(25, 14, view, "shut", lean(-3), dx=-1),
                body(21, 19, view, "open", lean(-3), dx=-1),
                body(25, 16, view, "open", lean(5), dx=2),
                body(27, 14, view, "open", lean(4), dx=2),
                body(27, 13, view, "shut", lean(2), dx=2),
                body(25, 15, view, "calm", lean(0.5), dx=1),
                base,
            ]
        else:
            dy = 1 if view == "down" else -1
            attack = [
                body(26, 14, view, "shut"),
                body(21, 20, view, "open"),
                body(28, 18, view, "open", dy=dy),
                body(30, 15, view, "open", dy=dy),
                body(30, 13, view, "shut", dy=dy),
                body(26, 15, view, "calm"),
                base,
            ]
        animations["attack"][view] = Anim(attack, fps=10, loop=False)

        # Special, split: stretch wide, pinch at the waist, divide, the halves slide apart
        animations["special"][view] = Anim(
            [
                base,
                body(26, 15, view, "shut", lean(0)),
                body(30, 13, view, "shut", lean(0)),
                peanut(17, 13, 13, view),
                peanut(15, 12, 14, view),
                twins([(14, 10, -7, "small_shut", False), (14, 10, 7, "small_shut", True)], view),
                twins([(13, 9, -8, "small_open", False), (13, 9, 8, "small_open", True)], view),
                twins([(12, 8, -8, "small", False), (12, 8, 8, "small", True)], view),
            ],
            fps=8,
            loop=False,
        )

        # Death: flash, deflate, spread into a puddle that dries up round the skull
        dead = "dead" if view != "up" else "none"
        puddle = body(30, 5, view, "none", 0.0, gut=None)
        skull_on = lambda f: paste(f, SKULL, H - 1 - len(SKULL), W // 2 - len(SKULL[0]) // 2)  # noqa: E731
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                body(27, 12, view, dead, lean(0)),
                body(30, 8, view, dead, 0.0, gut=None),
                skull_on(puddle),
                skull_on(dissolve(puddle, 0.5)),
                dissolve(skull_on(dissolve(puddle, 0.75)), 0.55),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="slime",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="A low lime blob with a half-digested skull inside; hops to move, lunges to "
            "engulf. Special: split (stretches, pinches and divides into two slime_small).",
            shadow=24,
        )
    )
