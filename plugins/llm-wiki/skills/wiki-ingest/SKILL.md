---
name: wiki-ingest
description: 'Add one source to an existing knowledge wiki — register it, read it, extract, place, write, update index and log. Use when adding any source (article, video, doc, transcript, local file) to a wiki that already has an index and registry. Not for building a wiki from scratch (use wiki-init first).'
argument-hint: 'Path or URL of the source to ingest, and the wiki root'
---

# Wiki Ingest

Adds a **single** source to an existing wiki without letting it drift.

```
register ──▶ read ──▶ extract ──▶ place ──▶ write ──▶ sweep ──▶ record
 stable ID   whole    claims      new page  pages +   cross-    index +
 + registry  source   + conf.     or edit?  conflicts  refs      log
```

One source typically touches **5–15 pages**. If an ingest touched only 1–2, the sweep was skipped.

## Step 0 — Preflight

Before writing anything, read:

| File | Why |
|---|---|
| `wiki/_meta/registry.md` | Confirm this source is not already ingested. |
| `wiki/index.md` | What already exists, and the stated corpus boundary. |
| `wiki/_meta/taxonomy.md` | If it exists: the closed topic list. You may not invent topics. |

Re-ingesting under a second ID silently double-counts every claim it corroborates. Check by intrinsic ID, not by title.

If there is no `index.md` or `registry.md`, run `wiki-init` first.

## Step 1 — Register

Assign a stable ID **intrinsic to the source**: DOI, ticket number, URL hash, video ID. Never a sequence number — those shift as the corpus grows.

Append to `wiki/_meta/registry.md`. Record the version or date the source **describes**, not when it was published. That field decides every conflict this source will be part of.

## Step 2 — Read the Whole Source

Read to the end, in large chunks, before extracting anything. A partial read produces a confabulated remainder indistinguishable from a real one in the output.

For sources over ~100KB, read explicitly in large sequential chunks, noting the byte range actually covered.

## Step 3 — Extract

List the claims worth writing. For each, note:

- **Topic** — which topic it belongs to. If taxonomy exists, use only its closed list; unsorted claims go to the `unsorted` slug and are flagged in `wiki/_meta/conventions.md`. If no taxonomy, invent a consistent slug and record it in `conventions.md`.
- **Confidence** — `demonstrated` / `stated` / `hedged` / `opinion`, drawn from how the source presents the claim, not from how plausible it sounds.

This is a working list, not a permanent ledger. Its only job is to guide steps 4–5.

## Step 4 — Place: New Page or Edit?

Per [wiki-conventions.md](../../references/wiki-conventions.md):

- **New page** — a distinct concept that other pages would link *to*.
- **Edit in place** — an attribute, refinement, correction, or example of something with an existing page.

Search the index by ID **and** by synonym first. When torn, edit — a stub never retrieved on its own is worse than a slightly long page.

## Step 5 — Write

- **Source page** — `wiki/sources/<source-id>.md`: what it is, its date/version, what it covers, what it notably does not.
- **Topic pages** — insert each claim with its inline `` `[source-id]` `` citation at the point of assertion. Not a footnote; a retrieved fragment must carry its own provenance.
- **Conflicts** — where the new source disagrees with an existing claim, apply the standing precedence: newer version/date first, then `demonstrated > stated > hedged > opinion`, then more specific beats more general. Demote the loser to a superseded block; **never delete it** — deleting invites re-adding the stale claim from the original source later. Log to `wiki/_meta/conflicts.md`.
- **Frontmatter** — update `updated`, `sources`, `claims`, `has_conflicts` on every page touched. Stale frontmatter breaks retrieval filtering silently.

## Step 6 — Sweep

Walk outward from what was written:

- Links resolve both directions — new page linked from somewhere, not just linking out.
- Existing pages that mention the new concept in prose but do not link it yet.
- Existing claims this source **corroborates** — add its ID to their `sources` list. Corroboration is a confidence signal; dropping it wastes the source.
- Existing claims this source contradicts that were outside the topics you just edited.

Then list the pages touched. If the count is 1–2, find what was missed.

Verify with `../../scripts/check-wiki.sh --wiki wiki/ --strict`: catches unresolvable citations, broken cross-links, pages without frontmatter, and frontmatter drift.

## Step 7 — Record

1. **`wiki/index.md`** — add or update the entry (link, one-line summary). Revise the corpus boundary if this source closed or opened a gap.
2. **`wiki/_meta/coverage.md`** — if the source was partial, paywalled, or garbled, write it down. Absence of a note must never be read as absence of evidence.
3. **`wiki/log.md`** — append one entry:

```markdown
## [YYYY-MM-DD] ingest | source-abc123 | Configuration Guide
Pages: configuration, setup, troubleshooting, index
Claims: +8 (2 corroborate existing)
Conflicts: 0
```

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Pages silently stale after ingests | Cross-references never updated | Step 6, non-optional |
| Two pages for one concept | Created without searching synonyms | Step 4 index check |
| Claim count inflated, false corroboration | Same source ingested twice | Step 0 registry check |
| Taxonomy sprawls one topic per ingest | Vocabulary extended at ingest time | Use `unsorted`; note in `conventions.md` |
