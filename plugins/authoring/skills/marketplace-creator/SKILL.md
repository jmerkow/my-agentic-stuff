---
name: marketplace-creator
description: >
  Create, publish, and register plugin marketplaces for GitHub Copilot in VS
  Code and the GitHub Copilot CLI. A marketplace is a Git repo (or local
  directory) with a marketplace.json manifest that lists installable plugins.
  Use when authoring marketplace.json, choosing where to place it, registering a
  marketplace via chat.plugins.marketplaces or copilot plugin marketplace add,
  or recommending marketplaces to a project with extraKnownMarketplaces and
  enabledPlugins.
  Keywords: marketplace.json, plugin marketplace, chat.plugins.marketplaces,
  copilot plugin marketplace add, extraKnownMarketplaces, enabledPlugins.
---

# Marketplace Creator

A marketplace is a Git repo (or local directory) with a `marketplace.json` manifest that lists installable plugins. VS Code and the Copilot CLI read that manifest and offer its `plugins` for install. This skill covers authoring, registering, and installing from a marketplace.

To author the plugins a marketplace lists (`plugin.json`, skills, agents, hooks, MCP servers), use the **plugin-creator** skill first.

Official docs:

- VS Code: [Agent plugins in VS Code (Preview) § Configure plugin marketplaces](https://code.visualstudio.com/docs/agent-customization/agent-plugins)
- Copilot CLI: [Creating a plugin marketplace for GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-marketplace)

For the full schema, source forms, install layouts, and troubleshooting, load [references/marketplace-reference.md](references/marketplace-reference.md).

> **Last verified:** 2026-07-07. Agent plugins are a Preview feature, so there is no stable version to pin. See [references/sources.md](references/sources.md) for the full source list. Re-verify if behavior differs.

## Create a marketplace

### 1. Author the plugins

Each plugin needs its own `plugin.json` in a bounded subdirectory (e.g., `plugins/<name>/`). Use the **plugin-creator** skill to scaffold them.

### 2. Add `marketplace.json`

Place it at one of these paths (pick one). `.claude-plugin/marketplace.json` is the recommended default: it works in VS Code, the Copilot CLI, and Claude Code.

| Path | Notes |
|------|-------|
| `.claude-plugin/marketplace.json` | Recommended default. |
| `.github/plugin/marketplace.json` | Recommended by the Copilot CLI docs. |
| `marketplace.json` (repo root) | Recognized. |
| `.plugin/marketplace.json` | OpenPlugin-format layout. |

```json
{
  "name": "my-marketplace",
  "owner": { "name": "Your Organization", "email": "plugins@example.com" },
  "metadata": { "description": "Curated plugins for our team", "version": "1.0.0" },
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
      "source": { "source": "github", "repo": "your-org/security-plugins", "path": "checks", "ref": "v1.3.0" }
    }
  ]
}
```

Required top-level fields: `name` (kebab-case, max 64 chars), `owner`, and `plugins`. Each plugin entry needs `name` and `source`. See [references/marketplace-reference.md § marketplace.json](references/marketplace-reference.md) for every field.

### 3. Point `source` at each plugin

`source` resolves relative to the marketplace repo root. It is one of:

- **String — local subdirectory:** `"source": "./plugins/frontend-design"`. Point at a bounded subdirectory. Never use `"source": "./"`; it installs the whole repo instead of one plugin.
- **Object — plugin in another repo:** `"source": { "source": "github", "repo": "owner/repo", "path": "subdir", "ref": "branch-tag-or-sha" }`. Only `repo` is required; `path` selects a subdirectory; `ref` (or `sha`) pins a version.

See [references/marketplace-reference.md § Source forms](references/marketplace-reference.md).

### 4. Validate

If your repo ships a validator, run it (this repo does):

```bash
python3 scripts/validate-marketplace.py
```

## Register a marketplace

**VS Code** — add the repo to `chat.plugins.marketplaces` in `settings.json`:

```json
"chat.plugins.marketplaces": [
  "owner/repo",
  "https://github.com/o/r.git",
  "git@github.com:owner/repo.git",
  "file:///path/to/local-marketplace"
]
```

**Copilot CLI:**

```bash
copilot plugin marketplace add OWNER/REPO      # GitHub repo
copilot plugin marketplace add /path/to/local  # local directory
copilot plugin marketplace list
```

`copilot-plugins` and `awesome-copilot` are registered out of the box.

## Install from a marketplace

- **VS Code:** Extensions view → search `@agentPlugins` → **Install**. The first install from a new marketplace shows a trust prompt.
- **Copilot CLI:** `copilot plugin install PLUGIN-NAME@MARKETPLACE-NAME`.

## Recommend a marketplace to a project

Add `extraKnownMarketplaces` and `enabledPlugins` to `.claude/settings.json` or `.github/copilot/settings.json` to surface a marketplace and pre-enable plugins for everyone. VS Code shows these under `@agentPlugins @recommended`.

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": { "source": "github", "repo": "your-org/plugin-marketplace" }
    }
  },
  "enabledPlugins": { "code-formatter@company-tools": true }
}
```

## More

- Full schema, install layouts, and **troubleshooting**: [references/marketplace-reference.md](references/marketplace-reference.md)
- Public example marketplaces: [github/copilot-plugins](https://github.com/github/copilot-plugins), [github/awesome-copilot](https://github.com/github/awesome-copilot)
- Sources and verification date: [references/sources.md](references/sources.md)
