"""A mock room built from the environment tiles and props: a preview only.

    python3 art/build.py env_room

Writes art/out/environment/mock_room@3x.png (as drawn) and mock_room_lit@3x.png (dark
ambient plus the torch light texture at every torch and the brazier), using the wall
layout in NOTES.md: a 20 x 12 floor, the back wall two faces tall (the lower face in
the wall's cell, the upper face in the cell above), caps for the side and front walls
and the rock around.
"""

from __future__ import annotations

import random

import pixel
from environment import _shared as sh
from environment import env_effects as fx
from environment import env_props as props
from environment import env_tiles as tiles
from environment import env_traps as traps
from environment._shared import T

W, H = 22, 16  # tiles: 20 x 12 floor inside one-tile walls, with rock rows above
FLOOR_TOP, FLOOR_BOTTOM = 3, 14  # floor rows
BACK = 2  # the back wall's row (lower faces); row 1 holds the upper faces

Rgb = tuple[int, int, int]


class Canvas:
    """RGB pixels with real alpha blending, so translucent letters (shadows, glow)
    darken or tint what is under them as they will in the game."""

    def __init__(self, w: int, h: int) -> None:
        self.w, self.h = w, h
        self.px: list[list[Rgb]] = [[pixel.PREVIEW_BG] * w for _ in range(h)]

    def draw(self, sprite: list[str], top: int, left: int) -> None:
        for r, row in enumerate(sprite):
            y = top + r
            if not 0 <= y < self.h:
                continue
            for c, ch in enumerate(row):
                x = left + c
                rgba = pixel.PALETTE[ch]
                if rgba is None or not 0 <= x < self.w:
                    continue
                self.px[y][x] = pixel._blend(rgba, self.px[y][x])

    def tile(self, sprite: list[str], row: int, col: int) -> None:
        self.draw(sprite, row * T, col * T)

    def stand(self, sprite: list[str], row: int, col: int, cols: int = 1) -> None:
        """A prop whose canvas bottom sits on the bottom of floor cell (row, col),
        centred across cols cells."""
        w, h = pixel.size(sprite)
        self.draw(sprite, (row + 1) * T - h, col * T + (cols * T - w) // 2)

    def write(self, name: str, scale: int, pixels: list[list[Rgb]] | None = None) -> None:
        rows = pixels or self.px
        big = [[(*p, 255) for p in row for _ in range(scale)] for row in rows for _ in range(scale)]
        path = sh.OUT / f"{name}@{scale}x.png"
        path.write_bytes(pixel._png_bytes(big))
        print(path)


def layout() -> tuple[Canvas, list[tuple[int, int]]]:
    rng = random.Random(5)
    c = Canvas(W * T, H * T)
    stone = [tiles.FLOOR_STONE_A, tiles.FLOOR_STONE_B, tiles.FLOOR_STONE_C]
    # Floor: stone flags mixed at random, moss creeping in near the ruined wall
    for r in range(FLOOR_TOP, FLOOR_BOTTOM + 1):
        for col in range(1, W - 1):
            t = rng.choices(stone, weights=[11, 6, 3])[0]
            if col >= 12 and r <= 5 and rng.random() < 0.6:
                t = rng.choice([tiles.FLOOR_MOSS_A, tiles.FLOOR_MOSS_B])
            c.tile(t, r, col)
    c.tile(tiles.STAIRS_DOWN, 13, 18)
    c.tile(tiles.STAIRS_UP, 13, 2)
    c.tile(traps.TRAP_PRESSURE_PLATE_UP, 8, 4)
    # Shadows cast by the back and left walls (light from the top left)
    for col in range(2, W - 1):
        c.tile(tiles.SHADOW_N, FLOOR_TOP, col)
    for r in range(FLOOR_TOP + 1, FLOOR_BOTTOM + 1):
        c.tile(tiles.SHADOW_W, r, 1)
    c.tile(tiles.SHADOW_NW, FLOOR_TOP, 1)
    # Rock and the side and front walls: caps
    for r in range(H):
        for col in range(W):
            if r < BACK or r > FLOOR_BOTTOM or col in (0, W - 1) or (r == BACK and col in (0, W - 1)):
                c.tile(tiles.WALL_STONE_CAP, r, col)
    # The back wall: lower faces on row 2, upper faces on row 1
    lower = {4: traps.TRAP_ARROW_IDLE, 7: tiles.WALL_STONE_CRACKED, 14: tiles.WALL_STONE_RUINED,
             17: tiles.SECRET_CLOSED, 19: tiles.WALL_STONE_CRACKED}
    upper = {11: tiles.WALL_STONE_CRACKED}
    for col in range(1, W - 1):
        c.tile(upper.get(col, tiles.WALL_STONE_INTACT), BACK - 1, col)
        c.tile(lower.get(col, tiles.WALL_STONE_INTACT), BACK, col)
    c.draw(tiles.DOOR_WOOD_CLOSED, (BACK - 1) * T, 10 * T)
    # On the wall: torches, banners, chains, cobwebs
    torch = props.torch_frames()[0]
    lights = []
    for col in (3, 8, 12, 18):
        c.tile(torch, BACK - 1, col)
        lights.append(((BACK - 1) * T + 4, col * T + 8))
    statics = {k: v for k, (v, _) in props.statics().items()}
    c.draw(statics["decor_banner_red"], (BACK - 1) * T, 6 * T)
    c.draw(statics["decor_banner_purple"], (BACK - 1) * T, 16 * T)
    c.draw(statics["decor_chains_hanging"], (BACK - 1) * T, 13 * T)
    c.draw(statics["decor_cobweb_left"], (BACK - 1) * T, 1 * T)
    c.draw(statics["decor_cobweb_right"], (BACK - 1) * T, 20 * T)
    # Floor props, back to front
    chest = props.chest_frames()
    brazier = props.brazier_frames()[0]
    placed = [
        (3, 1, statics["decor_bookshelf_a"], 2),
        (3, 14, statics["decor_rubble_a"], 1),
        (3, 19, statics["decor_weapon_rack"], 2),
        (4, 15, statics["decor_mushrooms_a"], 1),
        (5, 20, statics["decor_bed_cot"], 1),
        (6, 4, statics["decor_pillar_stone"], 1),
        (6, 17, statics["decor_pillar_broken"], 1),
        (7, 6, statics["decor_chair_wood"], 1),
        (7, 7, statics["decor_table_wood"], 2),
        (7, 9, statics["decor_chair_wood"], 1),
        (8, 10, brazier, 1),
        (8, 14, chest["closed"], 2),
        (9, 2, statics["decor_barrel_a"], 1),
        (9, 1, statics["decor_crate_a"], 1),
        (10, 1, statics["decor_sack_a"], 1),
        (10, 13, statics["decor_bones_a"], 1),
        (10, 18, statics["decor_coffin_a"], 1),
        (11, 4, statics["decor_pillar_stone"], 1),
        (11, 17, statics["decor_pillar_stone"], 1),
        (11, 8, statics["decor_skull_a"], 1),
        (12, 11, statics["decor_skull_pile"], 2),
        (12, 15, chest["trapped"], 2),
        (13, 5, statics["decor_urn_a"], 1),
        (14, 8, statics["decor_rubble_b"], 1),
        (14, 13, statics["decor_bones_b"], 1),
    ]
    c.tile(fx.BLOOD["fx_blood_a"], 10, 12)
    c.tile(fx.BLOOD["fx_blood_c"], 11, 13)
    for row, col, sprite, cols in sorted(placed, key=lambda p: p[0]):
        c.stand(sprite, row, col, cols)
    lights.append((8 * T + 6, 10 * T + 8))
    return c, lights


def lit(c: Canvas, lights: list[tuple[int, int]], ambient: float = 0.28) -> list[list[Rgb]]:
    """The room in the dark: each pixel scaled by ambient plus the torch texture's alpha
    at every light (warm-tinted), as Godot's CanvasModulate and additive PointLight2D
    would roughly do."""
    mask = fx.light_rows()
    half = len(mask) // 2
    scale = 1.5  # PointLight2D texture_scale
    warm = (1.0, 0.82, 0.55)
    out = []
    for y, row in enumerate(c.px):
        line = []
        for x, (r, g, b) in enumerate(row):
            light = [ambient] * 3
            for ly, lx in lights:
                mx, my = int((x - lx) / scale) + half, int((y - ly) / scale) + half
                if 0 <= mx < len(mask) and 0 <= my < len(mask):
                    a = mask[my][mx][3] / 255
                    light = [light[i] + a * warm[i] for i in range(3)]
            line.append(tuple(min(255, round(v * min(light[i], 1.6))) for i, v in enumerate((r, g, b))))
        out.append(line)
    return out


def build() -> None:
    c, lights = layout()
    c.write("mock_room", 3)
    c.write("mock_room_lit", 3, lit(c, lights))
