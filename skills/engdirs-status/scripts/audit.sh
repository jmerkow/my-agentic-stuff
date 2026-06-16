#!/usr/bin/env bash
# Audit .eng/ git repos under given roots (default: ~/Code; override via args).
# Read-only. Usage: audit.sh [root ...]
set -u

ROOTS=("$@")
[[ ${#ROOTS[@]} -eq 0 ]] && ROOTS=("$HOME/Code")

echo "| Repo | Branch | Behind | Ahead | Dirty | Notes | Path |"
echo "|---|---|--:|--:|--:|---|---|"

# -P = don't follow symlinks (avoids mirror-tree duplicates)
find -P "${ROOTS[@]}" -maxdepth 3 -type d -name .eng 2>/dev/null | sort -u | while read -r eng; do
  [[ -e "$eng/.git" ]] || continue
  cd "$eng" || continue

  repo=$(basename "$(dirname "$eng")")
  branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "(detached)")

  ab=$(git rev-list --left-right --count '@{u}...HEAD' 2>/dev/null)
  if [[ -n "$ab" ]]; then
    behind=$(echo "$ab" | awk '{print $1}')
    ahead=$(echo "$ab" | awk '{print $2}')
    notes=""
  else
    behind="—"
    ahead="—"
    notes="no upstream"
  fi

  dirty=$(git status --porcelain 2>/dev/null | wc -l)

  echo "| $repo | \`$branch\` | $behind | $ahead | $dirty | $notes | $eng |"
done
