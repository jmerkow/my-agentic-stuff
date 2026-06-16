---
name: worktree-setup
description: Set up a git worktree as an isolated workspace for Copilot agent work. Use when creating a worktree branch, wiring up `.eng/` shared engineering state, linking sibling repos via `external/`, or preparing a clean environment for isolated agent changes. Keywords: worktree, git worktree, workspace setup, isolated branch, sibling repos, external/, .eng symlink, Copilot worktree, worktree scaffold.
---

# Worktree Setup

This skill covers the five steps needed to make a git worktree ready for Copilot agent work: branch creation, `.eng/` symlink, `external/` sibling repo symlinks, project-local file symlinks, and optional workstream activation.

## When to use

- You are about to start agent work that must stay isolated from the main checkout
- A worktree directory exists but is missing `.eng/`, `external/`, or project-local symlinks
- You need to read or write sibling repo files without guessing long absolute paths

## Step 1 — Create the worktree

> In VS Code background mode this step is done automatically when launching a new copilot session.

From the main checkout:

```bash
git worktree add ../<ProjectName>.worktrees/copilot-worktree-<timestamp> -b <branch-name> <base-branch>
```

This creates a new directory under `<ProjectName>.worktrees/` branching from `<base-branch>`. The main checkout is undisturbed.

## Step 2 — Symlink `.eng/`

`.eng/` is the shared engineering state directory (its own git repo on EngDirs). The worktree lives two levels below the workspace root (`<root>/<ProjectName>.worktrees/<worktree-dir>/`). Check both candidate locations:

```bash
# Option A: .eng/ sits directly at the workspace root
ls ../../.eng

# Option B: .eng/ sits inside a sibling repo under the workspace root
ls ../../<parentRepo>/.eng
```

Use whichever path exists:

```bash
cd <worktree-path>
ln -s ../../.eng .eng               # Option A
# or
ln -s ../../<parentRepo>/.eng .eng  # Option B
```

Verify `.eng/` is in `.gitignore` (it usually is, but check):

```bash
grep -qx '.eng/' .gitignore || echo '.eng/' >> .gitignore
```

After this, all workstream paths resolve from `.eng/workstreams/…` inside the worktree.

## Step 3 — Link sibling repos via `external/`

**Ask the user which sibling repos and workspace-level shared directories they need.** Then symlink them into `external/`:

```bash
cd <worktree-path>
mkdir -p external
ROOT=<workspace-root>   # e.g. /home/user/Code/MyWorkspace
ln -s "$ROOT/SiblingRepoA"  external/SiblingRepoA
ln -s "$ROOT/shared-data"   external/shared-data
```

Add `external/` to `.gitignore` if not already present:

```bash
grep -qx 'external/' .gitignore || echo 'external/' >> .gitignore
```

## Step 4 — Link project-local files from the main checkout

**Ask the user which project files aren't in the worktree branch** — checkpoints, `.env` files, large data files, gitignored configs, etc. Symlink these directly at their natural path in the worktree root:

```bash
MAIN=<main-checkout-path>   # e.g. /home/user/Code/MyWorkspace/ProjectName
ln -s "$MAIN/checkpoints"   checkpoints
ln -s "$MAIN/.env"          .env
```

These should already be in `.gitignore`. Check before adding:

```bash
grep -qx 'checkpoints/' .gitignore || echo 'checkpoints/' >> .gitignore
grep -qx '.env' .gitignore          || echo '.env' >> .gitignore
```

**Use absolute paths for all symlinks** (Steps 3 and 4). Relative symlinks resolve relative to the symlink's location on disk. Because the worktree is nested under `.worktrees/`, a relative link points to the wrong place.

## Step 5 — Activate the workstream (if using EngDirs)

If the work belongs to a specific workstream, store the active workstream path in session memory so tools resolve `.eng/` writes to the right directory automatically. See the **eng-workstream** skill for the full activation contract.

## Why it works

| Concern | Solution |
|---|---|
| Isolated changes | Worktree has its own working tree and index; the main checkout is unaffected |
| Shared eng state | `.eng/` symlink — workstream docs accessible at `.eng/workstreams/…` |
| Sibling repo access | `external/` symlinks — reference files without long absolute paths |
| Merge hygiene | `.eng/` and `external/` are gitignored; the worktree branch merges cleanly |
