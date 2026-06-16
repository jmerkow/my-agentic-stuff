#!/usr/bin/env bash
# Install agentic stuff into the right Copilot directories.
#
# Currently handles:
#   skills/<name>/SKILL.md  →  ~/.copilot/skills/<name>           (copy)
#
# Usage:
#   ./install.sh                # install everything in every category
#   ./install.sh skills         # install all skills only
#   ./install.sh skills/build-deck   # install one skill by path
#   ./install.sh <name>...      # install named skills (looked up under skills/)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_TARGET="${COPILOT_SKILLS_DIR:-$HOME/.copilot/skills}"

# Map: category dir → install target dir
declare -A CATEGORY_TARGETS=(
  ["skills"]="$SKILLS_TARGET"
)

# Map: category dir → manifest filename used to detect a valid item
declare -A CATEGORY_MARKERS=(
  ["skills"]="SKILL.md"
)

install_item() {
  local category="$1"
  local name="$2"
  local src="$REPO_DIR/$category/$name"
  local target_dir="${CATEGORY_TARGETS[$category]}"
  local marker="${CATEGORY_MARKERS[$category]}"
  local dst="$target_dir/$name"

  if [[ ! -d "$src" ]]; then
    echo "  SKIP $category/$name (no such dir)" >&2
    return
  fi
  if [[ ! -f "$src/$marker" ]]; then
    echo "  SKIP $category/$name (no $marker)" >&2
    return
  fi

  mkdir -p "$target_dir"

  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ -L "$dst" ]]; then
      rm "$dst"
    elif [[ -d "$dst" ]]; then
      rm -rf "$dst"
    else
      echo "  ERROR $dst exists and is not a symlink or directory. Move or delete it manually." >&2
      exit 1
    fi
  fi

  cp -r "$src" "$dst"
  echo "  installed $category/$name → $dst (copy)"
}

install_category() {
  local category="$1"
  local src_dir="$REPO_DIR/$category"
  local marker="${CATEGORY_MARKERS[$category]:-}"

  if [[ -z "$marker" || ! -d "$src_dir" ]]; then
    return
  fi
  mapfile -t names < <(find "$src_dir" -mindepth 2 -maxdepth 2 -name "$marker" -printf '%h\n' | xargs -n1 basename | sort)
  for name in "${names[@]}"; do
    install_item "$category" "$name"
  done
}

# Parse args
if [[ $# -eq 0 ]]; then
  for category in "${!CATEGORY_TARGETS[@]}"; do
    install_category "$category"
  done
else
  for arg in "$@"; do
    if [[ "$arg" == */* ]]; then
      category="${arg%%/*}"
      name="${arg#*/}"
      install_item "$category" "$name"
    elif [[ -n "${CATEGORY_TARGETS[$arg]:-}" ]]; then
      install_category "$arg"
    else
      found=0
      for category in "${!CATEGORY_TARGETS[@]}"; do
        if [[ -f "$REPO_DIR/$category/$arg/${CATEGORY_MARKERS[$category]}" ]]; then
          install_item "$category" "$arg"
          found=1
          break
        fi
      done
      if [[ $found -eq 0 ]]; then
        echo "  ERROR no item named '$arg' in any category" >&2
        exit 1
      fi
    fi
  done
fi
