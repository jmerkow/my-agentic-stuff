# Slide spec format

The spec is markdown. One H2 per slide. Each slide has a small set of structured fields the agent fills in before writing the SVG.

## Why

Writing prose first surfaces the slide's argument before you sink time into layout. A bad bullet on paper is a bad bullet on a slide.

## Structure

````markdown
## Slide N — <short title>
- **Layout:** one line describing the visual shape (e.g. "two columns, chart left, bullets right")
- **Headline / subtitle:** the slide's argument in one sentence
- **Content blocks:**
  - bullets / tables / table-rows / numbered lists, structured by section
- **Visuals:** chart paths, photo paths, asset notes
- **Artifact sources:** absolute or repo-relative paths to source data
- **Talking points:** what the slide is about, context for the spec, NOT shown to the audience or speaker
- **Speaker notes:** compact glance-able cues for the live presenter; exported to `.pptx` notes pane
- **Status:** ✅ ready / ⚠️ needs data / ❌ blocked
````

End the spec with an **asset checklist** table summarizing every chart, photo, and external doc the deck depends on, with a status column. It's the at-a-glance "what's blocking the deck" view.

```markdown
## Asset checklist

| Asset | Slide | Status |
|---|---|---|
| Vuln burndown stacked-area chart | 8b | ✅ rendered |
| UW workshop photos | 11 | ⚠️ need permissions |
```

## Conventions

- Numbers in the spec must be the numbers on the slide. If you don't have them yet, mark `[TBD]` and status ⚠️.
- Bullets in the spec should be short, declarative, and shippable as the slide's actual text. If a bullet reads as prose, tighten before turning it into a slide.
- **Talking points** are context for the spec, what the slide is about, why it's in the deck, what argument it makes. They live in `slide-spec.md` only and are not exported anywhere. Prose-style is fine; this is for the author/reviewer.
- **Speaker notes** are what shows up in PowerPoint's notes pane during presentation mode. Compact cues, not a script. They get pulled into `deck.yaml` and embedded in the `.pptx`. See *Writing speaker notes* below.
- **Artifact source** paths let later edits trace numbers back to the original report / log / chart script.
- Slides may have sub-slides (8a, 8b, 8c) when the same visual progresses with reveals. Each sub-slide gets its own H2.

## Writing speaker notes

Speaker notes are a glance-able reminder during presentation, not a script. You look down for a beat between thoughts; you don't read off them. Compact enough to absorb in two seconds, detailed enough to anchor what you actually want to say.

Aim for short bullets: fragments, keywords, structure markers. One thought per bullet. Top bullet is what you want top of mind; bottom is the optional tangent.

### Good

````markdown
- **Speaker notes:**
  - dy pattern, no bullet drift on edit
  - dx=16 is the body offset; bump if marker glyph changes
  - bold means structural, not decorative — call it out
````

### Bad (too prose; you end up reading it)

````markdown
- **Speaker notes:**
  - We use the dy pattern because if you put one <text> per row you get drift when you add or remove items from the bullet list.
  - The dx="16" value controls the offset of the body text from the bullet glyph, so you should adjust it if you change the glyph width.
  - The inline bold using body-bold is intentional here to call out a structural rule, not just for decoration.
````

### Rules of thumb

- 5 to 15 words per bullet. If you need a full sentence, you're writing a script.
- Capture what you'd misremember on stage: exact numbers, names, the punchline.
- 3 to 6 bullets per slide. More than that and the slide is doing too much.
- Order top-down by what you want top-of-mind first, not by what you'd say first.
- Use `**bold**` or ALL CAPS sparingly for things you must hit verbatim (an exact phrase, a number).
- If a bullet only restates what's on the slide, drop it.

## Anti-patterns

- Treating Talking points as Speaker notes, they're different. Talking points stay in the spec for context; Speaker notes get pulled into the `.pptx` for the presenter. Mixing them either bloats the `.pptx` or strips useful context from the spec.
- Long paragraphs of explanation in `Content blocks` — that's a sign the slide is doing too much.
- Skipping the spec and writing SVG directly — painful for everything except the title slide.
- Adding fields beyond the eight above (plus the Asset checklist) — keep the per-slide schema as: Layout, Headline/subtitle, Content blocks, Visuals, Artifact sources, Talking points, Speaker notes, Status.

## Linting the spec

`parse-spec.py` validates `slide-spec.md` before writing `deck.yaml`. Run it in lint-only mode for a fast check without generating output:

```bash
uv run <skill>/scripts/parse-spec.py --lint-only [deck-dir]
```

Exit 0 if clean; exit 1 if errors. Warnings always print to stderr but never block.

### Error catalog (block writes, exit 1)

| Code | Rule |
|---|---|
| E1 | Every `## Slide N — title` header must parse: ID present, dash separator (`—` or `-`), non-empty title. |
| E2 | Slide IDs must be unique. |
| E3 | Every slide must resolve to an SVG file (via explicit `- **File:**`, slug match, or `slide-<id>-*.svg` glob). |
| E4 | If `- **File:**` is present, the referenced SVG must exist. |
| E6 | Every slide requires `- **Status:**`. |

### Warning catalog (print to stderr, don't block)

| Code | Rule |
|---|---|
| W1 | Slide IDs should be sequential (gaps flagged). |
| W2 | Unknown `- **Foo:**` fields outside the documented schema. |
| W3 | `Status:` value should be `✅`, `⚠️`, or `❌`. |
| W4 | Visual asset paths in `- **Visuals:**` not found in the Asset checklist table. |
| W5 | Asset checklist row references a slide ID that doesn't exist. |
| W6 | Empty `- **Talking points:**` block (header present, no bullets). |
| W7 | Empty `- **Speaker notes:**` block (header present, no bullets). |

### Finding format

```
E3 (Slide 3 — Title): no matching SVG file found in deck dir
W2 (Slide 4 — Tables and columns): unknown field '**Reference:**' (not in documented schema)
```

Errors print with the slide context to make navigation fast.
