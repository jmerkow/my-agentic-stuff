# Tables

Tables are NOT lists — they're a grid of positioned `<text>` elements. Resist the urge to `dy` them; column alignment is the whole point.

## Pattern

```xml
<!-- Background stripes (zebra) -->
<rect x="160" y="270" width="1600" height="56" class="surface" />
<rect x="160" y="326" width="1600" height="58" class="surface-alt" />
<rect x="160" y="442" width="1600" height="58" class="surface-alt" />

<!-- Row separator lines -->
<line x1="160" y1="326" x2="1760" y2="326" class="border" stroke-width="1" />
<line x1="160" y1="384" x2="1760" y2="384" class="border" stroke-width="1" />

<!-- Header row -->
<text x="184" y="307" class="body-bold text" font-size="22">Column 1</text>
<text x="660" y="307" text-anchor="end" class="body-bold text" font-size="22">Numeric</text>
<text x="700" y="307" class="body-bold text" font-size="22">Wide column</text>

<!-- Data rows -->
<text x="184" y="364" class="body text" font-size="22">Row 1, col 1</text>
<text x="660" y="364" text-anchor="end" class="body text" font-size="22">1,234</text>
<text x="700" y="364" class="body text" font-size="22">Description text</text>
```

## Conventions

- **Header background `surface`, data rows `surface-alt`** — subtle stripe via the theme.
- **Right-align numeric columns** with `text-anchor="end"` and place `x` at the *end* of the column.
- **Row height** typically 50–58px at 22px font; tune per density.
- **Header height** slightly larger (56px) so the bold text doesn't crowd the separator.
- **Separator lines** use `class="border"`; don't draw between every row, only at section breaks.

## Highlighting a row

Emphasize one row (e.g. the big number, the P7 row) by switching its class to `body-bold text` or `body-bold accent`:

```xml
<text x="184" y="613" class="body-bold text" font-size="22">P7 — AML Network Isolation</text>
<text x="660" y="613" text-anchor="end" class="body-bold accent" font-size="22">0 / 2</text>
```

One highlighted row per table. More than that and nothing stands out.

## Totals row

Final row gets `class="surface"` (same as header) + `body-bold` text:

```xml
<rect x="80" y="682" width="1000" height="50" class="surface" />
<text x="100" y="713" class="body-bold text" font-size="20">Total</text>
<text x="660" y="713" text-anchor="end" class="body-bold accent" font-size="20">6 / 25</text>
```

## When to use a table vs bullets

- **Table** — comparison of named rows on the same dimensions (perturbation conditions, model load-test results, threat-model programs).
- **Bullets** — narrative points, takeaways, recommendations.
- **Chart** — magnitude story where a glance beats a number.

If the rows have varying numbers of fields, it's bullets. If they share a schema, it's a table.

## Anti-patterns

- Using `dy` to space table rows — column alignment drifts.
- Centering numeric columns — pretty in isolation, unreadable when comparing rows.
- Drawing a border around every cell — turns it into a spreadsheet, not a slide.
- More than 7–8 rows on a single slide — split or summarize.
