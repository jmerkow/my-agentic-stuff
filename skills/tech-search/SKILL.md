---
name: tech-search
description: Search internal engineering knowledge for technical and internal-tool questions. Use when asking an engineering-systems question (es chat, eschat, es-chat), searching EngHub or eng.ms (eng hub, enghub, eng-hub), finding a TSG, schema, onboarding guide, or source link, figuring out why an internal tool or MCP path does not work, finding a known setting or solution for an internal system, or running a /tech-search lookup. Also triggers on: stack overflow, stackoverflow for teams, internal Q&A, internal engineering how-to. Does NOT cover personal M365 activity — use work-search for that.
---

# Tech Search

Focused search across internal engineering knowledge for technical, tool, and system questions:

1. **ES Chat** — AI assistant that internally searches Eng Hub, ADO wikis and work items, IcM incidents, and custom sources
2. **EngHub (eng.ms)** — authoritative internal docs, TSGs, source links, and the ServiceTree
3. **Stack Internal** — peer Q&A and knowledge articles from the org's Stack Overflow for Teams
4. **Microsoft Learn** — official product and platform guidance, when the question is not about an internal system

Pick the source first, then the tool.

## Tool Landscape

## ES Chat

### ES Chat (`mcp_microsoft_es__es_*`)

Internal AI assistant over engineering systems. Searches Eng Hub, ADO wikis and work items, IcM incidents, and custom sources as one operation. Phrase questions as direct technical queries — omit "engineering systems", "engsys", or "es" from the question text, as those qualifiers mislead the tool and narrow results incorrectly.

| Tool | Use |
|------|-----|
| `mcp_microsoft_es__es_ask` | Ask a natural-language engineering question (best first stop when the owning system is unknown) |
| `mcp_microsoft_es__es_search` | Keyword search across engineering systems |
| `mcp_microsoft_es__es_resolve` | Resolve an entity identifier (URL, GUID, numeric ID) to information about it |

**Best for:** Orientation AND answers. ES Chat is conversational — ask it, read the synthesized answer and its citations, then ask follow-ups to narrow in. Lean on it across multiple turns, not as a single first step. Good for broad technical questions, incident lookups, internal system troubleshooting, and figuring out which service or doc set owns an answer.

**Use throughout:** Return to ES Chat whenever you need to reorient or refine — it is the workhorse, not just the entry point. It frequently answers the question outright because it already searches Eng Hub, ADO wikis, and IcM under the hood.

**Its citations are not trustworthy:** ES Chat routinely cites the wrong page or a non-existent one. Always verify a citation by opening the source with the actual tool (`mcp_stackoverflow_get_question`, `mcp_engineeringhu_fetch`) before repeating a claim or acting on it.

**Pair with EngHub:** ES Chat tells you *what* the answer is and *where* it lives; EngHub pulls the specific authoritative doc or TSG behind that answer and its ADO/GitHub source link.

## Internal Engineering Docs

### EngHub (`mcp_engineeringhu_*`)

eng.ms documentation — the authoritative source for internal docs, TSGs, team docs, onboarding guides, and service content. A seven-tool workflow built around the ServiceTree, not just search and fetch.

| Tool | Use |
|------|-----|
| `mcp_engineeringhu_resolve_service` | Resolve a service name → ServiceTree serviceId(s). Scoping entry point. |
| `mcp_engineeringhu_search` | Search docs and TSGs with optional scoping by `serviceIds`, `nodeTypes`, or `urlPath` |
| `mcp_engineeringhu_fetch` | Fetch full page body, metadata, and child pages from an eng.ms URL |
| `mcp_engineeringhu_get_service_nodes` | Enumerate ALL content for a known serviceId, with optional tag filter |
| `mcp_engineeringhu_get_node_tree` | Browse the ServiceTree hierarchy one level at a time |
| `mcp_engineeringhu_get_source_link` | Get the ADO/GitHub source-markdown link and owners for an eng.ms article |
| `mcp_engineeringhu_submit_feedback` | Submit thumbs up/down to doc owners after a page was used |

**`nodeTypes` scoping is unreliable:** the documented values (`TSGs`, `Team Docs`, `Onboarding Guides`, `OpenAPI`, `Popular`, `Featured`) often fail to resolve, and the search silently falls back to unscoped. Treat it as a hint, not a filter — rely on the query text and `serviceIds` for scoping.

**`fetch` can return metadata only:** sometimes a page body is not in the search index and `fetch` returns just metadata. When that happens, use `get_source_link` to read the source markdown in ADO/GitHub (or open the eng.ms URL in a browser), and don't `submit_feedback` on a page you could not actually read.

**Best for:** Internal docs, TSGs, service-specific onboarding, and source-link attribution. The only tool that returns the ADO/GitHub origin of an eng.ms page.

**Use when:** You know the question involves a specific internal service or team and need the actual source content.

**Pair with Stack Internal:** Run `mcp_stackoverflow_search` in parallel to catch peer answers that TSGs may not mention.

## Peer Q&A

### Stack Internal (`mcp_stackoverflow_*`)

The org's Stack Overflow for Teams — peer Q&A, knowledge articles, and SME discovery. Use keyword phrasing in search, not full sentences.

| Tool | Use |
|------|-----|
| `mcp_stackoverflow_search` | Keyword search; returns lightweight summaries with IDs |
| `mcp_stackoverflow_get_question` | Full question + all answers by question ID |
| `mcp_stackoverflow_get_article` | Full knowledge article + comments by article ID |
| `mcp_stackoverflow_get_comments` | Comments on a question or a specific answer |
| `mcp_stackoverflow_get_existing_tags` | List all valid tags — required before creating any content |
| `mcp_stackoverflow_recommend_SME` | Recommend subject-matter experts for a tag ID |
| `mcp_stackoverflow_get_questions_to_answer` | Find unanswered questions by topic or tag |

**Best for:** Niche problems and troubleshooting — how others actually solved it, community workarounds, confirmed settings, and gotchas that official docs and TSGs omit. For internal-tool failure modes it is often the *primary* source, not a supplement.

**Use when:** Anything niche or troubleshooting-flavored — run it early, in parallel with ES Chat and EngHub, not just as a fallback. It frequently carries the decisive operational detail (feature flags, intake steps, known bugs) that no doc mentions.

## Official Product Docs

### Microsoft Learn (`mcp_microsoft_lea_microsoft_*`)

Official Microsoft and Azure documentation. Use only when the question is product or platform guidance rather than internal system knowledge.

| Tool | Use |
|------|-----|
| `mcp_microsoft_lea_microsoft_docs_search` | Search official Microsoft/Azure docs |
| `mcp_microsoft_lea_microsoft_docs_fetch` | Fetch the full content of a docs page |
| `mcp_microsoft_lea_microsoft_code_sample_search` | Search official code samples (supports `language` filter) |

**Best for:** Azure, M365, Copilot, Foundry, SDK/API reference, official implementation examples.

**Use when:** The question is "how does this Microsoft product work" rather than "how does this internal tool or team process work".

**Required pattern:** Search first, then fetch the most relevant page when details matter.

## Query Strategy: A Suggested Flow

This is a suggestion, not a fixed pipeline. If you already know the specifics — the exact service, the doc, or that it's a niche troubleshooting issue — skip the orientation step and jump straight to the right tool (EngHub or Stack Internal).

```
ES Chat (ask → read answer + citations → ask follow-ups; revisit anytime)
  └─ EngHub resolve_service → search (scope by serviceIds) or get_service_nodes(serviceId)
       └─ EngHub fetch (read the page before citing it)
            └─ get_source_link (cite ADO/GitHub origin) → submit_feedback (close the loop)
Stack Internal (mcp_stackoverflow_search) — run early, in parallel — best for niche / troubleshooting
Microsoft Learn — run in parallel for public product/platform questions
```

### Ordering guidance

1. **Start with ES Chat, but treat it as a suggestion** (`es_ask`) — ask, read the answer and citations, ask follow-ups. It both orients you and often answers directly. If you already know the specifics, skip ahead to EngHub or Stack Internal. **Verify its citations** — they are not trustworthy; open any cited source with the real tool before repeating it.
2. **Use EngHub to pull the specific sources** ES Chat points you to — the authoritative doc or TSG and its origin. Call `resolve_service` when the service name is known, always `fetch` before citing, and `get_source_link` when you want the origin link (also your fallback when `fetch` returns no body).
3. **Search Stack Internal early, in parallel** — it is the best place for niche problems and troubleshooting, and often carries the decisive detail (feature flags, intake steps, known bugs) that docs and TSGs omit.
4. **Run Microsoft Learn in parallel for public product/platform questions** — don't force it to the end when current Microsoft docs answer directly.

## Worked Examples

### Example: Find whether a known setting or workaround exists for an internal tool

```
1. mcp_microsoft_es__es_ask("Does X support Y setting?")          → orient, identify service/doc set
2. mcp_stackoverflow_search("X Y setting")                         → peer answers (in parallel)
3. mcp_engineeringhu_resolve_service("X")                         → get serviceId
4. mcp_engineeringhu_search(serviceIds=[...], query="Y setting")  → find the doc or TSG
5. mcp_engineeringhu_fetch(url)                                   → read the source before acting on it
6. mcp_engineeringhu_submit_feedback(url, "up")                   → close the loop
```

### Example: Find a TSG and its ADO/GitHub source link

```
1. mcp_engineeringhu_resolve_service("service name")              → serviceId
2. mcp_engineeringhu_search(serviceIds=[...], query="topic TSG")   → scope by serviceIds; put "TSG" in the query (nodeTypes filter is unreliable)
3. mcp_engineeringhu_fetch(url)                                   → read the TSG (fall back to get_source_link if body is empty)
4. mcp_engineeringhu_get_source_link(url)                         → ADO/GitHub origin + owners
5. mcp_engineeringhu_submit_feedback(url, rating)                 → close the loop
```

### Example: Figure out why an MCP path or internal tool does not work

```
1. mcp_microsoft_es__es_ask("Why does X fail when calling Y?")    → orient and identify known issues
2. mcp_microsoft_es__es_resolve(identifier)                       → resolve entity ID if you have one
3. mcp_stackoverflow_search("X error Y")                          → peer-confirmed workarounds (in parallel)
4. mcp_engineeringhu_search(query="X troubleshooting")            → TSG or known-issue doc
5. mcp_engineeringhu_fetch(url)                                   → read before acting on it
```

### Example: Confirm a value or workflow — product or platform question

```
1. mcp_microsoft_lea_microsoft_docs_search("Azure X feature Y")
2. mcp_microsoft_lea_microsoft_docs_fetch(url)                    → full page with steps
3. mcp_microsoft_lea_microsoft_code_sample_search("X Y", language="python")
```
