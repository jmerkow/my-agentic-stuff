# Building the .pptx

The build packages a `<slides-root>/` into a self-contained PowerPoint file. Each slide SVG becomes a full-bleed vector image at 16:9 (12,192,000 × 6,858,000 EMU). All referenced assets (charts, photos) are **inlined into the SVG as base64 data URIs**, so the resulting `.pptx` has no external file dependencies.

## Run

```bash
# Simplest: from inside the deck dir, all defaults
uv run <skill>/scripts/build-pptx.py

# Or pass the deck dir explicitly:
uv run <skill>/scripts/build-pptx.py path/to/<slides-root>

# Override the output path:
uv run <skill>/scripts/build-pptx.py --output custom.pptx
```

`deck.yaml` is optional. On verifier failure, the script exits 1 with a diagnostic — fix the reported file and re-run.

## `deck.yaml` manifest

All keys are optional. Provide a manifest when you want to pin slide order, override the template, or set a specific output path.

| Key | Type | Default | Notes |
|---|---|---|---|
| `output` | string | `<deck-dirname>.pptx` | Path for the built `.pptx` (relative to deck dir, or absolute). Parent dirs auto-created. |
| `template` | string | skill's `templates/blank.pptx` | Path to a template `.pptx` (relative to deck dir, or absolute). Provides slide master, theme, layouts. |
| `slides` | list of objects | sorted `slide-*.svg` | Each object has `file` (required) and optional `notes` (multiline speaker text). |

`--output PATH` on the CLI overrides whatever's in the manifest.

Minimum example (pin output, accept other defaults):

```yaml
output: out/deck.pptx
```

Explicit slide order example:

```yaml
output: out/team-update.pptx
slides:
  - file: slide-01-title.svg
  - file: slide-02-agenda.svg
    notes: |
      Open with team count and scope.
      Remind audience this covers Q3 only.
  - file: slide-08a-vuln-totals.svg
  - file: slide-08b-vuln-whats-going-on.svg
```

## What it does

1. For each slide SVG: inline every `<image href>` as a base64 data URI, strip the `<?xml-stylesheet?>` PI, and write the result to `ppt/media/imageN.svg` in the output pptx.
2. Use the template `.pptx` as a scaffold (slide master, theme, layouts, content types, props are preserved).
3. Generate one `ppt/slides/slideN.xml` per slide — a single `<p:pic>` covering the full 16:9 slide, referencing the SVG via `asvg:svgBlip` on `rId2`.
4. Patch `ppt/presentation.xml`, `ppt/_rels/presentation.xml.rels`, and `[Content_Types].xml` to register the new slides.

## Why base64 inlining

PowerPoint can resolve relative `<image href>` inside a packaged SVG (against `ppt/media/`), but the current script side-steps that machinery entirely: it flattens each slide into a single self-contained SVG before packaging. Pros: simpler verifier, no chance of broken refs in the built pptx, no `assets/` subtree in `ppt/media/`. Con: file size grows with embedded raster size.

This is an implementation choice — rsvg-convert previews still use the relative `<image href>` paths in your source SVG, so authoring is unaffected. The flattening only happens at build time.

## Verifier

The build re-opens the output pptx and checks four classes of bug that produce PowerPoint's "found a problem with content" repair dialog:

- No duplicate or phantom slide overrides in `[Content_Types].xml`.
- Every `sldId` references a real `rId` of type `slide` (catches the "master is showing as slide 1" bug).
- All `.rels` targets exist in the package.
- No SVG contains `<?xml-stylesheet?>` (PowerPoint can't resolve external CSS) and no `<image href>` points outside the package.

On failure, exits 1 with a diagnostic.

## Deliberately not in scope

- No layout logic. SVGs already say where everything goes; the pptx is a vector-image carrier.
- No font embedding (relies on Segoe UI being available).
- No animations / transitions — add in PowerPoint after if needed.
- No edit round-trip. Always edit the SVG; the next build overwrites pptx content.

## Current status

- A bundled template ships at `<skill>/templates/blank.pptx` and is used by default. To override (e.g. corporate theme, custom slide dimensions, embedded fonts), generate one from a PowerPoint blank deck saved as `.pptx` and point `deck.yaml`'s `template` at it.
