---
name: diagram-help
description: >-
  Lightweight reference for Mermaid and SVG diagram rendering gotchas. Use when
  choosing between Mermaid, Mermaid-rendered SVG, and direct SVG, or when
  producing diagrams that must render reliably through mmdc, rsvg-convert, PNG,
  or PowerPoint. Keywords: diagram, mermaid, mmdc, SVG, rsvg, PowerPoint,
  rendering, portability.
---

# Diagram Help

This is a small reference skill, not a diagram workflow. Use it for the handful of diagram facts that are easy to forget and expensive to debug.

## Decision

- Use **Mermaid** for structured diagrams that fit Mermaid's model: flowcharts, sequence diagrams, state machines, class diagrams, ER diagrams, and simple timelines.
- Use **Mermaid to SVG** when Mermaid mostly gets the structure right but the final visual needs manual polish. Render with `mmdc`, then edit the SVG.
- Use **direct SVG** when layout, spacing, shapes, or visual hierarchy matter more than Mermaid's automatic layout.

## Things Worth Remembering

### 1. Mermaid can become SVG

```bash
mmdc -i diagram.mmd -o diagram.svg -w 1920 -H 1080
mmdc -i diagram.mmd -o diagram.png -w 1920 -H 1080 -s 2
```

Use `-s 2` for PNGs that need to stay crisp when downscaled into slides or docs.

### 2. Standalone SVG needs inline style

`rsvg-convert` and PowerPoint do not reliably load external CSS or honor `<?xml-stylesheet?>`. Put the `<style>` block inside the SVG.

```xml
<style type="text/css"><![CDATA[
.bg { fill: #ffffff; }
.text { fill: #1a1a1a; font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; }
.accent-stroke { stroke: #0078d4; fill: none; }
]]></style>
```

### 3. Paint the background with a rect

`svg { background-color: ... }` is ignored by `rsvg-convert` and PowerPoint. Add an explicit background rectangle after the style block.

```xml
<rect x="0" y="0" width="1920" height="1080" class="bg" />
```

### 4. Use system fonts for render fidelity

`rsvg-convert` resolves fonts through fontconfig on the render host. If a named font is missing, fallback glyph metrics can change wrapping, overflow labels, or collide with positioned shapes.

Use:

```text
-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif
```

Avoid Google Fonts, `@import`, and distinctive display faces unless the rendering environment is known to have them.

### 5. Avoid renderer-sensitive SVG tricks

- Avoid `currentColor` for chained fills; it works in browsers but is inconsistent in `rsvg-convert` and PowerPoint.
- Avoid scattered `fill="#xxx"` and `stroke="#xxx"` if you expect to retheme the SVG. Prefer classes.
- Avoid external assets unless the output path is known to preserve them.

### 6. Two tiny layout snippets

Hub-and-spoke placement:

```text
x = cx + r * cos((2 * pi / N) * i)
y = cy + r * sin((2 * pi / N) * i)
```

Visible self-loop in direct SVG:

```xml
<path d="M 335 160 C 310 95 440 95 415 160" class="accent-stroke" />
```

These are snippets, not rules. Adjust coordinates to the actual viewBox and label lengths.
