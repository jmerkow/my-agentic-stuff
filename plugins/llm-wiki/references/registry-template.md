# Source Registry

`wiki/_meta/registry.md`. One row per source, keyed by stable ID.

Claims reference sources by `id` only.

## Template

```markdown
---
id: registry
type: meta
updated: YYYY-MM-DD
sources_total: 0
ingested: 0
cited_only: 0
---

# Source Registry

| ID | Title | Author | Kind | Version | Published | Accessed | URL | Note | Density |
|---|---|---|---|---|---|---|---|---|---|
| `source-abc123` | Some Guide | Author Name | article | 2025-06 | 2025-06-20 | 2026-01-15 | <url> | [note](../sources/source-abc123.md) | high |
| `source-def456` | A Reference Page | community | wiki | — | — | 2026-01-15 | <url> | — | not ingested |
```

## Columns

| Column | Notes |
|---|---|
| `ID` | Intrinsic and stable — DOI, ticket number, URL hash, video ID. Never a sequence index. |
| `Kind` | `video` / `wiki` / `forum` / `doc` / `changelog` / `article` |
| `Version` | Version or date the source **describes**, not when it was published. |
| `Accessed` | Required for anything that mutates — wikis, forums, live docs. |
| `Note` | Link to the source page in `wiki/sources/`, or `—` if never ingested. |
| `Density` | `high` / `medium` / `low` — how much usable content survived digestion. |

## Rules

- **Every cited source gets a row**, including ones never ingested. `Note: —` plus `Density: not ingested` is the honest record, and it is what keeps a bibliography from implying coverage that does not exist.
- **`Version` is what the source describes.** A document published after a release but written before it describes the *older* version. Getting this wrong corrupts conflict resolution.
- Sources that failed acquisition still get a row, with the reason in `Density` (`paywalled`, `dead link`, `access denied`).
- Keep the counts in frontmatter accurate — `ingested` vs `cited_only` is the corpus boundary in two numbers.
