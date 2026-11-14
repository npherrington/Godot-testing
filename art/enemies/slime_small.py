"""Slime (small): one of the two halves a slime splits into when hit.

A half-size lime blob with a gnawed bone floating in it, the same white eyes and
glint as its parent, and a quicker, smaller hop.
Special, "squish": it flattens itself to the floor to duck a blow, then pops back up.

Built like slime.py: _batch_a.slime(w, h, view, mood) draws the lit dome at any size,
so every frame is just a shape. Left is mirror()ed from right.
"""

from pixel import Anim, Character, Sprite, dissolve, mirror, silhouette, write_character

from enemies._batch_a import GUT_BONE, ol, slime, stand

W, H = 32, 48  # the cell
BASE = (12, 8)  # the resting blob, fill only


def body(
    w: int, h: int, view: str, mood: str = "small", lean: float = 0.0, lift: int = 0, dx: int = 0,
    dy: int = 0, gut: Sprite | None = GUT_BONE,
) -> Sprite:
    """The small slime w x h (fill size) on the cell, lifted lift rows off the ground."""
    if view == "right":
        lean += 1.0
    return stand(ol(slime(w, h, view, mood, lean, gut, bubbles=False)), W, H, dx, dy - lift)


# Hop: (w, h, lift, lean): gather, spring, fly, land, settle
HOP = [
    (12, 8, 0, 0.0),
    (14, 6, 0, -0.5),
    (10, 10, 1, 1.0),
    (11, 9, 3, 0.5),
    (11, 9, 5, 0.0),
    (11, 9, 3, -0.5),
    (14, 6, 0, 0.0),
    (13, 7, 0, 0.0),
]


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    for view in ("down", "up", "right"):
        side = view == "right"
        base = body(*BASE, view)

        # Idle: a quick nervous wobble
        animations["idle"][view] = Anim(
            [base, body(13, 7, view), base, body(11, 9, view, lean=0.5 if side else 0)], fps=6
        )

        # Walk: a short hop per cycle
        animations["walk"][view] = Anim(
            [body(w, h, view, lean=n if side else 0, lift=lift) for w, h, lift, n in HOP], fps=10
        )

        # Attack: gather, rear, snap forward with the mouth open, chomp, settle
        if side:
            attack = [
                body(13, 7, view, "small_shut", -1.5, dx=-1),
                body(10, 10, view, "small_open", -1.5, dx=-1),
                body(13, 8, view, "small_open", 3.0, dx=2),
                body(14, 7, view, "small_shut", 2.0, dx=2),
                body(13, 7, view, "small", 0.5, dx=1),
                base,
            ]
        else:
            dy = 1 if view == "down" else -1
            attack = [
                body(13, 7, view, "small_shut"),
                body(10, 10, view, "small_open"),
                body(14, 9, view, "small_open", dy=dy),
                body(15, 7, view, "small_shut", dy=dy),
                body(13, 7, view),
                base,
            ]
        animations["attack"][view] = Anim(attack, fps=10, loop=False)

        # Special, squish: flatten to the floor to duck, shiver, pop back up
        flat = body(16, 4, view, "small_shut", gut=None)
        animations["special"][view] = Anim(
            [
                body(14, 6, view, "small_shut"),
                flat,
                body(16, 4, view, "small_shut", dx=1, gut=None),
                flat,
                body(10, 10, view, "small", lift=1),
                base,
            ],
            fps=10,
            loop=False,
        )

        # Death: flash, deflate, a puddle that dries away
        dead = "small_dead" if view != "up" else "none"
        puddle = body(16, 3, view, "none", gut=None)
        animations["death"][view] = Anim(
            [
                silhouette(base, "W"),
                body(14, 6, view, dead),
                puddle,
                dissolve(puddle, 0.5),
                dissolve(puddle, 0.8),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="slime_small",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Half a slime: a small lime blob with a bone inside, spawned in pairs when a "
            "slime splits; quick hops. Special: squish (flattens to the floor to duck, pops up).",
            shadow=12,
        )
    )
