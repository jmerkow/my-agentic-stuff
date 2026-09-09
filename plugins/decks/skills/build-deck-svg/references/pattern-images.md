# Images and photos

Embed raster images (charts, photos, screenshots) via `<image>` with both `href` and `xlink:href` set.

## Pattern

```xml
<image
  href="./assets/team-workshop/group.png"
  xlink:href="./assets/team-workshop/group.png"
  x="1240" y="220" width="620" height="350"
  preserveAspectRatio="xMidYMid slice" />
```

Required attributes:

- **Both `href` and `xlink:href`** — rsvg-convert prefers one, PowerPoint the other. Set both to the same value.
- **`preserveAspectRatio`** — controls fit. See below.
- **Path** — relative from the slide SVG, typically `./assets/<subdir>/<name>.png`.

### Why the relative path matters

The deck dir mirrors `ppt/media/` inside the built `.pptx`. A slide referencing `./assets/chart.png` resolves the same way under rsvg-convert (preview) and under PowerPoint (built). Never use absolute paths or paths that escape the deck dir — they break the build invariant. See `pptx-export.md`.

## Aspect ratio behavior

| Value | Behavior |
|---|---|
| `xMidYMid meet` | Letterbox — show entire image inside the box, may leave gaps |
| `xMidYMid slice` | Crop — fill the box entirely, may clip edges |
| `none` | Stretch — usually wrong |

Charts → `meet` (don't crop axis labels). Photos → `slice` (no awkward whitespace).

## Caption pattern

Captions go in a `<text>` block immediately below the image, in muted text:

```xml
<image href="./assets/team-workshop/group.png" xlink:href="..." x="1240" y="220" width="620" height="350" preserveAspectRatio="xMidYMid slice" />
<text x="1240" y="592" class="body text-muted" font-size="16">L→R: Dr. Rivera, Dr. Okafor, Alex Chen,</text>
<text x="1240" y="614" class="body text-muted" font-size="16">Dr. Patel, Jordan Lee, Sam Morgan.</text>
```

Two short lines beat one long one — captions wrap badly in SVG.

## Staging photos

Photos almost always need renaming and a clean subdir:

```bash
mkdir -p <slides-root>/assets/<event-name>/
cp "source dir/group photo.png" <slides-root>/assets/<event-name>/group.png
cp "source dir/pic of room.png" <slides-root>/assets/<event-name>/room.png
```

Don't reference paths with spaces or punctuation. Rename to short, lowercase, hyphen-separated.

## File-lock gotcha (WSL + VS Code)

If `cp` fails with permission denied on a file that exists, a Windows process (often the VS Code image preview tab) is holding it open. Either:

1. Close the preview tab in VS Code, OR
2. Copy under a new name (`-v2.png`) and update the slide's `href`.

## Anti-patterns

- Embedding images as base64 data URIs — bloats the SVG, breaks diffs.
- `<use href="#image-symbol">` — text contents of the referenced image are dropped by some renderers. Use `<image>`.
- Linking to a path outside `<slides-root>/` — breaks portability. Copy into `assets/`.
- `width` / `height` matching the source's pixel size — over-resolves; the slide is 1920×1080 max.
