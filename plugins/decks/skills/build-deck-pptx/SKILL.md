---
name: build-deck-pptx
description: Build, revise, render, and QA native editable PowerPoint presentations with PptxGenJS from a standalone deck report. Use only after the user explicitly chooses native PPTX output. Keywords native PowerPoint builder, editable PPTX, pptxgenjs, deck-report.
---

# build-deck-pptx

Build presentations as native `.pptx` files whose text, shapes, tables, and charts remain individually editable. Start from the standalone `deck-report.md` produced by `plan-deck`, author a purpose-built JavaScript generator with `pptxgenjs`, render the actual file, inspect it, revise it, and verify it again.

Do not select this builder by inference. If the user has not explicitly chosen native PPTX output, ask them to choose between `build-deck-pptx` and `build-deck-svg` before constructing slides.

Do not force every presentation through a generic generator. Write the deck-specific JavaScript needed for the report, audience, and visual system in front of you.

Use SVG as a local construction tool for diagrams that are genuinely easier to express as SVG. Do not flatten an entire slide into one SVG or image unless the user explicitly values exact rendering over editability.

## Input contract

- `deck-report.md` is detailed source material, not a slide specification.
- Read the complete report before deciding slide count or structure.
- Derive titles, bullets, layouts, emphasis, and omissions during generation.
- Preserve qualifications and evidence; do not turn nuanced findings into unsupported slogans.
- Reuse diagrams embedded in the report when suitable, or reconstruct them as native shapes when editability warrants it.

## Output contract

- The JavaScript generator is the layout source of truth.
- The `.pptx` is the editable deliverable.
- Rendered slide images are the visual QA evidence.
- Native objects are the default. Raster images are for photos and rendered data graphics, not text or whole slides.

## Workflow

1. **Read the report** — understand its thesis, evidence, diagrams, caveats, and sources before planning slides.
2. **Make an internal slide plan** — choose the audience-facing argument, sequence, slide boundaries, and what can be omitted. This is generator working state, not a rewrite of the report.
3. **Write a design plan** — define color roles, type scale, spacing unit, layout concept, and one content-specific signature element. See `references/visual-construction.md`.
4. **Choose object strategies** — use native PowerPoint text, shapes, tables, and charts by default. Use photos as images. Use SVG only for focused diagrams that benefit from SVG authoring.
5. **Create the deck workspace** — choose a path outside the installed skill, such as `path/to/new-deck/`. Keep the report, generator, assets, output, and renders there.
6. **Copy and edit the generator template** — run `cp <skill>/templates/deck-template.js path/to/new-deck/build-deck.js`, then replace its sample slides with purpose-built code for this report and audience. The copied file already imports `pptxgenjs`, defines safe starter helpers, and writes `output.pptx` beside itself; it is source code to edit, not a generic report converter. Never edit the bundled template in place.
7. **Check the workspace dependency** — run `node -e "require.resolve('pptxgenjs', { paths: ['path/to/new-deck'] })"`. If it fails, ask before running `npm install --prefix path/to/new-deck pptxgenjs`. Do not install globally or into the skill.
8. **Generate and inspect structure** — run `node path/to/new-deck/build-deck.js`, then `python <skill>/scripts/inspect-pptx.py path/to/new-deck/output.pptx`. Fix structural failures in the generator rather than patching packed XML.
9. **Check content** — if `markitdown` is available, run `python -m markitdown path/to/new-deck/output.pptx`; otherwise inspect the slide text and notes with `python-pptx`. Compare claims, numbers, and qualifications to the report.
10. **Render and look** — run `python <skill>/scripts/render-pptx.py path/to/new-deck/output.pptx --output-dir path/to/new-deck/renders`. Inspect every full-size rendered slide and use an image contact sheet when the environment already provides one.
11. **Revise and re-verify** — record concrete issues, fix the copied generator, regenerate, re-extract, inspect, and re-render affected slides. One fix-and-verify cycle is mandatory.

## Prerequisites

Required for generation:

- Node.js 18+
- `pptxgenjs`

Required for QA:

- Python 3.9+
- `python-pptx` 1.0+ for structural inspection
- LibreOffice (`libreoffice` or `soffice`) for rendering
- Poppler (`pdftoppm`) for PNG conversion

Check the deck workspace before installing anything:

```bash
node -e "require.resolve('pptxgenjs', { paths: ['path/to/new-deck'] }); console.log('pptxgenjs available')"
python -c "import pptx; print(pptx.__version__)"
command -v libreoffice || command -v soffice
command -v pdftoppm
```

If `pptxgenjs` is absent, ask before installing it. Do not silently add packages.

`npm install --prefix path/to/new-deck pptxgenjs` installs into the external deck workspace. It creates or updates local npm metadata and `node_modules`; it does not modify the installed skill or install globally.

Throughout this skill, `<skill>` means the directory containing this `SKILL.md`. Resolve it from the active skill at runtime; do not assume a harness-specific install path.

## Directory structure

Use one deck directory outside `<skill>`:

```
path/to/new-deck/
├── deck-report.md
├── build-deck.js
├── assets/
│   ├── source-photo.jpg
│   └── generated-chart.png
├── output.pptx
└── renders/
	├── slide-01.png
	└── slide-02.png
```

## Hard rules

- Use six-digit RGB colors. Do not include `#` or alpha in PowerPoint color values.
- Set `pptx.layout = "LAYOUT_WIDE"` before adding slides.
- Create a fresh `pptxgenjs` presentation object for every output.
- Use one native text box per logical block. Do not convert slide text to an image.
- Use real bullets or separate paragraph objects, never a literal bullet glyph.
- Use fresh option, fill, and shadow objects for each `add*` call; PptxGenJS may mutate them.
- Keep every object inside the slide canvas. The structural inspector treats out-of-bounds objects as errors.
- Do not use a full-slide image as the default construction method. The inspector rejects it unless explicitly allowed.
- Write speaker notes with `slide.addNotes(...)`, not onto the slide.
- Keep at least 0.5-inch outer margins and a stable spacing unit across the deck.
- Never declare success from code inspection. Render and inspect every slide.
- Do not use private or proprietary third-party skill scripts as bundled resources. Reuse ideas and public libraries, not copied implementations.

## Existing decks and templates

Do not rebuild an existing presentation from scratch unless the user asks for a redesign. First extract its text, render a thumbnail overview, and inspect its masters and layouts in PowerPoint or through package metadata. Preserve the original file and write changes to a new output path.

Use `python-pptx` for straightforward edits to native text, shapes, tables, notes, and slide order. For unsupported objects such as SmartArt, embedded workbooks, or complex template relationships, prefer a narrow OOXML edit that preserves unrelated package parts. Re-run structure, content, and render checks against the resulting deck.

## Native object choices

| Content | Default object | Why |
|---|---|---|
| Titles, labels, prose | text boxes | searchable and editable |
| Boxes, arrows, dividers | PowerPoint shapes | editable geometry and styling |
| Tables | native tables | editable cells and accessible reading order |
| Business charts | native charts | editable data and series |
| Scientific plots | high-resolution image plus source script | faithful rendering; reproducible source |
| Photos | image | source is already raster |
| Complex technical diagram | native shapes or focused SVG | choose based on complexity and editability need |

## References (load on demand)

- `references/native-pptx.md` — `pptxgenjs` construction patterns and object rules
- `references/visual-construction.md` — design planning and pixel-review checklist

## Bundled tools

- `templates/deck-template.js` — copy to `build-deck.js`, then edit into the purpose-built deck generator
- `scripts/inspect-pptx.py` — package, bounds, and full-slide-image checks
- `scripts/render-pptx.py` — deterministic LibreOffice and Poppler rendering

## Companion skills

- **`slop-check`** (if available) — run on audience-facing slide text before declaring done. Cliché filler reads worse on a slide than in prose.
- **`visual-design`** (if available) — run on slide layout and visual choices before declaring done. The visual counterpart to `slop-check`'s prose pass; flags defaults and templated patterns.
