"""Harpy: flying attacker.

A wild bird-woman: a fierce face with burning yellow eyes under a spiky crest of red
feathers, a ruff of pale chest feathers, broad brown hawk wings for arms with dark
flight feathers, a fanned tail, and scaly yellow legs ending in black talons. It hovers
above its shadow, beating its wings.
Attack: a swooping dive, talons first.
Special: a screech that drives a gust of wind and feathers (Effects gust, feathers).

Built like skeleton_warrior: a body per view with wing parts pasted per frame (up, mid
and down for the flap), animations from those poses with the transforms, left mirrored
from right. Bodies are drawn as fills; _batch_b.place() seals the silhouette in K.
"""

from pixel import (
    Anim,
    Character,
    Effect,
    Sprite,
    arc,
    baseline,
    blank,
    check,
    pad,
    dissolve,
    flip,
    mirror,
    paste,
    recolour,
    rotate,
    shear,
    shift,
    silhouette,
    underlay,
    write_character,
)

from enemies._batch_b import place, seal, trim

W, H = 32, 48
HOVER = 6  # rows between the talons and the floor

# ---------------------------------------------------------------------------------
# Down: facing the camera. Body 14 wide, shoulders at row 11; wings attach behind them.
# ---------------------------------------------------------------------------------

BODY_DOWN = [
    "...R.R..R.R...",
    "..RRrR.RRrRR..",
    "..rRRRRRRRRr..",
    ".RrRRRRRRRRrR.",
    ".rRRSSSSSSRRr.",
    ".rRSKYSSYKSRr.",
    ".rrSSSTTSSSrr.",
    "..rRSSTOSSRr..",
    "..rRTSKKSTRr..",
    "..r.TSSSST.r..",
    "....WTSSTW....",
    "...WSWWSWSW...",
    "...TSWSSWST...",
    "...TTSWWSTT...",
    "...BTTSSTTB...",
    "...BBTTTTBB...",
    "....BBBBBB....",
    "...bBbBBbBb...",
    "...bBb..bBb...",
    "....OY..YO....",
    "....OY..YO....",
    "...OYO..OYO...",
    "...K.K..K.K...",
]
# The screech: crest flared, eyes blazing, mouth wide
HEAD_DOWN_SCREECH = [
    ".R.R.R..R.R.R.",
    "..RRrR.RRrRR..",
    ".RrRRRRRRRRrR.",
    "RrRRRRRRRRRRrR",
    ".rRRSSSSSSRRr.",
    ".rRKYYSSYYKRr.",
    ".rrSSSTTSSSrr.",
    "..rRSKrrKSRr..",
    "..rRTKrrKTRr..",
    "..r.TSKKST.r..",
]
# Talons thrown forward for the strike: legs spread, claws open
LEGS_DOWN_STRIKE = [
    "...OY....YO...",
    "..OY......YO..",
    ".OYO......OYO.",
    ".K.K......K.K.",
]

# Wings, screen left (the right is the mirror), each with the (row, column) of its
# top-left in body coordinates; they sit behind the shoulders.
WING_UP_DOWN = [
    "S...........",
    "ST..........",
    "STb.........",
    "STBb........",
    ".STBb.......",
    ".STBBb......",
    ".STBbBb.....",
    "..STBBbb....",
    "..STBBBBb...",
    "...STBbBBb..",
    "...STBBBbBb.",
    "....STTBBBBb",
    ".....STTBBBB",
    "......SSTTBB",
    "........TTTB",
    "..........TT",
]
WING_MID_DOWN = [
    "......TTSST",
    "...TTTSSTTT",
    ".TTTBBTTTBB",
    "TBBBBBBBBBB",
    "BBbBBbBBbBb",
    "bBbBbBbbBb.",
    "b.bbb.bb...",
    "...b.b.....",
]
WING_DOWN_DOWN = [
    ".......TTT",
    ".....TTSTT",
    "....TTBBBB",
    "...TBBBBBb",
    "..TBBbBBb.",
    ".TBBbBbb..",
    ".TBbBbb...",
    "TBbBbb....",
    "TBbBb.....",
    "Bbbb......",
    "bBb.......",
    "bb........",
    "b.........",
]
WINGS_DOWN = {
    "up": (WING_UP_DOWN, -4, -8),
    "mid": (WING_MID_DOWN, 9, -8),
    "down": (WING_DOWN_DOWN, 10, -7),
}

# ---------------------------------------------------------------------------------
# Up: the back. The crest falling to a mane, brown back plumage, the tail fanned.
# ---------------------------------------------------------------------------------

BODY_UP = [
    "...R.R..R.R...",
    "..RRrRRRRrRR..",
    "..rRRRRRRRRr..",
    ".RrRRRRRRRRrR.",
    ".rRRRRrRRRRRr.",
    ".rRRrRRRRrRRr.",
    ".rrRRRRRRRRrr.",
    "..rRRrRRrRRr..",
    "..rRrRRRRrRr..",
    "..r.rRrrRr.r..",
    "....BTrrTB....",
    "...BTBBBBTB...",
    "...TBBTBBBb...",
    "...BBTBBBbb...",
    "...BBBTBBbb...",
    "...bBBBBbbb...",
    "...bBbBbBbb...",
    "..bBbBbBbBbb..",
    ".bBb.bBb.bBb..",
    "....OY..YO....",
    "....OY..YO....",
    "...OYO..OYO...",
    "...K.K..K.K...",
]
WINGS_UP = {k: (recolour(s, {"S": "T", "T": "B"}), r, c) for k, (s, r, c) in WINGS_DOWN.items()}

# ---------------------------------------------------------------------------------
# Right: profile, facing right. The crest sweeps back, the tail trails; the near wing
# is drawn whole over the body, the far one shows past it.
# ---------------------------------------------------------------------------------

BODY_RIGHT = [
    "....R.R.......",
    "..RRRrRR......",
    ".RrRRRRRr.....",
    "RrrRRRSSSS....",
    ".RrRRSSKYS....",
    "..RrRSSSSTO...",
    "..rRrSSSKK....",
    "...rRTSSS.....",
    "...r.WTST.....",
    "....WSWSW.....",
    "....TSWWST....",
    "....TTSWST....",
    "....BTTSTB....",
    "....BBTTBB....",
    "...bBBBBBb....",
    "..bbBbBBb.....",
    ".bb.bBb.......",
    "bb...OY.......",
    "......OY......",
    "......OYY.....",
    "......YOYY....",
    "......K.KK....",
]
HEAD_RIGHT_SCREECH = [
    "R...R.R.......",
    ".RRRRrRR......",
    "RRrRRRRRr.....",
    "RrrRRRSSSS....",
    ".RrRRSSKYY....",
    "..RrRSSSSKKO..",
    "..rRrSSSKrrK..",
    "...rRTSSKKK...",
]
LEGS_RIGHT_STRIKE = [
    "......OYYY....",
    "........OYY...",
    ".........OYYY.",
    ".........K.KK.",
]

WING_UP_RIGHT = [
    "bB...........",
    "bBT..........",
    ".bBT.........",
    ".bBBT........",
    "..bBBT.......",
    "..bBBTT......",
    "...bBBTS.....",
    "...bBBBTS....",
    "....bBBBTS...",
    ".....bBBTTS..",
    "......bBBTTS.",
    ".......bBBTT.",
]
WING_MID_RIGHT = [
    "....TTTTSSSST.",
    ".TTTBBBTTTTTTS",
    "bBBBBBBBBBBBT.",
    ".bBbBBbBBBb...",
    "..b.bBb.bb....",
]
WING_DOWN_RIGHT = [
    "........TTS",
    "......BBTTS",
    ".....bBBBT.",
    "....bBBBb..",
    "...bBBbB...",
    "..bBbBb....",
    ".bBbBb.....",
    ".bBb.b.....",
    "bb.........",
]
WINGS_RIGHT = {
    "up": (WING_UP_RIGHT, -2, -4),
    "mid": (WING_MID_RIGHT, 8, -6),
    "down": (WING_DOWN_RIGHT, 9, -2),
}

# Lying dead, sprawled on the floor: wings splayed flat, eyes shut, a leg in the air
DEAD = [
    "..........R.R.............",
    ".bb.....RRrRRr.......bb...",
    "bBBb...rRSSSRr.....bBBBb..",
    "BBTTb..rSKSKSr....bTTBBBb.",
    ".bBTTBbrRSSSRrBbbTTBBb....",
    "..bBBTTBWSWSWBTTTBBbb.....",
    "...bbBBBTSWSTBBBbb........",
    ".....bbBBBBBBBbb..OY......",
    "........bBBbb.....YOK.....",
]
for _name, _sprite in list(globals().items()):
    if _name.isupper() and isinstance(_sprite, list) and _sprite and isinstance(_sprite[0], str):
        check(_sprite, _name)


def _far(s: Sprite) -> Sprite:
    return recolour(s, {"S": "T", "T": "B", "B": "b"})


# ---------------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------------

VIEWS = {
    "down": (BODY_DOWN, WINGS_DOWN, HEAD_DOWN_SCREECH, LEGS_DOWN_STRIKE),
    "up": (BODY_UP, WINGS_UP, BODY_UP[:8], LEGS_DOWN_STRIKE),
    "right": (BODY_RIGHT, WINGS_RIGHT, HEAD_RIGHT_SCREECH, LEGS_RIGHT_STRIKE),
}


def harpy(view: str, wing: str = "mid", screech: bool = False, strike: bool = False,
          dy: int = 0, dx: int = 0) -> Sprite:
    """The view's body with both wings in position wing, hovering HOVER rows up and then
    moved (dx, dy)."""
    body, wings, head, talons = VIEWS[view]
    if screech:
        body = head + body[len(head):]
    if strike:
        body = body[: len(body) - 4] + talons
    s, r, c = wings[wing]
    bw = len(body[0])
    front, back = [], []
    if view == "right":
        front.append((s, r, c))
        back.append((_far(s), r - 1, c + 3))
    else:
        back += [(s, r, c), (flip(s), r, bw - c - len(s[0]))]
    return place(body, W, H, front=front, back=back, dx=dx, dy=dy - HOVER)


# ---------------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------------

FEATHER = ["..T", ".TB", "Tb."]


def _gust_frame(n: int) -> Sprite:
    """Wind rings rolling out to the right, a feather caught in them."""
    w, h = 24, 20
    f = blank(w, h)
    for k in range(3):
        r = 3 + 5 * k + 2 * n
        if r > 22:
            continue
        a = arc(w, h, 0, h / 2, r, -50, 50, ":", thickness=1.5, edge="W" if k == n % 3 else "L")
        f = underlay(f, a, 0, 0)
    f = paste(f, FEATHER, 3 + n, 6 + 4 * n)
    f = paste(f, flip(FEATHER), 14 - n, 4 + 4 * n)
    return f


GUST = [_gust_frame(n) for n in range(4)]

FEATHERS = [
    paste(paste(paste(blank(16, 16), FEATHER, 1 + n, 2 + n), flip(FEATHER), 6 + n, 10 - n),
          rotate(FEATHER, n), 10 + n // 2, 5 + n)
    for n in range(4)
]


# ---------------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------------


def build() -> None:
    animations: dict[str, dict[str, Anim]] = {
        "idle": {}, "walk": {}, "attack": {}, "special": {}, "death": {},
    }
    floor = baseline(H)
    for view in VIEWS:
        lean = 1 if view == "right" else 0

        # Idle: a steady beat; the body lifts on the downstroke and sinks on the up
        animations["idle"][view] = Anim(
            [harpy(view, "up", dy=1), harpy(view, "mid"), harpy(view, "down", dy=-1), harpy(view, "mid")],
            fps=8,
        )

        # Walk (flying): two quicker beats, leaning into the flight
        beat = [("up", 1), ("mid", 0), ("down", -1), ("mid", -1)]
        animations["walk"][view] = Anim(
            [shear(harpy(view, w, dy=d), 2 * lean, 40) for w, d in beat * 2], fps=10
        )

        # Attack: climb with wings high, fold and dive, talons strike at the floor with
        # a slash, then beat back up
        climb = harpy(view, "up", dy=-3)
        if view == "right":
            dive = shear(harpy(view, "up", strike=True, dy=2, dx=2), 4, 40)
            hit = shear(harpy(view, "down", strike=True, dy=5, dx=4), 2, 40)
            slash = arc(14, 12, 0, 0, 11, 270, 360, ":", thickness=2.5, edge="W")
            hit = paste(hit, slash, floor - 12, 18)
        else:
            dive = harpy(view, "up", strike=True, dy=3)
            hit = harpy(view, "mid", strike=True, dy=HOVER)
            slash = arc(20, 8, 10, -6, 12, 200, 340, ":", thickness=2.5, edge="W")
            hit = paste(hit, slash, floor - 6, 6)
        animations["attack"][view] = Anim(
            [climb, shift(climb, 0, -1), dive, hit, harpy(view, "down", dy=1), harpy(view, "mid")],
            fps=10,
            loop=False,
        )

        # Special, screech: rear up with wings high, then sweep them forward screaming,
        # the gust rolling out (the Effect carries it on)
        rear = harpy(view, "up", dy=-2)
        cry = harpy(view, "down", screech=True, dy=1)
        cry2 = harpy(view, "mid", screech=True)
        if view == "right":
            rings = arc(10, 16, 0, 8, 8, -60, 60, ":", thickness=1.5, edge="W")
            cry = paste(cry, rings, 15, 22)
            cry2 = paste(cry2, shift(rings, 1, 0), 15, 22)
        else:
            rings = arc(16, 8, 8, 0, 7, 200, 340, ":", thickness=1.5, edge="W")
            wide = arc(24, 10, 12, 0, 10, 205, 335, ":", thickness=1.5, edge="L")
            cry = paste(paste(cry, rings, 39, 8), wide, 38, 4)
            cry2 = paste(paste(cry2, rings, 40, 8), wide, 39, 4)
        animations["special"][view] = Anim(
            [harpy(view, "mid"), rear, shift(rear, 0, -1), cry, cry2, cry, cry2, harpy(view, "mid")],
            fps=9,
            loop=False,
        )

        # Death: struck, it flashes, tumbles, drops to the floor and lies with a wing
        # splayed, feathers drifting, then fades
        hurt = harpy(view, "up")
        tumble = shear(harpy(view, "down", dy=2), -3, 40)
        if view == "right":
            lying = trim(rotate(trim(harpy(view, "mid", dy=HOVER)), 1))
        else:
            lying = seal(pad(DEAD if view == "down" else flip(DEAD), 1, 1, 1, 1))
        down = paste(blank(W, H), lying, floor - len(lying), (W - len(lying[0])) // 2)
        drift = paste(paste(down, FEATHER, floor - 18, 6), flip(FEATHER), floor - 22, 22)
        animations["death"][view] = Anim(
            [
                silhouette(hurt, "W"),
                tumble,
                shift(rotate_cell(tumble), 0, 2),
                drift,
                dissolve(drift, 0.5),
                dissolve(drift, 0.85),
            ],
            fps=8,
            loop=False,
        )

    write_character(
        Character(
            name="harpy",
            kind="enemies",
            size=(W, H),
            animations={name: mirror(views) for name, views in animations.items()},
            notes="Flying attacker: a bird-woman with a red feather crest, yellow eyes, brown "
            "hawk wings for arms and yellow talons, hovering over its shadow. Attack is a "
            "talon dive. Special: screech (a wing gust that throws wind and feathers).",
            shadow=12,
            effects=(
                Effect("gust", GUST, fps=10, loop=False,
                       notes="Wind rings rolling out to the right with feathers caught in them."),
                Effect("feathers", FEATHERS, fps=8, loop=True,
                       notes="Loose feathers drifting down: the screech's debris, or a hit."),
            ),
        )
    )


def rotate_cell(f: Sprite) -> Sprite:
    """The cell's figure turned a quarter clockwise about its middle: mid-tumble."""
    body = trim(f)
    turned = rotate(body, 1)
    bw, bh = len(turned[0]), len(turned)
    return paste(blank(W, H), turned, (H - bh) // 2 + 6, (W - bw) // 2)
