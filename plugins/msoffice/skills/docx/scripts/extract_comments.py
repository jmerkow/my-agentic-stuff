#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["python-docx"]
# ///
"""Extract comments (author, date, text, and anchored span) from a Word .docx.

Usage (uv auto-installs python-docx from the inline metadata above):
    uv run extract_comments.py <file.docx>

Comment metadata and text come from python-docx; the anchored body span (the
text a comment points at) is read from the document body's
commentRangeStart/End markers, which python-docx does not expose directly.
"""
import sys

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def anchored_spans(doc) -> dict:
    """Map comment id -> anchored body text, from commentRangeStart/End markers.

    Walk the body in document order; a run's text belongs to every comment
    whose range is currently open. Handles overlapping/nested ranges.
    """
    active: set = set()
    buf: dict = {}
    for el in doc.element.body.iter():
        tag = el.tag
        if tag == W + "commentRangeStart":
            cid = el.get(W + "id")
            active.add(cid)
            buf.setdefault(cid, [])
        elif tag == W + "commentRangeEnd":
            active.discard(el.get(W + "id"))
        elif tag == W + "t" and active:
            for cid in active:
                buf[cid].append(el.text or "")
    return {cid: "".join(parts) for cid, parts in buf.items()}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    try:
        from docx import Document
    except ImportError:
        print("Requires python-docx. Run via uv:  uv run extract_comments.py <file.docx>")
        return 2

    try:
        doc = Document(path)
    except Exception as e:  # noqa: BLE001 - report any open failure with a hint
        with open(path, "rb") as f:
            magic = f.read(4)
        print(f"Could not open as .docx: {e}")
        if magic[:2] == b"\xd0\xcf":
            print(
                "  -> OLE2 container. Usually an IRM/sensitivity-label ENCRYPTED docx "
                "or a legacy Word 97-2003 .doc. Check the file's OneDrive metadata "
                "(irmEnabled / irmEffectivelyEnabled) and see the docx SKILL.md."
            )
        return 1

    comments = list(doc.comments)
    print(f"COMMENT COUNT: {len(comments)}")
    if not comments:
        return 0

    spans = anchored_spans(doc)
    for c in comments:
        date = c.timestamp.date().isoformat() if c.timestamp else ""
        stamp = f" {date}" if date else ""
        text = " ".join((c.text or "").split())
        print(f"\n[{c.author}{stamp}] {text}")
        anchor = " ".join(spans.get(str(c.comment_id), "").split())[:160]
        if anchor:
            print(f"    on: \u201c{anchor}\u201d")
    return 0


if __name__ == "__main__":
    sys.exit(main())
