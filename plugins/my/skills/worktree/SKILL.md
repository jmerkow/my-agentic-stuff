---
name: worktree
description: >
  Convention-aware worktree setup for a my-workspace topology.
  Naming: worktrees for repoX/ go in repoX.worktrees/<branch-name>/.
  Propose-approve-execute with standard preflight.
  Keywords: worktree, git worktree, isolated branch, worktree scaffold.
---

# Worktree Setup

## Convention

Worktrees for `repoX/` live at `repoX.worktrees/<branch-name>/` (sibling to the repo). Copilot inside a worktree orients from `my-workspace.yaml` — walk up from cwd to find the workspace root. No fixed-depth path math. No `external/` linking.

## Propose → confirm → execute

Collect: target repo, branch name, base branch (default `origin/main`). Show the plan before executing:

```
Proposed actions:
  FETCH   git -C "$ROOT/$REPO" fetch origin
  CREATE  "$ROOT/$REPO.worktrees/$BRANCH/"  (worktree add -b "$BRANCH" "$BASE")
```

Get explicit approval, then run preflight:

```bash
git -C "$ROOT/$REPO" fetch origin   # always fetch first

git -C "$ROOT/$REPO" diff --quiet && git -C "$ROOT/$REPO" diff --cached --quiet \
  || { echo "ERROR: dirty tree — stash or commit first"; exit 1; }
git -C "$ROOT/$REPO" branch --list "$BRANCH" | grep -q . \
  && { echo "ERROR: branch $BRANCH already exists locally"; exit 1; }
[[ -e "$DEST" ]] && { echo "ERROR: $DEST already exists"; exit 1; }

git -C "$ROOT/$REPO" worktree add "$DEST" -b "$BRANCH" "$BASE"
```
