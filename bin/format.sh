#!/usr/bin/env bash
# bin/format.sh: formats every .gd file in place with gdformat.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
git ls-files -co --exclude-standard -z -- '*.gd' | xargs -0 tools/.venv/bin/gdformat
