---
name: build-deck
description: Build a presentation deck as standalone 1920×1080 SVG slides, themed via shared CSS, rendered with `rsvg-convert` for preview, and packaged into a self-contained `.pptx` for delivery. Use when authoring team updates, design reviews, conference talks, or any deck where diffable source matters. Keywords presentation, deck, slides, SVG, pptx, slide-spec.
---

# build-deck

Build a presentation as a folder of standalone 1920×1080 SVG slides. Each slide is one file, themed via shared CSS, rendered with `rsvg-convert` for preview, then imported into PowerPoint as a PNG (or SVG) per slide.

This skill replaces the legacy JS / pptxgenjs approach. SVG-first is faster to iterate, easier to diff, and trivially importable to PPT one slide at a time.

## When to use

- Team update, design review, conference talk, customer share-out
- Anytime you'd reach for PowerPoint but want diffable, reviewable source
- When the deck has charts (matplotlib) and the agent will own layout

## When NOT to use

- Live, interactive presentations needing animations or transitions
- Decks templated from corp branding that requires editing in PPT directly
- Single-slide quick visuals — use the `diagram` skill instead

## Prerequisites

Required on `PATH`:

- `python3` (3.9+) — for the build script
- `rsvg-convert` — for slide previews (Debian/Ubuntu: `apt install librsvg2-bin`; macOS: `brew install librsvg`)
- `xmllint` — for the hard rule "all slides validate as XML" (Debian/Ubuntu: `apt install libxml2-utils`; macOS: ships with Xcode CLT)

Python packages:

- scripts use PEP 723 inline metadata and run via `uv run`; if `uv` is not available, `pip install pyyaml` works too (the scripts import `yaml`)
- install `uv` if needed: `curl -LsSf https://astral.sh/uv/install.sh | sh` (or see <https://docs.astral.sh/uv/>)
- `matplotlib` — `pip install matplotlib` (only needed if you generate matplotlib charts)

Throughout this skill, `<skill>` refers to the skill's install directory — typically `~/.copilot/skills/build-deck/` after global install, or wherever you have it checked out during development.

## Workflow

1. **Write the spec first** — `slide-spec.md` with one section per slide. See `references/slide-spec-format.md`. The spec is what `parse-spec.py` reads to drive notes and ordering; skip it and you lose those.
2. **Scaffold** — create `<slides-root>/` with the structure below. If you intend to swap themes via `apply-theme.sh`, copy `<skill>/themes/*.css` into `<slides-root>/themes/` and copy `<skill>/scripts/apply-theme.sh` into `<slides-root>/scripts/`. Otherwise the inline theme block in each slide is sufficient and `themes/` can be omitted.
3. **For each slide** — copy `templates/slide-base.svg` (or a layout from `templates/layouts/`) to `<slides-root>/slide-NN-name.svg`, then fill in content using the right pattern reference.
4. **Render and *look*** — `rsvg-convert -w 1920 -h 1080 slide-NN-name.svg -o renders/slide-NN-name.png` after every edit, then **open the PNG and review it**. Visual checks the build can't do: text wraps, alignment, density, contrast. Non-negotiable; the build verifier doesn't catch layout bugs.
5. **Iterate** — fix layout, re-render, repeat. Run `slop-check` on text content before declaring done.
6. **Build the deck** — run `uv run <skill>/scripts/parse-spec.py [--lint-only]` to lint the spec and write `deck.yaml` (inline speaker notes included); then run `uv run <skill>/scripts/build-pptx.py <slides-root>`. Use `--lint-only` for a fast validation pass without writing. Pre-existing `deck.yaml` `output`/`template` values are preserved. See `references/pptx-export.md`.

## Directory structure

`<slides-root>/` is the deck directory you create per project — name it whatever fits (`slides-svg/`, `deck/`, `imports/rollup-YYYY-MM-DD/slides-svg/`, etc.). The structure inside is fixed:

```
<slides-root>/
├── slide-01-title.svg
├── slide-02-agenda.svg
├── ...
├── slide-12-closing.svg
├── themes/
│   ├── light-classic.css
│   └── dark-classic.css
├── scripts/
│   ├── apply-theme.sh         # copied from this skill
│   └── slideN-<chart>.py      # matplotlib chart generators (one per chart)
├── assets/
│   ├── <chart>.png            # matplotlib outputs, embedded via <image>
│   └── <photo>.png            # photos, copied here from source dirs
├── renders/                   # rsvg-convert PNG previews; throwaway
├── slide-spec.md              # source of truth for slide content
└── deck.yaml                  # build manifest (template, output, slides)
```

### `deck.yaml` (build manifest)

Optional — `build-pptx.py` works with no manifest at all if you accept the defaults:

- `output` defaults to `<deck-dirname>.pptx` in the deck dir
- `template` defaults to the skill's bundled `templates/blank.pptx`
- `slides` defaults to sorted glob `slide-*.svg`

Provide a `deck.yaml` when you want to pin slide order, override the template, or set a specific output path:

```yaml
output: out/deck.pptx
```

Paths are relative to the deck dir. `--output PATH` on the CLI overrides whatever's in the manifest.

## Hard rules

- **All color and font lives in `themes/*.css`.** Never inline `fill="#xxx"` or `font-family="..."` on a slide element. Use class names from the theme.
- **Background is a `<rect class="bg">` covering the viewBox.** Do NOT use `svg { background: ... }` — neither rsvg-convert nor PowerPoint honor it.
- **Embed images with both `href` and `xlink:href`.** Renderer compatibility.
- **Bullets use the `dx`/`dy` pattern, never one `<text>` per row.** (Tables are different — see `references/pattern-tables.md`.) See `references/pattern-bullets.md`.
- **Tables stay as positioned `<text>` rows.** They're not lists. See `references/pattern-tables.md`.
- **Never edit the `<style>` block by hand.** Use `scripts/apply-theme.sh` to swap themes. The `/* THEME-START */` and `/* THEME-END */` markers must be preserved exactly — the script keys off them.
- **One spec → one deck.** `slide-spec.md` is the source of truth; SVGs follow it.
- **All slides validate as XML.** `xmllint --noout slide-*.svg` should be quiet.

## Anti-patterns (learned the hard way)

- One `<text>` per bullet → bullet drift when you add/remove items. Use `dy` siblings.
- `<tspan class="body-bold text">` for emphasis on every bullet → reads as visual noise. Bold should be rare and meaningful.
- Italic subtitles + italic dates + italic captions → font soup. Stick to one italic per slide.
- Hard-coded indent (`x="192"`) instead of `dx="16"` after the bullet → breaks when you change the bullet column.
- `<foreignObject>` for HTML inside SVG → dropped by rsvg-convert and PPT. Don't.
- `<use href="#sym">` to share text glyphs → text style loss in some renderers. Inline the text.

## References (load on demand)

- `references/slide-spec-format.md` — spec file format and conventions
- `references/pattern-bullets.md` — bullets and numbered lists via `dx`/`dy`
- `references/pattern-tables.md` — table rows, headers, striping
- `references/pattern-images.md` — embedding photos and charts
- `references/pattern-charts.md` — matplotlib → asset → embed pipeline
- `references/pattern-diagrams.md` — flow diagrams in native SVG (`<rect>` + `<line>` + `<marker>`)
- `references/layouts.md` — picking a macro layout for a slide
- `references/theming.md` — themes, why CSS-only, how `apply-theme.sh` works
- `references/pptx-export.md` — building the `.pptx` from the deck dir

## Scripts

- `scripts/apply-theme.sh <theme-name> <slide.svg>` — swap the theme block in a slide. Use `--list` to list themes.
- `scripts/parse-spec.py` — lint `slide-spec.md` and write `deck.yaml` with inline speaker notes. Use `--lint-only` for a fast validation pass.
- `scripts/build-pptx.py` — package the deck dir into a self-contained `.pptx`. Reads `<slides-root>/deck.yaml` for template, output, and slide order. Speaker notes come from the `notes` field in `deck.yaml`. Run from the deck dir, or pass the deck path as the first arg: `uv run <skill>/scripts/build-pptx.py <deck-dir>`. See `references/pptx-export.md`.

## Templates

- `templates/slide-base.svg` — blank slide with theme block and title placeholder
- `templates/slide-spec-template.md` — blank spec to start a new deck
- `templates/blank.pptx` — bundled scaffold the build uses by default (slide master, theme, layouts, content-type defaults). Override via `deck.yaml` only if you need custom corporate scaffolding.
- `templates/layouts/` — macro layouts modeled on PowerPoint's standard set: title card, title+body, two-column, three-up cards, sections-stacked, 2×2 grid, title-only, full-bleed diagram. **Starting points, not constraints** — copy one, adjust positions, invent new layouts when the content needs it. See `references/layouts.md`.

## Example deck

`example/` ships a 7-slide self-documenting deck — each slide is the demo of one feature (title card, bullets, numbered lists, tables, matplotlib chart, native SVG flow diagram, table-plus-bullets combo). It ships a `deck.yaml` generated from its `slide-spec.md` (with speaker notes on the bullets, chart, and diagram slides) and builds with `uv run ../scripts/build-pptx.py` from `example/` to verify the skill end-to-end.

## Companion skills

- **`slop-check`** — run on `slide-spec.md` and on each slide's text before declaring done. Cliché filler reads worse on a slide than in prose.
- **`visual-design`** (if available) — run on slide layout and visual choices before declaring done. The visual counterpart to `slop-check`'s prose pass; flags defaults and templated patterns.
- **`diagram`** — use for one-off diagrams that aren't part of a deck.
