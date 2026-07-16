# Agent Plugin Reference

Field reference, snippets, lifecycle events, and gotchas for Copilot plugins (VS Code + Copilot CLI). Sourced from the official VS Code and GitHub Copilot CLI plugin docs; see [sources.md](sources.md) for the full source list and verification date. For marketplace authoring and registration, see the **marketplace-creator** skill.

---

## plugin.json

`plugin.json` is the required manifest at the plugin root. The only required field is `name`.

### Required field

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Kebab-case (lowercase letters, digits, hyphens). Max 64 chars. |

### Optional metadata fields

| Field | Type | Notes |
|-------|------|-------|
| `description` | string | Max 1024 chars. |
| `version` | string | Semantic version (e.g., `1.0.0`). Bump for updates. |
| `author` | object | `{ name (required), email?, url? }` |
| `homepage` | string | Plugin homepage URL. |
| `repository` | string | Source repository URL. |
| `license` | string | License identifier (e.g., `MIT`). |
| `keywords` | string[] | Search keywords. |
| `category` | string | Plugin category. |
| `tags` | string[] | Additional tags. |

### Component path fields

All optional; defaults are used if omitted.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `agents` | string \| string[] | `agents/` | Path(s) to agent directories (`.agent.md` files). |
| `skills` | string \| string[] | `skills/` | Path(s) to skill directories (`SKILL.md` files). |
| `commands` | string \| string[] | none | Path(s) to command directories. |
| `hooks` | string \| object | none | Path to a hooks config file, or an inline hooks object. |
| `mcpServers` | string \| object | none | Path to an MCP config file (e.g. `.mcp.json`), or inline server definitions. |
| `lspServers` | string \| object | none | Path to an LSP config file, or inline server definitions. |
| `extensions` | string \| string[] \| object | none | Path(s) to extension directories. Object form `{ paths: [...], exclusive: true }` suppresses built-ins. |

### Example

```json
{
  "name": "my-dev-tools",
  "description": "React development utilities",
  "version": "1.2.0",
  "author": { "name": "Jane Doe", "email": "jane@example.com" },
  "license": "MIT",
  "keywords": ["react", "frontend"],
  "agents": "agents/",
  "skills": ["skills/", "extra-skills/"],
  "hooks": "hooks.json",
  "mcpServers": ".mcp.json"
}
```

### Recognized manifest paths

VS Code and the Copilot CLI check for `plugin.json` in this order:

1. `.plugin/plugin.json`
2. `plugin.json` (root)
3. `.github/plugin/plugin.json`
4. `.claude-plugin/plugin.json`

The manifest location also signals the plugin format; see [Plugin formats](#plugin-formats) and [other-platforms.md](other-platforms.md) for details.

---

## Plugin formats

VS Code auto-detects the plugin format from the manifest location:

| Format | Manifest location | Hook config |
|--------|-------------------|-------------|
| Copilot (default) | `plugin.json` (root) | `hooks.json` (root) |
| Claude | `.claude-plugin/plugin.json` | `hooks/hooks.json` |
| OpenPlugin | `.plugin/plugin.json` | none |

A single plugin repo can carry manifests for multiple formats and be consumed cross-tool.

---

## Components

### Custom agent (`agents/<name>.agent.md`)

```markdown
---
name: my-agent
description: Helps with specific tasks
tools: ["bash", "edit", "view"]
---

You are a specialized assistant that...
```

### Skill (`skills/<name>/SKILL.md`)

```markdown
---
name: deploy
description: Deploy the current project to...
---

Instructions for the skill...
```

The skill's `name` field must match the parent directory name exactly. The plugin name is automatically prefixed at runtime (`/<plugin-name>:<skill-name>`); do not add it manually.

### Hooks (`hooks.json`)

```json
{
  "hooks": {
    "PostToolUse": [
      { "type": "command", "command": "./scripts/format.sh" }
    ]
  }
}
```

Lifecycle events:

| Event | Fires when |
|-------|------------|
| `SessionStart` | The agent session begins |
| `UserPromptSubmit` | The user submits a prompt |
| `PreToolUse` | Before the agent invokes a tool |
| `PostToolUse` | After a tool completes successfully |
| `PreCompact` | Before conversation context is compacted |
| `SubagentStart` | A subagent is spawned |
| `SubagentStop` | A subagent completes |
| `Stop` | The agent session ends |

Hooks communicate over stdin/stdout JSON. VS Code parses the Claude-style `matcher` field for cross-tool compatibility but ignores its filter values; hooks fire regardless. Put any filtering logic inside the hook script.

Each hook command entry accepts optional properties beyond `type` and `command`:

| Property | Notes |
|----------|-------|
| `windows` / `linux` / `osx` | OS-specific command override for that platform |
| `cwd` | Working directory, relative to repo root |
| `env` | Extra environment variables (object) |
| `timeout` | Seconds before the hook is killed (default 30) |

### MCP servers (`.mcp.json`)

```json
{
  "mcpServers": {
    "plugin-database": {
      "command": "./servers/db-server",
      "args": ["--config", "./config.json"]
    },
    "plugin-api": {
      "command": "npx",
      "args": ["@company/mcp-server", "--plugin-mode"]
    }
  }
}
```

The top-level key is `mcpServers`, not `servers` (which is the workspace `.vscode/mcp.json` shape).

Plugin MCP servers are trusted at plugin-install time; they don't trigger the per-workspace MCP trust prompt.

### MCP config locations (for orientation)

| Config type | File | Top-level key |
|-------------|------|---------------|
| Plugin-bundled | `.mcp.json` at plugin root | `mcpServers` |
| Workspace | `.vscode/mcp.json` | `servers` |
| User profile | User profile `mcp.json` | `servers` |

---

## marketplace.json

Authoring a marketplace, its schema, source forms, plugin source layouts, registration (`chat.plugins.marketplaces`, `copilot plugin marketplace add`), and workspace recommendations are covered by the **marketplace-creator** skill. See its [marketplace-reference.md](../../marketplace-creator/references/marketplace-reference.md).

---

## Installing and registering

### VS Code

```json
// settings.json
"chat.pluginLocations": {
  "/path/to/my-plugin": true
}
```

Command palette:

- `Chat: Install Plugin From Source`: install directly from a Git URL.

For registering a marketplace via `chat.plugins.marketplaces`, see the **marketplace-creator** skill.

### Copilot CLI

```bash
# Install from local path, marketplace, or Git repo
copilot plugin install ./my-plugin
copilot plugin install PLUGIN-NAME@MARKETPLACE-NAME
copilot plugin install OWNER/REPO
copilot plugin install OWNER/REPO:PATH/TO/PLUGIN
copilot plugin install https://github.com/owner/repo.git

# Manage plugins
copilot plugin list
copilot plugin enable PLUGIN-NAME
copilot plugin disable PLUGIN-NAME
copilot plugin update PLUGIN-NAME
copilot plugin update --all
copilot plugin uninstall PLUGIN-NAME
```

Marketplace management commands (`copilot plugin marketplace ...`) live in the **marketplace-creator** skill.

### Copilot CLI install layout

| Source | Path |
|--------|------|
| Marketplace install | `~/.copilot/installed-plugins/<MARKETPLACE>/<PLUGIN-NAME>/` |
| Direct install | `~/.copilot/installed-plugins/_direct/<SOURCE-ID>/` |

---

## Loading order and precedence (Copilot CLI)

- **Custom agents:** first-found-wins, deduplicated by ID (derived from filename).
- **Skills:** first-found-wins, deduplicated by `name` in `SKILL.md`.
- **MCP servers:** last-loaded-wins, deduplicated by server name. Plugin MCP servers can override earlier ones; `--additional-mcp-config` takes the highest priority.
- **Built-in tools and agents** are always present and cannot be overridden.

This means plugin components cannot override project-level or personal definitions of the same name.

---

## Gotchas

- **`chat.plugins.enabled` must be on (VS Code).** Preview/org-managed flag; confirm before debugging anything else.
- **Kebab-case names are required.** Plugin and component names: `[a-z0-9-]+` only. Invalid names silently fail.
- **Skill `name` must equal directory name.** Otherwise the skill is silently skipped.
- **No manual namespacing on skill names.** Don't write `myorg/skill-name` or `myorg:skill-name`. The plugin context provides scoping.
- **MCP key mismatch.** Plugin `.mcp.json` uses `mcpServers`; workspace `.vscode/mcp.json` uses `servers`.
- **Bump `version` for updates** to be picked up in `plugin.json` (and the marketplace entry).
- **Copilot CLI caches components.** Reinstall with `copilot plugin install ./path` after local edits.
- **Path tokens vary by plugin format.** Copilot-format plugins do not expose a plugin-root token. Claude-format plugins expose `${CLAUDE_PLUGIN_ROOT}`; OpenPlugin-format plugins expose `${PLUGIN_ROOT}`. Both are usable in hook commands and MCP server config fields (`command`, `args`, `cwd`, `env`, `url`, `headers`) and injected as environment variables. All formats expose a persistent writable per-plugin directory: `${COPILOT_PLUGIN_DATA}` (Copilot format) or `${CLAUDE_PLUGIN_DATA}` (Claude format). Use this for runtime data instead of paths inside the install cache.
- **Plugin MCP is pre-trusted.** Plugin-bundled MCP servers bypass the per-workspace trust prompt.
- **Classic extension boundary is hard.** Agent plugins cannot access `vscode.*` APIs, register Chat Participants, or use the Language Model Tools API. Those require a classic TypeScript extension.

---

## Sources

See [sources.md](sources.md) for the full source list and verification date.
