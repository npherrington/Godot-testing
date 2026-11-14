#!/usr/bin/env python3
"""Build the game's art into assets/.

    python3 art/build.py                     every module
    python3 art/build.py player slime        just these (a module's file name, no .py)
    python3 art/build.py --gifs slime        also write GIF previews (slower)
    python3 art/build.py --list              the modules

A module is any .py file in art/ (other than pixel.py and build.py) or in art/enemies/,
art/environment/ or art/ui/ with a build() function. Previews go to art/out/
(gitignored). Audio has its own build: art/audio/build_audio.py.
"""

import argparse
import importlib
import sys
import time
from pathlib import Path

ART = Path(__file__).resolve().parent
sys.path.insert(0, str(ART))

import pixel  # noqa: E402

FOLDERS = ["", "enemies", "environment", "ui"]
SKIP = {"pixel", "build", "peek"}


def modules() -> dict[str, str]:
    """name -> import path."""
    found = {}
    for folder in FOLDERS:
        for path in sorted((ART / folder).glob("*.py")):
            if path.stem in SKIP or path.stem.startswith("_"):
                continue
            found[path.stem] = f"{folder}.{path.stem}" if folder else path.stem
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("only", nargs="*", help="module names to build; all when none")
    parser.add_argument("--gifs", action="store_true", help="also write GIF previews")
    parser.add_argument("--list", action="store_true", help="list the modules")
    args = parser.parse_args()
    found = modules()
    if args.list:
        print("\n".join(f"{k}  ({v})" for k, v in found.items()))
        return
    unknown = set(args.only) - found.keys()
    if unknown:
        sys.exit(f"no such module: {', '.join(sorted(unknown))}. Try --list")
    pixel.GIFS = args.gifs
    names = args.only or list(found)
    if not args.only:
        pixel.write_palette()
    for name in names:
        start = time.time()
        module = importlib.import_module(found[name])
        if not hasattr(module, "build"):
            continue
        module.build()
        print(f"  built {name} in {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
