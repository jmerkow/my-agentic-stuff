# Wiki Conventions

Rules that make the output readable by a model retrieving one page with no neighbors.

## Every page is self-contained

The single most important rule. A page will be retrieved **alone**, with no siblings, no parent, and no reading order.

- No "as mentioned above", "see previous section", "continuing from".
- Restate the subject in the first sentence.
- Define domain jargon on first use **on that page**, even if defined elsewhere too. Redundancy across pages is correct here; it is retrieval insurance, not a DRY violation.

## One concept per page

Split when a page covers two things someone would query separately. Merge when a page is a stub that never gets retrieved on its own. Target a few hundred to ~1,500 words.

## New page vs. edit in place

- **New page** — a distinct entity or concept that other pages would link *to*.
- **Edit in place** — an attribute, refinement, correction, or new example of something that already has a page.

Search the index by ID **and** by synonym before creating anything. The same concept arriving under a second title is the main source of near-duplicate pages, and nothing downstream catches it automatically. When torn, edit — an unretrieved stub is worse than a slightly long page.

## Stable IDs, links by ID

Titles drift; IDs do not. Cross-reference `[[topic-id]]`, never "the configuration page above". Retired IDs stay retired — never recycled for new content.

## Frontmatter on everything

```yaml
---
id: configuration
title: Configuration Guide
type: topic            # topic | source | meta
updated: 2026-01-15
sources: [source-abc123, source-def456]
claims: 12
has_conflicts: false
---
```

Frontmatter is what lets a retrieval layer filter by version, source, or confidence without parsing prose.

## Inline citation

Every claim carries its source ID at the point of assertion:

```markdown
The default retry limit is 3 and resets after a successful request. `[source-abc123]`
```

Not footnotes, not end-of-page bibliographies. A retrieved fragment must carry its own provenance, because the fragment may be all the model ever sees.

## Superseded material

Keep it, subordinate it. Never delete — deletion destroys the audit trail and invites re-adding the stale claim from the original source later.

```markdown
> **Superseded (v2):** The connection timeout defaulted to 10 seconds.
> Changed in v3 — raised to 30 seconds with per-request override. `[source-ghi789]`
```

## Uncertainty is stated, not implied

Hedged and opinion claims are marked as such in the text. A model reading the page must be able to tell a measured fact from someone's preference without consulting a schema.

## Corpus boundary in `index.md`

State plainly: what was ingested, what was cited but not ingested, the version/date skew, and which topics are thin. A wiki that hides its gaps produces confident answers about things it never read.

## `log.md` entry format

Append-only, chronological, one entry per operation. The prefix is fixed so the log stays greppable without a parser — `grep '^## \[' log.md | tail -5` gives the last five operations.

```markdown
## [2026-01-15] ingest | source-abc123 | Configuration Guide
Pages: configuration, setup, troubleshooting, index
Claims: +8 (2 corroborate existing)
Conflicts: 0
```

Operation is one of `ingest`, `query`, `lint`. `index.md` answers *what is in the wiki*; `log.md` answers *what happened to it and when*. Do not merge them.
