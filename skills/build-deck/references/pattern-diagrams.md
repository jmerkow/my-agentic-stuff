# Flow diagrams in native SVG

Process diagrams, architecture sketches, pipelines — anything with boxes and arrows. Build these in **native SVG primitives** (`<rect>`, `<line>`, `<text>`, `<marker>`). Don't reach for matplotlib.

## Why not matplotlib

Matplotlib's strength is data visualization with axes. For boxes-and-arrows it produces blurry rasters, weird font rendering, and a brittle script. SVG primitives give you crisp vector output, full control over geometry, no rasterization step, no chart pipeline.

## Pattern

### 1. Define an arrow marker once

```xml
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="8" markerHeight="8" orient="auto">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#0078d4" />
  </marker>
</defs>
```

The marker is the arrowhead. `orient="auto"` rotates it to follow whatever line it's attached to. `refX="9"` puts the tip 1px shy of the line's endpoint (looks cleaner).

### 2. Boxes are `<rect>` (with rounded corners and a border)

```xml
<rect x="160" y="450" width="360" height="180" rx="16" ry="16" class="surface" />
<rect x="160" y="450" width="360" height="180" rx="16" ry="16" class="border" stroke-width="2" />
<text x="340" y="528" text-anchor="middle" class="body-bold text" font-size="32">Box label</text>
<text x="340" y="572" text-anchor="middle" class="body text-muted" font-size="22">subtitle</text>
```

Two `<rect>`s with the same geometry: one for the fill (`class="surface"`), one for the border (`class="border"` + `stroke-width="2"`). Center the label with `text-anchor="middle"` at the box's horizontal center.

### 3. Arrows are `<line>` + `marker-end`

```xml
<line x1="520" y1="500" x2="760" y2="370"
      class="accent-stroke" stroke-width="4" marker-end="url(#arrow)" />
```

Compute the line endpoints from box edges. The `marker-end` attaches the arrowhead to the `(x2, y2)` end.

### 4. Use `full-bleed-diagram` layout

The `templates/layouts/full-bleed-diagram.svg` starter already includes the marker def and a compact title region. Copy it and replace the example shape.

## Anti-patterns

- **Matplotlib for flow diagrams.** Use SVG primitives — see Why not matplotlib above.
- **`<path>` for boxes when `<rect>` works.** Rounded rects (`rx`/`ry`) cover 95% of the cases.
- **Hand-computing arrow endpoints to land exactly on box edges.** Slight overlap (1–2px) looks fine and saves the math. Or land slightly *inside* the box and let the line disappear under it.
- **Drop shadows / 3D fills.** Modern decks read flat; shadows make boxes look 2010.
- **Many different box colors.** Use `class="surface"` for all boxes; differentiate with text or position, not hue. Accent color on arrows is enough visual interest.
- **Diagonal arrows where orthogonal works.** Right angles read as flow; diagonals read as chaos. If the visual reads better with diagonals (e.g. a network topology), use them, but default to right angles.

## When the diagram gets complex

If you're drawing more than ~10 boxes or need swimlanes/groups, consider whether the diagram is doing the work or fighting it:

- **2–6 boxes:** ideal — copy `full-bleed-diagram` and lay them out by hand.
- **7–12 boxes:** consider whether you can simplify; if not, build it.
- **>12 boxes:** the diagram is probably overloaded. Either split across two slides or use a different visual (timeline, table, layered architecture).

For complex diagrams the `diagram` skill (separate, for one-off non-deck diagrams) may be a better fit.

## Worked example

See `example/slide-06-svg-diagram.svg` for a complete 4-box flow with two branches (preview path + build path from a single source).
