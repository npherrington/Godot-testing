"""Zombie: slow shambling.

A hunched corpse with grey-green rotting skin (lit grey, green in the shadows), sunken
sockets with milky eyes, a slack jaw, a torn navy shirt hanging off one bare shoulder,
ragged brown trousers over bare shins, and raw wounds. One arm reaches out, hand
hanging limp; the other dangles. Its left leg is stiff and drags.
Attack: a lunging grab and bite.
Special, "rise": it claws up out of the floor, revealed bottom-up from the baseline,
starting as hands in the dirt.

Built like skeleton_warrior: a head and torso on a set of legs per view, arm parts
pasted per frame, animations from those poses with the transforms, left mirrored from
right. Bodies are drawn as fills; _batch_b.place() seals the silhouette in K.
"""

from pixel import (
    Anim,
    Character,
    Sprite,
    baseline,
    blank,
    check,
    dissolve,
    flip,
    mirror,
    paste,
    recolour,
    rotate,
    shear,
    shift,
    silhouette,
    squash,
    underlay,
    write_character,
)

from enemies._batch_b import bury, place, puff, seal, trim

W, H = 32, 48
FPS_WALK = 5

# ---------------------------------------------------------------------------------
# Down: facing the camera. 22 wide; head rows 0-9, torso 10-21, legs 22-29. The
# reaching arm is screen right, the limp one screen left; the stiff leg screen right.
# ---------------------------------------------------------------------------------

HEAD_DOWN = [
    "........D.b...........",
    "......DVGDVb..........",
    ".....GGVGVVVv.........",
    ".....GVVVVGVv.........",
    ".....GDKVVDKv.........",
    ".....GKWVVKLv.........",
    ".....GVVvVVVv.........",
    ".....VFKKKKVv.........",
    "......VKWKWv..........",
    "......vVKVvv..........",
]
# Jaws wide for the bite, both eyes lit
HEAD_DOWN_BITE = [
    "........D.b...........",
    "......DVGDVb..........",
    ".....GGVGVVVv.........",
    ".....GVVVVGVv.........",
    ".....GDKVVDKv.........",
    ".....GKWVVKWv.........",
    ".....GVWKKWVv.........",
    ".....VKrrrrKv.........",
    ".....VKrFFrKv.........",
    "......vWKKWv..........",
]

TORSO_DOWN = [
    "........vVv...........",
    ".....GGVuuuuuuu.......",
    "....GGVvUUuuuuuv......",
    "....GVvUUKLLKuuu......",
    "....uuUUurFrruuu......",
    ".....uUUKLLKuuu.......",
    ".....uuUuruuuUu.......",
    ".....uuUuuuuuuu.......",
    ".....u.uUu.uuu.u......",
    "......BBBBbBBBBb......",
    "......BBBBbBBBBb......",
    "......BBBBbbBBBb......",
]

LEGS_DOWN = [
    "......BBBb..BBBb......",
    "......BbBb..BBbb......",
    "......bBb...bBBb......",
    ".......GV....GVv......",
    ".......Vv....Vv.......",
    ".......GV....Vv.......",
    "......GVv...GVv.......",
    "......VVVv..VVVv......",
]
# The good leg (screen left) lifted in a step; the stiff one planted
LEGS_DOWN_STEP = [
    "......BBBb..BBBb......",
    "......BbBb..BBbb......",
    ".....bBBb...bBBb......",
    ".....GVv.....GVv......",
    ".....VVVv....Vv.......",
    "......vv.....Vv.......",
    ".............GVv......",
    "............VVVv......",
]
# The stiff leg dragged, its foot twisted in and scraping
LEGS_DOWN_DRAG = [
    "......BBBb..BBBb......",
    "......BbBb..BBbb......",
    "......bBb...bBBb......",
    ".......GV.....GVv.....",
    ".......Vv.....Vv......",
    ".......GV......Vv.....",
    "......GVv......GV.....",
    "......VVVv....vVV.....",
]

LIMP_DOWN = [
    "GG.",
    "GVV",
    "GVv",
    "Vv.",
    "GV.",
    "VF.",
    "Vr.",
    "Vv.",
    "GV.",
    "GVv",
    "VVv",
    "v.v",
]
# Reaching toward the camera: the upper arm out, the forearm foreshortened, the hand
# hanging limp in front at chest height
REACH_DOWN = [
    "uuGG....",
    ".uGVG...",
    "..GVVG..",
    "..vGVVG.",
    "...GGGVv",
    "...GVVVv",
    "...VvVvv",
    "...v.v.v",
]
# Both arms up and out to grab, fingers hooked
GRAB_DOWN = [
    "G.G.",
    "GVGV",
    "VVVv",
    "GVv.",
    ".GVv",
    "..GV",
    "..vV",
]
# Both arms straight up, clawing: the rise
ARM_UP_DOWN = [
    "G.G.",
    "GVGV",
    "VVVv",
    ".GVv",
    ".GV.",
    ".VF.",
    ".Vr.",
    ".GV.",
    ".Vv.",
    ".GV.",
    ".Vv.",
    ".GV.",
    ".GVv",
    ".GVV",
    "..GV",
    "..Vv",
    "..GG",
]

# ---------------------------------------------------------------------------------
# Up: the back. Sparse hair over a mottled scalp, a rip down the shirt over the spine.
# ---------------------------------------------------------------------------------

HEAD_UP = [
    "........D.b...........",
    "......DbDDbD..........",
    ".....GDVbVDVv.........",
    ".....GVVVbVVv.........",
    ".....GVVVVVVv.........",
    ".....GVVGVVVv.........",
    ".....GVVVVVVv.........",
    ".....vGVVVVVv.........",
    "......vVVVVv..........",
    "......vvVVvv..........",
]
TORSO_UP = [
    "........vVv...........",
    ".....uuUUuuuuu........",
    "....uUUUuuuuuuv.......",
    "....uUUuGVvuuuu.......",
    "....uUUuVGvuuuu.......",
    ".....uUuGVvuuu........",
    ".....uUuuVuuUu........",
    ".....uuUuuuuuu........",
    ".....u.uUu.uuu.u......",
    "......BBBBbBBBBb......",
    "......BBBBbBBBBb......",
    "......BBBBbbBBBb......",
]
LEGS_UP = [r[::-1] for r in LEGS_DOWN]
LEGS_UP_STEP = [r[::-1] for r in LEGS_DOWN_STEP]
LEGS_UP_DRAG = [r[::-1] for r in LEGS_DOWN_DRAG]

# ---------------------------------------------------------------------------------
# Right: profile, facing right. 20 wide. The head pokes forward of the hunched torso;
# the near arm reaches straight out, wrist limp. The stiff leg is the far one.
# ---------------------------------------------------------------------------------

HEAD_RIGHT = [
    "....................",
    ".......D.bD.........",
    "......DGGVGVb.......",
    ".....GGVVVVVVv......",
    ".....GVVVVVDKVv.....",
    ".....GVVVVVKWVVv....",
    ".....vGVVVVVVVVVv...",
    "......vVVVVVKKKv....",
    "......vVVVVKWKW.....",
    ".......vVVvvKKv.....",
]
HEAD_RIGHT_BITE = [
    "....................",
    ".......D.bD.........",
    "......DGGVGVb.......",
    ".....GGVVVVVVv......",
    ".....GVVVVVDKVv.....",
    ".....GVVVVVKWVVvv...",
    ".....vGVVVVVVWKWW...",
    "......vVVVVKrrrK....",
    "......vVVVKrFF......",
    ".......vVVVKWKW.....",
]
TORSO_RIGHT = [
    "........vVVv........",
    "....uuuuuuuu........",
    "...uUUuuuUuu........",
    "...uUUGVuuuu........",
    "....uUVFuuUu........",
    "....uUVruuuu........",
    "....uuUuuUuu........",
    "....uUuuuuUu........",
    "....u.uuu.uu........",
    ".....BBBBBBb........",
    ".....BBBBBBb........",
    ".....BBBBBbb........",
]
LEGS_RIGHT = [
    ".....BBBbBBb........",
    ".....BbBbBBb........",
    ".....bBb.bBb........",
    "......GV..GV........",
    "......Vv..Vv........",
    "......GV..GV........",
    "......Vv..Vv........",
    "......VVVv.VVVv.....",
]
# The good leg forward and bent, the stiff one trailing straight, its toe on the floor
LEGS_RIGHT_STEP = [
    ".....BBBbBBb........",
    "....BbB..BBBb.......",
    "....bBb...bBBb......",
    "...GV.......GVv.....",
    "...Vv.......Vv......",
    "..GV........GV......",
    "..Vv........Vv......",
    ".Vv.........VVVv....",
]
# The body over the good leg, the stiff leg dragged behind, toe scraping
LEGS_RIGHT_DRAG = [
    ".....BBBbBBb........",
    "....BbB.BBBb........",
    "...bBb..bBBb........",
    "..GV.....GV.........",
    ".GV......Vv.........",
    ".Vv......GV.........",
    "GV.......Vv.........",
    "Vv.......VVVv.......",
]

REACH_RIGHT = [
    "GGVVFrVVGG..",
    "vVVvvvvVVVG.",
    "........GVVv",
    "........VvVv",
    "........v.v.",
]
GRAB_NEAR_RIGHT = [
    "GGVVFrVVVGG...",
    "vVVvvvvvVVVGv.",
    "..........GVVv",
    "..........Vv.v",
]
GRAB_FAR_RIGHT = [
    "vVVVVVVvV..",
    ".vvvvvvVVVv",
    "........v.v",
]
# The near arm up for the rise: forward under the chin, then the forearm straight up
# in front of the face
ARM_UP_RIGHT = [
    "........G.G.",
    "........GVGV",
    "........VVVv",
    ".........GVv",
    ".........GV.",
    ".........VF.",
    ".........Vr.",
    ".........GV.",
    ".........Vv.",
    ".........GV.",
    ".........Vv.",
    ".........GV.",
    ".......GGVv.",
    "....GGVVVv..",
    "GGVVVvvv....",
    "uuvv........",
]

# The mound it digs out of: clods of dirt over the floor line
MOUND = [
    "......bB..Tb......",
    "...bBTBbBBBTBb....",
    ".bBTBBbBTBBbBTBb..",
    "bBbBBTBbBBbBBbBBbb",
]
MOUND_LOW = [
    "......b...........",
    "..bBb.BTBb..bBb...",
    ".bBTBbBBbBTBBbBb..",
]
CLODS = [
    "..b.......B.....",
    "B.......b....b..",
    "......T.........",
]

for _name, _sprite in list(globals().items()):
    if _name.isupper() and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)


def _darker(s: Sprite) -> Sprite:
    """A far limb: a shade darker."""
    return recolour(s, {"G": "V", "V": "v", "F": "r"})


# ---------------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------------

VIEWS = {
    "down": {
        "head": HEAD_DOWN, "bite": HEAD_DOWN_BITE, "torso": TORSO_DOWN,
        "legs": LEGS_DOWN, "step": LEGS_DOWN_STEP, "drag": LEGS_DOWN_DRAG,
        "reach": ([(LIMP_DOWN, 11, 3), (REACH_DOWN, 11, 13)], []),
        "grab": ([(GRAB_DOWN, 5, 1), (flip(GRAB_DOWN), 5, 15)], []),
        "up": ([(ARM_UP_DOWN, -6, 2), (flip(ARM_UP_DOWN), -6, 14)], []),
    },
    "up": {
        "head": HEAD_UP, "bite": HEAD_UP, "torso": TORSO_UP,
        "legs": LEGS_UP, "step": LEGS_UP_STEP, "drag": LEGS_UP_DRAG,
        "reach": ([(flip(LIMP_DOWN), 11, 15), (_darker(flip(REACH_DOWN)), 11, 0)], []),
        "grab": ([(GRAB_DOWN, 5, 0), (flip(GRAB_DOWN), 5, 14)], []),
        "up": ([(ARM_UP_DOWN, -6, 1), (flip(ARM_UP_DOWN), -6, 13)], []),
    },
    "right": {
        "head": HEAD_RIGHT, "bite": HEAD_RIGHT_BITE, "torso": TORSO_RIGHT,
        "legs": LEGS_RIGHT, "step": LEGS_RIGHT_STEP, "drag": LEGS_RIGHT_DRAG,
        "reach": ([(REACH_RIGHT, 11, 6)], []),
        "grab": ([(GRAB_NEAR_RIGHT, 11, 5)], [(_darker(GRAB_FAR_RIGHT), 8, 9)]),
        "up": ([(ARM_UP_RIGHT, -4, 5)], [(_darker(ARM_UP_RIGHT), -6, 7)]),
    },
}


def zombie(view: str, legs: str = "legs", arms: str = "reach", head: str = "head",
           dx: int = 0, dy: int = 0) -> Sprite:
    v = VIEWS[view]
    body = v[head] + v["torso"] + v[legs]
    front, back = v[arms]
    return place(body, W, H, front=front, back=back, dx=dx, dy=dy)


def sag(f: Sprite, n: int = 1) -> Sprite:
    """The body sunk n rows at the hips, the feet still planted."""
    return squash(f, n, 34)


def dust(f: Sprite, left: int) -> Sprite:
    """A scuff of dust at the floor, under the figure."""
    return underlay(f, [":.:.", ".::.", "::::"], baseline(H) - 3, left)


# ---------------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------------


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    floor = baseline(H)  # the first row under the feet
    for view in VIEWS:
        base = zombie(view)
        step = zombie(view, "step")
        drag = zombie(view, "drag")
        lean = 1 if view != "up" else -1  # which way a lurch tips, per view
        toe = {"down": 18, "up": 10, "right": 6}[view]

        # Idle: swaying on the spot, head lolling, jaw working
        animations["idle"][view] = Anim(
            [base, shear(base, lean, 30), sag(shear(base, lean, 30)), shear(base, -lean, 30)],
            fps=4,
        )

        # Walk: a quick lurch onto the good leg, then the long drag of the stiff one,
        # the toe scraping up dust; the body tips and sinks out of step
        animations["walk"][view] = Anim(
            [
                shear(step, lean, 34),
                sag(shear(step, 2 * lean, 34)),
                sag(shear(base, lean, 34)),
                dust(shear(drag, 0, 34), toe),
                dust(sag(shear(drag, -lean, 34)), toe),
                dust(sag(shear(drag, -lean, 34), 2), toe - 1),
                shear(base, -lean, 34),
                base,
            ],
            fps=FPS_WALK,
        )

        # Attack: rear back with both arms up, lunge, bite, worry at it, let go
        grab = zombie(view, arms="grab")
        bite = zombie(view, arms="grab", head="bite")
        if view == "right":
            lunge = shear(shift(bite, 2, 0), 3, 34)
            chomp = shear(shift(grab, 2, 0), 3, 34)
            spray = paste(chomp, ["!.!", ".!!", "!.."], 20, 26)
        else:
            lunge = squash(bite, 1, 30)
            chomp = squash(grab, 2, 30)
            spray = paste(chomp, ["!.!.!", ".!!!.", "!...!"], 25, 12)
        animations["attack"][view] = Anim(
            [shear(grab, -lean, 34), lunge, spray, shift(spray, 1, 0), chomp, base],
            fps=8,
            loop=False,
        )

        # Special, rise: hands break the dirt, then head, shoulders and body push up
        # out of the floor, bottom-up from the baseline
        risen = zombie(view, arms="up")
        top = next(y for y, row in enumerate(risen) if row.strip("."))
        height = floor - top  # rows from the top of its hands to the floor

        def mound(f: Sprite, low: bool = False) -> Sprite:
            m = MOUND_LOW if low else MOUND
            return paste(f, seal(m), floor - len(m), (W - len(m[0])) // 2 - 1)

        def dug(depth: int, low: bool = False) -> Sprite:
            return mound(bury(risen, depth, floor - 2), low)

        animations["special"][view] = Anim(
            [
                mound(blank(W, H)),
                dug(height - 6),
                dug(height - 9),
                paste(dug(height - 14), CLODS, floor - 12, 8),
                dug(height - 20),
                paste(dug(height - 26), CLODS, floor - 18, 8),
                dug(5),
                dug(1, low=True),
                paste(risen, seal(MOUND_LOW), floor - 2, 6),
                base,
            ],
            fps=7,
            loop=False,
        )

        # Death: a flash as it jerks back, the knees go, it pitches over and lies
        # there, then rots away into a sour haze
        lying = trim(base)
        lying = rotate(lying, 1 if view != "up" else 3)
        fallen = paste(blank(W, H), lying, floor - len(lying), (W - len(lying[0])) // 2)
        rot = puff(24, 10, "%", 0.7)
        animations["death"][view] = Anim(
            [
                silhouette(shear(base, -lean, 34), "W"),
                sag(shear(base, -lean, 34), 4),
                shear(sag(base, 9), 3 * lean, 40),
                fallen,
                underlay(dissolve(fallen, 0.45), rot, floor - 12, 4),
                dissolve(underlay(fallen, rot, floor - 14, 4), 0.8),
            ],
            fps=7,
            loop=False,
        )

    write_character(
        Character(
            name="zombie",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Slow shambler: a hunched, rotting grey-green corpse in a torn shirt, one "
            "arm reaching, dragging a stiff leg. Attack is a lunging grab and bite. "
            "Special: rise (claws up out of the floor, hands first).",
            shadow=14,
        )
    )
