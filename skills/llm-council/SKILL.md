---
name: llm-council
description: >
  Run an LLM council: pose a question to multiple orthogonal models and/or specialist
  personas in parallel via runSubagent, anonymize and synthesize the responses with a
  separate chair model. Use when the user wants diverse model perspectives, a panel of
  specialist lenses (concise, skeptic, coder, prose), or cross-model review of a
  high-stakes or ambiguous question, or asks to ask the council, panel, or multiple models.
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

## Roles

- **Council members:** N seats that answer independently. A seat is a `(model, persona/agent)` pairing — vary the model (Ensemble), the persona/agent (Panel), or both (Hybrid). Each seat sees ONLY the question (plus its own persona framing in Panel mode), never another seat's answer.
- **Chair (synthesizer):** A separate model from a different vendor than the council majority. Receives the original question plus all anonymized responses. Never holds a council seat.

## The 5-Step Flow

### Step 1 — Select Council

See [references/model-selection.md](references/model-selection.md) for roster discovery and seat selection. Key rules:
- Default 3-seat council: Claude Sonnet 4.6 + Gemini 2.5 Pro + GPT-5.5 (cross-vendor, mid-tier)
- Default 4-seat for code-heavy questions: add MAI-Code-1-Flash
- Discover the live roster first via the invalid-model probe; treat seats as roles, not fixed names
- `Auto` may chair but must never hold a council seat
- Respect the `model` parameter override if the user specified seats explicitly
- **Panel/Hybrid mode:** pick specialist lenses from [references/specialists.md](references/specialists.md) (or a preset panel there); optionally pair each with a distinct model, or target an existing agent (e.g. `eng-code-sub`, `Explore`) via `agentName`

**If `runSubagent` does not accept a `model` parameter in your environment:** ask the user for explicit model names, or fall back to the default agent (no override) and note that diversity is reduced.

Config knobs:
- `council_size`: 3 (default), 4 for code-heavy
- `models`: explicit list overrides defaults (e.g., `["Claude Sonnet 4.6 (copilot)", "Gemini 2.5 Pro (copilot)", "GPT-5.5 (copilot)"]`)
- `synthesizer`: model for the chair step (default: `Auto` or a model from a different vendor than the council majority)

### Step 2 — Fan-Out (Independent Answering)

Spawn one `runSubagent` call per council seat. Run ALL in parallel.

**Critical invariant — no cross-contamination:** No seat ever sees another seat's answer, your synthesis reasoning, or context the user didn't provide. This holds in every mode.

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
1. **Synthesized answer** (the chair's output, presented as the primary response)
2. **Appendix — Council Details:**
   - Council composition: which models were seated and which was the chair (de-anonymized for the user)
   - Per-model responses: the original (un-anonymized) responses, labeled by model name
   - If any seat failed: note which model failed and that it was excluded from synthesis

## Graceful Degradation

| Situation | Action |
|---|---|
| A seat times out | Note the failure; continue with survivors |
| A seat returns an error | Note the failure; continue with survivors |
| Only 2 survivors | Synthesize from 2 (note reduced council in appendix) |
| Fewer than 2 survivors | Abort council; return the single surviving response with a note, or escalate to user |

Never block the entire council on a single seat failure.

## Notes

- **Member isolation is not automatic.** If members run as a full agent with tool access, they may read the repo or pull in extra context — grounded, but a deviation from strict context isolation. For a faithful cold-read council, constrain members to answering from the bare question only.
- Independence rationale (why no cross-contamination): Mixture of Agents (Wang et al. 2024) — cross-provider diversity outperforms single-provider ensembles.
- Anonymization rationale: LLM-as-a-Judge (Zheng et al.) — randomizing order and stripping labels prevents position bias and self-enhancement bias.
- Model discovery and orthogonal seat selection: [references/model-selection.md](references/model-selection.md).
- Specialist personas and panel presets: [references/specialists.md](references/specialists.md).
