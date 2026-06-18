---
name: visual-design
description: >
  Judge and improve the visual design of static artifacts (presentation slides, decks,
  diagrams, posters, SVG figures, any laid-out visual) so they read as intentional rather
  than templated or AI-generated. Covers anti-default calibration (naming and avoiding
  defaults before committing a visual choice), signature + restraint (one bold element,
  everything else quiet), and plan-then-critique (two-pass design loop). For STATIC visual
  artifacts only; not for web UI runtimes. Keywords: visual design, layout design, slide
  design, deck aesthetics, diagram design, poster design, avoid templated look, design
  judgment, AI slop visual, anti-default, signature element, plan then critique.
---

# visual-design

Design judgment for static visual artifacts: slides, decks, diagrams, posters, standalone SVG figures, any laid-out visual. The visual sibling to `slop-check`: where that skill catches prose clichés, this one catches visual defaults that make output look generated rather than considered. It does not produce files; pair it with whatever building skill makes the artifact and run it as a review pass before declaring done.

## When to use

- Reviewing any laid-out visual for a templated, AI-generated look
- Auditing a diagram, slide, or figure before exporting or presenting
- Designing a one-off visual where deliberate choices matter
- Any time the brief calls for something that should look intentional, not assembled

## When NOT to use

- Web UI with runtime concerns (motion, responsive layout, hover states, keyboard focus, CSS specificity); those need a web-design approach, not this skill
- Prose and text quality: use `slop-check`
- You are building, not reviewing: load the relevant building skill directly

## The method: is this a choice or a default?

Before committing any visual decision, ask: would I make this same choice for any similar brief? If yes, it is a default, not a choice. Defaults are not wrong, but spending your design freedom on them produces templated output. Name them before you use them.

The tells below are examples grouped by artifact type. They are not exhaustive; the method is what generalizes, the examples just show what defaults look like in practice.

**Slide and deck tells:**

- A1: Centered title with italic subtitle on every title slide, regardless of content tone
- A2: Exactly three evenly-spaced bullets on every content slide
- A3: Big gradient number callout with a small label, used as a visual anchor
- A4: A 2x2 grid applied to content that is not a genuine four-quadrant relationship
- A5: Numbered markers (01 / 02 / 03) on content that is not a genuine sequence

**Diagram and figure tells:**

- A6: Everything in left-to-right boxes-and-arrows when the relationship is not a flow
- A7: Evenly-spaced nodes that hide the real structure (clusters, hierarchies, loops)

If you catch yourself using one of these without a brief-specific reason, stop and ask what the content actually requires.

## Spend boldness in one place

Pick one signature element: a color choice, an unusual layout beat, a weight contrast, a figure that anchors the whole piece. Make that one thing the memorable visual. Keep everything around it quiet and disciplined. Cut decoration that does not serve the brief.

Do a subtraction pass before calling it done: identify the weakest decorative element and remove it. Structure should encode something true. Numbering, dividers, and labels earn their place only if they carry real information.

## Plan, then critique

Work in two passes.

**Pass 1: design plan.** Write a compact token system before building:

- Colors: 4-6 named hex values with roles (background, surface, text, muted, accent, accent-alt)
- Type: scale and weight roles within the available font (title weight, body weight, caption size); not a font choice
- Layout concept: one sentence on how space is organized
- Signature element: the one thing you are doing that is not a default

**Pass 2: critique before building.** Read the plan against the brief. For each token, ask: is this what I would produce for any similar brief? If yes, revise it and say what you changed and why. Confirm relative uniqueness, then build, deriving every decision from the plan. Skipping this pass and building from defaults is how visual slop happens.

## Typography constraint

Type guidance here is limited to **scale, weight, and hierarchy within an available font**, not picking a font. Vary those three levers. Reaching for an exotic display face to look less templated adds little real distinctiveness and usually reads as trying too hard.

For **static-render targets** (anything where text is rasterized or outlined at render time, such as SVG rendered by `rsvg-convert`, or PowerPoint's convert-to-shapes) there is a hard reason on top of taste: the font must be installed on the render host. If a named font is missing, the renderer falls back silently and the fallback's glyph metrics differ (advance width, x-height, kerning), so text overflows, wraps wrong, or collides with positioned elements. See `build-deck` for the deck-specific version.

## Anti-patterns (learned the hard way)

- **Gradient accent number with label** (A3): almost always a default. Ask what information it actually communicates.
- **The 2x2 grid** (A4): use it only when the content has genuine two-axis structure. Otherwise it imposes a false relationship.
- **Numbered markers on non-sequences** (A5): implies an order that is not there. Use bullets or labels without ordinal numbering.
- **Boxes-and-arrows for everything** (A6): if the relationship is hierarchical, spatial, or cyclic, use the shape that matches the actual structure.
- **Signature element applied everywhere**: repeated on every slide, panel, or section, it stops being a signature and becomes another default.
- **Font chosen to look less AI-generated**: breaks layout silently on any render host missing that font. See Typography constraint.

## Companion skills

- **`slop-check`**: the prose equivalent. Run it on any text in the artifact (slide copy, labels, captions).
