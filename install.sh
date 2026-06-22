#!/usr/bin/env bash
# DEPRECATED: this repo is now a Copilot plugin marketplace. Prefer installing
# plugins (see README.md). This rsync installer is kept for direct skill mirroring
# but is no longer the supported path and may be removed. Docs: INSTALL-RSYNC.md
#
# Install agentic stuff into the right Copilot directories.
#
# Currently handles:
#   skills/<name>/SKILL.md  →  ~/.copilot/skills/<name>           (rsync mirror)
#
# Usage:
#   ./install.sh                              # preview everything in every category
#   ./install.sh --apply                      # install everything in every category
#   ./install.sh --update                     # preview updates to already-installed items only
#   ./install.sh --apply --update             # update already-installed items, skip new ones
#   ./install.sh --host my-host               # preview everything on a remote host
#   ./install.sh skills                       # preview all skills only
#   ./install.sh --apply skills               # install all skills only
#   ./install.sh --host my-host skills/build-deck
#                                            # preview one skill by path on a remote host
#   ./install.sh <name>...                    # preview named skills (looked up under skills/)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLY_MODE=0
UPDATE_MODE=0
HOST=""

# Parse args
declare -a selectors=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      APPLY_MODE=1
      shift
      ;;
    --update)
      UPDATE_MODE=1
      shift
      ;;
    --host)
      if [[ $# -lt 2 ]]; then
        echo "  ERROR --host requires a host argument" >&2
        exit 1
      fi
      HOST="$2"
      shift 2
      ;;
    *)
      selectors+=("$1")
      shift
      ;;
  esac
done

if ! command -v rsync >/dev/null 2>&1; then
  echo "  ERROR rsync is required but was not found in PATH." >&2
  exit 1
fi

if [[ -n "$HOST" && -z "${COPILOT_SKILLS_DIR:-}" ]]; then
  SKILLS_TARGET='~/.copilot/skills'
else
  SKILLS_TARGET="${COPILOT_SKILLS_DIR:-$HOME/.copilot/skills}"
fi

# Map: category dir → install target dir
declare -A CATEGORY_TARGETS=(
  ["skills"]="$SKILLS_TARGET"
)

# Map: category dir → manifest filename used to detect a valid item
declare -A CATEGORY_MARKERS=(
  ["skills"]="SKILL.md"
)

# Files/dirs never worth mirroring into an install target.
declare -a RSYNC_EXCLUDES=(
  --exclude='__pycache__/'
  --exclude='*.pyc'
  --exclude='.gitignore'
  --exclude='.DS_Store'
)

collect_rsync_output() {
  local rsync_output=""
  local rsync_status=0

  set +e
  rsync_output="$(rsync "$@" 2>&1)"
  rsync_status=$?
  set -e

  printf '%s' "$rsync_output"
  return "$rsync_status"
}

# Translate rsync -i itemized output (read from stdin) into readable change
# lines: "+ path" (new), "~ path" (updated), "- path" (deleted). Directory-only
# and timestamp-noise entries are dropped. Emits nothing when there are no
# meaningful changes.
format_rsync_changes() {
  local line flags ftype attrs path
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    case "$line" in
      'created directory '*) continue ;;   # rsync's mkdir notice, not a change
      '*deleting '*)
        path="${line#'*deleting'}"
        path="${path#"${path%%[![:space:]]*}"}"   # trim leading whitespace
        path="${path%/}"
        [[ -z "$path" ]] && continue
        printf '    - %s\n' "$path"
        continue
        ;;
    esac
    flags="${line%% *}"
    path="${line#* }"
    ftype="${flags:1:1}"
    [[ "$ftype" == "d" ]] && continue   # skip directory entries (files inside cover it)
    attrs="${flags:2}"
    if [[ "$attrs" == "+++++++++" ]]; then
      printf '    + %s\n' "$path"
    else
      printf '    ~ %s\n' "$path"
    fi
  done
}

# Decide whether an item is a brand-new install (target does not exist yet).
# Local: a cheap filesystem check. Remote: fall back to an rsync dry-run and
# treat "nothing but additions" as new. Returns 0 (true) when new.
item_is_new() {
  local src="$1" dst="$2" rsync_dst="$3"
  if [[ -z "$HOST" ]]; then
    [[ ! -e "$dst" && ! -L "$dst" ]]
    return
  fi
  local out changes
  out="$(collect_rsync_output -ain --delete "${RSYNC_EXCLUDES[@]}" "$src/" "$rsync_dst/")"
  changes="$(printf '%s\n' "$out" | format_rsync_changes)"
  [[ -n "$changes" ]] && ! printf '%s\n' "$changes" | grep -qv '^    + '
}

install_item() {
  local category="$1"
  local name="$2"
  local src="$REPO_DIR/$category/$name"
  local target_dir="${CATEGORY_TARGETS[$category]}"
  local marker="${CATEGORY_MARKERS[$category]}"
  local dst="$target_dir/$name"
  local rsync_dst="$dst"
  local preview_output=""

  if [[ ! -d "$src" ]]; then
    echo "  SKIP $category/$name (no such dir)" >&2
    return
  fi
  if [[ ! -f "$src/$marker" ]]; then
    echo "  SKIP $category/$name (no $marker)" >&2
    return
  fi

  if [[ -n "$HOST" ]]; then
    rsync_dst="$HOST:$dst"
  elif [[ -e "$dst" && ! -d "$dst" && ! -L "$dst" ]]; then
    echo "  ERROR $dst exists and is not a symlink or directory. Move or delete it manually." >&2
    exit 1
  fi

  if [[ $APPLY_MODE -eq 0 ]]; then
    if preview_output="$(collect_rsync_output -ain --delete "${RSYNC_EXCLUDES[@]}" "$src/" "$rsync_dst/")"; then
      local is_new=0
      if [[ -z "$HOST" && ! -e "$dst" && ! -L "$dst" ]]; then
        is_new=1
      fi

      local changes
      changes="$(printf '%s\n' "$preview_output" | format_rsync_changes)"

      # A remote target with nothing but additions is also a fresh install.
      if [[ $is_new -eq 0 && -n "$changes" ]] && ! printf '%s\n' "$changes" | grep -qv '^    + '; then
        is_new=1
      fi

      if [[ $is_new -eq 1 ]]; then
        if [[ $UPDATE_MODE -eq 1 ]]; then
          SKIPPED_NEW+=("$category/$name")
          return
        fi
        NEW_ITEMS+=("$category/$name → $rsync_dst")
        return
      fi

      if [[ -z "$changes" ]]; then
        UNCHANGED_ITEMS+=("$category/$name")
        return
      fi

      UPDATE_NAMES+=("$category/$name → $rsync_dst")
      UPDATE_BLOCKS+=("$changes")
      return
    fi

    echo "  ERROR rsync preview failed for $category/$name → $rsync_dst" >&2
    if [[ -n "$preview_output" ]]; then
      printf '%s\n' "$preview_output" >&2
    fi
    exit 1
  fi

  if [[ $UPDATE_MODE -eq 1 ]] && item_is_new "$src" "$dst" "$rsync_dst"; then
    echo "  skipped $category/$name (not installed; --update only touches existing)"
    return
  fi

  if [[ -z "$HOST" && ! -e "$dst" && ! -L "$dst" ]]; then
    mkdir -p "$dst"
  fi

  if ! rsync -a --delete "${RSYNC_EXCLUDES[@]}" "$src/" "$rsync_dst/"; then
    echo "  ERROR rsync apply failed for $category/$name → $rsync_dst" >&2
    exit 1
  fi

  echo "  installed $category/$name → $rsync_dst (rsync)"
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

if [[ $APPLY_MODE -eq 0 ]]; then
  echo "Preview only (nothing written).  + add   ~ update   - delete"
  echo "Run with --apply to sync."
  echo
fi

declare -a NEW_ITEMS=()
declare -a UPDATE_NAMES=()
declare -a UPDATE_BLOCKS=()
declare -a UNCHANGED_ITEMS=()
declare -a SKIPPED_NEW=()

if [[ ${#selectors[@]} -eq 0 ]]; then
  for category in "${!CATEGORY_TARGETS[@]}"; do
    install_category "$category"
  done
else
  for arg in "${selectors[@]}"; do
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

# Grouped preview summary (apply mode prints inline above and skips this).
if [[ $APPLY_MODE -eq 0 ]]; then
  if [[ ${#NEW_ITEMS[@]} -gt 0 ]]; then
    echo "New installs:"
    for item in "${NEW_ITEMS[@]}"; do
      echo "  $item"
    done
    echo
  fi

  if [[ ${#UPDATE_NAMES[@]} -gt 0 ]]; then
    echo "Updates:"
    for i in "${!UPDATE_NAMES[@]}"; do
      echo "  ${UPDATE_NAMES[$i]}"
      printf '%s\n' "${UPDATE_BLOCKS[$i]}"
    done
    echo
  fi

  if [[ ${#UNCHANGED_ITEMS[@]} -gt 0 ]]; then
    echo "Unchanged: ${#UNCHANGED_ITEMS[@]} (${UNCHANGED_ITEMS[*]})"
  fi

  if [[ ${#SKIPPED_NEW[@]} -gt 0 ]]; then
    echo "Skipped (not installed, --update): ${#SKIPPED_NEW[@]} (${SKIPPED_NEW[*]})"
  fi

  if [[ ${#NEW_ITEMS[@]} -eq 0 && ${#UPDATE_NAMES[@]} -eq 0 && ${#SKIPPED_NEW[@]} -eq 0 ]]; then
    echo "Nothing to install. Everything is up to date."
  fi
fi
