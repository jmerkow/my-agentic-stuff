#!/usr/bin/env python3
"""Extract comments (and their anchored text) from a Word .docx file.

Usage:
    extract_comments.py <file.docx>

Prints each comment with its author, date, text, and the document text span it
is anchored to. Exits non-zero with a diagnostic hint if the file is not a valid
.docx (e.g. legacy .doc / IRM-encrypted — see the docx SKILL.md).
"""
import sys
import re
import html
import zipfile


def strip(x: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


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
                "or a legacy Word 97-2003 .doc. Check the file's OneDrive metadata "
                "(irmEnabled / irmEffectivelyEnabled) and see the docx SKILL.md."
            )
        return 1

    names = set(z.namelist())
    if "word/comments.xml" not in names:
        print("No comments in this document (no word/comments.xml part).")
        return 0

    comments_xml = z.read("word/comments.xml").decode("utf-8", "replace")
    doc_xml = ""
    if "word/document.xml" in names:
        doc_xml = z.read("word/document.xml").decode("utf-8", "replace")

    matches = re.findall(
        r'<w:comment\b[^>]*?w:id="(\d+)"[^>]*?w:author="([^"]*)"'
        r'(?:[^>]*?w:date="([^"]*)")?[^>]*>(.*?)</w:comment>',
        comments_xml,
        re.S,
    )
    print(f"COMMENT COUNT: {len(matches)}")
    for cid, author, date, body in matches:
        text = strip(body)
        anchor = ""
        m = re.search(
            r'<w:commentRangeStart w:id="' + cid + r'"/>(.*?)'
            r'<w:commentRangeEnd w:id="' + cid + r'"/>',
            doc_xml,
            re.S,
        )
        if m:
            anchor = strip(m.group(1))[:160]
        d = f" {date[:10]}" if date else ""
        print(f"\n[{author}{d}] {text}")
        if anchor:
            print(f"    on: \u201c{anchor}\u201d")
    return 0


if __name__ == "__main__":
    sys.exit(main())
