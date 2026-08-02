---
name: wiki-init
description: 'Scaffold a new knowledge wiki at a given path — create the directory tree and seed the index, log, registry, and conventions file. Use when starting a wiki from scratch; not for adding sources to an existing one (use wiki-ingest for that).'
argument-hint: 'Target directory for the new wiki'
---

# Wiki Init

Creates the standard wiki layout at `<wiki-root>/`:

```
<wiki-root>/
  raw/                      # original sources, never modified after acquisition
  wiki/
    index.md                # entry point — page map, corpus boundary, citation format
    log.md                  # append-only operations log
    topics/                 # one .md page per topic
    sources/                # one provenance .md page per source
    _meta/
      registry.md           # source metadata keyed by stable ID
      conventions.md        # project-specific decisions co-evolved with the corpus
```

## Steps

1. **Create dirs** — `raw/`, `wiki/topics/`, `wiki/sources/`, `wiki/_meta/`.

2. **Seed `wiki/index.md`** — YAML frontmatter (`id: index`, `type: meta`, `updated: <today>`). Body: corpus boundary statement (what this wiki covers and what it does not), an empty pages table, and the citation format note (`` `[source-id]` `` inline on every factual claim).

3. **Seed `wiki/log.md`** — YAML frontmatter (`id: log`, `type: meta`). Body: one bootstrap entry dated today with operation `init`.

4. **Seed `wiki/_meta/registry.md`** from the template at [registry-template.md](../../references/registry-template.md). Set `sources_total: 0`, `ingested: 0`, `cited_only: 0`. Empty table body.

5. **Seed `wiki/_meta/conventions.md`** — freeform doc for domain-specific decisions: preferred source ID format, any custom frontmatter fields, source kinds in use. Keeps corpus conventions in the repo rather than in chat history.

That is all. Do not create taxonomy, claims ledger, or any other file.

After scaffolding, use `wiki-ingest` to add the first source.

## Growth

1. Ingesting pre-cleaned local markdown or text (no extraction step needed).
2. Documentation trees: copy the whole tree into `raw/`, or reference in place? Tradeoff: reproducibility vs. repo bloat.
3. Mining codebases as sources.
4. Other source classes: email, work documents, internal systems, HTML artifacts.
5. **qmd as retrieval backend** (`tobi/qmd`, BM25+vector+rerank over markdown). The layout above is plain markdown — a qmd index can be built at any time with `qmd update`, which is read-only and never modifies the corpus. When qmd is available, `wiki-query` uses it for page discovery instead of grepping the index.
