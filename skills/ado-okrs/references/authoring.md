# Authoring notes

Verified mechanics for creating and updating OKR items via the Azure DevOps MCP tools.

## What the tools cannot do

- **Area Paths cannot be created.** There is no classification-node write tool. Areas must be
  added once in the UI (Project Settings > Boards > Project configuration > Areas). Until then,
  use Tags for the per-doc axis.
- **Projects and wikis cannot be created** — only work items, iterations, and wiki *pages* in a
  wiki that already exists.

## Field reference names

| Meaning | Field |
|---|---|
| Weight (%) | `Microsoft.VSTS.Common.BusinessValue` |
| Effort (weeks) | `Microsoft.VSTS.Scheduling.Effort` |
| Quarter | `System.IterationPath`, also mirrored as a `System.Tags` tag |
| Doc / workstream | `System.AreaPath`, else `System.Tags` |

## Gotchas

- **Iteration path drops the `\Iteration\` segment.** The node is created at
  `\Project\Iteration\FY27Q1`, but the field value is `Project\FY27Q1`.
- **Set the iteration on the Epic too**, not just its Features — otherwise a "this quarter"
  query misses the objective itself.
- **`format: "Markdown"`** is required on multiline fields (Description) for markdown to render,
  and must be *omitted* on single-line fields (Title, Tags) — ADO rejects it with
  "Operation of changing value type is not supported".
- **Tags** are semicolon-separated and get reordered alphabetically on save.
- **Feature exists only in Agile and Scrum**, not Basic. Detect the process by checking whether
  `User Story` (Agile) or `Product Backlog Item` (Scrum) resolves.

## Useful calls

- `add_child` creates children *and* links them to the parent in one call, and accepts
  `areaPath` / `iterationPath` per child.
- `update_batch` applies field edits across many items at once:
  `[{"id":123,"op":"Add","path":"/fields/...","value":"30"}]`.
