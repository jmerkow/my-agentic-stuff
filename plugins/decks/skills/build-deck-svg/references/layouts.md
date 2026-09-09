# Layouts

Macro layouts modeled on PowerPoint's standard set plus a few we've found useful in practice. Each one is a copy-paste starter at `templates/layouts/<name>.svg` — copy it, rename, fill in content.

**These are starting points, not constraints.** If the content needs a layout that isn't in the catalog, invent one. The catalog covers ~80% of cases; the remaining 20% should not be forced into a layout that almost fits.

## When to use what

Pick by **content shape**, not aesthetic:

| Shape of the content | Layout |
|---|---|
| Opening / closing / section divider | [`title-card`](#title-card) |
| One body region (bullets, table, chart) | [`title-body`](#title-body) |
| Single big visual that should dominate | [`title-only`](#title-only) or [`full-bleed-diagram`](#full-bleed-diagram) |
| Two parallel regions side-by-side | [`two-column`](#two-column) |
| Three parallel topics shown horizontally | [`three-up-cards`](#three-up-cards) |
| Multiple labeled sections stacked vertically | [`sections-stacked`](#sections-stacked) |
| Four parallel topics shown as a grid | [`grid-2x2`](#grid-2x2) |
| A flow / process / pipeline | [`full-bleed-diagram`](#full-bleed-diagram) + see `pattern-diagrams.md` |

If two layouts could work, pick the one with **less** structure — the empty space is doing work.

## Layout catalog

### `title-card`
Centered title and italic subtitle with an accent band across the middle. Optional footer credit at the bottom.
- **PowerPoint analog:** Title Slide.
- **Use for:** opening slide, section divider, closing slide.

### `title-body`
Title and optional subtitle at the top, single 1600×740 body region underneath.
- **PowerPoint analog:** Title and Content.
- **Use for:** the workhorse — bullets, a table, a single chart with caption.

### `title-only`
Title and optional subtitle at the top; body left blank.
- **PowerPoint analog:** Title Only.
- **Use for:** when you want minimal chrome above a full-width composition you'll lay out yourself.

### `two-column`
Title + two equal columns (770 px each, gap = 60).
- **PowerPoint analog:** Two Content.
- **Use for:** chart + bullets; table + emphasis; photo + caption; before/after.

### `three-up-cards`
Title + three 480-wide cards across the slide, each with its own accent strip header and bullets.
- **PowerPoint analog:** Comparison, extended to three regions.
- **Use for:** three parallel topics (e.g. HIMSS / UW / SIIM; Done / Now / Next as cards).

### `sections-stacked`
Title + N section headers stacked vertically, bullets under each. Pre-wired for three sections at y=240/468/696; adjust spacing for more or fewer.
- **PowerPoint analog:** none directly — extends "Title and Content" with sub-headers.
- **Use for:** themed groupings (Done / Now / Next stacked, 4-section "Evals / Load Testing / Packaging / Documentation").

### `grid-2x2`
Title + four equal quadrants (TL/TR/BL/BR).
- **PowerPoint analog:** Comparison, extended to a 2×2 grid.
- **Use for:** four parallel topics that share a frame (skills / agents / mcp / habits; current / past / risks / next).

### `full-bleed-diagram`
Compact title in the top-left, large diagram region underneath (x=80..1840, y=180..1020). Includes a starter `<marker id="arrow">` def.
- **PowerPoint analog:** Title Only with one large shape.
- **Use for:** flow diagrams, architecture sketches, process visuals where the visual is the point.

## Conventions

- All layouts use the same column grid: left margin x=160 for centered layouts, x=80 for full-bleed. Title baseline y=144 (large) or y=90 (compact).
- Section/card headers use `class="h2 accent"`, body uses `class="body text"`.
- Replace placeholder text. Delete the example shape on `full-bleed-diagram`.
- The layouts are starters, not constraints — modify positions as needed. The point is to start from a known-good frame.

## Anti-patterns

- Picking a layout because it looks fancy — pick the simplest one that fits the content.
- Squeezing six bullets into `grid-2x2`'s 4 quadrants instead of using `sections-stacked` — respect the structure.
- Using `title-card` for a body slide because it has an accent band — that band is for opening / closing, not decoration.
- Re-doing the coordinate math from scratch when one of these layouts already covers the shape.
- Treating the catalog as fixed. If your slide needs a layout that isn't here, build it. Don't deform a near-match.
