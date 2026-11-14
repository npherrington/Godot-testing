"""Environment effects: fire, smoke, fog, blood splatters, and the torch light texture.

    python3 art/build.py env_effects

Writes assets/sprites/environment/fx_*.png (strips with SpriteFrames for the animated
ones), light_torch.png, the "effects" section of assets/animations/environment.json, and
art/out/environment/effects@4x.png.
"""

from __future__ import annotations

import math

import pixel
from environment import _shared as sh
from environment._shared import noise
from environment.env_props import BIG_FLAMES, glow

# =================================================================================
# Fire: a ground fire on charred sticks, six flickers
# =================================================================================

EMBERS = [
    "..bKOb.bKb....",
    ".bbORbbObbKb..",
    "KbbbKbRbbbbbK.",
]


def fire_frames() -> list[list[str]]:
    shapes = BIG_FLAMES + [pixel.flip(BIG_FLAMES[1]), pixel.flip(BIG_FLAMES[2])]
    sparks = [[(2, 4)], [(0, 11), (3, 2)], [(1, 6)], [(0, 3), (2, 12)], [(1, 10)], [(3, 5), (0, 9)]]
    base = sh.on_canvas(sh.outlined(EMBERS), 16, 24, 14)
    frames = []
    for n, flame in enumerate(shapes):
        f = pixel.paste(base, glow(flame), 7, 2)
        f = pixel.paste(f, flame, 8, 3)
        f = pixel.paste(f, sh.outlined(EMBERS)[2:], 19, 0)  # sticks in front of the flame's foot
        f = pixel.paint(f, sparks[n], "*")
        frames.append(pixel.check(f))
    return frames


# =================================================================================
# Smoke: translucent puffs rising and spreading, a seamless loop
# =================================================================================


def smoke_frames(count: int = 6, w: int = 16, h: int = 32) -> list[list[str]]:
    """Puffs 12 pixels apart, each rising 2 a frame: after 6 frames every puff stands
    where the one above it started, so the loop has no seam. A puff grows and thins
    as it rises."""
    step, gap = 2, 12
    frames = []
    for n in range(count):
        f = pixel.blank(w, h)
        for k in range(-1, 4):
            y = h - 4 - (k * gap + step * n)  # the puff's bottom row
            rise = (h - 4 - y) / (h - 4)  # 0 at the source, 1 at the top
            if not -0.2 <= rise <= 1.05:
                continue
            pw, ph = 6 + round(6 * max(rise, 0)), 5 + round(4 * max(rise, 0))
            puff = pixel.ellipse(pw, ph, "~")
            puff = pixel.outline(pixel.pad(puff, 1, 1, 1, 1), ":")
            puff = pixel.dissolve(puff, min(0.75, max(0.0, rise * 0.85 - 0.15)))
            sway = round(2 * math.sin(y / 5))
            f = pixel.paste(f, puff, y - len(puff), (w - len(puff[0])) // 2 + sway)
        frames.append(pixel.check(f))
    return frames


# =================================================================================
# Fog: a tileable patch of mist, and a thinner one to layer over it
# =================================================================================


def fog_tile(seed: int, size: int = 64, density: float = 0.5) -> list[str]:
    """Mist (":") whose dot density follows wrapping noise: thick in the middle of a
    bank, thinning through the Bayer pattern to clear air between banks."""
    broad, fine = noise(seed, size, size, cells=size // 16), noise(seed + 7, size, size, cells=size // 8)
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            v = 0.6 * broad[y][x] + 0.4 * fine[y][x] + (pixel.BAYER[y % 4][x % 4] - 7.5) / 16 * 0.7
            row.append(":" if v > 1 - density else ".")
        rows.append("".join(row))
    return rows


# =================================================================================
# Blood: flat decals on the floor, no outline
# =================================================================================

BLOOD = {
    "fx_blood_a": [  # a pool
        "................",
        "................",
        "................",
        "......r.........",
        "....rrrrr.......",
        "...rrRRrrrr..r..",
        "..rrRFRRrrrr....",
        "..rRRRRRRrrrr...",
        ".rrRRRRRRRrrr...",
        "..rrRRRRRrrr..r.",
        "...rrrRRrrrr....",
        ".r..rrrrrrr.....",
        "......rrr.......",
        "................",
        "................",
        "................",
    ],
    "fx_blood_b": [  # a splash thrown to the right
        "................",
        "................",
        "...........r....",
        "..rr.....r......",
        ".rRrr..r....r...",
        ".rRRrrr..rr.....",
        "..rrRRrrrrRr..r.",
        "...rrrRRRrrr....",
        "....rrrrrr..r...",
        ".....r..rr....r.",
        "..........r.....",
        "....r...........",
        "................",
        "................",
        "................",
        "................",
    ],
    "fx_blood_c": [  # drips and drops
        "................",
        "................",
        "....r...........",
        "...rRr......r...",
        "....r....r......",
        "...........rr...",
        "..r.......rRr...",
        "......rr...r....",
        ".....rRr........",
        "......r.....r...",
        "..r.............",
        ".........r......",
        "........rRr.....",
        ".........r......",
        "................",
        "................",
    ],
    "fx_blood_d": [  # a smear dragged across the floor
        "................",
        "................",
        "................",
        "................",
        ".r.r..r.........",
        "rrrrrrrrr.r.....",
        "rRRrRrrrrrrr.r..",
        "rRRRRRrRrrrrrr..",
        "rrRRrRRrrrrr.r.r",
        ".rrrrrrrr.r.....",
        "...r..r.........",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
}

# =================================================================================
# Torch light: a mask for PointLight2D, outside the palette
# =================================================================================

LIGHT_SIZE = 128
# (outer radius as a fraction of the half-size, alpha) from the centre out
LIGHT_BANDS = [(0.22, 255), (0.40, 205), (0.56, 155), (0.70, 110), (0.82, 70), (0.92, 36), (1.0, 14)]


def light_rows(size: int = LIGHT_SIZE) -> list[list[tuple[int, int, int, int]]]:
    """White with stepped alpha: flat rings that fall off toward the edge, each ring's
    edge dithered with the Bayer pattern (about 2 pixels wide) so the steps read as
    pixel art rather than a smooth gradient. Fully transparent at the corners."""
    half = size / 2
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            r = math.hypot(x + 0.5 - half, y + 0.5 - half) / half
            r += (pixel.BAYER[y % 4][x % 4] - 7.5) / 16 * (4 / half)
            alpha = 0
            for edge, a in LIGHT_BANDS:
                if r < edge:
                    alpha = a
                    break
            row.append((255, 255, 255, alpha))
        rows.append(row)
    return rows


def write_light() -> dict:
    path = sh.SPRITES / "light_torch.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = light_rows()
    path.write_bytes(pixel._png_bytes(rows))
    # A preview on the dungeon dark, as the light would add to it
    bg = pixel.PREVIEW_BG
    look = [[(*(round(bg[i] + (255 - bg[i]) * a / 255) for i in range(3)), 255) for (_, _, _, a) in row]
            for row in rows]
    big = [[px for px in row for _ in range(3)] for row in look for _ in range(3)]
    (sh.OUT / "light_torch@3x.png").write_bytes(pixel._png_bytes(big))
    return {"png": sh.res(path), "size": [LIGHT_SIZE, LIGHT_SIZE],
            "notes": "PointLight2D texture: white, stepped alpha falloff with dithered band edges. "
                     "Not palette art. texture_scale 1.5 gives about a 6-tile radius."}


def build() -> None:
    entries: dict[str, dict] = {}
    fire = fire_frames()
    smoke = smoke_frames()
    entries["fx_fire_loop"] = sh.write_anim("fx_fire_loop", fire, 6, True,
                                            "a ground fire; pair with a PointLight2D")
    entries["fx_smoke_loop"] = sh.write_anim("fx_smoke_loop", smoke, 5, True,
                                             "translucent; set the bottom on the source (torch, brazier, fire)")
    fog_a, fog_b = fog_tile(71, density=0.55), fog_tile(75, density=0.35)
    entries["fx_fog_a"] = sh.write_static("fx_fog_a", fog_a,
                                          "tileable 64x64 mist; repeat it (texture_repeat) and scroll slowly")
    entries["fx_fog_b"] = sh.write_static("fx_fog_b", fog_b, "a thinner tileable layer to scroll over fx_fog_a")
    for name, art in BLOOD.items():
        entries[name] = sh.write_static(name, pixel.check(art, name), "floor decal, no outline")
    entries["light_torch"] = write_light()
    sh.merge_env_json("effects", entries)

    fog_look = sh.repeat(fog_a, 2, 2)
    print(sh.preview("effects", pixel.stack([
        sh.sheet(fire + smoke, 6, 4), sh.sheet(list(BLOOD.values()), 4, 4),
        pixel.strip([sh.repeat(fog_a, 2, 2), sh.repeat(fog_b, 2, 2)], 8)], 6), 3))
