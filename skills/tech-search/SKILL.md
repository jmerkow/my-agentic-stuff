---
name: tech-search
description: Search internal engineering knowledge for technical and internal-tool questions. Use when asking an engineering-systems question (es chat, eschat, es-chat), searching EngHub or eng.ms (eng hub, enghub, eng-hub), finding a TSG, schema, onboarding guide, or source link, figuring out why an internal tool or MCP path does not work, finding a known setting or solution for an internal system, or running a /tech-search lookup. Also triggers on: stack overflow, stackoverflow for teams, internal Q&A, internal engineering how-to. Covers internal engineering and technical knowledge, tools, and troubleshooting; does NOT cover personal M365 activity such as mail, calendar, Teams messages, or meeting summaries.
---

# Tech Search

Search internal engineering knowledge for technical, tool, and system questions across four sources. Pick the source first, then the tool.

> Tool names below are short (e.g. `es_ask`, `enghub/search`). The real MCP tool names carry prefixes that change over time — don't treat these as literal.

## Which source, when

| Source | Reach for it when | What to know |
|--------|-------------------|--------------|
| **ES Chat** (`es/*`) | You need to orient, or want a fast answer and don't know which system owns it | Conversational — ask, read, follow up, revisit. Often answers outright, since it already searches EngHub, ADO wikis, and IcM. |
| **EngHub** (`enghub/*`) | You need the authoritative eng.ms doc/TSG, or its ADO/GitHub source link | `resolve_service` scopes to a service; `get_source_link` gives the origin + owners. |
| **Stack Internal** (`stackoverflow/*`) | Niche problems, troubleshooting, "how did others solve this" | Often the *primary* source for internal-tool failure modes — feature flags, intake steps, known bugs that no doc mentions. |
| **Microsoft Learn** (`learn/*`) | Public Microsoft/Azure product or platform guidance | Not for internal knowledge. |

## Strategy

Think in roles, not fixed tools — each source below plays one, and so do tools not listed here:

- **Orient** — get a fast synthesized read and find which system or doc owns the answer (ES Chat). Iterative: ask, read, follow up.
- **Ground** — pull the authoritative primary source and verify before citing (EngHub for internal docs/TSGs; Microsoft Learn for public products; a library-docs tool like context7 for third-party frameworks).
- **Peer / troubleshoot** — how others actually solved it: niche fixes, gotchas, known bugs (Stack Internal; also issue trackers or other Q&A).

```
orient  ─────  ES Chat  (often answers outright)
ground  ─────  EngHub   (authoritative doc + ADO/GitHub source link)
parallel ────  Stack Internal (niche / troubleshooting)  ·  Microsoft Learn (public product)
```

- **It's a suggestion, not a pipeline.** If you already know the service, or that it's a niche troubleshooting issue, skip ES Chat and go straight to EngHub or Stack Internal.
- **These four are a starting point, not the whole toolbox.** Reach for anything that fills a role — context7 or other doc search for external libraries, issue trackers for prior troubleshooting.
- **Run Stack Internal early and in parallel**, not as a fallback — for internal-tool gotchas it often carries the decisive detail.
- **Ground before you cite:** `fetch` the EngHub page (then `get_source_link` for the origin) before repeating a claim or acting on it.

## Gotchas (figured out the hard way)

- **ES Chat citations aren't trustworthy.** It cites wrong or non-existent pages — verify every citation by opening it (`get_question`, `fetch`) before repeating it.
- **EngHub `nodeTypes` scoping silently fails.** Documented values often don't resolve and search quietly falls back to unscoped; scope with query text + `serviceIds` instead.
- **EngHub `fetch` can return metadata only** (body not indexed). Fall back to `get_source_link` or a browser, and don't `submit_feedback` on a page you couldn't actually read.
