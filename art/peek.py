#!/usr/bin/env python3
"""Blow up part of a sheet to look at it.

    python3 art/peek.py assets/sprites/enemies/char_ghost_normal.png --rows 8-11 --scale 6
    python3 art/peek.py <sheet.png> --cell 32x48 --rows 0,4,8 --out /tmp/look.png

Reads a PNG this pipeline wrote, keeps the given cell rows (0-based; a range or a
comma list) and writes them scaled on the preview background, with a faint grid, to
--out (default art/out/peek.png). Then open that file to look.
"""

import argparse
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pixel  # noqa: E402


def read_png(path: Path) -> list[list[tuple[int, int, int, int]]]:
    """RGBA rows of an 8-bit RGBA PNG (what pixel.write_png writes)."""
    data = path.read_bytes()
    pos, idat, w, h = 8, b"", 0, 0
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos : pos + 8])
        body = data[pos + 8 : pos + 8 + length]
        if kind == b"IHDR":
            w, h, depth, colour = struct.unpack(">IIBB", body[:10])
            assert (depth, colour) == (8, 6), "only 8-bit RGBA PNGs"
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = w * 4
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1 : (y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - 4] if i >= 4 else 0
            b = prev[i]
            c = prev[i - 4] if i >= 4 else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append([tuple(line[i : i + 4]) for i in range(0, stride, 4)])
        prev = line
    return rows


def parse_rows(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += range(int(a), int(b) + 1)
        elif part:
            out.append(int(part))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("png", type=Path)
    p.add_argument("--cell", default="32x48", help="cell WxH (default 32x48)")
    p.add_argument("--rows", default="", help="cell rows to keep, e.g. 8-11 or 0,4,8 (default all)")
    p.add_argument("--scale", type=int, default=6)
    p.add_argument("--out", type=Path, default=pixel.OUT / "peek.png")
    a = p.parse_args()
    cw, ch = (int(n) for n in a.cell.lower().split("x"))
    img = read_png(a.png)
    keep = parse_rows(a.rows) or list(range(len(img) // ch))
    bg, line = pixel.PREVIEW_BG, (64, 60, 76)
    out = []
    for r in keep:
        for y in range(r * ch, (r + 1) * ch):
            row = []
            for x, px in enumerate(img[y]):
                under = line if (x % cw == 0 or y % ch == 0) else bg
                al = px[3] / 255
                rgb = tuple(round(px[i] * al + under[i] * (1 - al)) for i in range(3))
                row += [(*rgb, 255)] * a.scale
            out += [row] * a.scale
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(pixel._png_bytes(out))
    print(a.out)


if __name__ == "__main__":
    main()
