# Output Format — Review Findings

One file per functional group, written by the orchestrator after merging both sub-agents' results. The complete template:

````markdown
---
group: <group-name>
files: [list of reviewed files]
reviewed: YYYY-MM-DD
---

# <Group Name> — Code Review

## Findings

### R1 — file.py:12-14 [#11] fix

```python
CHECKPOINT_DIR = "/mnt/hlsrad8455624441/..."
```

Hardcoded checkpoint path instead of env/config lookup

- **Rule**: [#11] Hardcoded paths or magic constants
- **Severity**: fix
- **Reviewers**: both

**Your response**:
> 

### R2 — config.py:5-8 [#9] nit

```python
import os
import os.path
from pathlib import Path
```

Mixed os.path and pathlib in the same file

- **Rule**: [#9] Import clutter
- **Severity**: nit
- **Reviewers**: agent-A

**Your response**:
> 

### R3 — utils.py:44-48 [#2 / #6] fix / nit — disagreement

```python
try:
    value = int(os.environ.get("TIMEOUT", "30"))
except (ValueError, TypeError):
    value = 30
```

- **Agent A** [#2] fix — Unnecessary defensive programming; env var is always set by the caller
- **Agent B** [#6] nit — Minor over-engineering but harmless

**Your response**:
> 

## Summary

- **Total findings**: 3
- **fix**: 1 (excludes disagreements)
- **nit**: 1 (excludes disagreements)
- **Disagreements**: 1 (severity TBD by user)
- **Agreements**: 1
- **Unique to Agent A**: 1
- **Unique to Agent B**: 0
````

## Field Reference

- **ID** — `R1`, `R2`, … sequential within the file
- **Location** — `file.py:line` or `file.py:start-end`
- **Rule** — `[#N]` checklist rule (1–16), or `[#0]` for unlisted concerns
- **Severity** — `fix` (should change) or `nit` (minor, optional)
- **Snippet** — offending code, 1–5 lines in a fenced block
- **Reviewers** — `both` if both sub-agents flagged it; `agent-A` or `agent-B` if only one did
- **Your response** — freeform blockquote for the user
- **Description** — one line explaining the issue
- **Reviewers** — `both`, `agent-A`, or `agent-B`
- **Disagreement** — when both agents flag the same location differently, show both assessments and append `— disagreement` to the heading
- **Your response** — blockquote for the user: `accept`, `reject`, `defer`, or freeform

## Status Tags (Phase 3)

After triage, the orchestrator prepends a status tag to each finding heading. Use both the emoji and a text label so the meaning is unambiguous to both humans and agents:

```markdown
### R1 ✅ accepted — file.py:12-14 [#11] fix
### R2 ❌ rejected — config.py:5-8 [#9] nit
### R3 ⏳ deferred — utils.py:44-48 [#2] fix
```

- **✅ accepted** — A Change Request will be written for this finding.
- **⏳ deferred** — Acknowledged but not actionable now (WIP dependency, backlog, future work).
- **❌ rejected** — No action. User disagrees or considers it not worth changing.

Findings without a tag still need triage.

If the orchestrator answered a user question, add a **Reviewer note** below the user's response:

```markdown
**Your response**:
> is this expensive?

**Reviewer note**: No — Template() parsing is microseconds for small templates. **No action.**
```

## Change Request Section (Phase 3)

Appended after the Summary, separated by `---`. One CR per logical change:

````markdown
---

## Change Requests

Accepted findings, ready for implementation.

### CR1 — Short description (from R1)

**File:** `path/to/file.py`

**Action:** What to do, with enough detail that an implementing agent can execute
without re-reading the findings. Include exact signatures, preserve dependent
attributes, and resolve any cross-CR conflicts.

### CR2 — Short description (from R2 + R5)

**Files:** `file_a.py`, `file_b.py`

**Action:** ...
````

Rules:
- One CR per logical change. Merge related findings if they interact.
- Name file(s), action, and exact detail — no ambiguity.
- If a CR changes a signature, show the new signature.
- If CRs conflict (one removes what another adds), resolve in the CR text.
