# build-deck example deck

Smoke-test deck for the `build-deck` skill. It builds itself as a `.pptx` and serves as a copy-paste reference for new decks.

## Build

```bash
cd <skill>/example
uv run ../scripts/build-pptx.py
```

Output: `example.pptx` next to this README.

`deck.yaml` is generated from `slide-spec.md` by `parse-spec.py` and carries slide order plus inline speaker notes. Output path and template fall back to defaults (`<deck-dirname>.pptx`, `<skill>/templates/blank.pptx`).

## Layout

Each slide demonstrates one feature. Title = what it is. Subtitle = how it works. Body = the demo.

| Slide | File | Demonstrates |
|---|---|---|
| 1 | `slide-01-title.svg` | title card — centered title, accent band, footer credit |
| 2 | `slide-02-bullets.svg` | bullet list (`dx`/`dy` pattern), inline emphasis |
| 3 | `slide-03-numbered.svg` | numbered list variant |
| 4 | `slide-04-tables.svg` | 2-column layout, zebra-striped table, code sample callout |
| 5 | `slide-05-matplotlib-chart.svg` | matplotlib horizontal-bar chart, palette pulled from theme |
| 6 | `slide-06-svg-diagram.svg` | flow diagram in native SVG primitives (no chart pipeline) |
| 7 | `slide-07-table-and-bullets.svg` | table + bullets combo on one slide (numeric table + takeaways) |

`slide-spec.md` is the source of truth for the deck content; SVGs follow it.

## Regenerate the chart

```bash
python3 scripts/slide5-perturbation-chart.py
```
