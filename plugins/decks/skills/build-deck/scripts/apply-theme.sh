#!/usr/bin/env bash
# Apply a named theme to one SVG file with THEME-START / THEME-END markers.
#
# Usage:
#   ./apply-theme.sh <theme> <svg-file>     # apply theme to one slide
#   ./apply-theme.sh --list                 # show available themes
#
# Examples:
#   ./apply-theme.sh dark-classic slide-05-perturbation.svg
#   ./apply-theme.sh light-classic slide-01-title.svg
#
# Convention in each .svg's inline <style>:
#   /* THEME-START */
#   ...replaceable theme rules (replaced by contents of themes/<name>.css)...
#   /* THEME-END */
#
# Theme files: themes/<name>.css contains ONLY the rules (no markers).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEMES_DIR="$DIR/../themes"

if [[ "${1:-}" == "--list" ]]; then
  echo "Available themes:"
  for f in "$THEMES_DIR"/*.css; do
    [[ -f "$f" ]] && echo "  - $(basename "$f" .css)"
  done
  exit 0
fi

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <theme> <svg-file>" >&2
  echo "       $0 --list" >&2
  exit 1
fi

THEME_NAME="$1"
SVG="$2"
THEME_FILE="$THEMES_DIR/${THEME_NAME}.css"

if [[ ! -f "$THEME_FILE" ]]; then
  echo "ERROR: theme file not found: $THEME_FILE" >&2
  echo "Run with --list to see available themes." >&2
  exit 1
fi

if [[ ! -f "$SVG" ]]; then
  echo "ERROR: svg file not found: $SVG" >&2
  exit 1
fi

if ! grep -q "THEME-START" "$SVG"; then
  echo "ERROR: $SVG has no THEME-START marker" >&2
  exit 1
fi

awk -v theme_file="$THEME_FILE" '
  BEGIN { while ((getline line < theme_file) > 0) block = block (block ? "\n" : "") line }
  /\/\* THEME-START \*\// { print; print block; in_block=1; next }
  /\/\* THEME-END \*\// { in_block=0; print; next }
  !in_block { print }
' "$SVG" > "$SVG.new" && mv "$SVG.new" "$SVG"

echo "Applied theme '$THEME_NAME' to $SVG"
