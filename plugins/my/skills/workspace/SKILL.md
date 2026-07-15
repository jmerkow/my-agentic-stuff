---
name: workspace
description: >
  Workspace topology inspector and reconciler. Marker: my-workspace.yaml at root
  (also the index and the only loose file unless a file has its own index
  entry). Default mode is read-only.
  Reconcile only after proposing an exact plan and receiving explicit consent.
  Never auto-assigns vc_exception — propose, confirm per-dir.
  Keywords: workspace, conventions, layout, validate, is my workspace in a good
  state, topology, manifest, index.
---

# Workspace

## The Model

Root is a **mount point** — not a git repo, no loose files, only directories. `my-workspace.yaml` at root is the index (the only loose file allowed at root, or a file with its own index entry as an explicit exception).

**Discovery is root-level only.** The agent reconciles the top-level entries and never recurses into subdirectories on its own. Every top-level directory must be either listed in `my-workspace.yaml` (with a `description`, and made compliant — `.git` present or a `vc_exception: <reason>`) **or moved out** of the root. `vc_exception` absent means "expected to be a git repo."

**Common defaults** — seed these in a new `my-workspace.yaml`, but stay loose (list only what the workspace actually has): `.eng`, `.github`, `sandbox`, `.vscode`, `*.worktrees`. The validator does no special-casing — any directory present at root simply needs an index entry.

`.eng/` at root — engineering state. `.github/` — optional, Copilot customization only (`copilot-instructions.md`; root `AGENTS.md` maps to `copilot-instructions.md`, root-level only). Worktrees for `repoX/` live at `repoX.worktrees/<branch>/`.

### Index schema

```yaml
repoName:
  description: One-line description   # required
  vc_exception: reason                # absent → git repo expected
  reference-only: true                # optional; read-only reference
```

Starter defaults for a new workspace (keep what applies, drop the rest):

```yaml
.eng:
  description: engineering state
.github:
  description: Copilot customization (copilot-instructions.md)
sandbox:
  description: scratch / experiments
```

**Never write `vc_exception` autonomously** — propose the value, confirm per-dir.

### Sub-dir entries (on request only)

Nested entries like `repoX/subdir` are optional — add them **only when asked** (e.g. "add the sub-dirs in `repoX` to the index"). Then `ls` that directory, add the named entries, and the same rules apply (each needs `.git` or a `vc_exception`). Never auto-populate sub-dirs.

## Behavior

| Mode | Trigger | Mutates? |
|---|---|---|
| **Inspect** (default) | validate / check / status / is my workspace in a good state | No |
| **Reconcile** | after exact plan + explicit approval | Yes |

## Inspect

```bash
uv run <skill>/scripts/validate.py [workspace-root] [--json]
```

Report output verbatim, then a one-sentence summary: pass/fail + violation count. Add `--json` when you need to parse results reliably (e.g. paths with spaces). If `validate.py` is unavailable, manually check `my-workspace.yaml` exists at root; list root dirs; for each, verify it's in the index and has `.git` unless `vc_exception` is set.

## Reconcile — consent flow

Propose the exact plan, get approval, execute. Show all changes upfront:

```
Proposed changes:
  MOVE    notes.md → sandbox/
  INDEX   add: datasets (vc_exception: large-binary — confirm value)
  INDEX   remove: old-repo (drift — not on disk)
```

Steps (after approval):
1. **`.eng/`** — if absent and wanted, tell the user to run the `push` plugin.
2. **`.github/`** — optional. If absent and wanted, `git init .github`; seed `copilot-instructions.md` stub.
3. **Loose files** — propose a destination per file; never bulk-move or delete.
4. **Unclassified dirs** — propose index entry + `vc_exception` if non-git; confirm before writing.
5. **Drift** — index keys with no dir on disk → propose removal.

Script: [`scripts/validate.py`](scripts/validate.py)
