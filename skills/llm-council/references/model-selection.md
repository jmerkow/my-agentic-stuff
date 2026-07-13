# Model Selection (reference)

Roster discovery, orthogonality heuristics, and default council configurations for the `llm-council` skill. This is a reference for the **orchestrator** running the council (choosing seats and the chair) — council members themselves do not need it.

> **Environment note.** This guidance assumes a Copilot agent harness (VS Code or the Copilot CLI), where subagents launch via a `runSubagent` tool with a `model` parameter formatted `"Model Name (Vendor)"` and cross-vendor models are available. On **Claude Code**, seats launch via the `Task` tool against `.claude/agents/` and models are the Anthropic family only — the cross-vendor guidance below does not apply; use Panel-mode persona diversity (optionally across Opus / Sonnet / Haiku) instead. If no `model` parameter is available at all, switch to persona diversity rather than running identical seats.

## 1. Model Discovery (Copilot harnesses)

Copilot harnesses have no list-models API. To discover the current roster:

1. Call `runSubagent` with an intentionally invalid `model` value (e.g., `"__invalid__"`).
2. The error response lists all valid model names.
3. Parse the roster from the error and cache it for the session.
4. **Never hardcode the roster** — it is environment-specific and changes without notice.

This probe is Copilot-specific. On Claude Code, do not probe — assume the Anthropic family and select seats by tier and persona instead.

Example probe invocation (the model value is intentionally wrong):
```
runSubagent(model="__invalid__", ...)
```

The error message enumerates the valid model strings. The format is `"Model Name (Vendor)"` — e.g., `"Claude Sonnet 4.6 (copilot)"`.

**Example snapshot (2026-07-13 — illustrative only, not authoritative; re-discover per environment):**

| Vendor | Models |
|---|---|
| Anthropic | Claude Opus 4.6, Claude Opus 4.7, Claude Opus 4.8, Claude Sonnet 4.6, Claude Sonnet 4.5, Claude Sonnet 5, Claude Haiku 4.5 |
| Google | Gemini 3.1 Pro (Preview), Gemini 3.5 Flash, Gemini 3 Flash (Preview), Gemini 2.5 Pro |
| OpenAI | GPT-5.3-Codex, GPT-5.4 mini, GPT-5.4, GPT-5.5, GPT-5.6 Luna, GPT-5.6 Sol, GPT-5.6 Terra, GPT-5 mini |
| Microsoft (MAI) | MAI-Code-1-Flash |
| Auto | Auto |

Note: All models use vendor `(copilot)` in the format string.

## 2. Cross-Vendor Tiers (weight classes)

Models fall into rough tiers across vendors. Pick seats by **matching** a tier (fair comparison) or **spanning** tiers (breadth). Output cost (credits per 1M) is a decent tier proxy — but Google prices below Anthropic/OpenAI at the same tier, so also judge within a vendor.

| Tier | Anthropic | Google | OpenAI | Microsoft |
|---|---|---|---|---|
| **Flagship** — heaviest reasoning, priciest | Opus 4.6 / 4.7 / 4.8 | Gemini 3.1 Pro (Preview) | GPT-5.5, GPT-5.6 **Sol** | — |
| **Workhorse** — balanced cost/quality | Sonnet 4.6, Sonnet 5 | Gemini 2.5 Pro | GPT-5.4, GPT-5.6 **Terra** | — |
| **Light** — cheap, fast | Haiku 4.5 | Gemini 3.5 Flash, Gemini 3 Flash (Preview) | GPT-5.6 **Luna**, GPT-5.4 mini, GPT-5 mini | — |
| **Code specialist** | — | — | GPT-5.3-Codex | MAI-Code-1-Flash |

- **The GPT-5.6 trio is three tiers, not three personas:** Sol ≈ flagship (output cost 3000), Terra ≈ workhorse (1500), Luna ≈ light (600). Same base — seat only one, chosen by the tier you want.
- **Newer Sonnet is cheaper:** Sonnet 5 (output 1000) prices below Sonnet 4.6 (1500) — a strong, cheap workhorse.
- **Google is cheaper per token** at each tier; don't read its lower price as a lower tier.
- **MAI-Code-1-Flash is tools-only (no vision)** and light-tier — use it for code, not image/multimodal questions.
- **Context windows vary within a tier** (e.g. Gemini 2.5 Pro is 173K while most flagships are ~1M) — check it if your input is large.

For a council, one seat per tier row across different vendors maximizes both capability and orthogonality; the default (§5) is one flagship each from Anthropic / Google / OpenAI.

## 3. Orthogonality Heuristics

A council's value comes from error coverage, not average accuracy. Two models are orthogonal when they disagree on the examples each gets wrong. Correlated models vote together even when wrong.

Apply these rules in order:

1. **Prefer cross-vendor, but it is not required.** Across 3 seats, 3 different vendors (Anthropic, Google, OpenAI) give the most orthogonality — different pipelines, alignment regimes, and documented failure modes. But a same-vendor multi-tier council is a legitimate fallback when cross-vendor isn't available (e.g. Claude Code) or when you want tighter cost/latency control: Anthropic in particular spans Opus / Sonnet / Haiku, which differ enough in scale to give useful (if correlated) spread. A same-vendor council shares that vendor's blind spots — weight its agreement accordingly.
2. **Avoid same named-variant clusters.** Do not seat GPT-5.6 Luna AND GPT-5.6 Sol — they share the same vendor and generation-variant cluster. Pick at most one from any named-variant cluster:
   - Luna / Sol / Terra → one seat maximum
   - Opus 4.6 / 4.7 / 4.8 → one seat maximum
   - Gemini 3.5 Flash / Gemini 3 Flash → one seat maximum
3. **Match tier to the job.** The default council uses current **flagships** (Opus, Gemini Pro, the latest GPT) for maximum capability. For cheaper, faster parallel fan-out, drop to **mid-tier** (Sonnet, Gemini Pro over Flash, GPT-5.5) — the capability gap is usually smaller than the diversity gain from a third vendor. Either way, keep the small tier (Flash / Haiku / mini) off the core seats (see next rule).
4. **Reserve small models for 4th+ seats.** Flash, mini, and Haiku add more noise than signal for complex reasoning in a 3-model council. Use them only in ≥4-model councils or for an explicit fast-sanity-check role.
5. **MAI-Code-1-Flash as a code-specialist 4th seat.** Code-specialization produces a different error profile from general-instruction models. Add it as Seat 4 for code-heavy questions.
6. **Exclude Auto from council seats.** `Auto`'s model selection is non-deterministic across parallel calls — it cannot contribute an independent, reproducible perspective. `Auto` may chair the synthesis step.

## 4. Cluster Correlation Reference

Use this table to avoid seating correlated models together:

| Cluster | Correlation | Reason |
|---|---|---|
| Claude Opus 4.6 / 4.7 / 4.8 | HIGH | Sequential safety/quality updates on a shared base, same pretraining data and RLHF pipeline |
| GPT-5.6 Luna / Sol / Terra | HIGH | Three tiers of a shared GPT-5.6 base (Luna light / Terra workhorse / Sol flagship) — seat only one |
| GPT-5.4 mini / GPT-5.4 | HIGH | Contemporaneous generation; mini is a scaled-down variant |
| Gemini 3.5 Flash / Gemini 3 Flash (Preview) | HIGH | Both Flash tier; 3 Flash is the preview predecessor |
| Gemini 2.5 Pro / Gemini 3.1 Pro (Preview) | MODERATE | Generational gap is larger; 3.1 is preview |
| GPT-5.4 / GPT-5.5 / GPT-5.6 | MODERATE-LOW | Different training runs within same vendor |
| Any Anthropic vs. any Google vs. any OpenAI | LOW (desired) | Cross-vendor diversity |
| MAI-Code-1-Flash vs. any of the above | LOW | 4th vendor, independent Microsoft training infrastructure |

## 5. Default Councils

> **Verify before use.** The concrete model names below are an illustrative snapshot. Re-run the discovery probe (§1) and remap the roles to the live roster before each council. Treat the seats as **roles**, not fixed names — that is what survives roster churn.

### 3-Model Default (latest, cross-vendor)

| Seat | Role | Current model (2026-07-13) | Rationale |
|---|---|---|---|
| 1 | Anthropic flagship | Claude Opus 4.8 | Strongest Anthropic reasoning; Constitutional AI gives distinctive biases |
| 2 | Google Pro | Gemini 3.1 Pro (Preview) | Latest Google Pro; multimodal-first pretraining (only current Pro is a Preview build) |
| 3 | OpenAI current | GPT-5.6 Sol | Latest OpenAI generation; Sol is its flagship-tier variant (Terra = workhorse, Luna = light) |

This default favors the **latest, strongest** model per vendor. Swap for a cheaper or more stable council as needed:
- **Cost / latency:** drop to mid-tier — Claude Sonnet 5 (or 4.6), Gemini 2.5 Pro, GPT-5.5. Often nearly as good, and faster/cheaper for parallel fan-out.
- **Stability:** Gemini 3.1 Pro is a **Preview** build; for a documented, stable release use Gemini 2.5 Pro.
- **Simplicity:** GPT-5.6 comes as three tiers (Sol = flagship, Terra = workhorse, Luna = light); this default uses Sol. Use GPT-5.5 instead to avoid the 5.6 line entirely.

### 4-Model Council (code-heavy questions)

Add **MAI-Code-1-Flash** (Microsoft, code-specialist) as Seat 4. This adds a 4th vendor and a coding-specialist error profile.

| Seat | Role | Current model |
|---|---|---|
| 1 | Anthropic flagship | Claude Opus 4.8 |
| 2 | Google Pro | Gemini 3.1 Pro (Preview) |
| 3 | OpenAI current | GPT-5.6 Sol |
| 4 | Microsoft code-specialist | MAI-Code-1-Flash |

### Updating for Roster Churn

When the roster changes, re-run the discovery probe and remap roles:
- Anthropic flagship → latest Opus (mid-tier alternative: latest Sonnet)
- Google Pro → latest Gemini Pro (prefer a non-Preview build if one exists)
- OpenAI current → latest GPT generation (if it ships only as named variants, pick one)
- Code specialist → any code-tuned model from a vendor not already in the council

## 6. Pinning Models

Two ways to fix which models sit on the council:

- **Role-pinned (default, portable).** Store seats as roles — "Anthropic mid-tier", "Google Pro", "OpenAI current" — and resolve them to concrete names at run time from the live roster. Survives roster churn; the same council definition works across environments.
- **Name-pinned (reproducible).** Store exact names (e.g. `Claude Sonnet 4.6`). Use only when you need reproducibility — benchmarking, or explicitly comparing named models — because pinned names go stale as models are retired.

Whichever you use, **record the exact resolved model names (and the chair) in the run's appendix.** A role-pinned run is only reproducible after the fact if you captured what the roles resolved to. Pin the chair the same way you pin the seats.
