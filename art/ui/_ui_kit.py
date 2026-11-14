"""Shared helpers for the UI modules (ui_hud, ui_menus, ui_font, ui_mock).

Not a module build.py runs: the leading underscore keeps it out. It holds the output
paths, a ui.json merge (each module owns one section of it), 9-slice expansion, a
wrap-around paste for tileable textures, and an RGB canvas that blends the translucent
letters properly, for the mock screens.
"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import pixel

Sprite = pixel.Sprite

UI = pixel.ASSETS / "sprites" / "ui"
FONTS = pixel.ASSETS / "fonts"
OUT = pixel.OUT / "ui"
UI_JSON = pixel.ASSETS / "animations" / "ui.json"
UI_FPS = 12  # the spec's frame rate for animated UI


def res(path: Path) -> str:
    return "res://" + path.relative_to(pixel.ROOT).as_posix()


def save(name: str, sprite: Sprite, preview_scale: int = 4) -> str:
    """assets/sprites/ui/<name>.png and a preview on the dungeon-dark background in
    art/out/ui/. Returns the res:// path."""
    pixel.check(sprite, name)
    path = UI / f"{name}.png"
    pixel.write_png(path, sprite)
    pixel.write_png(OUT / "parts" / f"{name}@{preview_scale}x.png", sprite, preview_scale, pixel.PREVIEW_BG)
    return res(path)


def strip_out(name: str, frames: list[Sprite], loop: bool, fps: int = UI_FPS) -> dict:
    """An animated UI piece: assets/sprites/ui/<name>.png + .tres via pixel.write_strip."""
    return pixel.write_strip(UI / name, frames, fps, loop, preview_dir=OUT / "parts")


def merge_json(section: str, data: object) -> None:
    """Writes data under section in assets/animations/ui.json, keeping the other sections."""
    doc = json.loads(UI_JSON.read_text()) if UI_JSON.exists() else {}
    doc[section] = data
    UI_JSON.parent.mkdir(parents=True, exist_ok=True)
    UI_JSON.write_text(json.dumps(doc, indent=2) + "\n")


# ---------------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------------


def fill(w: int, h: int, letter: str) -> Sprite:
    return [letter * w] * h


def rows(*parts: str) -> Sprite:
    """A sprite from rows given as separate strings (for short inline matrices)."""
    return list(parts)


def wrap_paste(base: Sprite, sprite: Sprite, top: int, left: int) -> Sprite:
    """paste, but what leaves one edge comes back on the opposite one: for tiles."""
    grid = [list(row) for row in base]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(sprite):
        for c, ch in enumerate(row):
            if ch != ".":
                grid[(top + r) % h][(left + c) % w] = ch
    return ["".join(row) for row in grid]


def tile(sprite: Sprite, w: int, h: int, ox: int = 0, oy: int = 0) -> Sprite:
    sw, sh = pixel.size(sprite)
    return ["".join(sprite[(y + oy) % sh][(x + ox) % sw] for x in range(w)) for y in range(h)]


def nine(src: Sprite, left: int, top: int, right: int, bottom: int, w: int, h: int) -> Sprite:
    """src drawn at w x h as a 9-slice: corners kept, edges and centre tiled. With a flat
    centre this is what Godot's NinePatchRect / StyleBoxTexture draw (nearest filter)."""
    sw, sh = pixel.size(src)
    cw, ch = sw - left - right, sh - top - bottom

    def col(x: int) -> int:
        if x < left:
            return x
        if x >= w - right:
            return sw - (w - x)
        return left + (x - left) % cw

    def row(y: int) -> int:
        if y < top:
            return y
        if y >= h - bottom:
            return sh - (h - y)
        return top + (y - top) % ch

    return ["".join(src[row(y)][col(x)] for x in range(w)) for y in range(h)]


def assert_nine(src: Sprite, left: int, top: int, right: int, bottom: int, name: str) -> None:
    """Checks src stretches cleanly as a 9-slice: each edge strip is the same along its
    length and the centre is one flat letter."""
    w, h = pixel.size(src)
    cols, rows = range(left, w - right), range(top, h - bottom)
    for y in list(range(top)) + list(range(h - bottom, h)):
        assert len({src[y][x] for x in cols}) == 1, f"{name}: top/bottom edge row {y} varies"
    for x in list(range(left)) + list(range(w - right, w)):
        assert len({src[y][x] for y in rows}) == 1, f"{name}: left/right edge column {x} varies"
    assert len({src[y][x] for y in rows for x in cols}) == 1, f"{name}: centre is not flat"


# ---------------------------------------------------------------------------------
# RGB canvas for mock screens (blends the translucent letters)
# ---------------------------------------------------------------------------------


def _blend(px: pixel.Rgba, bg: pixel.Rgb) -> pixel.Rgb:
    a = px[3] / 255
    return (round(px[0] * a + bg[0] * (1 - a)), round(px[1] * a + bg[1] * (1 - a)), round(px[2] * a + bg[2] * (1 - a)))


class Canvas:
    def __init__(self, w: int, h: int, rgb: pixel.Rgb = pixel.PREVIEW_BG):
        self.w, self.h = w, h
        self.px = [[rgb] * w for _ in range(h)]

    def draw(self, sprite: Sprite, x: int, y: int) -> None:
        """sprite with its top-left corner at (x, y)."""
        for r, row in enumerate(sprite):
            yy = y + r
            if not 0 <= yy < self.h:
                continue
            line = self.px[yy]
            for c, ch in enumerate(row):
                xx = x + c
                if ch == "." or not 0 <= xx < self.w:
                    continue
                line[xx] = _blend(pixel.PALETTE[ch], line[xx])

    def tile(self, sprite: Sprite) -> None:
        sw, sh = pixel.size(sprite)
        for y in range(0, self.h, sh):
            for x in range(0, self.w, sw):
                self.draw(sprite, x, y)

    def shade(self, x: int, y: int, w: int, h: int, letter: str = "_") -> None:
        self.draw(fill(w, h, letter), x, y)

    def write(self, path: Path, scale: int = 1, crop: tuple[int, int, int, int] | None = None) -> None:
        """PNG at scale; crop is (x, y, w, h) in canvas pixels."""
        x0, y0, cw, ch = crop or (0, 0, self.w, self.h)
        raw = bytearray()
        for row in self.px[y0 : y0 + ch]:
            line = b"".join(bytes(rgb) * scale for rgb in row[x0 : x0 + cw])
            raw += (b"\x00" + line) * scale

        def chunk(kind: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

        header = struct.pack(">IIBBBBB", cw * scale, ch * scale, 8, 2, 0, 0, 0)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")
        )
