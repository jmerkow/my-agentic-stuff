---
name: plan-deck
description: Research and write a standalone, information-dense deck report with complete narrative, evidence, tables, citations, and diagrams embedded in the report. Use before building a presentation or when the user needs the durable source document behind a deck. The report is not a slide outline and does not prescribe bullets or layouts. Keywords presentation planning, deck research, deck report, presentation brief, diagrams, evidence.
---

# plan-deck

Create `deck-report.md`: a standalone report that gives a cold reader the complete argument, evidence, context, qualifications, and diagrams needed to understand the subject without opening a presentation or companion document.

The report is durable source material for either `build-deck-svg` or `build-deck-pptx`. It is also useful on its own.

## Output contract

- Write one self-contained Markdown report.
- Organize it as a report, not as slides or a slide outline.
- Explain what matters in detailed prose. Do not pre-compress findings into presentation bullets.
- Put complete tables and exact values in the report.
- Create diagrams in the report instead of describing diagrams someone should make later.
- Use inline Mermaid for diagrams whenever it can express the relationship faithfully, so the diagram source remains inside the report.
- Cite claims where a reader can verify them. Distinguish sourced facts, interpretation, and unresolved questions.
- Include enough surrounding context to preserve caveats and prevent misleading compression during deck generation.

The report must not prescribe slide count, slide titles, layouts, bullet wording, object strategy, colors, fonts, or spacing. Those are decisions for the selected build skill.

## Workflow

1. **Frame the work** — identify the audience, purpose, decision or understanding sought, scope, and questions the report must answer.
2. **Gather evidence** — read supplied materials and retrieve missing authoritative sources. Record source links or repository paths as you work.
3. **Find the argument** — determine the central conclusion, supporting findings, meaningful counterevidence, and what remains uncertain.
4. **Write the report** — develop the reasoning in information-dense prose. State concrete details, numbers, causes, consequences, and qualifications.
5. **Construct diagrams** — create an inline diagram for every relationship that is materially clearer visually: process, architecture, chronology, hierarchy, dependency, feedback loop, or comparison.
6. **Add evidence structures** — include complete tables, data definitions, and chart-ready values where they support the findings.
7. **Cold-read review** — verify that the report stands alone, diagrams are explained in nearby prose, terms are defined, sources are traceable, and no section assumes access to a future deck.
8. **Writing review** — run `slop-check` when available and remove vague claims, filler, fake quotations, and unsupported certainty.

## Diagram rules

- Make the diagram; never leave instructions such as “add a workflow diagram here.”
- Keep Mermaid source in the report. Do not require a separate diagram file to understand the report.
- Give each diagram a descriptive heading and explain the takeaway immediately before or after it.
- Label nodes and edges with domain language, not generic placeholders.
- Encode a real relationship. Decorative boxes are not a diagram.
- Prefer flowcharts for processes and architecture, sequence diagrams for interactions, state diagrams for lifecycle behavior, and timelines for chronology.
- If Mermaid cannot represent the subject faithfully, embed the completed visual in the report and include the underlying data or source description nearby.

## Prose rules

- Lead sections with the conclusion or important finding, then support it with detail.
- Use paragraphs for reasoning and explanation.
- Use lists only for genuinely enumerable items, not as a substitute for analysis.
- Include exact numbers, dates, names, definitions, and limitations when available.
- Explain why evidence matters instead of merely cataloging it.
- Preserve disagreement and uncertainty rather than forcing false consensus.

## Resources

- `references/report-format.md` — required report structure and quality bar
- `templates/deck-report-template.md` — starting point for the standalone report

## Companion skills

- **`slop-check`** (if available) — use for the final prose pass.
- **`build-deck-svg`** — choose when visual control and diffable slide source matter most.
- **`build-deck-pptx`** — choose when native PowerPoint editability matters most.
