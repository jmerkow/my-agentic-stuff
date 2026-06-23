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

Two-pass system for detecting AI slop in text:
1. **Mechanical lint** — script flags known sloppy words/phrases with line numbers
2. **Agent review** — contextual judgment the linter can't do

## Bundled Resources

- **[slop_lint.py]** — Python linter script. Requires pyyaml. Run via `uv run scripts/slop_lint.py` (auto-provisions dep) or ensure pyyaml is installed in the active environment.
- **[slop-words.yaml]** — Flat list of rules, each tagged with a rule ID and level.

[slop_lint.py]: scripts/slop_lint.py
[slop-words.yaml]: references/slop-words.yaml

## Workflow

### Step 1: Run the linter

Run [slop_lint.py] on the target file:

```bash
python <path-to-slop_lint.py> <file>
```

Options:
- `--format json` — machine-readable output
- `--text "inline text"` — lint a string directly

The linter reads patterns from [slop-words.yaml]. Each finding includes a rule ID (category), level, line number, matched text, and a fix suggestion.

### Step 2: Agent review pass

After running the linter, do a manual read-through checking for issues the regex can't catch:

1. **Vagueness** — Paragraphs with no specific names, dates, numbers, or examples. Every claim should be verifiable or grounded.
2. **Information gain** — After reading each paragraph, is there something new? If you could delete it and lose nothing, flag it.
3. **Tone mismatch** — Overly formal language in casual contexts (or vice versa). Hedging everything to avoid commitment.
4. **Structural slop** — Formulaic intro that restates the topic. Excessive "on one hand / on the other hand" balance. Everything in bullet lists when prose would be clearer.
5. **Unearned profundity** — Dramatic single-sentence reveals ("Something shifted."), fortune-cookie wisdom, platitudes dressed as insight.
6. **Uncited authority** — "Studies show…" or "Research indicates…" without naming the study. "Experts agree" without naming experts.

### Step 3: Produce a report

Combine linter output and agent findings into a single report. Group by severity.

For each finding:
- Quote the problematic text
- State the issue (one line)
- Suggest a concrete fix or flag for author decision

### Step 4: Fix (if requested)

When fixing, follow these rules:

- **High severity** — Fix or delete unless there's an explicit justification. If the slop word is genuinely the right word (e.g., "leverage" for financial leverage, "journey" for actual travel), keep it and add a brief inline comment noting it's intentional.
- **Medium severity** — Fix the obvious ones. For borderline cases, note them but don't force a change.
- **Low severity** — Fix only if there's a clear better word. Don't over-correct — personality and style matter.
- **Never** introduce new slop while fixing old slop.
- **Preserve voice** — The goal is clarity and substance, not sterile prose.

#### Em dashes

Em dashes flag at `info` level. Bold lead-in labels like `**Label** —` are exempt and will not fire. When an em dash is flagged, do NOT mechanically substitute a comma, semicolon, or period. The dash is almost always there because two clauses have a real relationship. Rephrase the sentence so that relationship is expressed without the dash.

- ❌ `This was hard — we shipped anyway.`
- ✅ `Despite the difficulty, we shipped on schedule.`

## Level Guide

Each finding carries a **rule ID** (the category, e.g. `fake-authority`, `em-dash-prose`) and a **level** tag. Multiple rule IDs can share a level. Output is grouped by rule ID, sorted highest level first.

| Level | Meaning | Action |
|-------|---------|--------|
| 🔴 High | Almost always slop. Dead openers, fake authority, fortune-cookie wisdom. | Fix, delete, or explicitly justify. |
| 🟡 Medium | Frequently sloppy but sometimes defensible. Buzzwords, weasel words, hedging. | Review and fix obvious cases. |
| 🔵 Low | Style nits. Overused but not inherently bad. | Fix in aggregate; ignore in isolation. |
| ⚪ Info | Not wrong on its own. Em dashes, fancy unicode, etc. | Be aware, do not overuse. Only act when density is high. |

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
  level: medium
  pattern: "\\bsome-regex\\b"
  suggestion: "Better alternative."
  note: "Optional — when the word is acceptable."
  unless: "\\bcontextual-exemption\\b"
```

Fields: `rule` (stable kebab-case ID), `level` (`high`/`medium`/`low`/`info`), `pattern` (Python regex, case-insensitive), `suggestion` (fix guidance), `note` (optional context), `unless` (optional per-line exemption regex — if it matches the line, the rule is skipped for that line).

Always include `\b` word boundaries for single-word patterns to avoid false positives.
