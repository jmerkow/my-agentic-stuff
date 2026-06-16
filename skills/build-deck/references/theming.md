# Theming

All visual style lives in `themes/<name>.css`. Slides reference style via class names; the theme block is duplicated inline (between `THEME-START` / `THEME-END` markers) so the SVG renders standalone — rsvg and PowerPoint don't reliably honor `<?xml-stylesheet?>`.

## Why this dance

- **CSS-only rule** keeps the deck consistent. No `fill="#0078d4"` scattered through 12 files.
- **Inline theme block** because external CSS isn't honored by every renderer we ship to. We accept the duplication for portability.
- **Marker-bracketed block** so `apply-theme.sh` can swap themes mechanically.

## Theme block contract

Every slide SVG contains exactly one `<style>` block with this shape:

```xml
<style type="text/css"><![CDATA[
/* THEME-START */
.bg          { fill: #ffffff; }
.surface     { fill: #f5f7fa; }
.surface-alt { fill: #fafbfc; }
.text        { fill: #1a1a1a; }
.text-muted  { fill: #666666; }
.accent      { fill: #0078d4; }
.accent-stroke { stroke: #0078d4; }
.border      { stroke: #e5e7eb; fill: none; }
.title       { font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 700; }
.subtitle    { font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; font-style: italic; }
.h2          { font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 700; }
.body        { font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 400; }
.body-bold   { font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 700; }
.italic      { font-style: italic; }
/* THEME-END */
]]></style>
```

The `THEME-START` / `THEME-END` lines are required exactly as shown. `apply-theme.sh` replaces everything between them with the contents of the chosen theme.

## Required classes

Themes must define these classes — slides assume them:

| Class | Purpose |
|---|---|
| `bg` | Slide background (`<rect>` covering viewBox) |
| `surface` | Card / header strip backgrounds |
| `surface-alt` | Alternate stripe / softer card |
| `text` | Default text fill |
| `text-muted` | Captions, dates, secondary info |
| `accent` | Bullets, links, section headers, highlighted numbers |
| `accent-stroke` | Stroked variants (lines, borders matching accent) |
| `border` | Table separators, card outlines |
| `title` | Slide title (font-weight 700) |
| `subtitle` | Slide subtitle (italic) |
| `h2` | Section headers (font-weight 700) |
| `body` | Default text (font-weight 400) |
| `body-bold` | Emphasized text (font-weight 700) |
| `italic` | Inline italic |

## Background rect (mandatory)

After the `<style>` block, every slide opens with:

```xml
<rect x="0" y="0" width="1920" height="1080" class="bg" />
```

`svg { background-color: ... }` is NOT a substitute — rsvg-convert and PowerPoint both ignore it. The `<rect>` is the only reliable way to paint the slide background.

## Swapping themes

```bash
./scripts/apply-theme.sh --list                       # show available themes
./scripts/apply-theme.sh light-classic slide.svg      # apply
```

The script:
1. Reads `themes/<name>.css`.
2. Finds the `/* THEME-START */` ... `/* THEME-END */` block in the slide.
3. Replaces the block contents with the CSS file.
4. Leaves everything else untouched.

To re-theme an entire deck:
```bash
for f in slide-*.svg; do ./scripts/apply-theme.sh dark-classic "$f"; done
```

When you switch theme:
- Chart palettes don't auto-update — re-run the chart scripts with matching colors (see `pattern-charts.md`).
- Photos are theme-independent.

## Adding a new theme

Drop a file at `<skill>/themes/<name>.css` that defines every class listed in **Required classes** above. `apply-theme.sh` reads from the skill's `themes/` directory, so new themes there are immediately available to every deck. If a deck keeps a local `themes/` copy (for offline work or theme overrides), sync the file there too. Pull color values from a coherent palette (one accent hue, one neutral surface family, contrast-checked text).

Anti-pattern: forking a theme by editing the inline block in one slide. Always edit `themes/<name>.css` and re-apply.

## Anti-patterns

- Inline `fill="#xxx"` anywhere — breaks the single-source-of-truth rule.
- Editing only the inline THEME block in one slide — next `apply-theme.sh` wipes it. Edit the theme file.
- Adding a new color class to one slide — add it to every theme or it's not a class, it's a special case.
- Using `currentColor` to chain fills — works in browsers, inconsistent in rsvg/PPT.
