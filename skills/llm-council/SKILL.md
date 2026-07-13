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

- **Ensemble mode** — the same bare question goes to N diverse *models* (see [references/model-selection.md](references/model-selection.md)). Pure independence; maximizes error de-correlation. Use for factual/analytical questions where you want blind-spot coverage. The minimal Ensemble is **2 seats — two independent cold reads for a quick second opinion** (two different vendors); 3 is the default.
- **Panel mode** — the question goes to N *specialists* (persona and/or agent lenses; see [references/specialists.md](references/specialists.md)), optionally each on a different model. Deliberately varies framing to get different *kinds* of feedback (concise vs. thorough, coder vs. prose). Use for reviews, designs, and judgment calls.
- **Hybrid** — combine both axes: specialists each seated on a distinct model, varying lens *and* blind spots at once.

All modes keep seat independence (no seat sees another's answer) and use the same chair/synthesis step. Ensemble seats get the task as-is; Panel seats also get a persona preamble.

## Presets (quick invocation)

Lead with a shorthand code: `/llm-council <seats>-<tier> <question>`, where tier is `flag` (flagship) or `horse` (workhorse) — so `3-flag` is three flagships and `2-horse` is two workhorse cold reads. Any `<seats>-<tier>` works; a `2-*` is two cold reads, where disagreement means "look closer," not "majority wins." Named extras: `4-code` (flagships + a light code-tuned 4th lens) and `panel` (Panel mode with review lenses). Vendor priority is Anthropic → OpenAI → Google, so a `2-*` uses Anthropic + OpenAI and a `3-*` adds Google (see [references/model-selection.md](references/model-selection.md)); no preset → `3-flag`.

## Portability (harness adapters)

The packaging (`plugin.json`, `SKILL.md`, `references/`, `.claude-plugin/marketplace.json`) is portable, but the **runtime differs by harness**. Before executing, load [references/model-selection.md](references/model-selection.md) and [references/specialists.md](references/specialists.md), then pick the adapter:

- **VS Code Copilot / Copilot CLI:** spawn seats with the `runSubagent` tool, an explicit `model` (`"Model Name (Vendor)"`), and optional `agentName`. Cross-vendor seats (Anthropic + Google + OpenAI) are available.
- **Claude Code:** seats spawn via the `Task` tool against agents under `.claude/agents/`; models are the Anthropic family only (no `(copilot)` suffix). Cross-vendor Ensemble mode is **not** available — use **Panel mode**, where diversity comes from personas (optionally across Opus / Sonnet / Haiku tiers).
- **No subagent tool at all:** tell the user the council can't run; offer a single-model answer.

## Roles

- **Council members:** N seats that answer independently. A seat is a `(model, persona/agent)` pairing — vary the model (Ensemble), the persona/agent (Panel), or both (Hybrid). Each seat gets the full task (question + any context it needs), plus its persona framing in Panel mode — never another seat's answer or your own take.
- **Chair (synthesizer):** reconciles the seats. **The calling agent chairs by default** — it produced none of the seat answers, so it reads them cold. Spawn a *separate* chair only for a fresh perspective; then use any model that isn't one of the seats (`Auto` or a workhorse is fine). The chair sees the question plus every labeled response.

## The 5-Step Flow

### Step 1 — Select Council

See [references/model-selection.md](references/model-selection.md) for roster discovery and seat selection. Key rules:
- **Default seats** — fill in vendor-priority order:
  1. Anthropic (Opus)
  2. OpenAI (GPT flagship)
  3. Google (Gemini Pro)
  4. Microsoft (MAI-Code) — code lens only

  So **2 seats = 1–2**, **3 seats = 1–3** (the default), **4-code = 1–4**. Resolve names at run time.
- **Lighter / faster:** when the question doesn't need flagship power, drop to the workhorse tier — Sonnet, GPT-5.6 Terra, Gemini 2.5 Pro (same vendor priority).
- **Code-heavy:** the flagships already code best; optionally add a light code-tuned model (MAI-Code) as a cheap 4th lens.
- **Cross-vendor is *preferred, not required*:** a same-vendor multi-tier council (Opus + Sonnet + Haiku) is a valid fallback and the only option on single-vendor harnesses — it shares that vendor's blind spots, so weight its agreement accordingly.
- **Pinning:** resolve roles at run time; name-pin exact models only for reproducibility, and record the resolved names in the footer. See [references/model-selection.md](references/model-selection.md).
- On Copilot harnesses, discover the live roster first via the invalid-model probe; if that fails, ask the user for model names. On Claude Code, the roster is the Anthropic family (see Portability) — use Panel mode.
- A dynamic/auto-routing model (e.g. Copilot `Auto`) may chair but must never hold a seat (non-deterministic).
- Respect the user's explicit model or persona choices if given.
- **Panel/Hybrid mode:** pick specialist lenses from [references/specialists.md](references/specialists.md) (or a preset panel). Optionally pair each with a distinct model, or target an existing agent via `agentName` — but agent names like `eng-code-sub` / `Explore` are examples that may not exist; if absent, fall back to the persona preamble alone.

**If seats cannot be given distinct models** (harness has one model family, or the subagent tool has no `model` parameter): switch to Panel mode so diversity comes from personas. Do NOT silently run every seat on the same default model — that is a fake council with no error de-correlation. If neither distinct models nor personas are possible, tell the user and offer a single-model answer.

Config knobs:
- `council_size`: 2 (two cold reads — a quick second opinion), 3 (default), 4 (code-heavy)
- `models`: explicit list overrides defaults (e.g., `["Claude Opus 4.8 (copilot)", "GPT-5.6 Sol (copilot)", "Gemini 3.1 Pro (Preview) (copilot)"]`) — a manual override can collapse the cross-vendor/tier spread; note that in the footer if it does
- `synthesizer`: chair model, only when spawning a *separate* chair (default: the calling agent itself; else `Auto` or any non-seat model)

**Effort:** you can't set a seat's reasoning effort. For more depth, pick a higher tier (a flagship reasons more than a mini) or ask for it in the prompt.

### Step 2 — Fan-Out (Independent Answering)

Spawn one seat per council member (see Portability for the per-harness call). Run them all in parallel.

**Guardrails — include vs. withhold.** Give every seat the same, complete task: the question plus whatever context it needs to answer well. Don't starve a seat for the sake of "purity" — embedding the task's data is expected. Withhold only the contaminants: other seats' answers, your own opinion or the conclusion you expect, and hints about what you want to hear. A tool-using seat can pull its own extra context — fine, but it makes seats less independent, so in **Ensemble** mode prefer plain model seats and don't seat agent-backed (`agentName`) ones.

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
  - Write each seat to its own **uniquely named** file (e.g. `<seat-model-or-persona>.md`); tell the seat to write ONLY its own file and never read the council directory, so seats still can't see each other.
  - Location: if an `.eng/` directory exists at the workspace root, use the active workstream's `council/<date>-<slug>/` (or `.eng/council/<date>-<slug>/` when no workstream is active); otherwise a path the user names, or inline when small.
  - Collect the paths so the chair (Step 4) can read the full artifacts.

If a seat fails or times out: log it, continue with survivors (minimum 2). One failure never blocks the council.

### Step 3 — Collect

Gather every successful response and keep it **labeled** with its seat (model, and persona in Panel mode). Don't anonymize or shuffle — the chair needs identities to attribute stances and show who agrees with whom.

### Step 4 — Synthesize (Chair Step)

The chair (usually you — see Roles) reads the question and every labeled response, and returns two things:

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

Strong agreement can be correlated bias rather than confirmation — especially among same-vendor seats.
