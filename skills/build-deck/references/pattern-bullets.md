# Bullets and numbered lists

One `<text>` block per list. Each row is a pair of `<tspan>`s — the marker and the body. Vertical spacing is `dy`, horizontal indent after the marker is `dx`.

## Why

SVG has no flow layout. Without this pattern you end up with one `<text>` per bullet, each with its own absolute `y`. Adding or reordering bullets means renumbering every `y`. With `dy` you only set the starting `y` once.

## Pattern

```xml
<text x="160" y="354" xml:space="preserve" class="body text" font-size="26">
  <tspan x="160" class="accent">•</tspan><tspan dx="16">First bullet text.</tspan>
  <tspan x="160" dy="1.5em" class="accent">•</tspan><tspan dx="16">Second bullet.</tspan>
  <tspan x="160" dy="1.5em" class="accent">•</tspan><tspan dx="16">Third bullet.</tspan>
</text>
```

What each piece does:

- `x="160" y="354"` on the parent — origin of the first row
- `xml:space="preserve"` — required so the `dx` whitespace renders consistently across rsvg / PPT
- `class="body text"` on parent — default text style for all children
- First marker `<tspan x="160" class="accent">•</tspan>` — sets the column for every subsequent marker (`x="160"` repeated)
- `<tspan dx="16">text</tspan>` — advances 16px past the marker, then renders the body text
- Subsequent rows: `<tspan x="160" dy="1.5em" class="accent">•</tspan><tspan dx="16">text</tspan>` — `dy="1.5em"` advances one line; `x="160"` resets the column

## Numbered list

```xml
<text x="160" y="488" xml:space="preserve" class="body text" font-size="24">
  <tspan x="160" class="accent">1.</tspan><tspan dx="16">Agent alone.</tspan>
  <tspan x="160" dy="1.8em" class="accent">2.</tspan><tspan dx="16">Agent + skill.</tspan>
  <tspan x="160" dy="1.8em" class="accent">3.</tspan><tspan dx="16">Agent + skill + foundation model.</tspan>
</text>
```

## Inline emphasis

Bold a phrase mid-bullet by switching class on a tspan:

```xml
<tspan x="160" class="accent">•</tspan><tspan dx="16" class="body-bold text">Headline phrase.</tspan><tspan class="body text"> Rest of the sentence.</tspan>
```

Rules:
- Use bold sparingly — one or two bullets per slide.
- Don't bold the whole bullet; bold the lead phrase or key number only.

## Spacing reference

| `dy` value | Use for |
|---|---|
| `1.3em` | tight rows (sub-items, citations) |
| `1.5em` | default bullets in body text |
| `1.6em` | bullets that often wrap to a second line |
| `1.8em` | numbered lists, larger fonts |
| `2em` | airy lists, accent rows |

`dx` scales with font size — eyeball it against the rendered preview:

| font-size | `dx` after the marker |
|---|---|
| 22–26 | `16` |
| 28–32 | `20` |
| 36+   | `24` |

## Anti-patterns

- One `<text>` per bullet with absolute `y` — fragile.
- `x="192"` (hard-coded indent) instead of `dx="16"` after the bullet — couples the indent to bullet column.
- Leading whitespace before the first `<tspan>` when `xml:space="preserve"` is set — pushes the first bullet right. The first child tspan must start immediately after the opening `<text>`.
- Setting `dy` on the *first* row — only set on rows 2+; row 1's position comes from the parent `y`.
- `<tspan>` with CSS `padding` or `margin` — SVG ignores box-model properties. Use `dx` / `dy`.

## Long bullets — explicit wrap

If a bullet must wrap, do it manually by starting a new `<tspan x="..." dy="...">` *without* a marker:

```xml
<tspan x="160" class="accent">•</tspan><tspan dx="16">Long first line that runs past the readable column,</tspan>
<tspan x="184" dy="1.2em">continuation indented under the text, not the bullet.</tspan>
```

The continuation `x` is the **text column** — bullet `x` + glyph width + `dx`. For the default `•` glyph at font-size 22–26 with `dx="16"`, that's bullet `x + 24` (so `x="160"` → continuation `x="184"`; `x="80"` → continuation `x="104"`). For larger glyphs (`1.` at 44pt) the offset is bigger — eyeball the rendered preview. `dy` is shorter than the inter-bullet spacing (`1.2em` for a `1.5em` list).
