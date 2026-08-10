---
name: ado-okrs
description: Layout for tracking quarterly OKRs on an Azure DevOps board so objectives are trackable across workspaces and repos. Use when asked about quarterly goals, OKRs, objectives, key results, deliverable weights or scoring, quarter planning, where the OKR board lives, or when creating or editing the fields and text of an ADO work item. Keywords OKR, objectives, key results, quarterly goals, quarter planning, ADO board, epics, features, business value, weights, work item, area path, iteration path.
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

- **Description** — the prose: deliverable, scoring detail, effort range, risk. Epic
  description carries the objective's purpose and context.

Both numeric fields roll up on the parent Epic.

## Writing item text

Drafting and filing items in the user's name follow `outbound-review`.

For field reference names, tool limits, and gotchas when creating or updating items, see
`references/authoring.md`.
