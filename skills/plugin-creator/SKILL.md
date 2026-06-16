---
name: plugin-creator
description: >
  Create, inspect, install, and troubleshoot plugins for GitHub Copilot in
  VS Code and the GitHub Copilot CLI. Plugins are file-based bundles that
  ship custom agents, agent skills, hooks, MCP servers, and slash commands
  via a single plugin.json manifest. Use when scaffolding a new plugin
  directory, authoring plugin.json or marketplace.json, wiring
  chat.pluginLocations or chat.plugins.marketplaces in VS Code settings,
  installing a plugin from a local path or Git URL, registering a plugin
  marketplace, or debugging why a plugin's components are not loading.
  Keywords: Copilot plugins, VS Code agent plugins, Copilot CLI plugins,
  plugin.json, marketplace.json, chat.pluginLocations,
  chat.plugins.marketplaces, copilot plugin install, .mcp.json, SKILL.md,
  .agent.md, hooks, MCP servers, plugin marketplace, local plugin install.
---

# Plugin Creator

This skill follows the official Copilot plugin docs:

- VS Code: [Agent plugins in VS Code (Preview)](https://code.visualstudio.com/docs/copilot/customization/agent-plugins)
- Copilot CLI: [Creating a plugin for GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)

Both surfaces use the **same plugin format** (a directory with a `plugin.json` manifest). A single plugin can be installed by both VS Code Copilot and Copilot CLI.

For the full field reference, lifecycle events, marketplace schema, and gotchas, load [references/agent-plugin-reference.md](references/agent-plugin-reference.md). If you encounter a plugin shaped for Claude Code or OpenPlugin, load [references/other-platforms.md](references/other-platforms.md) for orientation.

## What plugins provide

A plugin can bundle any combination of:

- **Slash commands** — additional `/` commands in chat
- **Agent skills** — `SKILL.md` directories with instructions, scripts, and resources
- **Custom agents** — `.agent.md` files with specialized personas and tool configs
- **Hooks** — shell commands that run at agent lifecycle points
- **MCP servers** — external tool integrations via Model Context Protocol

Once installed, plugin-provided customizations appear alongside locally defined ones (e.g., skills from a plugin show up in `Configure Skills`; MCP servers appear in the MCP server list).

## Plugin structure

Minimum: a directory with a `plugin.json` manifest at the root.

```text
my-plugin/
  plugin.json
```

Typical:

```text
my-plugin/
├── plugin.json           # Required manifest
├── agents/               # Custom agents (optional)
│   └── helper.agent.md
├── skills/               # Skills (optional)
│   └── deploy/
│       └── SKILL.md
├── hooks.json            # Hook configuration (optional)
└── .mcp.json             # MCP server config (optional)
```

The structure above is taken directly from the Copilot CLI docs and is also recognized by VS Code.

## Creating a plugin

### 1. Create the plugin directory and manifest

Add `plugin.json` at the root. The only required field is `name`:

```json
{ "name": "my-plugin" }
```

A fuller example:

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

Component path fields default to conventional locations (`agents/`, `skills/`) when omitted. See [references/agent-plugin-reference.md § plugin.json](references/agent-plugin-reference.md) for all fields.

### 2. Add components

| Component | Where it lives | Format |
|-----------|----------------|--------|
| Agent | `agents/<name>.agent.md` | Markdown with YAML frontmatter (`name`, `description`, `tools`) |
| Skill | `skills/<name>/SKILL.md` | Markdown with YAML frontmatter; `name` must match parent dir |
| Hooks | `hooks.json` at the plugin root | JSON map of lifecycle events to commands |
| MCP servers | `.mcp.json` at the plugin root | Top-level key is `mcpServers` |

Reference component examples and event names in [references/agent-plugin-reference.md](references/agent-plugin-reference.md).

### 3. Install locally for development

**VS Code** — register the plugin path in `settings.json`:

```json
"chat.pluginLocations": {
  "/absolute/path/to/my-plugin": true
}
```

**Copilot CLI** — install from the local path:

```bash
copilot plugin install ./my-plugin
```

### 4. Verify it loaded

**VS Code**: Open the Extensions view, filter by `@agentPlugins`, and confirm the plugin appears in `Agent Plugins - Installed`. Components also appear in their respective UIs (`Configure Skills`, agents dropdown, MCP server list).

**Copilot CLI**:

```bash
copilot plugin list
```

Or, in an interactive session:

```text
/plugin list
/agent
/skills list
```

### 5. Iterate

After local edits, reload to pick up changes.

- **VS Code**: VS Code reloads plugins from `chat.pluginLocations` when configuration changes; otherwise reload the window.
- **Copilot CLI**: components are cached; rerun `copilot plugin install ./my-plugin` to refresh.

When publishing changes, **bump `version` in `plugin.json`** so update checks pick them up.

## Installing a published plugin

**VS Code**:

- From a marketplace: Extensions view → search `@agentPlugins`.
- From a Git URL: command palette → `Chat: Install Plugin From Source`.
- From a local marketplace clone: add a `file:///` URI to `chat.plugins.marketplaces`.

**Copilot CLI**:

```bash
copilot plugin install PLUGIN-NAME@MARKETPLACE-NAME
copilot plugin marketplace add OWNER/REPO          # add a marketplace
copilot plugin marketplace add /path/to/local      # local marketplace
```

Default Copilot CLI marketplaces (registered out of the box): `copilot-plugins`, `awesome-copilot`.

## Distributing a plugin

To distribute, add the plugin to a marketplace by creating `marketplace.json`. The recommended location is `.github/plugin/marketplace.json` in a Git repository. Each entry in the `plugins` array references a plugin directory. See [references/agent-plugin-reference.md § marketplace.json](references/agent-plugin-reference.md) for the schema.

Reference marketplaces:

- [github/copilot-plugins](https://github.com/github/copilot-plugins)
- [github/awesome-copilot](https://github.com/github/awesome-copilot)

## Troubleshooting

- **`chat.plugins.enabled` must be on (VS Code).** This is a preview/org-managed flag.
- **Names must be kebab-case.** Plugin name and component names: lowercase letters, digits, hyphens only. Invalid names silently fail.
- **Skill `name` must match parent directory.** Otherwise the skill is silently skipped.
- **Don't manually namespace skill names.** When a skill ships in a plugin, VS Code prefixes the plugin name automatically (`/my-plugin:my-skill`).
- **MCP key mismatch.** Plugin `.mcp.json` uses `mcpServers`; workspace `.vscode/mcp.json` uses `servers`.
- **Bump `version` for updates** in `plugin.json` (and the marketplace entry).
- **Copilot CLI caches plugin components.** Reinstall with `copilot plugin install ./my-plugin` to pick up local edits.

See [references/agent-plugin-reference.md § Gotchas](references/agent-plugin-reference.md) for the complete list, including hook format details and the classic-extension boundary.
