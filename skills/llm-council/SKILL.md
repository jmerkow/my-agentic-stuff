---
name: llm-council
description: >
  Run an LLM council: pose a question to multiple orthogonal models and/or specialist
  personas in parallel (via the harness's subagent tool), then summarize each stance and
  synthesize the responses with a separate chair model. Use when the user wants diverse
  model
  perspectives, a panel of specialist lenses (concise, skeptic, coder, prose), or
  cross-model review of a high-stakes or ambiguous question, or asks to ask the council,
  panel, or multiple models.
  Keywords: council, panel, specialists, personas, multiple models, diverse perspectives,
  ensemble, model comparison, cross-model review, fan-out, synthesize.
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

- **Ensemble mode** — the same bare question goes to N diverse *models* (see [references/model-selection.md](references/model-selection.md)). Pure independence; maximizes error de-correlation. Use for factual/analytical questions where you want blind-spot coverage.
- **Panel mode** — the question goes to N *specialists* (persona and/or agent lenses; see [references/specialists.md](references/specialists.md)), optionally each on a different model. Deliberately varies framing to get different *kinds* of feedback (concise vs. thorough, coder vs. prose). Use for reviews, designs, and judgment calls.
- **Hybrid** — combine both axes: specialists each seated on a distinct model, varying lens *and* blind spots at once.

All modes keep seat independence (no seat sees another's answer) and use the same chair/synthesis step. Panel mode intentionally relaxes the "bare question, no framing" rule of Ensemble mode — that is the point, not a bug.

## Portability (harness adapters)

The packaging (`plugin.json`, `SKILL.md`, `references/`, `.claude-plugin/marketplace.json`) is portable, but the **runtime differs by harness**. Before executing, load [references/model-selection.md](references/model-selection.md) and [references/specialists.md](references/specialists.md), then pick the adapter:

- **VS Code Copilot / Copilot CLI:** spawn seats with the `runSubagent` tool, an explicit `model` (`"Model Name (Vendor)"`), and optional `agentName`. Cross-vendor seats (Anthropic + Google + OpenAI) are available. Copilot CLI parity is assumed — verify `runSubagent` exists before relying on it.
- **Claude Code:** seats spawn via the `Task` tool against agents under `.claude/agents/`; models are the Anthropic family only (no `(copilot)` suffix). Cross-vendor Ensemble mode is **not** available — use **Panel mode**, where diversity comes from personas (optionally across Opus / Sonnet / Haiku tiers).
- **No subagent tool at all:** tell the user the council can't run; offer a single-model answer.

Below, "spawn a seat" means the current harness's subagent call — not literally `runSubagent`.

## Roles

- **Council members:** N seats that answer independently. A seat is a `(model, persona/agent)` pairing — vary the model (Ensemble), the persona/agent (Panel), or both (Hybrid). Each seat sees ONLY the question (plus its own persona framing in Panel mode), never another seat's answer.
- **Chair (synthesizer):** A model that did NOT produce any council answer — never one of the seats. Prefer a different vendor than the council; when there is no majority (e.g. the 3-vendor default) or only one vendor is available (Claude Code), pick any model/tier not used as a seat and note the reduced separation. Receives the question plus every seat's response, each labeled with its model and persona.

## The 5-Step Flow

### Step 1 — Select Council

See [references/model-selection.md](references/model-selection.md) for roster discovery and seat selection. Key rules:
- Default council = 3 cross-vendor **roles** at the latest tier: an Anthropic flagship (Opus) + a Google Pro + an OpenAI current model — today Claude Opus 4.8 + Gemini 3.1 Pro (Preview) + a GPT-5.6 variant (e.g. Sol); add a code-specialist 4th for code-heavy work. Drop to mid-tier (Sonnet 5 / Gemini 2.5 Pro / GPT-5.5) for cheaper, faster fan-out. Cross-vendor is *preferred, not required* — a same-vendor multi-tier council (e.g. Opus + Sonnet + Haiku) is a valid fallback and the only option on single-vendor harnesses; it shares that vendor's blind spots, so weight its agreement accordingly.
- **Pinning:** resolve roles to concrete names at run time (portable, survives churn). Name-pin exact models only for reproducibility or explicit model comparisons — and always record the resolved names in the appendix. See [references/model-selection.md](references/model-selection.md).
- On Copilot harnesses, discover the live roster first via the invalid-model probe. On Claude Code, the roster is the Anthropic family (see Portability) — use Panel mode.
- A dynamic/auto-routing model (e.g. Copilot `Auto`) may chair but must never hold a seat (non-deterministic).
- Respect the user's explicit model or persona choices if given.
- **Panel/Hybrid mode:** pick specialist lenses from [references/specialists.md](references/specialists.md) (or a preset panel). Optionally pair each with a distinct model, or target an existing agent via `agentName` — but agent names like `eng-code-sub` / `Explore` are examples that may not exist; if absent, fall back to the persona preamble alone.

**If seats cannot be given distinct models** (harness has one model family, or the subagent tool has no `model` parameter): switch to Panel mode so diversity comes from personas. Do NOT silently run every seat on the same default model — that is a fake council with no error de-correlation. If neither distinct models nor personas are possible, tell the user and offer a single-model answer.

Config knobs:
- `council_size`: 3 (default), 4 for code-heavy
- `models`: explicit list overrides defaults (e.g., `["Claude Opus 4.8 (copilot)", "Gemini 3.1 Pro (Preview) (copilot)", "GPT-5.6 Sol (copilot)"]`)
- `synthesizer`: model for the chair step (default: a model/tier not used as a seat; prefer a different vendor, or `Auto`)

### Step 2 — Fan-Out (Independent Answering)

Spawn one seat per council member (see Portability for the per-harness call). Run them all in parallel.

**Critical invariant — no cross-contamination:** No seat ever sees another seat's answer, your reasoning, or context the user didn't provide. Isolation is NOT automatic: a full-agent seat with tool access may read the repo or search the web, quietly re-correlating the seats. For a faithful Ensemble, pass only the question (plus a persona preamble in Panel mode) and prefer non-agentic seats; reserve tool-using agent seats for Panel mode.

**Build the seat prompt.** Every seat gets the *same* task text — vary only the model and (Panel) the persona preamble. A bare question is rarely enough; add an **output cap** (keeps answers comparable and synthesis tractable) and the **output shape** you want, matched to the question.

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

**Simple vs. advanced questions:**
- *Simple* — the templates above are enough; the seat answers directly.
- *Advanced* (long, multi-part, or the seat must orchestrate or produce a large artifact): spell out the exact output format, and if the answer is long, have the seat **write it to a file and return a short summary + the path** instead of dumping it inline.
  - If an `.eng/` directory exists at the workspace root, write there — the active workstream's `council/<date>-<slug>/` if one is active, else `.eng/council/<date>-<slug>/`.
  - Otherwise write to a path the user names, or return inline when small.
  - Collect the paths so the chair (Step 4) can read the full artifacts.

If a seat fails or times out: log it, continue with survivors (minimum 2). One failure never blocks the council.

### Step 3 — Collect

Gather every successful response and keep it **labeled** with its seat — the model, and in Panel mode the persona. You will summarize each councilor's stance for the user, so identity matters; do not strip it.

(No anonymizing or shuffling: an LLM chair can't be made truly blind, and knowing each councilor's identity is exactly what lets the synthesis attribute stances and show who agrees with whom.)

### Step 4 — Synthesize (Chair Step)

Give the chair the question and every labeled response. The chair did not produce any of them, so it reads them cold. It returns two things:

1. **Per-councilor stance** — one short paragraph per seat, in the chair's own words, capturing that councilor's position and what drives it. Label by model, plus persona when personas differ; skip persona labels when every seat shared one. Note where a councilor stands alone.
2. **Synthesis** — where councilors agree, where they genuinely disagree (with a reasoned call on each), any unique point worth keeping, and a grounded bottom line. Don't just echo the most confident seat.

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
| 1 | short title | all 3 · Sonnet, Gemini, GPT | High | one-line fix |
| 2 | short title | 2 · Sonnet, GPT | Med | one-line fix |
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
| Fewer than 2 survivors | Abort council; return the single surviving response with a note, or escalate to user |

Never block the entire council on a single seat failure.

## Notes

- Why independent first-pass answers: separate, uncontaminated seats reduce shared-context bias, so agreement becomes meaningful signal and disagreement surfaces blind spots (the Mixture-of-Agents finding).
- When seats strongly agree, treat it as possible correlated bias — not automatic truth — especially if they share a vendor.
- Model discovery and orthogonal seat selection: [references/model-selection.md](references/model-selection.md).
- Specialist personas and panel presets: [references/specialists.md](references/specialists.md).
