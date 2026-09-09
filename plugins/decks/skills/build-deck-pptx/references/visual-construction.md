# Visual construction and QA

## Design plan

Write this before drawing slides:

- **Audience and room:** who decides what, and how far away they sit
- **Layout concept:** one sentence describing how space behaves across the deck
- **Color roles:** background, surface, text, muted, accent, optional secondary accent
- **Type scale:** title, section, body, caption
- **Spacing unit:** one repeatable gap, usually 0.25 or 0.3 inches
- **Signature element:** one content-specific visual choice that earns attention
- **Avoided defaults:** visual habits rejected because they do not fit this content

Critique the plan before building. If the same plan would fit an unrelated deck, make it more specific.

## Constructing a slide

1. State the slide's argument in one sentence.
2. Choose the relationship the visual must communicate: sequence, comparison, hierarchy, trend, composition, or evidence.
3. Pick the simplest layout that expresses that relationship.
4. Build the dominant visual first.
5. Add only the text needed to interpret it.
6. Remove the weakest decorative element.

Vary layouts because the content relationships vary, not to create novelty. Avoid cards unless they represent genuinely repeated peer items.

## Structural QA

Run:

```bash
python <skill>/scripts/inspect-pptx.py path/to/new-deck/output.pptx
```

Fix every error before visual QA. A structural pass cannot detect text wrapping, low contrast, awkward whitespace, or poor hierarchy.

## Pixel QA

Render:

```bash
python <skill>/scripts/render-pptx.py path/to/new-deck/output.pptx --output-dir path/to/new-deck/renders
```

Open every PNG. Assume the first render has defects and inspect for:

- overlap, clipping, and text overflow
- weak contrast or hierarchy
- inconsistent margins, alignment, and spacing
- labels too far from the objects they describe
- unexplained empty space or cramped regions
- unsupported font substitution
- accidental repetition of the same layout
- decorative elements that imply false structure
- unreadable citations, legends, or chart labels
- placeholder text or missing assets

Write down the issues, fix the generator, regenerate, and re-render the affected slides. Do not call the deck complete until at least one fix-and-verify cycle has happened.