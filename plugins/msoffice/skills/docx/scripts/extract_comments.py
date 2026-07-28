#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["python-docx"]
# ///
"""Extract comments from a Word .docx — author, date, text, and resolved state.

Usage (uv auto-installs python-docx from the inline metadata above):
    uv run extract_comments.py <file.docx>              # writes <file>.comments.json + prints summary
    uv run extract_comments.py <file.docx> --out FILE   # write the JSON to a chosen path
    uv run extract_comments.py <file.docx> --stdout     # print JSON to stdout (write no file)
    uv run extract_comments.py <file.docx> --context 3  # look up what comment #3 is anchored to

Each JSON entry is one comment thread:
    {
      "id": "3",                      # comment ref id — the handle back into the docx
      "resolved": false,              # from commentsExtended.xml (w15:done)
      "context_hint": {               # what the comment sits on — orientation, NOT a locator
        "marks": "the highlighted text",        # null for a point anchor
        "surrounding_text": "the containing paragraph"
      },
      "comments": [                   # the thread, root first
        {"id": "3", "author": "Alice", "date": "2026-07-22", "text": "..."}
      ]
    }

`context_hint` tells you what a comment is about; do not use it to find the
comment in the markdown source. Reviewers anchor to repeated phrases, single
words, or nothing at all, and any anchor goes stale the moment the markdown is
edited. `--context ID` prints the same thing for one comment straight from the
docx, for when all you have is an id.

Comment metadata/text come from python-docx; thread links (w15:paraIdParent) and
resolved state (w15:done) are read from the raw parts, which python-docx does not
expose. Thread/resolved data only exists in real Word-authored docs
(commentsExtended.xml); when absent, each comment is its own unresolved thread.
"""
import json
import os
import sys
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
W14 = "{http://schemas.microsoft.com/office/word/2010/wordml}"
W15 = "{http://schemas.microsoft.com/office/word/2012/wordml}"

# Anchors can swallow a whole table; keep the hint readable.
HINT_MAX_CHARS = 500


def _norm(text: str) -> str:
    return " ".join((text or "").split())


def anchored_spans(doc) -> dict:
    """Map comment id -> anchored body text, from commentRangeStart/End markers.

    Walk the body in document order; a run's text belongs to every comment whose
    range is currently open. Handles overlapping/nested ranges.
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
    return {cid: _norm("".join(parts)) for cid, parts in buf.items()}


def _clip(text: str):
    if not text:
        return None
    return text if len(text) <= HINT_MAX_CHARS else text[:HINT_MAX_CHARS] + " …"


def containing_paragraphs(doc, cid: str) -> list:
    """Body paragraphs that carry this comment's range start or reference."""
    return [
        _norm(p.text)
        for p in doc.paragraphs
        if any(
            el.get(W + "id") == cid
            for el in p._p.iter()
            if el.tag in (W + "commentRangeStart", W + "commentReference")
        )
    ]


def print_context(doc, cid: str) -> int:
    """Show what a comment is anchored to: the marked text and its paragraph(s)."""
    anchor = anchored_spans(doc).get(cid)
    paras = containing_paragraphs(doc, cid)
    if anchor is None and not paras:
        print(f"No comment with id {cid!r} found in this document.")
        return 1
    print(f"COMMENT #{cid}")
    print(f"  marks: {anchor!r}" if anchor else "  marks: (nothing — point anchor)")
    for p in paras:
        print(f"  in paragraph: {p}")
    return 0


def _read_part(zf, name):
    try:
        from lxml import etree
    except ImportError:
        return None
    if name not in zf.namelist():
        return None
    return etree.fromstring(zf.read(name))


def thread_meta(path: str) -> dict:
    """From the raw parts: comment id -> {"resolved": bool, "parent": <id or None>}.

    Maps each comment to its paragraph paraId(s) (comments.xml), then to the
    matching commentEx (commentsExtended.xml) for done + paraIdParent.
    """
    meta: dict = {}
    with zipfile.ZipFile(path) as zf:
        comments = _read_part(zf, "word/comments.xml")
        extended = _read_part(zf, "word/commentsExtended.xml")
        if comments is None:
            return meta
        cid_paraids, paraid_cid = {}, {}
        for c in comments.iter(W + "comment"):
            cid = c.get(W + "id")
            pids = [p.get(W14 + "paraId") for p in c.iter(W + "p") if p.get(W14 + "paraId")]
            cid_paraids[cid] = pids
            for pid in pids:
                paraid_cid[pid] = cid
        ex = {}
        if extended is not None:
            for e in extended.iter(W15 + "commentEx"):
                ex[e.get(W15 + "paraId")] = (
                    e.get(W15 + "done") in ("1", "true"),
                    e.get(W15 + "paraIdParent"),
                )
        for cid, pids in cid_paraids.items():
            resolved, parent = False, None
            for pid in pids:
                done, parent_pid = ex.get(pid, (False, None))
                resolved = resolved or done
                if parent_pid and paraid_cid.get(parent_pid):
                    parent = paraid_cid[parent_pid]
            meta[cid] = {"resolved": resolved, "parent": parent}
    return meta


def build_threads(doc, path):
    """Return ordered list of thread dicts: {id, resolved, context_hint, comments}."""
    by_id = {}
    order = []
    for c in doc.comments:
        cid = str(c.comment_id)
        order.append(cid)
        by_id[cid] = {
            "id": cid,
            "author": c.author,
            "date": c.timestamp.date().isoformat() if c.timestamp else "",
            "text": _norm(c.text),
        }
    meta = thread_meta(path)
    spans = anchored_spans(doc)

    # Group replies under their root.
    children: dict = {}
    roots = []
    for cid in order:
        parent = meta.get(cid, {}).get("parent")
        if parent and parent in by_id:
            children.setdefault(parent, []).append(cid)
        else:
            roots.append(cid)

    threads = []

    def members_of(cid, seen):
        """The comment and all its descendants, depth-first in document order."""
        if cid in seen:
            return []
        seen.add(cid)
        out = [cid]
        for child in children.get(cid, []):
            out.extend(members_of(child, seen))
        return out

    for root in roots:
        members = members_of(root, set())
        anchor = next((spans.get(m, "") for m in members if spans.get(m)), "")
        paras = containing_paragraphs(doc, root)
        threads.append({
            "id": root,
            "resolved": bool(meta.get(root, {}).get("resolved")),
            "context_hint": {
                "marks": _clip(anchor),
                "surrounding_text": _clip(" ".join(paras)),
            },
            "comments": [by_id[m] for m in members],
        })
    return threads


def print_text(threads) -> None:
    print(f"COMMENT THREADS: {len(threads)}")
    for t in threads:
        mark = "RESOLVED" if t["resolved"] else "open"
        marks = t["context_hint"]["marks"]
        if marks and len(marks) > 80:
            marks = marks[:80] + " …"
        on = f" on: “{marks}”" if marks else ""
        print(f"\n[#{t['id']} {mark}]{on}")
        for c in t["comments"]:
            stamp = f" {c['date']}" if c["date"] else ""
            print(f"    [{c['author']}{stamp}] {c['text']}")


def main() -> int:
    argv = sys.argv[1:]
    to_stdout = False
    out = None
    context_id = None
    files = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--stdout":
            to_stdout = True
        elif a == "--out":
            out = argv[i + 1] if i + 1 < len(argv) else None
            i += 1
        elif a == "--context":
            context_id = argv[i + 1] if i + 1 < len(argv) else None
            i += 1
        elif not a.startswith("-"):
            files.append(a)
        i += 1
    if len(files) != 1:
        print(__doc__)
        return 2
    path = files[0]
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

    if context_id is not None:
        return print_context(doc, context_id)

    threads = build_threads(doc, path)
    if to_stdout:
        print(json.dumps(threads, indent=2, ensure_ascii=False))
        return 0

    if out is None:
        out = os.path.splitext(path)[0] + ".comments.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(threads, f, indent=2, ensure_ascii=False)
    print_text(threads)
    resolved = sum(1 for t in threads if t["resolved"])
    print(f"\n→ wrote {len(threads)} comment threads ({resolved} resolved) to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
