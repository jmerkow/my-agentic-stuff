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

**Example snapshot (2026-07-12 — illustrative only, not authoritative; re-discover per environment):**

| Vendor | Models |
|---|---|
| Anthropic | Claude Opus 4.6, Claude Opus 4.7, Claude Opus 4.8, Claude Sonnet 4.6, Claude Sonnet 4.5, Claude Sonnet 5, Claude Haiku 4.5 |
| Google | Gemini 3.1 Pro (Preview), Gemini 3.5 Flash, Gemini 3 Flash (Preview), Gemini 2.5 Pro |
| OpenAI | GPT-5.3-Codex, GPT-5.4 mini, GPT-5.4, GPT-5.5, GPT-5.6 Luna, GPT-5.6 Sol, GPT-5.6 Terra, GPT-5 mini |
| Microsoft (MAI) | MAI-Code-1-Flash |
| Auto | Auto |

Note: All models use vendor `(copilot)` in the format string.

## 2. Orthogonality Heuristics

A council's value comes from error coverage, not average accuracy. Two models are orthogonal when they disagree on the examples each gets wrong. Correlated models vote together even when wrong.

Apply these rules in order:

1. **Cross-vendor first.** With 3 seats, use 3 different vendors. Any combination spanning (Anthropic, Google, OpenAI) is more orthogonal than any within-vendor combination. Different labs use different pretraining pipelines, alignment regimes, and documented failure modes.
2. **Avoid same named-variant clusters.** Do not seat GPT-5.6 Luna AND GPT-5.6 Sol — they share the same vendor and generation-variant cluster. Pick at most one from any named-variant cluster:
   - Luna / Sol / Terra → one seat maximum
   - Opus 4.6 / 4.7 / 4.8 → one seat maximum
   - Gemini 3.5 Flash / Gemini 3 Flash → one seat maximum
3. **Use the mid-tier within each vendor.** Sonnet (not Opus), Gemini Pro (not Flash), GPT-5.5 or GPT-5.4 (not mini). The accuracy gain from a flagship over mid-tier is smaller than the orthogonality gain from a third distinct vendor.
4. **Reserve small models for 4th+ seats.** Flash, mini, and Haiku add more noise than signal for complex reasoning in a 3-model council. Use them only in ≥4-model councils or for an explicit fast-sanity-check role.
5. **MAI-Code-1-Flash as a code-specialist 4th seat.** Code-specialization produces a different error profile from general-instruction models. Add it as Seat 4 for code-heavy questions.
6. **Exclude Auto from council seats.** `Auto`'s model selection is non-deterministic across parallel calls — it cannot contribute an independent, reproducible perspective. `Auto` may chair the synthesis step.

## 3. Cluster Correlation Reference

Use this table to avoid seating correlated models together:

| Cluster | Correlation | Reason |
|---|---|---|
| Claude Opus 4.6 / 4.7 / 4.8 | HIGH | Sequential safety/quality updates on a shared base, same pretraining data and RLHF pipeline |
| GPT-5.6 Luna / Sol / Terra | HIGH | Named variants of GPT-5.6 — likely persona- or domain-fine-tuned from shared base weights |
| GPT-5.4 mini / GPT-5.4 | HIGH | Contemporaneous generation; mini is a scaled-down variant |
| Gemini 3.5 Flash / Gemini 3 Flash (Preview) | HIGH | Both Flash tier; 3 Flash is the preview predecessor |
| Gemini 2.5 Pro / Gemini 3.1 Pro (Preview) | MODERATE | Generational gap is larger; 3.1 is preview |
| GPT-5.4 / GPT-5.5 / GPT-5.6 | MODERATE-LOW | Different training runs within same vendor |
| Any Anthropic vs. any Google vs. any OpenAI | LOW (desired) | Cross-vendor diversity |
| MAI-Code-1-Flash vs. any of the above | LOW | 4th vendor, independent Microsoft training infrastructure |

## 4. Default Councils

> **Verify before use.** The concrete model names below are an illustrative snapshot. Re-run the discovery probe (§1) and remap the roles to the live roster before each council. Treat the seats as **roles**, not fixed names — that is what survives roster churn.

### 3-Model Default

| Seat | Role | Current model (2026-07-12) | Rationale |
|---|---|---|---|
| 1 | Anthropic mid-tier | Claude Sonnet 4.6 | Constitutional AI produces distinctive hedging and attribution patterns absent from other vendors |
| 2 | Google Pro (established) | Gemini 2.5 Pro | Multimodal-first pretraining; non-Preview release with documented benchmarks |
| 3 | OpenAI current unambiguous | GPT-5.5 | Single unambiguous model identity; avoids the GPT-5.6 variant cluster |

**Why not Opus?** Parallel throughput matters. Opus is slower; the incremental accuracy gain over Sonnet is smaller than the diversity gain from a third distinct vendor.
**Why Gemini 2.5 Pro over 3.1 Pro (Preview)?** Preview labels signal unstable/evaluation builds.
**Why GPT-5.5 over GPT-5.6 variants?** GPT-5.6 has three named variants — any single-seat pick from that cluster is arbitrary.

### 4-Model Council (code-heavy questions)

Add **MAI-Code-1-Flash** (Microsoft, code-specialist) as Seat 4. This adds a 4th vendor and a coding-specialist error profile.

| Seat | Role | Current model |
|---|---|---|
| 1 | Anthropic mid-tier | Claude Sonnet 4.6 |
| 2 | Google Pro | Gemini 2.5 Pro |
| 3 | OpenAI current | GPT-5.5 |
| 4 | Microsoft code-specialist | MAI-Code-1-Flash |

### Updating for Roster Churn

When the roster changes, re-run the discovery probe and remap roles:
- Anthropic mid-tier → first non-Opus, non-Haiku Anthropic model
- Google Pro → first non-Flash, non-Preview Google model
- OpenAI current → GPT generation between the latest and its mini variant (avoid named-variant clusters)
- Code specialist → any code-tuned model from a vendor not already in the council
