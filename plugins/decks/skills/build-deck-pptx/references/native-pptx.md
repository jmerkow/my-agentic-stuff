# Native PPTX construction with PptxGenJS

Use `pptxgenjs` when the delivered deck must remain editable. Copy the bundled template into an external deck workspace, then replace the sample content with the purpose-built presentation rather than starting from an empty script.

```bash
cp <skill>/templates/deck-template.js path/to/new-deck/build-deck.js
node path/to/new-deck/build-deck.js
```

Never edit `<skill>/templates/deck-template.js` in place. The template's `require("pptxgenjs")`, presentation setup, helpers, error handling, and output call are reusable scaffolding. Its sample slides are not; rewrite them from `deck-report.md`. The copied script writes `output.pptx` beside itself regardless of the shell's current directory.

## Construction rules

- Set `pptx.layout = "LAYOUT_WIDE"` before adding slides.
- Define color, type, and spacing tokens once near the top of the generator.
- Use inches for layout coordinates and points for type.
- Use `margin: 0` when exact text alignment matters.
- Add one shape per meaningful visual object so users can edit it later.
- Use `addTable()` and `addChart()` when users need to edit cells or series.
- Keep scientific plots as reproducible source scripts plus rendered images when native chart primitives cannot represent them faithfully.
- Add notes through `slide.addNotes("...")`.
- Use fresh option, fill, and shadow objects for each call; PptxGenJS may mutate option objects.
- Use six-digit colors without `#`. Express transparency as an option rather than alpha in the color string.

## Text

Use text runs with `bullet: true` and `breakLine: true`. Do not type the bullet glyph into text.

Use a minimum 28-32pt title, 17-20pt body text for normal rooms, and 11-12pt only for captions or citations. Tight layouts do not justify unreadable text; split the slide.

## Shapes and connectors

Use `addShape()` for boxes, markers, arrows, and dividers. Structure must encode a real relationship: sequence, hierarchy, comparison, grouping, or flow. Decorative boxes do not make a slide clearer.

Avoid grouping everything into one object. The user should be able to select a label, connector, or card and change it independently.

## Focused SVG diagrams

Use SVG for a focused technical diagram when its geometry would be cumbersome in native shapes. Keep slide titles, captions, and surrounding explanation native. If the final user needs every SVG element editable, tell them to insert the SVG in PowerPoint and use **Convert to Shape**; verify the converted result because fonts and clipping can change.

Do not use one full-slide SVG here. Choose `build-deck-svg` when exact SVG rendering is the priority for the whole deck.

## Output

```javascript
slide.addNotes("First cue\nSecond cue");
await pptx.writeFile({ fileName: "output.pptx" });
```

Keep notes compact: 3-6 cues, 5-15 words each. Keep authoring rationale in generator working notes, not the notes pane.