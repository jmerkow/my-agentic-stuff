---
name: slop-check
description: >
  Detect and fix AI slop in text — vague filler, fake authority, clichés, buzzwords,
  and structural patterns that signal low-value AI-generated content.
  Use when reviewing, editing, or writing any prose: docs, blog posts, emails,
  summaries, weekly updates, READMEs, or marketing copy.
  Keywords: slop, AI slop, cliché, filler, buzzwords, writing quality, lint, review text.
---

# Slop Check

Focused system for detecting AI slop in text:
1. **Phrase lint**: flags known sloppy words and phrases with line numbers
2. **Structure lint**: flags formulaic prose shapes with line numbers
3. **Agent review**: applies contextual judgment the linters can't do

## Bundled Resources

- **[slop_lint.py]**: Thin wrapper for the `slop-lint` package command.
- **[slop_structure_lint.py]**: Thin wrapper for the `slop-structure-lint` package command.
- **[slop-words.yaml]**: Phrase rules with regex patterns, suggestions, and fix types.
- **[slop-structure.yaml]**: Structure rules with check algorithm metadata, thresholds, patterns, suggestions, and fix types.
- **[slop-fix-types.yaml]**: Controlled vocabulary for `fix_type` values, with descriptions only.

[slop_lint.py]: scripts/slop_lint.py
[slop_structure_lint.py]: scripts/slop_structure_lint.py
[slop-words.yaml]: references/slop-words.yaml
[slop-structure.yaml]: references/slop-structure.yaml
[slop-fix-types.yaml]: references/slop-fix-types.yaml

## Workflow

### Step 1: Run the phrase linter

From the slop-check project, run the phrase linter on the target file:

```bash
uv run --project <path-to-slop-check> slop-lint <file>
```

Options:
- `--format json` — machine-readable output
- `--text "inline text"` — lint a string directly
- `--patterns <path>` — use a custom phrase-rule YAML file
- `--fix-types <path>` — use a custom fix-type YAML file

The linter reads patterns from [slop-words.yaml]. Each finding includes a rule ID (category), level, fix type, line number, matched text, and a fix suggestion.

### Step 2: Run the structure linter

Run the structure linter when reviewing longer prose or suspected AI-shaped writing:

```bash
uv run --project <path-to-slop-check> slop-structure-lint <file>
```

Options:
- `--format json` — machine-readable output
- `--text "inline text"` — lint a string directly
- `--rules <path>` — use a custom structure-rule YAML file
- `--fix-types <path>` — use a custom fix-type YAML file

The structure linter reads [slop-structure.yaml]. Keep rule metadata and `check` algorithm selectors in YAML where practical; Python should only implement the small registry of available structure-check algorithms.

Both linters validate each rule's `fix_type` against [slop-fix-types.yaml]. The vocabulary contains descriptions only; concrete edit guidance stays in each rule's `suggestion`.

### Step 3: Agent review pass

After running the linter, do a manual read-through checking for issues the regex can't catch:

1. **Vagueness** — Paragraphs with no specific names, dates, numbers, or examples. Every claim should be verifiable or grounded.
2. **Information gain** — After reading each paragraph, is there something new? If you could delete it and lose nothing, flag it.
3. **Tone mismatch** — Overly formal language in casual contexts (or vice versa). Hedging everything to avoid commitment.
4. **Structural slop** — Formulaic intro that restates the topic. Excessive "on one hand / on the other hand" balance. Everything in bullet lists when prose would be clearer.
5. **Unearned profundity** — Dramatic single-sentence reveals ("Something shifted."), fortune-cookie wisdom, platitudes dressed as insight.
6. **Uncited authority** — "Studies show…" or "Research indicates…" without naming the study. "Experts agree" without naming experts.

### Step 4: Produce a report

Combine linter output and agent findings into a single report. Group by numeric level.

For each finding:
- Quote the problematic text
- State the issue (one line)
- Suggest a concrete fix or flag for author decision

### Step 5: Fix (if requested)

When fixing, follow these rules:

- **Level 3**: Fix or delete unless there's an explicit justification. If the slop word is genuinely the right word (e.g., "leverage" for financial leverage, "journey" for actual travel), keep it and add a brief inline comment noting it's intentional.
- **Level 2**: Fix the obvious ones. For borderline cases, note them but don't force a change.
- **Level 1**: Fix only if there's a clear better word. Don't over-correct, personality and style matter.
- **Never** introduce new slop while fixing old slop.
- **Preserve voice** — The goal is clarity and substance, not sterile prose.

#### Em dashes

Em dashes flag at `level: 0`. Bold lead-in labels like `**Label** —` are exempt and will not fire. When an em dash is flagged, do NOT do a punctuation swap (`—` → `,`/`;`/`.`). That misses the real issue. Figure out whether the ideas belong together, then express that relationship directly:

1. Integrate both ideas into one natural sentence when they belong together.
2. Split into two sentences only when the clauses are genuinely independent.
3. Turn a mid-sentence definition into a parenthetical or a colon list.

A comma, semicolon, or period is a last resort only after a real rewrite.

- ❌ `This was hard — we shipped anyway.`
- ✅ `Despite the difficulty, we shipped on schedule.`

## Level Guide

Each finding carries a **rule ID** (the category, e.g. `fake-authority`, `em-dash-prose`) and a numeric **level**. Multiple rule IDs can share a level. Text output is grouped by level (highest first), then by rule ID; within a rule, findings that share a suggestion are collapsed into one entry that lists every location.

| Level | Meaning | Action |
|-------|---------|--------|
| 3 high | Almost always slop. Dead openers, fake authority, fortune-cookie wisdom. | Fix, delete, or explicitly justify. |
| 2 medium | Frequently sloppy but sometimes defensible. Buzzwords, weasel words, hedging. | Review and fix obvious cases. |
| 1 low | Style nits. Overused but not inherently bad. | Fix in aggregate; ignore in isolation. |
| 0 info | Not wrong on its own. Em dashes, fancy unicode, etc. | Be aware, do not overuse. Only act when density is high. |

## The Antidote Checklist

Good writing that avoids slop has these properties — use as a positive check:

- **Specificity** — Named people/places, dates, numbers. Fact-checkable claims.
- **Lived experience** — Personal stakes, failures, lessons from doing the thing.
- **Cited sources** — Named studies, linked references, attributed quotes.
- **Information gain** — Reader learns something new. Can summarize what was added.
- **Clear stance** — Opinions backed by reasoning, not safe platitudes.

## Updating Patterns

Add new slop patterns to [slop-words.yaml]:

```yaml
- rule: my-rule-id
  level: 2
  fix_type: rewrite
  pattern: "\\bsome-regex\\b"
  suggestion: "Better alternative."
  note: "Optional — when the word is acceptable."
  unless: "\\bcontextual-exemption\\b"
```

Fields: `rule` (stable kebab-case ID), `level` (`0` info, `1` low, `2` medium, `3` high), `fix_type` (key from [slop-fix-types.yaml]), `pattern` (Python regex, case-insensitive), `suggestion` (fix guidance), `note` (optional context), `unless` (optional per-line exemption regex; if it matches the line, the rule is skipped for that line).

`fix_type` must be one of the keys defined in [slop-fix-types.yaml]. Add a new fix type there only when existing edit intents do not fit; keep rule-specific fixes in `suggestion`.

Always include `\b` word boundaries for single-word patterns to avoid false positives.

Add structure rules to [slop-structure.yaml]. Keep rule metadata, `check` algorithm selectors, thresholds, and regex patterns there; only add Python code when a structure needs a new algorithm.
