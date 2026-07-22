#!/usr/bin/env python3
"""Extract body paragraphs from a Word .docx (accepted-changes view).

Usage:
    extract_body.py <file.docx>

Prints one line per ``<w:p>`` paragraph from ``word/document.xml``. Tracked
changes are rendered as if ACCEPTED: inserted text (``<w:ins>``) is kept, and
deleted / moved-away text (``<w:del>`` / ``<w:moveFrom>``) is dropped. Tabs
become spaces and whitespace is collapsed. Empty paragraphs print as blank lines
so paragraph structure lines up for a diff.

Pairs with ``extract_comments.py``. Enables a REVERSE reconcile (docx -> markdown):
diff this against the body of a doc freshly rendered from the markdown source to
see exactly which edits were made on the doc side, then fold them back into the
``.md`` (the source of truth). See the docx SKILL.md.

Exits non-zero with a diagnostic hint if the file is not a valid .docx.
"""
import sys
import re
import html
import zipfile


def _clean(x: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def para_text(para: str) -> str:
    # Accepted-changes view: drop deletions and moved-away text.
    para = re.sub(r"<w:del\b.*?</w:del>", "", para, flags=re.S)
    para = re.sub(r"<w:moveFrom\b.*?</w:moveFrom>", "", para, flags=re.S)
    # Walk runs in order: <w:t> text is kept (includes <w:ins> runs); <w:tab> is a space.
    parts = []
    for m in re.finditer(r"<w:t\b[^>]*>(.*?)</w:t>|<w:tab\b[^>]*/?>", para, re.S):
        parts.append(m.group(1) if m.group(1) is not None else " ")
    return _clean("".join(parts))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        with open(path, "rb") as f:
            magic = f.read(4)
        print(f"Not a valid .docx (zip). First bytes: {magic!r}")
        if magic[:2] == b"\xd0\xcf":
            print(
                "  -> OLE2 container. Usually an IRM/sensitivity-label ENCRYPTED docx "
                "or a legacy Word 97-2003 .doc. See the docx SKILL.md."
            )
        return 1
    if "word/document.xml" not in z.namelist():
        print("Not a Word document (no word/document.xml).")
        return 1

    doc_xml = z.read("word/document.xml").decode("utf-8", "replace")
    for para in re.findall(r"<w:p\b.*?</w:p>", doc_xml, re.S):
        print(para_text(para))
    return 0


if __name__ == "__main__":
    sys.exit(main())
