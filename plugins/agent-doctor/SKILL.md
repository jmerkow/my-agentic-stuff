---
name: agent-doctor
description: >
  Diagnose and fix Copilot / VS Code agent files (`*.agent.md`) — especially their `tools:` list —
  and keep them correct as plugins install and MCP servers change. Default posture is a read-only
  "doctor": when an agent can't use a tool, an install scrambled its tools, an MCP server renamed
  tools, you're onboarding a new MCP server, or you're setting up a new agent, work out what's
  wrong and what the fix is — then apply it only when asked. Intent lives in a version-controlled
  store and is expanded mechanically into each agent's `tools:`.
  Keywords: agent files, agent tools, doctor mode, agent can't use tool, tool not available,
  toolsets, tools frontmatter, tool drift, MCP tool rename, onboard MCP server, new agent,
  expand toolset, assignments, agent-doctor, DrAgent, fix agent tools.
---

# Agent Doctor

Installing a plugin's agents scrambles their `tools:` frontmatter, and when MCP servers change,
tool IDs drift (e.g. `workiq/ask_work_iq` → `workiq/ask`). The VS Code tool picker can't reliably
write selections back, so lists get hand-edited — a huge, error-prone surface. Agent Doctor makes
it mechanical.

## Understanding agent files

An agent is a markdown file (`<name>.agent.md`) with a YAML frontmatter block. **VS Code is the
primary target**; Copilot CLI and Claude Code read a subset. Fields (VS Code):

| field | meaning |
|---|---|
| `name` | agent id / display; defaults to the filename |
| `description` | what it's for; shown as the chat input placeholder |
| `tools` | the tool IDs it may use — **the field this skill manages** |
| `model` | model to run it (string or prioritized list); blank = picker default |
| `agents` | subagents it may use (`['*']` = all, `[]` = none; needs `agent` in `tools`) |
| `argument-hint` | hint text shown in the chat input |
| `user-invocable` | show in the agents **dropdown** (default `true`) — how you select it |
| `disable-model-invocation` | prevent other agents from auto-invoking it as a subagent |
| `handoffs` | next-agent buttons (`label`/`agent`/`prompt`/`send`/`model`); VS Code |
| `target` | `vscode` or `github-copilot` |
| `infer` | **deprecated** → use `user-invocable` + `disable-model-invocation` |

Copilot CLI and Claude Code (`.claude/agents/*.md`) use `name`/`description`/`tools`/`model`; the
rest are VS Code-only. You run a custom agent by picking it from the **agents dropdown** (there is no
`@`-mention). **Only ever touch `tools:` — leave the rest.**

**The name gap (what confuses everyone).** A tool has TWO names:
- **config name** — what goes in `tools:` and toolsets: `server/tool` (e.g. `workiq/ask`,
  `s360-breeze/get_kpi_health_stats`). Built-in tools use the same shape (`read/readFile`,
  `edit/createFile`); the bare names `read`/`edit`/… are toolset **groups** that expand to those
  concrete leaves. `todo` is the lone bare single-tool.
- **runtime name** — what the live tool is called in a session: `mcp_<server>_<tool>`
  (e.g. `mcp_workiq_mcp_se_ask`). The server segment can differ from the config alias
  (`s360-breeze` ⇄ `mcp_server_fo`).

Same tool, two names — which is why "is it connected?" is confusing and why you can't just eyeball
one against the other. There's no lookup file for the runtime↔config map — infer it from the server
prefix, and when unsure check your live tools (that's what DrAgent's `['*']` is for).

**Why a tool list needs managing at all** (open VS Code bugs): a toolset *reference* containing MCP
tools doesn't resolve in `tools:` — only built-ins do ([#298131](https://github.com/microsoft/vscode/issues/298131))
→ so we expand groups to **concrete leaves**; the tools-picker UI can't save
([#308887](https://github.com/microsoft/vscode/issues/308887)) → so we edit via CLI + git; plugin
installs overwrite frontmatter ([#314020](https://github.com/microsoft/vscode/issues/314020) /
[#321765](https://github.com/microsoft/vscode/issues/321765)) → so intent lives in the store and is
re-applied.

## Is a tool actually available? (two halves)

"Agent X can't use tool Y" is really two independent questions — answer both:

1. **Is the tool live in the session?** Only a running agent can tell: look at your *own* available
   tools for the `mcp_<server>_*` prefix (or `tool_search`). **Nothing on disk answers this** —
   `check` sees config, not the live server. Server down / not started → no `tools:` edit fixes it;
   that's an MCP/infra problem (start the server).
2. **Is it in the agent's `tools:`?** Config: read the agent file / its assignment / the group. Live
   server but tool not listed → a `tools:` gap → `assign`.

The classic trap: an agent reports "server not connected" when the server is actually live — it just
isn't in *that agent's* `tools:`. That's half 2, not half 1.

**This is why DrAgent runs with `tools: ['*']`** — it can see the whole live roster in its own
session, so it can tell half 1 from half 2 and can enumerate a newly-started server's tools for
onboarding. Great power, narrow job: it stays in its lane (diagnose + maintain tools), nothing else.

## Default: doctor mode (diagnose first, change only when asked)

Invoked without a specific request to modify files, **stay in diagnostic mode — read-only.** Your
job is to help figure out a tool problem: what's wrong, where the tool lives, and what the fix
would be. Investigate and explain; don't write until the user asks you to apply a change.

- **Diagnose (read-only — the default):** read the agent file + its assignment, check drift vs
  baseline (`check`), and reason about the tool (config-name vs runtime-name; is it live in the
  session at all?). Safe to run anytime.
- **Change (only when the user asks to apply a fix):** `assign --write`, `restore`, `save`. These
  edit agent files or the store — always preview the diff, confirm intent, then write.

Typical loop: user reports *"agent X can't use tool Y"* → check whether the tool is live in the
session vs merely missing from the agent's list → explain the gap and the `assignments.yaml` fix →
**only if they say go**, edit `assignments.yaml` + `assign --write`.

## Model

- **`*.toolsets.jsonc`** (VS Code toolsets file, auto-loaded from `User/prompts/`) defines named
  **groups**. The group NAME encodes a safety tier:

  | tier | naming | meaning |
  |---|---|---|
  | read | `read_*` | no state change |
  | safe mutation | `write_*_safe` | personal / reversible (draft, send-to-self) |
  | mutation | `write_*` | external, others see it |
  | destructive | `write_*_delete` | ⚠️ delete / not-undoable |

  `~presets` compose groups (groups-of-groups); builtins and MCP servers are themselves ordinary
  leaf-listing groups (VS Code also resolves the bare builtin names natively). Tiers organize how you
  **grant** capability; they are **not**
  enforced at runtime — keep the labels honest (a `_safe` group must genuinely stay in your outbox).

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
override with `--store`. Agent-file writes (`assign`, `restore`) show a diff and need `--write`;
`save`/`fmt` act on the store.

```bash
S=plugins/agent-doctor/scripts/medical_bag.py
AD="uv run $S"

# ── Diagnose (read-only — the default doctor posture) ──────────────────────────

# Compare each agent's file to its assignment (+ note baseline drift)
$AD check --agents-dir <plugin>/agents

# "Are our tools current?" — diff the live picker roster vs the store toolset (paste/pipe it)
$AD reconcile --ui picker.txt        # or: pbpaste | $AD reconcile

# ── Change (only when the user asks to apply a fix — these write) ──────────────

# Reconcile agents to assignments — PREVIEW (diff only, no write)
$AD assign --agents-dir <plugin>/agents
# ...then actually write + save baseline + commit the store
$AD assign --agents-dir <plugin>/agents --write

# Undo: write an agent's committed baseline back into its file (preview, then --write)
$AD restore eng --agents-dir <plugin>/agents
$AD restore eng --agents-dir <plugin>/agents --write

# Establish/update the baseline from the current files
$AD save --all --agents-dir <plugin>/agents

# Reflow the toolset jsonc to canonical form (preview; --write to apply + commit)
$AD fmt
```

Paths default to the store: `--toolsets`→`<store>/toolsets.toolsets.jsonc`, `--assignments`→
`<store>/assignments.yaml`. Pass them to override.

## Recipes (the four jobs)

Adapt these — they're the shape, not a script.

**1 — "Agent X can't use tool Y."** Answer the two halves. Server not live → say so (start it). Live
but missing from `tools:` → find which group grants it (grep the toolset), add that group to X in
`assignments.yaml`, `assign --write X`. No group grants it yet → it's a new tool: do recipe 3 first.

**2 — "A plugin update overwrote my tools."** `check` (file vs assignment). Anything OUT OF SYNC →
`assign --write` to regenerate from intent. `restore <agent>` for the last-known-good file first if
you want it. Intent survived because it lives in the store, not the agent file.

**3 — "Onboard a new MCP server."** Start the server. As DrAgent (`['*']`), read your own live tools
for the new `mcp_<server>_*` entries. For each: derive the config name (`server/tool`) and classify
by effect into a tier (`read_*` / `write_*` / `write_*_delete`). Define the `read_/write_` group(s)
in the toolset listing those concrete `server/tool` leaves. Then assign the group where wanted and
`assign --write`. Classification is
judgment — show the proposed grouping and get a nod before writing.

**4 — "Provision a new agent for job Z."** From Z, pick the minimum capabilities → the matching
groups (read the toolset's group descriptions). Add `<agent>: [groups]` to `assignments.yaml`,
`assign --write <agent>`. Start narrow; widen when something is actually blocked (that's how eng got
`read_s360`/`write_s360`).

## Validation: hard errors

`assign` **pre-validates** assignments (each agent → a list; each entry a defined group, a raw
leaf `server/tool`, or the bare builtin `todo`) and validates every expanded leaf:

- **Hard error → nothing is written** (fix the config): a bare token that isn't a defined group,
  a `/`-leaf, or `todo` — a dangling/typo'd group ref; a missing agent file; a malformed assignment
  (`eng: ~common` instead of a list); a `server/*` wildcard (list concrete leaves instead). Blocks
  even with `--write`.

After every write the file is **re-parsed and the tool set verified** against intent; a mismatch
aborts. Nothing is auto-added — a genuinely new tool is introduced deliberately via recipe 3
(onboard a server), so a typo can never silently become a "valid" tool.

## Store (git repo)

```
~/.copilot/agent-doctor/          # a git repo; writes auto-commit → history + drift baseline
  toolsets.toolsets.jsonc         # canonical groups + ~presets (also deployed to User/prompts/)
  assignments.yaml                # agent → [groups]  (intent; survives plugin reinstalls)
  agent-states/<agent>.json       # committed baseline (sorted, one-per-line) + restore source
```

Builtins and MCP servers are **ordinary leaf-listing groups** in the toolset (a `read` group lists
`read/readFile`…; an `enghub` group lists `enghub/fetch`…). `expand` is a **pure flatten** of group
composition into concrete leaf IDs — no wildcards, no separate lookup table. A bare token that isn't
a group (e.g. `todo`) is left as-is. `assign`/`check`
print a **per-server** diff (changed servers only, with tool names) so you can read a change at the
altitude you edit.

The toolset is also copied to the VS Code prompts folder as `agent-doctor.toolsets.jsonc` (auto-loaded;
multiple `*.toolsets.jsonc` coexist). That folder's location varies — Windows `%APPDATA%\Code\User\prompts`
vs the WSL/remote server dir — and may be absent on a headless remote; check both when syncing.
State files are **sorted + one-per-line** so a single tool
added/removed is a one-line git diff; agent files keep the compact `tools: [a, b]` (also sorted).
Comparisons are set-based, so the two formats never conflict.

- **Archive** = parked extension that may return: keep it as an **unreferenced group** (defined, in
  no `~preset`, so it never expands into an agent).

## Conventions

- **One agents dir at a time.** Commands take a single `--agents-dir`; there's no multi-plugin
  discovery or duplicate-name detection yet — point it at one plugin's `agents/` and keep agent
  names unique across the dirs you manage.
- Edit **groups** (toolset) and **assignments**, never an agent's `tools:` by hand — re-run `assign`.
- After a plugin reinstall or MCP change: `check` (in sync with intent?) then `assign --write`.
- `restore` is the undo if an install scrambled an agent. git history + `agent-states/` are the
  backup — there is no `backup/` dir (use `/tmp` for a one-off raw copy).
- Add a new server/builtin tool directly to its toolset group (the only bare builtin is `todo`).
