---
name: wiki-query
description: 'Answer questions from a knowledge wiki. Read the index first, cite every claim by source id inline, and apply the conflict-resolution order when sources disagree. Use when answering questions against an existing wiki built with wiki-ingest.'
---

# Wiki Query

The wiki is the answer source. Do not answer from memory of the subject.

**Layout**

| File | What it gives you |
|---|---|
| `wiki/index.md` | Map of every page. **Read this first, always.** |
| `wiki/_meta/registry.md` | Source id → title, kind, version, URL |
| `wiki/_meta/coverage.md` | What is *missing* from the corpus |
| `wiki/_meta/changelog.md` | What changed between versions (use if present) |

**Procedure**

1. **Index first.** Read `wiki/index.md`, then open only the pages it points to. Do not grep the whole wiki before consulting the index — that is what the index is for.
2. **Answer from pages, not from memory.** Carry each claim's inline source id into your answer, exactly as the page writes it: `` `[source-id]` ``.
3. **State gaps.** If the pages do not cover it, say so, then check `wiki/_meta/coverage.md` — the gap may already be known and documented. Never fill a gap from general knowledge without labelling it as outside the corpus.

**If qmd is available** (`qmd` CLI, `tobi/qmd`): use `qmd query <wiki-root> "<question>"` to find pages instead of grepping `index.md`. Fall back to grep if qmd is not installed. The wiki layout is plain markdown either way.

**When sources conflict**

Resolve in this order, and say which rule you applied:

1. Newer version/date wins — if `_meta/changelog.md` exists, confirm the topic actually changed before treating it as a real conflict. A newer source covering an unchanged area is not a conflict; both are current.
2. `demonstrated > stated > hedged > opinion`.
3. More specific beats more general.

If two same-version sources of equal weight disagree, **present both and say it is unresolved.** A fabricated resolution is indistinguishable from a real one to whoever reads it next.

**Answer format**

- Lead with the answer, then the support.
- Inline `` `[source-id]` `` on every factual claim.
- Note explicitly when a claim is **corroborated by multiple independent sources** — that is a confidence signal, and dropping it wastes the corpus.

**Never**

- Never cite a source id that is not in `wiki/_meta/registry.md`.
- Never present a superseded claim as current, or delete it — it is retained deliberately so the wiki can explain why an older guide disagrees.
- Never silently correct a term marked `(sic?)`. A plausible correction is indistinguishable from a real one.
- Never let absence of a page mean absence of evidence. Check `wiki/_meta/coverage.md`.

**Worth filing back**

If the answer required real synthesis — a comparison, a decision table, a connection between pages — it is worth saving as a new wiki page. Otherwise it dies in chat history and the next session re-derives it from scratch.
