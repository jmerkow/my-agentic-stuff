---
name: pandocx
description: Convert markdown files to styled .docx using pandoc with a bundled reference template. Use when the user asks to generate a Word document, convert markdown to docx, or export a document.
---

# Pandoc DOCX Conversion

Convert markdown to styled `.docx` using pandoc with the bundled reference template.

## Command

```bash
pandoc <input>.md -o <output>.docx --from=markdown+fancy_lists \
  --reference-doc=<skill-dir>/assets/template.docx \
  --metadata author="<author>"
```

Where `<skill-dir>` is the directory containing this SKILL.md.

## Rules

- Default `--reference-doc` to `assets/template.docx` in this skill's directory. To match an existing document's styles (e.g. regenerating a doc for Word Compare), point it at that `.docx` instead.
- Stamp the **Author** with `--metadata author="<author>"` (pandoc writes `dc:creator`). Never infer `<author>` without the user's confirmation; omit the flag if unknown.
- Keep `+fancy_lists` in `--from` so lettered/roman markers (`a.`, `b.`, `i.`, `ii.`) render as real Word lists and round-trip cleanly.
- **Separate list items with a blank line** (loose lists); tight lists render in pandoc's cramped `Compact` style, which looks malformed for multi-sentence bullets.
- Strip YAML frontmatter if pandoc chokes on it. Pipe through `sed '1{/^---$/,/^---$/d}'` first.
- Output file goes next to the input file unless the user specifies otherwise.
- If multiple files are requested, convert each separately.

## Fancy lists (lettered / roman)

The `+fancy_lists` extension lets the markdown use `a.`/`b.`/`c.` and `i.`/`ii.` list
markers, which map to real Word lettered and roman numbering in the `.docx`.

- Use fancy markers when the document is authored specifically to become a `.docx` and the
  outline lettering matters (legal-style outlines, structured specs).
- Tradeoff: fancy markers do NOT render as ordered lists in plain markdown previews
  (GitHub, VS Code). They show as literal text. For docs meant to be read as markdown, use
  plain numbered lists (`1.`/`2.`) instead. They render everywhere and still convert to
  decimal numbering in the `.docx`.

## Example

`examples/template-fancy.md` is a reference document that exercises the template's styles:
headings, fancy lettered/roman lists, bullets, a table, blockquote, inline and fenced code,
and a footnote. Convert it to see what the template produces:

```bash
pandoc examples/template-fancy.md -o /tmp/template-fancy.docx \
  --from=markdown+fancy_lists --reference-doc=assets/template.docx \
  --metadata author="<author>"
```

The `--metadata author="<author>"` flag stamps the doc's Author (`dc:creator`), which pre-fills
Word's **Compare → "Label changes with"** field so the redline is attributed without prompting.

- `git config user.name` is a reasonable starting point for `<author>`, but there may be others
  (the user's M365/display name, or the doc's existing metadata). Confirm with the user before stamping.

## Styles the template defines

The reference template carries named styles so generated docs are consistent:

- `Heading 1`–`Heading 4`, `Title`
- `SourceCode` (fenced code, Consolas + light shading) and `Verbatim Char` (inline code)
- `FootnoteReference` (superscript marker)
- `Table` (accent header + horizontal row banding)
- `Compact` (tight spacing between list items, with trailing space after the list)

To change the look, edit these styles in `assets/template.docx`. Pandoc generates its own
list numbering, so bullet glyphs and list `numId`s come from pandoc, not the reference doc.
