---
name: engdirs-status
description: 'Audit all .eng/ git repos under ~/Code/ by default, or under provided roots — report which are dirty, which have unpushed commits, and which look uninitialized. Read-only. Use when the user asks about EngDirs/.eng repo status, unpushed commits, dirty working trees, or "what needs to be pushed/committed". Triggers: eng status, engdirs status, eng audit, what'\''s dirty, unpushed eng.'
argument-hint: '[search-root ...] — optional override roots (default: ~/Code)'
---

# EngDirs Status

Audit of `.eng/` git repos. Reports branch, ahead/behind, and dirty files.

## Procedure

**Private config:** Default scan root is `~/Code`. If `private/config.md` exists, use the scan roots and ADO org listed there (pass roots as args to `audit.sh`).

```bash
bash scripts/audit.sh
```

Pass alternate roots as args. Default is `~/Code`. Uses `find -P` so symlinked mirror trees aren't visited twice.

If the script is missing or broken, fall back to running `find -P <roots> -maxdepth 3 -type d -name .eng` and then `cd` into each + `git status` / `git rev-list --left-right --count '@{u}...HEAD'` manually to build the same table. If no `.eng` repos are found under the searched roots, tell the user.

## Output

`audit.sh` emits a single markdown table. The agent runs the script, takes its output, and presents it to the user as-is — no per-repo prose, no narration. Example:

```
| Repo | Branch | Behind | Ahead | Dirty | Notes | Path |
|---|---|--:|--:|--:|---|---|
| RepoA | `projects/RepoA` | 0 | 7 | 4 |  | ~/Code/RepoA/.eng |
| RepoB | `projects/RepoB` | 0 | 29 | 1 |  | ~/Code/RepoB/.eng |
| RepoC |  | — | — | 2 | no upstream | ~/Code/RepoC/.eng |
| RepoD | `projects/RepoD` | 0 | 0 | 0 |  | ~/Code/RepoD/.eng |
```

The agent presents the table to the user.

## References

- `~/.copilot/engagent/skills/eng-push/SKILL.md` — sets up EngDirs push (initial config, not for routine pushes)
- If `private/troubleshooting.md` exists, consult it for environment-specific push/auth recovery steps.
