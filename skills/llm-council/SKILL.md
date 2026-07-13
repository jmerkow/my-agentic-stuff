---
name: llm-council
description: >
  Run an LLM council: pose a question to multiple orthogonal models and/or specialist
  personas in parallel (via the harness's subagent tool), then summarize each stance and
  synthesize the responses with a separate chair model. Use when the user wants diverse model
  perspectives, a panel of specialist lenses (concise, skeptic, coder, prose), or
  cross-model review of a high-stakes or ambiguous question, or asks to ask the council,
  panel, or multiple models.
  Keywords: council, panel, specialists, personas, multiple models, diverse perspectives,
  ensemble, model comparison, cross-model review, fan-out, synthesize, second opinion,
  3-flag, 2-horse.
---

# LLM Council

Structured multi-model review: fan out one question to N independent seats, then have a chair model summarize each councilor's stance and synthesize them into a single grounded answer.

## When to Use This Skill

Use the council pattern when:
- The user wants multiple or diverse model perspectives on a question
- You want a *panel of specialist lenses* (concise, skeptic, coder, prose), not just different models
- A question is high-stakes, ambiguous, or has genuine uncertainty
- The user says "ask the council," "check with multiple models," "panel review," or "get diverse opinions"
- You want error coverage across model blind spots rather than a single model's answer

Do NOT use for every question. A council is heavier than a single model call — use it when the cross-model diversity is worth the extra latency.

## Two Modes

- **Ensemble** — the same task to N diverse *models* (default). Independence → error de-correlation; use for factual/analytical questions.
- **Panel** — N specialist *personas* (see [references/specialists.md](references/specialists.md)), optionally each on a different model. Use for reviews, designs, judgment calls.
- **Hybrid** — distinct personas *and* models.

Seats are always independent (no seat sees another's answer) and feed the same chair step. Panel/Hybrid add a persona preamble; Ensemble gets the task alone. Min 2 seats, default 3.

## Presets (quick invocation)

Shorthand: `/llm-council <seats>-<tier> <question>` — tier is `flag` (flagship) or `horse` (workhorse), so `3-flag` = three flagships, `2-horse` = two workhorse cold reads. Extras: `4-code` (flagships + a code-tuned 4th lens), `panel` (Panel mode). No preset → `3-flag`. In a `2-*`, disagreement means "look closer," not "majority wins."

## Portability (harness adapters)

The packaging (`plugin.json`, `SKILL.md`, `references/`, `.claude-plugin/marketplace.json`) is portable; the **runtime differs by harness**. Load [references/model-selection.md](references/model-selection.md) and [references/specialists.md](references/specialists.md), then:

- **VS Code Copilot / Copilot CLI:** `runSubagent` with an explicit `model` (`"Model Name (Vendor)"`) + optional `agentName`; cross-vendor available.
- **Claude Code:** `Task` against `.claude/agents/`, Anthropic-only — no cross-vendor Ensemble, so use Panel mode (personas, optionally across Opus/Sonnet/Haiku).
- **No subagent tool:** say the council can't run; offer a single-model answer.

## Roles

- **Council members:** N independent seats. Each gets the full task (+ persona in Panel), never another seat's answer or your own take.
- **Chair:** the calling agent by default (it reads the seats cold). Spawn a separate chair only for a fresh perspective — any non-seat model (`Auto` or a workhorse).

## The 5-Step Flow

### Step 1 — Select Council

See [references/model-selection.md](references/model-selection.md) for roster discovery and seat selection. Key rules:
- **Default seats** — fill in vendor-priority order:
  1. Anthropic (Opus)
  2. OpenAI (GPT flagship)
  3. Google (Gemini Pro)
  4. Microsoft (MAI-Code) — code lens only

  So **2 seats = 1–2**, **3 seats = 1–3** (the default), **4-code = 1–4**. Resolve names at run time.
- **Lighter / faster:** drop to the workhorse tier — Sonnet, GPT-5.6 Terra, Gemini 2.5 Pro.
- **Code-heavy:** the flagships already code best; optionally add a light code-tuned model (MAI-Code) as a cheap 4th lens.
- **Cross-vendor preferred, not required:** a same-vendor multi-tier council (Opus + Sonnet + Haiku) is a valid fallback — and the only option on single-vendor harnesses — but shares blind spots, so discount its agreement.
- **Pinning:** resolve roles at run time; name-pin exact models only for reproducibility, and record the resolved names in the footer. See [references/model-selection.md](references/model-selection.md).
- On Copilot harnesses, discover the live roster first via the invalid-model probe; if that fails, ask the user for model names. On Claude Code, the roster is the Anthropic family (see Portability) — use Panel mode.
- A dynamic/auto-routing model (e.g. Copilot `Auto`) may chair but must never hold a seat (non-deterministic).
- Respect the user's explicit model or persona choices if given.
- **Panel/Hybrid mode:** pick specialist lenses from [references/specialists.md](references/specialists.md) (or a preset panel). Optionally pair each with a distinct model, or target an existing agent via `agentName` — but agent names like `eng-code-sub` / `Explore` are examples that may not exist; if absent, fall back to the persona preamble alone.

**No distinct models?** (one model family, or no `model` parameter) → use Panel mode (persona diversity). Never run identical seats — that's a fake council. Neither possible → tell the user and offer a single-model answer.

Config knobs:
- `council_size`: 2 (two cold reads — a quick second opinion), 3 (default), 4 (code-heavy)
- `models`: explicit list overrides defaults (e.g., `["Claude Opus 4.8 (copilot)", "GPT-5.6 Sol (copilot)", "Gemini 3.1 Pro (Preview) (copilot)"]`) — a manual override can collapse the cross-vendor/tier spread; note that in the footer if it does
- `synthesizer`: chair model, only when spawning a *separate* chair (default: the calling agent itself; else `Auto` or any non-seat model)

**Effort:** you can't set a seat's reasoning effort. For more depth, pick a higher tier (a flagship reasons more than a mini) or ask for it in the prompt.

### Step 2 — Fan-Out (Independent Answering)

Spawn all seats in parallel. Each gets the *same* task text; vary only the model and (Panel) the persona.

- **Include:** the full question + any context it needs — embedding the task's data is expected.
- **Withhold:** other seats' answers, your opinion, the conclusion you expect.
- **Cap the output** and match its shape to the question (templates below).
- **Ensemble independence:** prefer plain model seats; don't seat agent-backed (`agentName`) or tool-using ones (they pull extra context).

**Template A — opinion / take** (the question wants a position or answer):
```
{persona_preamble}          # Panel mode only

{question}

Answer in ≤200 words: state your position, then the 2-3 reasons that most drive it,
then your single biggest uncertainty. Don't hedge.
```

**Template B — findings / itemized** (the question is "find issues / review / list X"):
```
{persona_preamble}          # Panel mode only

{question}

Return a list, most important first, ≤8 items. For each: a short **title**, a
one-sentence explanation, and a severity (high / med / low). Name the single biggest one.
```

**Advanced** (long/multi-part, or a large artifact): give the exact output format, and if long, have each seat **write its own uniquely named file** (write only that file, never read the council dir) and return a summary + path. Location: under `.eng/`'s active-workstream `council/<date>-<slug>/` (or `.eng/council/<date>-<slug>/`), else a user path, or inline when small. Collect the paths for the chair.

A seat fails/times out → continue with survivors (min 2).

### Step 3 — Collect

Gather every successful response and keep it **labeled** with its seat (model, and persona in Panel mode). Don't anonymize or shuffle — the chair needs identities to attribute stances and show who agrees with whom.

### Step 4 — Synthesize (Chair Step)

The chair (you, by default) reads the question + labeled responses and returns:

1. **Stance summary** — one paragraph per councilor (label by model, + persona when they differ); note lone stances.
2. **Synthesis** — agreement, real disagreements (with a reasoned call), unique points, and a grounded bottom line. Don't just echo the most confident seat; treat unanimous agreement as possible correlated bias.

**Chair prompt template:**
```
You are the chair of a council. Below is a question and the independent responses of
several councilors, each labeled with its model (and persona, if any). Produce:

1. STANCE SUMMARY — one short paragraph per councilor, in your own words, capturing that
   councilor's position and what drives it. Note where a councilor stands alone.
2. SYNTHESIS — where councilors AGREE (likely reliable), where they DISAGREE (flag it and
   reason about which position is more defensible), and any UNIQUE point that adds value.
   End with a grounded bottom line. Do not merely echo the most confident answer; treat
   unanimous agreement as possible correlated bias, not automatic truth.

Question:
{question}

Councilor responses:
--- {model_1} / {persona_1} ---
{response_1}

--- {model_2} / {persona_2} ---
{response_2}
...
```

### Step 5 — Present

Match the presentation to what the councilors returned:

**If they returned lists / findings** (Template B — "find issues", reviews): present a **consolidated table**, consensus first, so agreement is obvious at a glance:

| # | Finding | Raised by | Severity | Fix |
|---|---|---|---|---|
| 1 | short title | all 3 · Opus, GPT, Gemini | High | one-line fix |
| 2 | short title | 2 · Opus, GPT | Med | one-line fix |
| … | lone-wolf items last | 1 · Gemini | Low | one-line fix |

Merge the same point raised by different councilors into one row and show who raised it — that agreement count is the signal. Follow the table with the chair's bottom line.

**If they returned takes / positions** (Template A — a question or topic): present the chair's **per-councilor stance paragraphs**, then the **synthesis**. No table — itemizing prose takes loses the reasoning.

**Always** end with a compact footer: council composition (models/personas, which chaired), any failed seats, and — if models were name-pinned or seats wrote to files — the resolved names and artifact paths. Offer full per-seat responses on request; don't dump them by default.

## Graceful Degradation

| Situation | Action |
|---|---|
| A seat times out | Note the failure; continue with survivors |
| A seat returns an error | Note the failure; continue with survivors |
| Only 2 survivors | Synthesize from 2 (note reduced council in appendix) |
| Fewer than 2 survivors | Don't synthesize — return the one response labeled "not a council result," or report the failure |

Never block the entire council on a single seat failure.

## References

- [model-selection.md](references/model-selection.md) — roster discovery, tiers, seat selection.
- [specialists.md](references/specialists.md) — personas and panel presets.
