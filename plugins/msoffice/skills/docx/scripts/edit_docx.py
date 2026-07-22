#!/usr/bin/env python3
"""Edit a Word .docx body while PRESERVING comments, then re-zip to a new file.

The document body lives in ``word/document.xml``; comments live in
``word/comments.xml`` with ``commentRangeStart/End`` anchors inside
``document.xml``. Editing text that sits INSIDE a comment's anchor range breaks
that comment, so this tool refuses to drop a paragraph that carries a comment
anchor unless ``--force`` is given.

Usage:
    edit_docx.py <in.docx> <out.docx> [operations...]

Operations (repeatable, applied in order):
    --drop-para "PHRASE"     Remove the first <w:p> whose text contains PHRASE.
    --replace "OLD=>NEW"     Literal text replace inside document.xml (first hit).

Always writes <out.docx> as a NEW file — never edit the canonical doc in place;
produce a "*-EDITED.docx" and merge via Word's Review > Compare (see SKILL.md).

Exit codes: 0 ok · 1 error (bad input, phrase not found, comment-anchor guard).
"""
import argparse
import re
import sys
import zipfile


def _paras(xml: str):
    # <w:p> elements do not nest, so a non-greedy match is safe.
    return re.findall(r"<w:p\b.*?</w:p>", xml, re.S)


def _para_text(para: str) -> str:
    return "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", para, re.S))


def _comment_count(zf: zipfile.ZipFile) -> int:
    if "word/comments.xml" not in zf.namelist():
        return 0
    return len(re.findall(r"<w:comment ", zf.read("word/comments.xml").decode("utf-8", "replace")))


def _anchored_ids(doc_xml: str) -> set:
    """IDs that still have a commentRangeStart anchor in the body.

    Comment COUNT is not enough: dropping anchored body text orphans a comment
    (its definition stays in comments.xml, so the count is unchanged) while the
    anchor in document.xml disappears. Diffing anchored IDs catches that.
    """
    return set(re.findall(r'<w:commentRangeStart w:id="(\d+)"', doc_xml))


def drop_para(xml: str, phrase: str, force: bool) -> str:
    for para in _paras(xml):
        if phrase in _para_text(para):
            if not force and re.search(r"w:commentRange(Start|End)|w:commentReference", para):
                raise SystemExit(
                    f"REFUSED: paragraph matching {phrase!r} carries a comment anchor; "
                    "dropping it would break the comment. Re-run with --force to override."
                )
            return xml.replace(para, "", 1)
    raise SystemExit(f"NOT FOUND: no paragraph contains {phrase!r}")


def replace_text(xml: str, spec: str) -> str:
    if "=>" not in spec:
        raise SystemExit(f"BAD --replace {spec!r}: expected 'OLD=>NEW'")
    old, new = spec.split("=>", 1)
    if old not in xml:
        raise SystemExit(f"NOT FOUND: --replace source {old!r} not present")
    return xml.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Edit a .docx body while preserving comments.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("--drop-para", action="append", default=[], metavar="PHRASE")
    ap.add_argument("--replace", action="append", default=[], metavar="OLD=>NEW")
    ap.add_argument("--force", action="store_true", help="allow dropping comment-anchored paragraphs")
    # Preserve operation order across the two flag types.
    args, _ = ap.parse_known_args()
    ops = []
    argv = sys.argv[3:]
    i = 0
    while i < len(argv):
        if argv[i] in ("--drop-para", "--replace") and i + 1 < len(argv):
            ops.append((argv[i], argv[i + 1]))
            i += 2
        else:
            i += 1

    try:
        zin = zipfile.ZipFile(args.infile)
    except (zipfile.BadZipFile, FileNotFoundError) as e:
        print(f"Cannot open {args.infile!r}: {e}")
        return 1
    if "word/document.xml" not in zin.namelist():
        print("Not a Word document (no word/document.xml).")
        return 1

    doc = zin.read("word/document.xml").decode("utf-8")
    before_comments = _comment_count(zin)
    anchors_before = _anchored_ids(doc)

    for flag, value in ops:
        if flag == "--drop-para":
            doc = drop_para(doc, value, args.force)
        elif flag == "--replace":
            doc = replace_text(doc, value)

    anchors_after = _anchored_ids(doc)
    lost_anchors = anchors_before - anchors_after

    # Re-zip: copy every part verbatim, swap in the edited document.xml.
    with zipfile.ZipFile(args.outfile, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = doc.encode("utf-8") if item.filename == "word/document.xml" else zin.read(item.filename)
            zout.writestr(item, data)

    with zipfile.ZipFile(args.outfile) as zchk:
        after_comments = _comment_count(zchk)
        bad = zchk.testzip()

    print(f"wrote {args.outfile}")
    print(f"  operations applied: {len(ops)}")
    print(f"  comments: {before_comments} -> {after_comments}"
          + ("  OK" if before_comments == after_comments else "  !! CHANGED — inspect"))
    print(f"  comment anchors: {len(anchors_before)} -> {len(anchors_after)}"
          + ("  OK" if not lost_anchors else f"  !! ORPHANED comment id(s) {sorted(lost_anchors)} — re-run without dropping their text"))
    print(f"  zip integrity: {'OK' if bad is None else 'BAD: ' + bad}")
    if before_comments != after_comments or lost_anchors or bad is not None:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
