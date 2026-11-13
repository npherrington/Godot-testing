#!/usr/bin/env bash
# bin/setup.sh: installs the pinned tools (godot-mcp-runtime, gdtoolkit) and imports the project.
# Safe to rerun. Needs Godot 4.7+ (brew install --cask godot), Node 20+ and Python 3.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

mkdir -p runs && touch runs/.gdignore
(cd tools && npm ci --no-audit --no-fund --loglevel=error)
[[ -x tools/.venv/bin/python ]] || python3 -m venv tools/.venv
tools/.venv/bin/pip install --quiet --disable-pip-version-check -r tools/requirements.txt
bin/godot --headless --path . --import >/dev/null 2>&1 || true
echo "setup done. Gate: bin/check.sh"
