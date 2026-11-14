"""Traps: the pressure plate (a floor tile), the spike wall and the arrow trap (wall
faces), and the arrow they shoot.

    python3 art/build.py env_traps

Writes assets/sprites/environment/trap_[type]_[state].png, strips with SpriteFrames
for the animated ones, its "traps" section of assets/animations/environment.json, and
art/out/environment/traps@6x.png. The static states also go into the tile atlas
(env_tiles imports TRAP_TILES).
"""

from __future__ import annotations

import pixel
from environment import _shared as sh
from environment._shared import T, tile_of
from environment.env_tiles import FLOOR_STONE_A, WALL_STONE_INTACT

# =================================================================================
# Pressure plate: a stone plate set into the flags
# =================================================================================

PLATE_UP = [
    "................",
    "................",
    "..KKKKKKKKKKKK..",
    "..KWLLLLLLLLGK..",
    "..KLGGGGGGGGDK..",
    "..KLGDDDDDDGDK..",
    "..KLGDGGGGLGDK..",
    "..KLGDGGGGLGDK..",
    "..KLGDGGGGLGDK..",
    "..KLGDGGGGLGDK..",
    "..KLGGLLLLLGDK..",
    "..KLGGGGGGGGDK..",
    "..KGDDDDDDDDDK..",
    "..KDDDDDDDDDDK..",
    "..KKKKKKKKKKKK..",
    "................",
]
# Pressed: sunk flush, its rim now in shadow along the top and left
PLATE_DOWN = [
    "................",
    "................",
    "..KKKKKKKKKKKK..",
    "..KKKKKKKKKKKK..",
    "..KKDDDDDDDDGK..",
    "..KKGGGGGGGGGK..",
    "..KDGDDDDDDGGK..",
    "..KDGDGGGGLGGK..",
    "..KDGDGGGGLGGK..",
    "..KDGDGGGGLGGK..",
    "..KDGDGGGGLGGK..",
    "..KDGGLLLLLGGK..",
    "..KDGGGGGGGGGK..",
    "..KDGGGGGGGGLK..",
    "..KKKKKKKKKKKK..",
    "................",
]
TRAP_PRESSURE_PLATE_UP = tile_of(sh.lay(FLOOR_STONE_A, PLATE_UP), "trap_pressure_plate_up")
TRAP_PRESSURE_PLATE_DOWN = tile_of(sh.lay(FLOOR_STONE_A, PLATE_DOWN), "trap_pressure_plate_down")

# =================================================================================
# Spike wall: an iron plate in the face with three holes; spikes thrust out toward
# the viewer, so in 3/4 they point down the screen over the floor
# =================================================================================

SPIKE_PLATE = [
    "................",
    "................",
    "................",
    "................",
    ".KKKKKKKKKKKKKK.",
    ".KLGGGLGGGLGGDK.",
    ".KDKKKDKKKDKKKK.",
    ".KDKKKDKKKDKKKK.",
    ".KDDDDDDDDDDDDK.",
    ".KKKKKKKKKKKKKK.",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]
SPIKE_PLATE = [row[:T] for row in SPIKE_PLATE]
# One steel spike, a cone pointing down the screen (toward the viewer)
SPIKE_LONG = sh.outlined(["LWG", "LWD", "LGD", ".W.", ".L.", ".D."])
SPIKE_SHORT = sh.outlined(["LWD", ".W."])
HOLES = [3, 7, 11]  # each hole's left column


def _spikes(spike: list[str]) -> list[str]:
    out = pixel.blank(T, T)
    for left in HOLES:
        out = sh.over(out, spike, 5, left - 1)
    return out


SPIKE_TIPS = _spikes(SPIKE_SHORT)
SPIKES_OUT = _spikes(SPIKE_LONG)
_SPIKE_BASE = sh.lay(WALL_STONE_INTACT, SPIKE_PLATE)
TRAP_SPIKE_WALL_RETRACTED = tile_of(_SPIKE_BASE, "trap_spike_wall_retracted")
TRAP_SPIKE_WALL_EXTENDING = tile_of(sh.lay(_SPIKE_BASE, SPIKE_TIPS), "trap_spike_wall_extending")
TRAP_SPIKE_WALL_EXTENDED = tile_of(sh.lay(_SPIKE_BASE, SPIKES_OUT), "trap_spike_wall_extended")

# =================================================================================
# Arrow trap: a slot in an iron-framed block; the arrow flies out toward the viewer
# =================================================================================

ARROW_SLOT = [
    "................",
    "................",
    "................",
    "................",
    "....DGGGGGGD....",
    "....GLLLLLLD....",
    "....GDKKKKGD....",
    "....GDKKKKGD....",
    "....GLDDDDGD....",
    "....DDDDDDDD....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]
ARROW_HEAD_OUT = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".......T........",
    ".......T........",
    "......LWK.......",
    "......KLK.......",
    ".......K........",
    "................",
    "................",
    "................",
    "................",
    "................",
]
DUST_PUFF = [
    "................",
    "................",
    "................",
    "...:L.......L:.",
    "..:L:.:..:.:L:..",
    ".:.L........:L..",
    "..::........::..",
    "...:........:...",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]
DUST_PUFF = [row.ljust(T, ".")[:T] for row in DUST_PUFF]
DUST_FADE = pixel.dissolve(DUST_PUFF, 0.5)

_ARROW_BASE = sh.lay(WALL_STONE_INTACT, ARROW_SLOT)
TRAP_ARROW_IDLE = tile_of(_ARROW_BASE, "trap_arrow_idle")
TRAP_ARROW_FIRING = tile_of(sh.lay(sh.lay(_ARROW_BASE, ARROW_HEAD_OUT), DUST_PUFF), "trap_arrow_firing")
ARROW_FIRING_FRAMES = [
    TRAP_ARROW_IDLE,
    tile_of(sh.lay(_ARROW_BASE, ARROW_HEAD_OUT), "trap_arrow_firing 1"),
    TRAP_ARROW_FIRING,
    tile_of(sh.lay(_ARROW_BASE, DUST_FADE), "trap_arrow_firing 3"),
]

# The arrow, pointing right; rotate the node for other directions
ARROW_BODY = [
    "RW.........L..",
    ".RTTTTTTTTTLLW",
    "RW.........D..",
]
TRAP_ARROW_PROJECTILE = sh.on_canvas(sh.outlined(ARROW_BODY), T, T, lift=5)

# Tiles for the atlas: (name, frame, solid)
TRAP_TILES: list[tuple[str, list[str], bool]] = [
    ("trap_pressure_plate_up", TRAP_PRESSURE_PLATE_UP, False),
    ("trap_pressure_plate_down", TRAP_PRESSURE_PLATE_DOWN, False),
    ("trap_spike_wall_retracted", TRAP_SPIKE_WALL_RETRACTED, True),
    ("trap_spike_wall_extending", TRAP_SPIKE_WALL_EXTENDING, True),
    ("trap_spike_wall_extended", TRAP_SPIKE_WALL_EXTENDED, True),
    ("trap_arrow_idle", TRAP_ARROW_IDLE, True),
    ("trap_arrow_firing", TRAP_ARROW_FIRING, True),
]

SPIKE_FRAMES = [TRAP_SPIKE_WALL_RETRACTED, TRAP_SPIKE_WALL_EXTENDING, TRAP_SPIKE_WALL_EXTENDED,
                TRAP_SPIKE_WALL_EXTENDED]


def build() -> None:
    entries: dict[str, dict] = {}
    for name, frame, _ in TRAP_TILES:
        if name == "trap_arrow_firing":
            continue  # written as a strip below
        entries[name] = sh.write_static(name, frame, "also in the tile atlas")
    entries["trap_spike_wall_extend"] = sh.write_anim(
        "trap_spike_wall_extend", SPIKE_FRAMES, 6, loop=False,
        notes="retracted, extending, extended, extended; play once, then hold or swap the tile")
    entries["trap_spike_wall_retract"] = sh.write_anim(
        "trap_spike_wall_retract", SPIKE_FRAMES[::-1], 6, loop=False, notes="extend played backwards")
    entries["trap_arrow_firing"] = sh.write_anim(
        "trap_arrow_firing", ARROW_FIRING_FRAMES, 6, loop=False,
        notes="idle, arrowhead out, loosed with dust, dust settles; frame 2 is the atlas tile")
    entries["trap_arrow_projectile"] = sh.write_static(
        "trap_arrow_projectile", TRAP_ARROW_PROJECTILE, "points right; rotate the node to aim it")
    entries["trap_arrow_projectile"]["origin"] = [8, 8]
    sh.merge_env_json("traps", entries)
    look = sh.sheet([TRAP_PRESSURE_PLATE_UP, TRAP_PRESSURE_PLATE_DOWN] + SPIKE_FRAMES[:3]
                    + ARROW_FIRING_FRAMES + [TRAP_ARROW_PROJECTILE], 5, 4)
    print(sh.preview("traps", look, 8))
