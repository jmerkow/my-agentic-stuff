---
name: llm-council
description: >
  Run an LLM council: pose a question to multiple orthogonal models and/or specialist
  personas in parallel (via the harness's subagent tool), anonymize and synthesize the
  responses with a separate chair model. Use when the user wants diverse model
  perspectives, a panel of specialist lenses (concise, skeptic, coder, prose), or
  cross-model review of a high-stakes or ambiguous question, or asks to ask the council,
  panel, or multiple models.
  Keywords: council, panel, specialists, personas, multiple models, diverse perspectives,
  ensemble, model comparison, cross-model review, fan-out, synthesize.
---

# LLM Council

Structured multi-model review: fan out one question to N independent models, anonymize and shuffle the responses, then have a chair model from a different vendor synthesize them into a single grounded answer.

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
- **Chair (synthesizer):** A model that did NOT produce any council answer — never one of the seats. Prefer a different vendor than the council; when there is no majority (e.g. the 3-vendor default) or only one vendor is available (Claude Code), pick any model/tier not used as a seat and note the reduced separation. Receives the question plus all anonymized responses.

## The 5-Step Flow

### Step 1 — Select Council

See [references/model-selection.md](references/model-selection.md) for roster discovery and seat selection. Key rules:
- Default council = 3 cross-vendor mid-tier **roles**: an Anthropic mid-tier + a Google Pro + an OpenAI current model; add a code-specialist 4th seat for code-heavy work. Resolve roles to concrete names at discovery time — do not hardcode.
- On Copilot harnesses, discover the live roster first via the invalid-model probe. On Claude Code, the roster is the Anthropic family (see Portability) — use Panel mode.
- A dynamic/auto-routing model (e.g. Copilot `Auto`) may chair but must never hold a seat (non-deterministic).
- Respect the user's explicit model or persona choices if given.
- **Panel/Hybrid mode:** pick specialist lenses from [references/specialists.md](references/specialists.md) (or a preset panel). Optionally pair each with a distinct model, or target an existing agent via `agentName` — but agent names like `eng-code-sub` / `Explore` are examples that may not exist; if absent, fall back to the persona preamble alone.

**If seats cannot be given distinct models** (harness has one model family, or the subagent tool has no `model` parameter): switch to Panel mode so diversity comes from personas. Do NOT silently run every seat on the same default model — that is a fake council with no error de-correlation. If neither distinct models nor personas are possible, tell the user and offer a single-model answer.

Config knobs:
- `council_size`: 3 (default), 4 for code-heavy
- `models`: explicit list overrides defaults (e.g., `["Claude Sonnet 4.6 (copilot)", "Gemini 2.5 Pro (copilot)", "GPT-5.5 (copilot)"]`)
- `synthesizer`: model for the chair step (default: `Auto` or a model from a different vendor than the council majority)

### Step 2 — Fan-Out (Independent Answering)

Spawn one `runSubagent` call per council seat. Run ALL in parallel.

**Critical invariant — no cross-contamination:** No seat ever sees another seat's answer, your synthesis reasoning, model identity, or context the user didn't provide. This holds in every mode. Isolation is NOT automatic: a full-agent seat with tool access may read the repo or search the web, quietly re-correlating the seats. For a faithful Ensemble, pass only the question text and prefer non-agentic (persona-only) seats; reserve tool-using agent seats for Panel mode, where framing is deliberately varied.

The `model` parameter format is `"Model Name (Vendor)"` — e.g., `"Claude Sonnet 4.6 (copilot)"`. For agent-backed seats, also set `agentName` (e.g. `eng-code-sub`).

**Ensemble-mode member prompt (bare question only):**
```
{user_question}
```
No preamble, no framing — the question only.

**Panel-mode member prompt (persona preamble + question):**
```
{persona_preamble}

{user_question}
```
The persona preamble (from [references/specialists.md](references/specialists.md)) is the ONLY framing added, and it is per-seat. Never add your own opinions or another seat's answer.

If a seat fails or times out: log it as failed, continue with survivors. Proceed to synthesis with a minimum of 2 surviving responses. One failure never blocks the council.

### Step 3 — Collect and Anonymize

After all parallel calls return (or time out with degradation applied):

1. Collect all successful responses.
2. Shuffle the response order randomly.
3. Label them Response A, Response B, Response C (etc.).
4. **Strip model identity** — the chair must not know which model produced which response.

Shuffling prevents position bias (LLM-as-a-Judge literature shows models prefer the first response when order is fixed). Anonymizing prevents self-enhancement bias (a model biased toward its own outputs if it can recognize them).

### Step 4 — Synthesize (Chair Step)

Call `runSubagent` with the chair model and the synthesis prompt below. The chair has NOT generated any of the constituent answers — it approaches them cold.

**Chair/synthesizer prompt template:**
```
You are synthesizing independent responses from multiple AI models to the following
question. Your role is to produce a single, well-grounded answer that is more
accurate and complete than any individual response.

Instructions:
1. Identify CONSENSUS — where models agree, the answer is likely reliable.
2. Identify DISAGREEMENTS — flag these explicitly and reason about which position
   is more defensible.
3. Identify UNIQUE CONTRIBUTIONS — insights or caveats present in only one response
   that add value.
4. Do not simply pick the most confident response. Synthesize.
5. Attribute significant claims to "multiple models" (if consensus) or
   "one model" (if unique or disputed). Do not speculate about which model.

Original question:
{question}

Independent responses (anonymized — do not speculate about model identity):
--- Response A ---
{response_a}

--- Response B ---
{response_b}

--- Response C ---
{response_c}
---

Synthesize your response now.
```

Adapt the number of `--- Response X ---` blocks to the actual number of survivors.

### Step 5 — Present

Return to the user:
1. **Synthesized answer** (the chair's output, as the primary response)
2. **Appendix — Council Details (compact by default):**
   - Council composition: which models/personas were seated and which chaired
   - Any seat that failed and was excluded
   - Full per-seat responses only when the user asks, the question is high-stakes, or the seats materially disagree — otherwise a one-line-per-seat gist

Anonymization (Step 3) is only for the chair; the appendix may name models unless the user asked for a blind review.

## Graceful Degradation

| Situation | Action |
|---|---|
| A seat times out | Note the failure; continue with survivors |
| A seat returns an error | Note the failure; continue with survivors |
| Only 2 survivors | Synthesize from 2 (note reduced council in appendix) |
| Fewer than 2 survivors | Abort council; return the single surviving response with a note, or escalate to user |

Never block the entire council on a single seat failure.

## Notes

- Why independent first-pass answers: separate, uncontaminated seats reduce shared-context bias, so agreement becomes meaningful signal and disagreement surfaces blind spots (the Mixture-of-Agents finding). Why anonymize + shuffle for the chair: it removes position and self-enhancement bias (the LLM-as-a-Judge finding).
- When seats strongly agree, treat it as possible correlated bias — not automatic truth — especially if they share a vendor.
- Model discovery and orthogonal seat selection: [references/model-selection.md](references/model-selection.md).
- Specialist personas and panel presets: [references/specialists.md](references/specialists.md).
