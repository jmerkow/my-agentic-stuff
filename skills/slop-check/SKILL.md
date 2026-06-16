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

- **[slop_lint.py]** — Python linter script. No external dependencies.
- **[slop-words.yaml]** — Pattern definitions.

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

The linter reads patterns from [slop-words.yaml]. Each finding includes line number, matched text, and a fix suggestion. Treat every finding as a candidate for review — the linter doesn't judge, you do.

### Step 2: Agent review pass

After running the linter, do a manual read-through checking for issues the regex can't catch:

1. **Vagueness** — Paragraphs with no specific names, dates, numbers, or examples. Every claim should be verifiable or grounded.
2. **Information gain** — After reading each paragraph, is there something new? If you could delete it and lose nothing, flag it.
3. **Tone mismatch** — Overly formal language in casual contexts (or vice versa). Hedging everything to avoid commitment.
4. **Structural slop** — Formulaic intro that restates the topic. Excessive "on one hand / on the other hand" balance. Everything in bullet lists when prose would be clearer.
5. **Unearned profundity** — Dramatic single-sentence reveals ("Something shifted."), fortune-cookie wisdom, platitudes dressed as insight.
6. **Uncited authority** — "Studies show…" or "Research indicates…" without naming the study. "Experts agree" without naming experts.

### Step 3: Produce a report

Combine linter output and agent findings into a single report.

For each finding:
- Quote the problematic text
- State the issue (one line)
- Suggest a concrete fix or flag for author decision

### Step 4: Fix (if requested)

When fixing, follow these rules:

- **Default to fixing** unless the matched word is genuinely the right one (e.g., "leverage" for financial leverage, "journey" for actual travel). Note intentional uses inline.
- **Never** introduce new slop while fixing old slop.
- **Preserve voice** — the goal is clarity and substance, not sterile prose.
- **Em dashes and ` - `** — see triage rules below.

## Em dash / spaced hyphen triage

The linter flags every line containing an em dash (`—`) or a mid-sentence ` - ` (bullets are skipped). It does **not** judge — you do. Apply these rules:

**Fix (replace with comma, colon, period, or parens):**
- Em dash used as sentence punctuation. *"This was hard — we shipped anyway."*
- Em dash inside a sentence joining clauses. *"The result — a 30% lift — surprised us."*
- Multiple em dashes on one line.
- Mid-sentence ` - ` standing in for an em dash.

**Keep:**
- `**Label** - details` — bold-label-then-detail pattern, especially in lists or definition-style prose.
- `Label — details` at the start of a bullet or paragraph where the dash separates the label from its expansion.
- Numeric ranges (`5 - 10`, though `5–10` or `5-10` is cleaner).

**Default action:** if you're not sure, fix it. AI overuses em dashes; humans rarely use them at all.

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
- pattern: "\\bsome-regex\\b"
  suggestion: "Better alternative."
  note: "Optional — when the word is acceptable."
```

Patterns are Python regexes matched case-insensitively. Always include `\b` word boundaries for single words to avoid false positives.
