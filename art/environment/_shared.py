"""Helpers for the environment modules (env_tiles, env_traps, env_props, env_effects,
env_room): wrap-around shifts for tiles, prop placement with a drop shadow, preview
sheets, the merged assets/animations/environment.json, and the tile atlas with its
Godot TileSet. No drawings live here."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

import pixel

T = 16  # tile size
SPRITES = pixel.ASSETS / "sprites" / "environment"
TILESETS = pixel.ASSETS / "tilesets"
ENV_JSON = pixel.ASSETS / "animations" / "environment.json"
OUT = pixel.OUT / "environment"
ENV_FPS = (4, 6)  # the spec's frame-rate range for environment animation

Sprite = pixel.Sprite


def res(path: Path) -> str:
    return "res://" + path.relative_to(pixel.ROOT).as_posix()


def dumps(doc: dict) -> str:
    """JSON, indented, with short number lists ([column, row], [w, h]) on one line."""
    import re

    text = json.dumps(doc, indent=2)
    return re.sub(r"\[\s+(-?[\d.]+),\s+(-?[\d.]+)\s+\]", r"[\1, \2]", text) + "\n"


# ---------------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------------


def roll(s: Sprite, dx: int, dy: int) -> Sprite:
    """s moved dx right and dy down, wrapping round: a tile stays seamless."""
    w, h = pixel.size(s)
    return ["".join(s[(y - dy) % h][(x - dx) % w] for x in range(w)) for y in range(h)]


def repeat(s: Sprite, nx: int, ny: int) -> Sprite:
    return [row * nx for row in s] * ny


def over(base: Sprite, top: Sprite, y: int = 0, x: int = 0) -> Sprite:
    """top pasted on base at (y, x); "." in top leaves base showing."""
    return pixel.paste(base, top, y, x)


def lay(base: Sprite, layer: Sprite) -> Sprite:
    """A same-size layer pasted over base."""
    return pixel.paste(base, layer, 0, 0)


def stamp(base: Sprite, sprite: Sprite, top: int, left: int) -> Sprite:
    """sprite pasted on base with wrap-around: what leaves one edge comes in at the
    opposite one, so a tile built this way repeats without a seam."""
    grid = [list(row) for row in base]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(sprite):
        for c, ch in enumerate(row):
            if ch != ".":
                grid[(top + r) % h][(left + c) % w] = ch
    return ["".join(row) for row in grid]


def bevel(sprite: Sprite, light: str, dark: str, body: str | None = None) -> Sprite:
    """A flat shape shaded as a lump lit from the top left: pixels with nothing above or
    to the left become light, pixels with nothing below or to the right become dark."""
    w, h = pixel.size(sprite)
    out = [list(r) for r in sprite]

    def empty(y: int, x: int) -> bool:
        return not (0 <= y < h and 0 <= x < w) or sprite[y][x] == "."

    for y in range(h):
        for x in range(w):
            if sprite[y][x] == "." or (body and sprite[y][x] != body):
                continue
            if empty(y + 1, x) or empty(y, x + 1):
                out[y][x] = dark
            elif empty(y - 1, x) or empty(y, x - 1):
                out[y][x] = light
    return ["".join(r) for r in out]


def noise(seed: int, w: int = T, h: int = T, cells: int = 4) -> list[list[float]]:
    """Smooth value noise in 0..1 that wraps round at w and h, so anything drawn from
    it tiles. cells is the number of lattice points across: fewer, bigger blobs."""
    import random

    rng = random.Random(seed)
    cy = max(1, round(cells * h / w))
    lat = [[rng.random() for _ in range(cells)] for _ in range(cy)]
    sx_, sy_ = w / cells, h / cy

    def smooth(t: float) -> float:
        return t * t * (3 - 2 * t)

    out = []
    for y in range(h):
        gy = y / sy_
        y0 = int(gy) % cy
        y1 = (y0 + 1) % cy
        fy = smooth(gy - int(gy))
        row = []
        for x in range(w):
            gx = x / sx_
            x0 = int(gx) % cells
            x1 = (x0 + 1) % cells
            fx = smooth(gx - int(gx))
            a = lat[y0][x0] * (1 - fx) + lat[y0][x1] * fx
            b = lat[y1][x0] * (1 - fx) + lat[y1][x1] * fx
            row.append(a * (1 - fy) + b * fy)
        out.append(row)
    return out


def bands(field: list[list[float]], ramp: list[tuple[float, str]], spread: float = 0.08) -> Sprite:
    """field turned to letters: ramp is [(threshold, letter), ...] from low to high,
    each letter used from its threshold up. Near a threshold the Bayer pattern decides,
    so bands meet in a dithered edge rather than a hard contour."""
    rows = []
    for y, line in enumerate(field):
        row = []
        for x, v in enumerate(line):
            v += (pixel.BAYER[y % 4][x % 4] - 7.5) / 16 * spread
            letter = ramp[0][1]
            for t, ch in ramp:
                if v >= t:
                    letter = ch
            row.append(letter)
        rows.append("".join(row))
    return rows


def tile_of(rows: list[str], name: str) -> Sprite:
    pixel.check(rows, name)
    assert pixel.size(rows) == (T, T), f"{name}: {pixel.size(rows)}, want 16x16"
    return rows


def outlined(body: Sprite, diagonal: bool = False) -> Sprite:
    """body padded by one pixel all round and given its K outline."""
    return pixel.outline(pixel.pad(body, 1, 1, 1, 1), "K", diagonal)


def on_canvas(sprite: Sprite, w: int, h: int, shadow: int = 0, dx: int = 0, lift: int = 1,
              shadow_h: int = 4) -> Sprite:
    """sprite on a w x h canvas, centred (moved dx right), its last row on row
    h - 1 - lift, with a translucent ellipse shadow `shadow` wide under its base."""
    sw, sh = pixel.size(sprite)
    assert sw <= w and sh + lift <= h, f"a {sw}x{sh} sprite does not fit a {w}x{h} canvas"
    left = (w - sw) // 2 + dx
    top = h - lift - sh
    out = pixel.paste(pixel.blank(w, h), sprite, top, left)
    if shadow:
        ell = pixel.ellipse(shadow, shadow_h, "_")
        out = pixel.underlay(out, ell, h - shadow_h, (w - shadow) // 2 + dx)
    return pixel.check(out)


# ---------------------------------------------------------------------------------
# Previews
# ---------------------------------------------------------------------------------


def sheet(sprites: list[Sprite], columns: int, gap: int = 4) -> Sprite:
    """Sprites of any size laid out in a grid of columns, each bottom-aligned in its
    cell, cells as big as the biggest sprite, with gap pixels between."""
    cw = max(pixel.size(s)[0] for s in sprites)
    ch = max(pixel.size(s)[1] for s in sprites)
    rows = []
    for i in range(0, len(sprites), columns):
        chunk = sprites[i : i + columns]
        cells = [pixel.paste(pixel.blank(cw, ch), s, ch - len(s), (cw - len(s[0])) // 2) for s in chunk]
        cells += [pixel.blank(cw, ch)] * (columns - len(cells))
        rows.append(pixel.strip(cells, gap))
    return pixel.stack(rows, gap)


def preview(name: str, sprite: Sprite, scale: int = 4, background=pixel.PREVIEW_BG) -> Path:
    path = OUT / f"{name}@{scale}x.png"
    pixel.write_png(path, sprite, scale, background)
    return path


# ---------------------------------------------------------------------------------
# environment.json: one file, one section per module
# ---------------------------------------------------------------------------------


def merge_env_json(section: str, entries: dict) -> None:
    """Replace one section of assets/animations/environment.json, keeping the others,
    so each module can be built on its own."""
    doc = {}
    if ENV_JSON.exists():
        try:
            doc = json.loads(ENV_JSON.read_text())
        except json.JSONDecodeError:
            doc = {}
    doc.setdefault("about", "Environment sprites and tiles: see art/environment/NOTES.md")
    doc[section] = entries
    ENV_JSON.parent.mkdir(parents=True, exist_ok=True)
    ENV_JSON.write_text(dumps(doc))


def static_entry(path: Path, sprite: Sprite, notes: str = "") -> dict:
    w, h = pixel.size(sprite)
    entry = {"png": res(path), "size": [w, h], "origin": [w // 2, h]}
    if notes:
        entry["notes"] = notes
    return entry


def write_static(name: str, sprite: Sprite, notes: str = "") -> dict:
    pixel.check(sprite, name)
    path = SPRITES / f"{name}.png"
    pixel.write_png(path, sprite)
    return static_entry(path, sprite, notes)


def write_anim(name: str, frames: list[Sprite], fps: int, loop: bool = True, notes: str = "") -> dict:
    assert ENV_FPS[0] <= fps <= ENV_FPS[1], f"{name}: environment animations run at 4-6 fps"
    entry = pixel.write_strip(SPRITES / name, frames, fps, loop, preview_dir=OUT / "strips")
    w, h = pixel.size(frames[0])
    entry["origin"] = [w // 2, h]
    if notes:
        entry["notes"] = notes
    return entry


# ---------------------------------------------------------------------------------
# Tile atlas and Godot TileSet
# ---------------------------------------------------------------------------------


class Tile(NamedTuple):
    name: str  # file stem: tile_floor_stone_a, trap_pressure_plate_up
    frames: list[Sprite]  # one 16x16 frame, or several for an animated tile
    solid: bool = False  # full-tile collision polygon on physics layer 0
    fps: int = 0  # animated tiles only
    group: str = ""  # floor, wall_face, wall_cap, door, stairs, secret, trap, overlay


class Atlas:
    """Tiles packed row by row on a 16-pixel grid, columns wide. An animated tile's
    frames sit side by side from its own cell, as Godot's TileSetAtlasSource expects."""

    def __init__(self, columns: int) -> None:
        self.columns = columns
        self.tiles: list[tuple[Tile, int, int]] = []
        self.col = 0
        self.row = 0

    def add(self, tile: Tile) -> None:
        for n, f in enumerate(tile.frames):
            pixel.check(f, f"{tile.name} {n}")
            assert pixel.size(f) == (T, T), f"{tile.name} {n}: {pixel.size(f)}, want 16x16"
        span = len(tile.frames)
        assert span <= self.columns, tile.name
        if self.col + span > self.columns:
            self.newline()
        self.tiles.append((tile, self.col, self.row))
        self.col += span

    def newline(self) -> None:
        if self.col:
            self.row += 1
            self.col = 0

    def image(self) -> Sprite:
        rows = self.row + (1 if self.col else 0)
        out = pixel.blank(self.columns * T, rows * T)
        for tile, c, r in self.tiles:
            for n, f in enumerate(tile.frames):
                out = pixel.paste(out, f, r * T, (c + n) * T)
        return out

    def write(self, stem: Path) -> dict:
        """<stem>.png, <stem>.json and <stem>.tres. Returns the JSON document."""
        png, tres, js = stem.with_suffix(".png"), stem.with_suffix(".tres"), stem.with_suffix(".json")
        pixel.write_png(png, self.image())
        coords = {t.name: [c, r] for t, c, r in self.tiles}
        anims = {t.name: {"frames": len(t.frames), "fps": t.fps} for t, _, _ in self.tiles if len(t.frames) > 1}
        groups: dict[str, list[str]] = {}
        for t, _, _ in self.tiles:
            groups.setdefault(t.group, []).append(t.name)
        doc = {
            "tile_size": [T, T],
            "texture": res(png),
            "tileset": res(tres),
            "source_id": 0,
            "physics_layer": 0,
            "tiles": coords,
            "animated": anims,
            "solid": [t.name for t, _, _ in self.tiles if t.solid],
            "groups": groups,
        }
        js.write_text(dumps(doc))
        tres.write_text(self._tres(res(png)))
        return doc

    def _tres(self, texture: str) -> str:
        h = T // 2
        square = f"PackedVector2Array(-{h}, -{h}, {h}, -{h}, {h}, {h}, -{h}, {h})"
        lines = []
        for tile, c, r in self.tiles:
            key = f"{c}:{r}"
            if len(tile.frames) > 1:
                lines.append(f"{key}/animation_columns = 0")
                lines.append(f"{key}/animation_speed = {float(tile.fps)}")
                lines.append(f"{key}/animation_frames_count = {len(tile.frames)}")
                for n in range(len(tile.frames)):
                    lines.append(f"{key}/animation_frame_{n}/duration = 1.0")
            lines.append(f"{key}/0 = 0")
            if tile.solid:
                lines.append(f"{key}/0/physics_layer_0/polygon_0/points = {square}")
        return (
            '[gd_resource type="TileSet" format=3]\n\n'
            f'[ext_resource type="Texture2D" path="{texture}" id="1_atlas"]\n\n'
            '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_dungeon"]\n'
            "resource_name = \"dungeon\"\n"
            'texture = ExtResource("1_atlas")\n'
            f"texture_region_size = Vector2i({T}, {T})\n"
            + "\n".join(lines)
            + "\n\n[resource]\n"
            f"tile_size = Vector2i({T}, {T})\n"
            "physics_layer_0/collision_layer = 1\n"
            "physics_layer_0/collision_mask = 1\n"
            'sources/0 = SubResource("TileSetAtlasSource_dungeon")\n'
        )
