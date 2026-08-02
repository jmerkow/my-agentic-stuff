#!/usr/bin/env bash
# Lint a knowledge wiki: verify citations resolve, cross-links resolve, frontmatter
# agrees with the body, and no page is orphaned.
#
# Catches the failure mode that matters most — a page citing a source id that does
# not exist. An unresolvable citation is worse than no citation: it looks like
# provenance and audits clean by eye.
#
# Usage:
#   check-wiki.sh --wiki wiki/ [--page-dirs topics,guides] [--strict]
#
# --page-dirs  Comma-separated list of subdirectory names under --wiki to scan for
#              pages. Defaults to auto-discovering all subdirs (excluding _meta)
#              that contain .md files.
# --strict     Also fails on orphan pages and frontmatter/body citation drift.

set -uo pipefail

WIKI="" STRICT=0 PAGE_DIRS_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --wiki)      WIKI="$2";      shift 2 ;;
    --strict)    STRICT=1;       shift ;;
    --page-dirs) PAGE_DIRS_ARG="$2"; shift 2 ;;
    -h|--help)   sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -d "$WIKI" ]] || { echo "missing or bad --wiki" >&2; exit 2; }

REGISTRY="$WIKI/_meta/registry.md"
TAXONOMY="$WIKI/_meta/taxonomy.md"
[[ -f "$REGISTRY" ]] || { echo "no registry at $REGISTRY" >&2; exit 2; }

source_ids=$(grep -oE '^\| `[^`]+`' "$REGISTRY" | tr -d '|` ' | sort -u)

# Taxonomy is optional in v1 wikis; cross-link checks are skipped if absent.
topic_ids=""
if [[ -f "$TAXONOMY" ]]; then
  topic_ids=$(grep -oE '^\| `[^`]+`' "$TAXONOMY" | tr -d '|` ' | sort -u)
else
  echo "note: no taxonomy.md — skipping cross-link checks"$'\n'
fi

PAGE_DIRS=()
if [[ -n "$PAGE_DIRS_ARG" ]]; then
  IFS=',' read -ra _dirs <<< "$PAGE_DIRS_ARG"
  for d in "${_dirs[@]}"; do
    [[ -d "$WIKI/$d" ]] && PAGE_DIRS+=("$WIKI/$d")
  done
else
  # Auto-discover: all subdirs of $WIKI (excluding _meta) that contain .md files.
  while IFS= read -r -d '' d; do
    [[ "$(basename "$d")" == "_meta" ]] && continue
    find "$d" -maxdepth 1 -name '*.md' -quit 2>/dev/null && PAGE_DIRS+=("$d")
  done < <(find "$WIKI" -mindepth 1 -maxdepth 1 -type d -print0)
fi
(( ${#PAGE_DIRS[@]} )) || { echo "no page directories found under $WIKI" >&2; exit 2; }

all_pages() { find "${PAGE_DIRS[@]}" -maxdepth 1 -name '*.md' "$@"; }

printf 'registry: %s sources\npages:    %s\n\n' \
  "$(echo "$source_ids" | grep -c . || true)" \
  "$(all_pages | wc -l)"

problems=0
report() {
  local label="$1" list="$2"
  [[ -z "$list" ]] && return 0
  printf '%s\n' "$label"
  sed 's/^/  /' <<<"$list"
  printf '\n'
  problems=$(( problems + $(wc -l <<<"$list") ))
}

# Inline citations look like `[source-id]` — a backticked, bracketed id.
cited_in() { grep -oE '`\[[A-Za-z0-9_-]+\]`' "$1" | tr -d '`[]' | sort -u; }
# A registry id in bare backticks is a citation that lost its brackets. Catch it
# explicitly: the bracketed matcher does not see it, so a page written entirely in
# bare form would lint perfectly clean while carrying no resolvable citations.
bare_cites_in() {
  grep -oE '`[A-Za-z0-9_.-]+`' "$1" | tr -d '`' | sort -u \
    | grep -xF -f <(echo "$source_ids") 2>/dev/null || true
}
# Cross-links look like [[topic-id]].
linked_in() { grep -oE '\[\[[A-Za-z0-9_-]+\]\]' "$1" | tr -d '[]' | sort -u; }

bad_cites="" bad_links="" no_front="" drift="" unbracketed=""

while IFS= read -r -d '' page; do
  name=$(basename "$page" .md)

  head -1 "$page" | grep -qx -- '---' || no_front+="$name"$'\n'

  while read -r id; do
    [[ -z "$id" ]] && continue
    grep -qxF -- "$id" <<<"$source_ids" || bad_cites+="$name -> $id"$'\n'
  done <<<"$(cited_in "$page")"

  if [[ -n "$topic_ids" ]]; then
    while read -r id; do
      [[ -z "$id" ]] && continue
      grep -qxF -- "$id" <<<"$topic_ids" || bad_links+="$name -> [[$id]]"$'\n'
    done <<<"$(linked_in "$page")"
  fi

  bare=$(bare_cites_in "$page")
  [[ -n "$bare" ]] && unbracketed+="$name -> $(tr '\n' ' ' <<<"$bare")"$'\n'

  # Frontmatter `sources:` must match what the body actually cites, in both
  # directions. Declared-but-uncited overstates provenance; cited-but-undeclared
  # breaks any retrieval layer that filters on frontmatter.
  declared=$(awk '/^sources:/{f=1} f{printf "%s ", $0; if (/\]/) exit} /^---$/{if(f)exit}' "$page" \
             | tr ',[]' '\n\n\n' | grep -oE '[A-Za-z0-9_-]{3,}' \
             | grep -vx 'sources' | sort -u)
  actual=$(cited_in "$page")
  if [[ -n "$declared" ]]; then
    only_declared=$(comm -23 <(echo "$declared") <(echo "$actual") | grep -v '^$' || true)
    only_cited=$(comm -13 <(echo "$declared") <(echo "$actual") | grep -v '^$' || true)
    [[ -n "$only_declared" ]] && drift+="$name declares but never cites: $(tr '\n' ' ' <<<"$only_declared")"$'\n'
    [[ -n "$only_cited" ]] && drift+="$name cites but never declares: $(tr '\n' ' ' <<<"$only_cited")"$'\n'
  fi
done < <(all_pages -print0)

report "Citation to a source id not in the registry:" "${bad_cites%$'\n'}"
report "Cross-link to a topic id not in the taxonomy:" "${bad_links%$'\n'}"
report "Page missing YAML frontmatter:" "${no_front%$'\n'}"
report "Source id cited in bare backticks, not as \`[id]\`:" "${unbracketed%$'\n'}"

# Orphans: a page no other page links to. Reachability is how a model navigates.
if [[ -f "$WIKI/index.md" ]]; then
  orphans=""
  all_links=$( { all_pages -exec cat {} + ; cat "$WIKI/index.md"; } 2>/dev/null \
              | grep -oE '\[\[[A-Za-z0-9_-]+\]\]|\(([^)]*/)?[A-Za-z0-9_-]+\.md\)' \
              | sed -E 's/[][()]//g; s#^.*/##; s/\.md$//' \
              | sort -u)
  while IFS= read -r -d '' page; do
    name=$(basename "$page" .md)
    grep -qxF -- "$name" <<<"$all_links" || orphans+="$name"$'\n'
  done < <(all_pages -print0)
  if (( STRICT )); then
    report "Orphan page (nothing links to it):" "${orphans%$'\n'}"
  elif [[ -n "$orphans" ]]; then
    printf 'orphan pages (warning):\n'; sed 's/^/  /' <<<"${orphans%$'\n'}"; printf '\n'
  fi
else
  echo "note: no index.md — skipping orphan check"$'\n'
fi

if (( STRICT )); then
  report "Frontmatter/body citation drift:" "${drift%$'\n'}"
elif [[ -n "$drift" ]]; then
  printf 'frontmatter drift (warning, %s pages)\n\n' "$(wc -l <<<"${drift%$'\n'}")"
fi

if (( problems > 0 )); then
  echo "$problems problem(s)."
  exit 1
fi
echo "wiki clean"
