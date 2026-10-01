---
name: agent-doctor
description: >
  Fix and maintain the tool-lists (`tools:` frontmatter) of Copilot agents when installing
  plugins scrambles them or MCP servers change tool names. Assign agents named tool GROUPS
  (from a *.toolsets.jsonc), then expand them to leaf tool IDs mechanically. Use when an
  agent lost its tools after a plugin update, an MCP server renamed/removed tools, you need
  to re-sync agent tools from group assignments, or audit which agent has which tools.
  Keywords: agent tools, toolsets, tools frontmatter, tool drift, MCP tool rename, expand
  toolset, assignments, agent-doctor, fix agent tools.
---

# Agent Doctor

Installing a plugin's agents scrambles their `tools:` frontmatter, and when MCP servers change,
tool IDs drift (e.g. `workiq/ask_work_iq` → `workiq/ask`). The VS Code tool picker can't reliably
write selections back, so lists get hand-edited — a huge, error-prone surface. Agent Doctor makes
it mechanical.

## Model

- **`*.toolsets.jsonc`** (VS Code toolsets file, auto-loaded from `User/prompts/`) defines named
  **groups**. The group NAME encodes a safety tier:

  | tier | naming | meaning |
  |---|---|---|
  | read | `read_*` | no state change |
  | safe mutation | `write_*_safe` | personal / reversible (draft, send-to-self) |
  | mutation | `write_*` | external, others see it |
  | destructive | `write_*_delete` | ⚠️ delete / not-undoable |

  `~presets` compose groups (groups-of-groups). Bare builtins (`read`, `edit`, `agent`, `todo`…)
  are leaves VS Code resolves itself.

- **`assignments.yaml`** maps `agent-name → [groups]`. This is the **source of truth for intent**,
  kept **separate from the agent files** so a plugin update can't wipe it.

- **`agent-doctor assign`** expands each agent's assigned groups to leaf tool IDs (BFS) and writes
  them into `tools:` — but only if every leaf is structurally valid (else it hard-errors). Agent
  files hold only the generated list — disposable; regenerate any time.

```
assignments.yaml  ──assign──▶  <agent>.agent.md  tools: [ …expanded leaves… ]
   (intent, kept safe)              (generated, overwritten by plugin updates → re-assign)
```

Expansion does **not** shrink the agent's runtime context (leaves and group-names load the same
tool descriptions); the win is human maintainability + following drift when a group changes.

## Commands

Run with `uv` (deps declared inline). Default store is `~/.copilot/agent-doctor/` (a git repo);
override with `--store`. `assign`, `restore`, and `save` preview added/removed tools first and need
`--write` to change files.

```bash
S=skills/agent-doctor/scripts/agent_doctor.py
AD="uv run $S"

# Reconcile agents to assignments — PREVIEW (diff only, no write)
$AD assign --agents-dir <plugin>/agents
# ...then actually write + save baseline + commit the store
$AD assign --agents-dir <plugin>/agents --write

# Dry-run assignments, comparing intended tools to current files and saved baseline (read-only)
$AD check --agents-dir <plugin>/agents

# Undo: write an agent's committed baseline back into its file (preview, then --write)
$AD restore eng --agents-dir <plugin>/agents
$AD restore eng --agents-dir <plugin>/agents --write

# Establish/update the baseline from the current files (preview, then --write)
$AD save --all --agents-dir <plugin>/agents
$AD save --all --agents-dir <plugin>/agents --write

# Inspect frontmatter as JSON
$AD get path/to/eng.agent.md

# Diagnose "agent X can't use tool Y" against store intent, current file, and saved state
$AD diagnose eng breeze --agents-dir <plugin>/agents

```

Paths default to the store: `--toolsets`→`<store>/toolsets.toolsets.jsonc`, `--assignments`→
`<store>/assignments.yaml`, `--defaults`→`<store>/defaults/`. Pass them to override.

## Validation: hard errors vs advisories

`assign` and `check` **pre-validate** the toolset shape and assignments before expanding:
each toolset entry must be an object with a `tools` list of strings; each assignment must be
`agent → [groups]`; and each bare token must be a defined group or known builtin. The standard
bare builtins `read`, `edit`, `agent`, and `todo` are known by default; add harness-specific
builtins in optional `defaults/builtins.yaml`. Raw leaves
are still allowed (`server/tool`) because this is groups-first, not groups-only.

- **Hard error → nothing is written** (fix the config): malformed toolset entries; a bare token
  that isn't a defined group or builtin; a malformed assignment (`eng: ~common` instead of a
  list); a wildcard entry; an expanded leaf that is not declared by the toolset or registry; or
  an assigned agent with no matching `<agent>.agent.md`. Blocks even with `--write`.
- **Advisory (reported, not blocking)**: a leaf in optional `defaults/tombstones.yaml`
  (removed/renamed). Harness-absent tools can't be verified, so they aren't errors.

After every write the file is **re-parsed and the tool set verified** against intent; a mismatch
aborts. Unknown leaves are never auto-added; declare intentional new tools in the toolset first.

## Store (git repo)

```
~/.copilot/agent-doctor/          # a git repo; writes auto-commit → history + drift baseline
  toolsets.toolsets.jsonc         # canonical groups + ~presets
  assignments.yaml                # agent → [groups]  (intent; survives plugin reinstalls)
  agent-states/<agent>.json       # committed baseline (sorted, one-per-line) + restore source
  defaults/                       # optional builtins.yaml + tombstones.yaml + registry.yaml
```

Optional `registry.yaml` holds the **concrete tool members** for each builtin group and MCP server.
`expand` resolves bare builtins (`read`, `edit`, …) into concrete leaf IDs when the registry knows
them; concrete MCP tools should be listed explicitly as `server/tool`. The toolset keeps group names
for readability. `assign`/`check` print a **per-server** diff (changed servers only, with one line
per changed tool) so you can read a change at the altitude you edit.

State files and agent files are **sorted + one-per-line** so a single tool added/removed is a
one-line git diff. Comparisons are set-based, so formatting churn does not affect drift checks.

- **Tombstone** = removed/renamed tool (advisory on reference).
- **Archive** = parked extension that may return: keep it as an **unreferenced group** (defined, in
  no `~preset`, so it never expands into an agent). Distinct from a tombstone.

## Conventions

- Edit **groups** (toolset) and **assignments**, never an agent's `tools:` by hand — re-run `assign`.
- After a plugin reinstall or MCP change: `check` (what would assignment produce, and does current
  or baseline differ?) then `assign --write` (fix it).
- `restore` is the undo if an install scrambled an agent; it writes `agent-states/<agent>.json`
  back into the agent file.
- Use `diagnose <agent> <tool-or-capability>` when a tool is unavailable. It does not write; it
  reports matching declared tools/groups, assignment coverage, current file coverage, and saved
  baseline coverage. If nothing matches, the likely next step is to connect/refresh the MCP server
  and then add explicit `server/tool` IDs to the toolset.
- Keep optional defaults in the store when useful for your harness; this repo does not ship
  `defaults/builtins.yaml` or `defaults/tombstones.yaml`.
