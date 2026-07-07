---
name: marketplace-creator
description: >
  Create, publish, and register plugin marketplaces for GitHub Copilot in VS
  Code and the GitHub Copilot CLI. A marketplace is a Git repo (or local
  directory) with a marketplace.json manifest that lists installable plugins.
  Use when authoring marketplace.json, choosing where to place it
  (.claude-plugin/marketplace.json, .github/plugin/marketplace.json, or repo
  root), wiring chat.plugins.marketplaces in VS Code settings, running copilot
  plugin marketplace add, referencing plugins by local path or GitHub source,
  recommending marketplaces to a project via extraKnownMarketplaces and
  enabledPlugins, or debugging why a marketplace or its plugins do not resolve.
  Keywords: marketplace.json, plugin marketplace, chat.plugins.marketplaces,
  copilot plugin marketplace add, extraKnownMarketplaces, enabledPlugins,
  .claude-plugin/marketplace.json, .github/plugin/marketplace.json, source
  forms, github source, distribute plugin, publish plugin.
---

# Marketplace Creator

This skill follows the official Copilot plugin marketplace docs:

- VS Code: [Agent plugins in VS Code (Preview) § Configure plugin marketplaces](https://code.visualstudio.com/docs/agent-customization/agent-plugins)
- Copilot CLI: [Creating a plugin marketplace for GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-marketplace)

A marketplace is how you **distribute** plugins. To author the plugins themselves (`plugin.json`, skills, agents, hooks, MCP servers), use the **plugin-creator** skill first, then list those plugins here.

For the full schema, source forms, layouts, and gotchas, load [references/marketplace-reference.md](references/marketplace-reference.md).

> **Last verified:** 2026-07-07. Agent plugins are a Preview feature, so there is no stable version to pin. See [references/sources.md](references/sources.md) for the full source list, verification date, and tooling versions. Re-verify against those docs if behavior differs.

## What a marketplace is

A plugin marketplace is a Git repo (or local directory) containing a `marketplace.json` file that lists installable plugins. VS Code and the Copilot CLI clone or read the repo, parse `marketplace.json`, and offer its `plugins` entries for install.

This repository is itself a working marketplace: see [.claude-plugin/marketplace.json](../../../../.claude-plugin/marketplace.json) for a complete, validated example.

## Where marketplace.json goes

VS Code and the Copilot CLI look for `marketplace.json` in these locations:

| Path | Notes |
|------|-------|
| `.claude-plugin/marketplace.json` | Recommended. VS Code and the Copilot CLI both support it; this repo uses it. |
| `.github/plugin/marketplace.json` | Recommended by the Copilot CLI docs; repo-embedded. |
| `marketplace.json` (repo root) | Also recognized. |
| `.plugin/marketplace.json` | OpenPlugin-format layout. |

Pick one. `.claude-plugin/marketplace.json` is the recommended default here because it works in VS Code, the Copilot CLI, and Claude Code, and keeps the manifest out of `.github/`.

## Creating a marketplace

### 1. Author the plugins

Each plugin needs its own `plugin.json`. Use the **plugin-creator** skill to scaffold them. Keep each plugin in a bounded subdirectory (e.g., `plugins/<name>/` or `skills/<name>/`).

### 2. Add marketplace.json

```json
{
  "name": "my-marketplace",
  "owner": {
    "name": "Your Organization",
    "email": "plugins@example.com"
  },
  "metadata": {
    "description": "Curated plugins for our team",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "frontend-design",
      "description": "Create a professional-looking GUI ...",
      "version": "2.1.0",
      "source": "./plugins/frontend-design"
    },
    {
      "name": "security-checks",
      "description": "Check for potential security vulnerabilities ...",
      "version": "1.3.0",
      "source": "./plugins/security-checks"
    }
  ]
}
```

Required top-level fields: `name` (kebab-case, max 64 chars), `owner` (`{ name, email? }`), and `plugins`. Each plugin entry needs `name` and `source`. See [references/marketplace-reference.md § marketplace.json](references/marketplace-reference.md) for every field.

### 3. Point `source` at each plugin

`source` resolves relative to the marketplace repo root and can be a string or an object:

- **Local subdirectory:** `"source": "./plugins/frontend-design"`. Always point at a bounded subdirectory. Never use `"source": "./"`: it installs the whole repo instead of one plugin.
- **Plugin in another repo:** `"source": { "source": "github", "repo": "owner/repo", "path": "subdir", "ref": "branch-tag-or-sha" }`. `repo` is required; `path` selects a subdirectory; `ref` (or `sha`) pins a version.

See [references/marketplace-reference.md § Source forms](references/marketplace-reference.md) and [§ Plugin source layouts](references/marketplace-reference.md).

### 4. Validate

If your repo ships a validator (this one does), run it:

```bash
python3 scripts/validate-marketplace.py
```

## Registering a marketplace

**VS Code** — add the repo to `chat.plugins.marketplaces` in `settings.json`:

```json
"chat.plugins.marketplaces": [
  "owner/repo",
  "https://github.com/o/r.git",
  "git@github.com:owner/repo.git",
  "file:///path/to/local-marketplace"
]
```

**Copilot CLI**:

```bash
copilot plugin marketplace add OWNER/REPO      # GitHub repo
copilot plugin marketplace add /path/to/local  # local directory
copilot plugin marketplace list
copilot plugin marketplace browse MARKETPLACE-NAME
copilot plugin marketplace remove MARKETPLACE-NAME
```

Default marketplaces registered out of the box: `copilot-plugins`, `awesome-copilot`.

## Installing from a marketplace

**VS Code**: Extensions view → search `@agentPlugins` → **Install**. The first install from a new marketplace shows a trust prompt.

**Copilot CLI**:

```bash
copilot plugin install PLUGIN-NAME@MARKETPLACE-NAME
```

## Recommending a marketplace to a project

To surface a marketplace and pre-enable plugins for everyone on a project, add `extraKnownMarketplaces` and `enabledPlugins` to `.claude/settings.json` or `.github/copilot/settings.json`. VS Code surfaces these as `@agentPlugins @recommended` in the Extensions view.

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": { "source": "github", "repo": "your-org/plugin-marketplace" }
    }
  },
  "enabledPlugins": {
    "code-formatter@company-tools": true
  }
}
```

## Reference marketplaces

- This repo: [.claude-plugin/marketplace.json](../../../../.claude-plugin/marketplace.json)
- [github/copilot-plugins](https://github.com/github/copilot-plugins)
- [github/awesome-copilot](https://github.com/github/awesome-copilot)

## Troubleshooting

- **`marketplace.json` not found.** Place it at one of the recognized paths above; a manifest elsewhere is ignored.
- **`"source": "./"` installs the whole repo.** Always point `source` at a bounded plugin subdirectory.
- **Marketplace and plugin `name` mismatch.** The marketplace entry `name` must equal the `name` in that plugin's `plugin.json`.
- **Component fields belong in the plugin, not the entry.** Keep `skills`, `agents`, `hooks`, `mcpServers`, etc. in each plugin's `plugin.json`; the marketplace entry only references the plugin via `source` (plus metadata).
- **Bump `version` for updates.** Update checks pick up a new `version` in the plugin's `plugin.json` (and the marketplace entry).
- **Kebab-case names are required.** Marketplace and plugin names: `[a-z0-9-]+`, max 64 chars. Invalid names silently fail.

See [references/marketplace-reference.md § Gotchas](references/marketplace-reference.md) for the complete list.

## Sources

See [references/sources.md](references/sources.md) for the full source list and verification date.
