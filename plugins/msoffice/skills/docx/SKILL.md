---
name: docx
description: >-
  Read, convert, revise, and troubleshoot Microsoft Word documents stored on OneDrive/SharePoint —
  extract comments (with authors/dates) from a .docx, convert a .docx to markdown/plain text an
  agent can read, revise a reviewed doc by regenerating from its markdown source and merging with
  Word Compare (comments preserved), reconcile a reviewed .docx against the local markdown, and
  diagnose access failures. Use when: reading or downloading a Word doc from a OneDrive/SharePoint
  sharing link; pulling review comments out of a document; converting a .docx to text; diffing a
  reviewed doc against its markdown source; exporting markdown to a styled Word doc; or hitting
  errors like "Session not found" (MPC -32001), "encrypted, IRM, or legacy .doc format", or a
  stale/empty local OneDrive copy. Keywords: docx, Word, OneDrive, SharePoint, GetDocumentContent,
  comments, IRM, sensitivity label, compatibility mode, session not found, pandoc, convert docx to
  markdown, reconcile, diff, python-docx, base64 binary read, preserve comments, Word Compare,
  redline, tracked changes, commentRangeStart.
---

# Word (.docx)

Working with Word documents stored in OneDrive/SharePoint. This skill is a starting point —
expand it as new cases come up.

Think of it as **two lifecycle phases**:
- **Phase 1 — author the doc the first time** (markdown → styled `.docx` → share with reviewers).
- **Phase 2 — revise a doc that's been sent off or arrived with comments**, using Word Compare so
  reviewer comment threads survive.

`Read` and `Diagnostics` below are shared utilities used by both. Diagnostics is generic to any
Office file in OneDrive/SharePoint (not just Word) — factor it into a shared skill if other Office
doc skills appear.

## Tools

> Tool names below are short (e.g. `GetDocumentContent`). The real MCP tool names carry prefixes
> that change over time — don't treat these as literal, and match by role (Documents / OneDrive /
> SharePoint) rather than by a specific server alias.

- **Documents tool** (`GetDocumentContent`) — takes a sharing URL, returns document text **and
  comments**. Fastest path when it works. Only handles clean, unencrypted OOXML `.docx`.
- **OneDrive file tools** (personal `*-my.sharepoint.com/personal/...`): `getFileOrFolderMetadataByUrl`,
  `readSmallBinaryFile…` (base64, <5 MB), `readSmallTextFile…`.
- **SharePoint file tools** (team sites): metadata + binary / text file reads.
- **pandoc** — generate `.docx` from markdown (see the `pandocx` skill) and convert a `.docx` back
  to markdown / plain text for reading and diffing.
- **`uv run scripts/extract_comments.py <file.docx>`** — extract comment threads to a JSON file
  (`<file>.comments.json` by default): id, author, date, text, resolved state, and a `context_hint`.
  `--context ID` prints the same context for a single comment when all you have is an id.

## Core operations

Three operations come up constantly, independent of the authoring lifecycle below:

1. **Get comments from a `.docx`** — `uv run scripts/extract_comments.py <file.docx>` writes
   `<file>.comments.json` beside the doc: per-comment id, author, date, text, `resolved` state, and
   a `context_hint` of `{marks, surrounding_text}` — the text the comment sits on and its containing
   paragraph. `--out PATH` writes it elsewhere; `--stdout` pipes it; `--context ID` prints the
   context for one comment straight from the docx.

   **`context_hint` is orientation, not a locator.** Use it to understand what a comment is about;
   don't use it to find the spot in the markdown. Reviewers anchor to repeated phrases, single
   words, or nothing at all, and any anchor goes stale as soon as the markdown is edited — work from
   the comment's meaning instead, and go back to the docx by `id` for anything ambiguous.
2. **Convert a `.docx` to readable text** — `pandoc doc.docx -t markdown` (structure) or
   `pandoc doc.docx -t plain --wrap=none` (one paragraph per line, for diffing). Add
   `--track-changes=accept` for the accepted view of a doc carrying tracked changes. (Image/layout
   rendering isn't available here — text only.)
3. **Reconcile a reviewed `.docx` against the local markdown** — see exactly what the doc-side edits
   were by rendering *both* sides through pandoc's plain writer (so formatting noise cancels), then
   diffing:
   ```bash
   pandoc canonical.docx -t plain --wrap=none --track-changes=accept > /tmp/canon.txt
   pandoc source.md      -t plain --wrap=none                        > /tmp/md.txt
   diff /tmp/md.txt /tmp/canon.txt
   ```
   Apply the deltas back into the markdown (the source of truth), then regenerate for the next round.

## Phase 1 — Author the doc the first time

Create the doc from a markdown source, then share it with reviewers.

1. **Write the content in markdown** and keep it in the repo — this is the **source of truth** for
   the life of the doc (Phase 2 edits happen here too, not in the `.docx`).
2. **Generate the `.docx` from the markdown** with the `pandocx` skill (bundled house template,
   author stamping, and list handling all live there).
   - The generated `.docx` then **doubles as the style reference** for every future regeneration —
     Phase 2 redlines stay clean with no separate template.
   - Targeting a synced OneDrive folder? Write straight to the local mount
     (`/mnt/c/Users/<user>/OneDrive - .../...`) and let OneDrive sync — avoids the flaky upload tools.
3. **Share the `.docx`** with reviewers (OneDrive/SharePoint). From here it's the *canonical* doc
   that may come back with comments → Phase 2.

## Phase 2 — Revise a sent-off or incoming doc (preserve comments)

Once the doc is out for review (or an incoming doc arrives) and may carry reviewer comments, do NOT
hand-edit the `.docx`. **No API edits Word body text.** WorkIQ exposes a full Graph-style CRUD
surface (fetch / create / update / delete / actions), and the Documents tool can add/reply to
comments — but none of them edit paragraphs. So regenerate the doc from its markdown source, then
let **Word's Compare** merge the change back as a reviewable redline.

**Key fact that makes this easy:** Word's Compare keeps the *Original's* comments, so reviewer
comment threads are never lost — which means the **revised copy can be regenerated however you want**
(it doesn't need to carry the comments itself).

### Primary loop — markdown source of truth + pandoc + Compare

Best when there's a markdown mirror of the doc and/or the edit volume is large.

> **Build the `.docx` last.** It's a render of the markdown — complete all content edits *and* a
> proofreading pass on the `.md` before running pandoc, or you'll ship (and have to rebuild) a docx
> with known typos, then redo the whole Compare/Accept pass.

1. **Edit the markdown, not the docx.** It's diffable, revertable, and in git — iterate freely here.
   Keep the markdown mirror in the repo as the source of truth.
2. **Regenerate the revised `.docx` from the markdown** with the `pandocx` skill, but point its
   `--reference-doc` at the canonical `.docx` itself (not the bundled template) so the redline shows
   *content* diffs, not formatting noise.
3. **Verify the regenerated docx actually contains the edits** — unzip `word/document.xml` and grep
   for a few expected phrases. Catches stale regenerations.
4. **Compare in Word → Review → Compare → Compare:** *Original* = canonical DRAFT, *Revised* = the
   regenerated file. Under **More → Show changes → Comments**, keep the **Original's** comments. The
   revised doc's Author (set when generating it — see `pandocx`) pre-fills **"Label changes with"**, so
   the redline is attributed to the author automatically instead of prompting each time.
5. **Accept/Reject** the tracked changes in the merged result — that becomes the new canonical.
   (Deleted text stays visible with strikethrough, and still appears in extractor output because it
   lives in `<w:del>`, until **Accept All Changes**.)

The regenerated revised docx has **no comments** — expected; they come from the Original side of
Compare.

### Always write a new file — never overwrite the canonical in place

The regenerated revised doc is a **new file** (`*-REVISED.docx`) you merge via Compare — which also
keeps the Original's comments. **Never overwrite the canonical directly;** in-place writes are
unreliable (file locks, propagation lag, conflicted copies) — see *Gotchas*.

> **Editing a `.docx` in place** (surgical body edits without the regenerate loop) is deferred to a
> separate skill — not covered here yet.

## Read a document's content and comments

1. **Try `GetDocumentContent`** with the sharing URL first. If it returns content, done.
2. **If it errors**, fall back to fetching the raw bytes and reading locally:
   - `getFileOrFolderMetadataByUrl(url)` → note `size`, `file.mimeType`, `irmEnabled`,
     `irmEffectivelyEnabled`, and the item `id`.
   - Read the small binary file by `id` (OneDrive or the SharePoint equivalent) → base64 bytes.
   - Decode the base64 to a file, then run `uv run scripts/extract_comments.py <file.docx>`.
   - Verify the decoded bytes look right: a real `.docx` starts with `PK` (a zip). If it starts
     with `d0 cf 11 e0` it is an OLE2 container — see diagnostics below.

## Gotchas

Things that bite you — check before assuming a document is broken or an operation failed.

- **`MPC -32001: Session not found`** — the MCP server's session expired. It is not an input
  error. Ask the user to restart that specific MCP server (mail, OneDrive, Word, etc.), then retry.
- **"encrypted, IRM, or legacy .doc format"** (from `GetDocumentContent`) — this one error covers
  several distinct causes. Check the metadata and the raw bytes to tell them apart:
  - **IRM / sensitivity-label encryption.** Check `irmEnabled` / `irmEffectivelyEnabled` in the
    metadata. If set, the file is encrypted by a protective label. The raw bytes are an OLE2
    container (`d0cf11e0`) whose streams include `DataSpaces/TransformInfo/DRMEncryptedTransform`
    and `EncryptedPackage` (inspect with `python3 -c "import olefile; …"`). **This cannot be
    decrypted locally** — it needs the user's Azure RMS rights. The user must set a
    **non-encrypting label** (e.g. "General") in Word, then re-save.
  - **Legacy Word 97-2003 `.doc`.** Also `d0cf11e0`, but no DRM streams. Happens when Word opens a
    file in **Compatibility Mode** and a plain Save writes `.doc` while keeping the `.docx`
    extension. Fix: **File → Info → Convert** (or Save As → "Word Document (.docx)").
- **Stale content after a re-save (propagation lag).** Right after a Word save/label change, the
  metadata can update (new size, `irmEnabled: false`) while the **content endpoints still serve the
  old bytes** — `GetDocumentContent` keeps erroring and the binary read returns the previous
  version. Don't trust an immediate read. Wait and retry, or have the user **Save As a new filename**
  (a fresh item id has no stale cache) — this is the most reliable way to dodge it.
- **Local OneDrive copies (`/mnt/c/Users/.../OneDrive - .../`)** may be **unsynced stubs** (Files
  On-Demand) or a locked/partial file while Word has it open. Symptoms: unchanged size, or `file`
  reports `0 words / 0 pages`. Prefer the cloud bytes over a suspect local copy.
- **Writing a `.docx` in place is unreliable.** A Graph in-place upload (upload-session) or a local
  `cp` over the OneDrive mount **hangs or conflicts when the doc is open in Word** (file lock), and
  overwriting an unsynced local file spawns a "…-conflicted copy". SharePoint re-saves server-side,
  so byte size shifts — **verify by content, not size.** Use the regenerate → Compare loop instead.
