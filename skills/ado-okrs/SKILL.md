---
name: ado-okrs
description: Layout for tracking quarterly OKRs on an Azure DevOps board so objectives are trackable across workspaces and repos. Use when asked about quarterly goals, OKRs, objectives, key results, deliverable weights or scoring, quarter planning, or where the OKR board lives. Keywords OKR, objectives, key results, quarterly goals, quarter planning, ADO board, epics, features, business value, weights.
---

# ADO OKRs

Quarterly OKRs live on an Azure DevOps board. Local references (org, project, board
and item URLs) are in `~/.copilot/ado-okrs/` — read that first to resolve specifics.

## Layout

| Level | Holds |
|---|---|
| Area Path | one per planning doc / workstream |
| Iteration Path | the quarter, with real start/finish dates |
| Epic | an objective |
| Feature | a deliverable / key result |
| Story, Task, comments | ad hoc, as needed |

## Fields

- **Business Value** — the deliverable's scoring weight (%). Features under an Epic sum to 100.
- **Effort** — estimate in weeks. Leave blank when ongoing or not time-boxed.
- **Description** — the prose: deliverable, scoring detail, effort range, risk. Epic
  description carries the objective's purpose and context.
- **Tags** — quarter and doc name, when Area Paths are unavailable.

Both numeric fields roll up on the parent Epic.

For field reference names, tool limits, and gotchas when creating or updating items, see
`references/authoring.md`.
