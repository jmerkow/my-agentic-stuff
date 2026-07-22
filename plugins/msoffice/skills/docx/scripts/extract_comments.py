#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["python-docx"]
# ///
"""Extract comments from a Word .docx — author, date, text, resolved state, and
the anchored segment (so the comment can be located in the source markdown).

Usage (uv auto-installs python-docx from the inline metadata above):
    uv run extract_comments.py <file.docx>            # human-readable
    uv run extract_comments.py <file.docx> --json     # structured JSON array

Each JSON entry is one comment thread:
    {
      "id": "3",                      # root comment ref id — go back to the docx for more
      "segment": "the highlighted text",   # or ["head words", "tail words"] if long; null if none
      "resolved": false,              # from commentsExtended.xml (w15:done)
      "comments": [                   # the thread, root first
        {"id": "3", "author": "Alice", "date": "2026-07-22", "text": "..."}
      ]
    }

Comment metadata/text come from python-docx; the anchored segment, thread links
(w15:paraIdParent) and resolved state (w15:done) are read from the raw parts,
which python-docx does not expose. Thread/resolved data only exists in real
Word-authored docs (commentsExtended.xml); when absent, each comment is its own
unresolved thread.
"""
import json
import sys
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
W14 = "{http://schemas.microsoft.com/office/word/2010/wordml}"
W15 = "{http://schemas.microsoft.com/office/word/2012/wordml}"

SEGMENT_MAX_CHARS = 200
HEADTAIL_WORDS = 12


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


def segment_for(text: str):
    """The locator used to find the anchor in the markdown: full text if short,
    else a [head, tail] pair; None if there's no anchored text."""
    if not text:
        return None
    if len(text) <= SEGMENT_MAX_CHARS:
        return text
    words = text.split()
    return [" ".join(words[:HEADTAIL_WORDS]), " ".join(words[-HEADTAIL_WORDS:])]


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
    """Return ordered list of thread dicts: {id, segment, resolved, comments}."""
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
    for root in roots:
        members = [root] + children.get(root, [])
        anchor = next((spans.get(m, "") for m in members if spans.get(m)), "")
        threads.append({
            "id": root,
            "segment": segment_for(anchor),
            "resolved": bool(meta.get(root, {}).get("resolved")),
            "comments": [by_id[m] for m in members],
        })
    return threads


def print_text(threads) -> None:
    print(f"COMMENT THREADS: {len(threads)}")
    for t in threads:
        seg = t["segment"]
        if isinstance(seg, list):
            loc = f"\u201c{seg[0]} … {seg[1]}\u201d"
        elif seg:
            loc = f"\u201c{seg}\u201d"
        else:
            loc = "(no anchored text — see docx)"
        mark = "RESOLVED" if t["resolved"] else "open"
        print(f"\n[#{t['id']} {mark}] on: {loc}")
        for c in t["comments"]:
            stamp = f" {c['date']}" if c["date"] else ""
            print(f"    [{c['author']}{stamp}] {c['text']}")


def main() -> int:
    argv = sys.argv[1:]
    as_json = "--json" in argv
    files = [a for a in argv if not a.startswith("-")]
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

    threads = build_threads(doc, path)
    if as_json:
        print(json.dumps(threads, indent=2, ensure_ascii=False))
    else:
        print_text(threads)
    return 0


if __name__ == "__main__":
    sys.exit(main())
