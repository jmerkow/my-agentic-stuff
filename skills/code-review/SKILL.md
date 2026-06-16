---
name: code-review
description: Local code-quality review — dual sub-agent review with human triage. Use when reviewing source code for style, slop, and structural issues without opening a PR.
---

# Code Review — Local Review Workflow

Identifies code-quality issues (style, slop, structure) via dual independent sub-agent review, then surfaces findings for human triage. All local, no PR required.

## Phase 1 — Discovery

Before reviewing, the orchestrator maps the codebase into **functional groups**. This is not hardcoded — it's discovered each time.

1. **Scan the target directory.** List all source and config files.
2. **Identify functional groups** by reading directory structure, imports, and file responsibilities. Group by concern — whatever natural boundaries the codebase has. Aim for ≤1000 LOC per group.
3. **Map dependencies between groups.** Note which groups import from or depend on others — this informs review order (review dependencies before dependents).
4. **Produce a group manifest** listing each group with its files, approximate LOC, and dependency edges.

### Gate: User confirms grouping

Present the manifest and **stop**. Do not proceed to Phase 2 until the user explicitly approves the groups. The user may merge, split, reorder, or exclude groups. Adjust and re-present if changes are requested.

## Phase 2 — Review (Dual Sub-Agent)

Process groups **one at a time**, in dependency order. For each group:

1. **Dispatch Sub-agent A** — `eng-code-sub` (required). Uses the review prompt in [references/review-prompt.md](references/review-prompt.md).
2. **Dispatch Sub-agent B** — orchestrator's choice (e.g., a language-specific agent, a second `eng-code-sub` instance, or the default agent). Uses the same review prompt.
3. Both receive the same file contents and checklist. Neither sees the other's output.
4. **Merge** findings when both return (see Merge below).
5. **Write the review file** for this group immediately — don't wait for other groups.
6. **Notify the user** that the file is ready for triage, then proceed to the next group.

The user can begin triaging one group's findings while the orchestrator reviews the next. This keeps the pipeline flowing.

### Merge

When both agents return, the orchestrator merges their findings:

- **Agreement** — both flagged the same issue (same file, same lines, same concern). Consolidate into one finding, note "flagged by both reviewers."
- **Unique** — only one agent flagged it. Include as-is, attributed to the reviewer that found it.
- **Disagreement** — both flagged the same location but with different assessments (e.g., one says `fix`, the other says `nit`, or they identify different problems on the same lines). Present both assessments side-by-side and let the user decide.

### Output

Write merged findings to a review file. Use the format in [references/output-format.md](references/output-format.md).

File naming: `<group-slug>-review.md` (e.g., `model-core-review.md`). When combining small groups, join the slugs (e.g., `config-and-meta-review.md`).

Output location: `.eng/scratch/reviews/` (or a user-specified directory).

## Phase 3 — Triage (Human Gate)

The user reviews each finding file and fills in the response blockquote. Responses are freeform — the user may accept, reject, ask questions, add context, or note something for later. The orchestrator does not prescribe a vocabulary.

This phase is conversational. If the user asks a question about a finding, the orchestrator answers and the user updates their response. Iterate until the user is satisfied with each finding before moving on.

### Status tagging

Once a finding has a final disposition (accepted, rejected, or deferred), the orchestrator adds a status emoji to the finding heading:

- **✅** — Accepted. A Change Request will be written.
- **⏳** — Deferred. Acknowledged but not actionable now (e.g., WIP dependency, future work).
- **❌** — Rejected / no action. The user disagrees or considers it not worth changing.

Findings without a status tag still need triage. This lets the user scan headings and immediately see what's resolved vs what needs attention.

If the user asked a question, the orchestrator adds a **Reviewer note** below the user's response with the answer. Once the user confirms a final disposition (even implicitly), the tag is applied.

### Change Requests

After all findings in a group are triaged, the orchestrator appends a `## Change Requests` section to the review file. Each CR distills one or more accepted findings into an implementation instruction:

- **One CR per logical change.** Related findings can merge into one CR (e.g., if R2 and R5 interact).
- **Name the file(s), the action, and enough detail** for an implementing agent to execute without re-reading the findings or guessing.
- **Pin exact signatures, preserve attributes** — if a refactor changes a function signature, specify the new one. If it removes code that other code depends on, say what happens to the dependent.
- **Cross-check CR interactions** — if CR1 removes an import that CR2 re-introduces, resolve the conflict in the CR text.

Optionally, dispatch `eng-code-sub` to validate CR clarity before finalizing. The sub-agent reads the CRs and the source files, then reports **CLEAR** or **UNCLEAR** per CR. Fix any unclear CRs before considering triage complete.

See [references/output-format.md](references/output-format.md) for the CR block template.

## Checklist

The procedure checklist in [references/checklist.md](references/checklist.md) is a quick-reference for the orchestrator — the step-by-step gates for each phase. The review rules themselves live in [references/review-prompt.md](references/review-prompt.md).

## Output Format

See [references/output-format.md](references/output-format.md) for the full finding block spec, including the user response field.

## Rules

- Phase 2 is read-only. Never edit files during review.
- Findings are style/slop only. Don't flag functional bugs (that's a different review).
- Empty findings are fine — say "no issues found" rather than manufacturing findings.
- One finding per issue. Don't bundle unrelated problems.
- Both sub-agents MUST run independently. Don't feed one agent's output to the other.
- The merge step belongs to the orchestrator, not the sub-agents.
