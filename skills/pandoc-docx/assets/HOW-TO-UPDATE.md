# Updating the template

The reference template is `assets/template.docx`. Pandoc copies its **named styles**
into every converted doc.

## Edit a style

1. Open `assets/template.docx` in Word.
2. Home → Styles → right-click a style → **Modify**. Change font, spacing, color there.
   - Edit the *style*, not selected text. Direct formatting is ignored by pandoc.
3. Save as `.docx`.

## Then run cleanup (required)

Saving in Word adds a sensitivity label and stamps your name. Strip both before using:

```bash
cd /tmp && rm -rf clean && mkdir clean && cd clean
unzip -q /path/to/assets/template.docx
rm -f docMetadata/LabelInfo.xml
sed -i 's#<dc:creator>[^<]*</dc:creator>#<dc:creator></dc:creator>#' docProps/core.xml
sed -i 's#<cp:lastModifiedBy>[^<]*</cp:lastModifiedBy>#<cp:lastModifiedBy></cp:lastModifiedBy>#' docProps/core.xml
rm -f word/comments*.xml word/people.xml
zip -q -r -X /path/to/assets/template.docx '[Content_Types].xml' _rels docProps word
```

## Test

```bash
pandoc examples/template-fancy.md -o /tmp/out.docx \
  --from=markdown+fancy_lists --reference-doc=assets/template.docx
```

Open `/tmp/out.docx` and check the change.

## Styles pandoc uses

`Heading 1`–`4`, `Title`, `Compact` (list spacing), `Table`, `SourceCode`,
`Verbatim Char`, `FootnoteReference`. Bullet glyphs and list numbering come from
pandoc, not the template.
