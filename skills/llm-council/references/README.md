# Model cards — how they were made

[model-cards.yaml](model-cards.yaml) has one entry per model with two kinds of data:

- **Grounded facts** — `tier`, `cost` (credits per 1M tokens, in/out), `context`, `vision`. Observed from the harness roster and pricing on 2026-07-13.
- **`stats`** — subjective quality ratings (1–10) for reasoning, coding, prose, math, knowledge, plus an `overall` mean. **Opinions, not benchmarks.**

## How `stats` were produced

A 3-model self-poll on 2026-07-13. Three cross-vendor flagships — Claude Opus 4.8, Gemini 3.1 Pro (Preview), GPT-5.6 Sol — each independently rated all 12 models (including themselves) on the five dimensions, 1–10. The published `stats` are the mean of the three ballots.

Raw per-councilor ballots: `.eng/workstreams/llm-council/ratings/2026-07-13-<rater>.md` (kept in the workstream, not shipped with the plugin).

## Caveats

- Ratings are opinions, not measurements; self-ratings showed mild inflation (~+0.5).
- They drift as models change.

## Regenerate

Run an Ensemble council (see the `llm-council` skill) with the current roster and the same five dimensions, one ballot per rater, then average. Refresh the grounded facts from a discovery probe + the pricing table.
