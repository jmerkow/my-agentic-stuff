# Marketplace Reference

Field reference, source forms, layouts, registration, and gotchas for Copilot plugin marketplaces (VS Code + Copilot CLI). Sourced from the official VS Code and GitHub Copilot CLI plugin docs; see [sources.md](sources.md) for the full source list and verification date.

To author the plugins that a marketplace lists, see the **plugin-creator** skill.

---

## marketplace.json

A plugin marketplace is a Git repo (or local directory) containing a `marketplace.json` file.

### Recognized paths

VS Code and the Copilot CLI look for the marketplace manifest in these locations:

| Path | Notes |
|------|-------|
| `.claude-plugin/marketplace.json` | Supported by VS Code and the Copilot CLI. Recommended default; this repo uses it. |
| `.github/plugin/marketplace.json` | Recommended by the Copilot CLI docs. |
| `marketplace.json` (repo root) | Recognized. |
| `.plugin/marketplace.json` | OpenPlugin-format layout. |

For a complete `marketplace.json` example, see the **marketplace-creator** SKILL.md.

### Top-level fields

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | Kebab-case, max 64 chars |
| `owner` | Yes | `{ name, email? }` |
| `plugins` | Yes | Array of plugin entries |
| `metadata` | No | `{ description?, version?, pluginRoot? }` |

### Plugin entry fields

Each entry in the `plugins` array supports:

- **Required:** `name` and `source`.
- **Metadata and component paths:** the same fields as `plugin.json` (`description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `category`, `tags`, `commands`, `agents`, `skills`, `hooks`, `mcpServers`, `lspServers`).
- **`source` resolution:** relative to the marketplace repo root; the leading `./` is optional (`"./plugins/x"` and `"plugins/x"` resolve the same).
- **`strict`** (optional, default `true`): full schema validation. Set `false` for relaxed validation on direct installs or legacy plugins.

Prefer keeping component path fields (`skills`, `agents`, `hooks`, `mcpServers`, ...) inside each plugin's own `plugin.json` rather than in the marketplace entry; the entry then only needs `name`, `source`, and light metadata.

### Source forms

`source` can be a string or an object.

- **String (local subdirectory of this marketplace repo):**
  ```json
  "source": "./plugins/frontend-design"
  ```
  Always point at a bounded subdirectory. Never use `"source": "./"`: it installs the entire repo instead of a single plugin.

- **Object (a plugin hosted in another repo, no submodule needed):**
  ```json
  "source": { "source": "github", "repo": "owner/repo", "path": "subdir", "ref": "branch-tag-or-sha" }
  ```
  `repo` is required. `path` selects a subdirectory inside that repo (omit if the plugin is at the repo root). `ref` pins a branch, tag, or sha; `sha` may also be given for an exact pin.

### Plugin source layouts

A plugin's source directory can be shaped two ways:

- **Single-skill plugin:** put `plugin.json` in `skills/<name>/` beside `SKILL.md`, with `"skills": ["./"]`. The marketplace entry `source` is `./skills/<name>`. It installs flat as `<name>/`.
- **Grouped multi-skill plugin:** put `plugins/<group>/plugin.json` with `"skills": ["./skills/<a>", "./skills/<b>"]`, and place each skill in `plugins/<group>/skills/<skill>/`. The marketplace entry `source` is `./plugins/<group>`. It installs as `<group>/skills/<skill>/`.

---

## Registering and installing

### VS Code

```json
// settings.json
"chat.plugins.marketplaces": [
  "owner/repo",
  "https://github.com/o/r.git",
  "git@github.com:owner/repo.git",
  "file:///path/to/local-marketplace"
]
```

Reference formats:

- **Shorthand:** `owner/repo` for public GitHub repos.
- **HTTPS git remote:** a full URL ending in `.git`.
- **SCP-style git remote:** `git@github.com:owner/repo.git`.
- **file URI:** `file:///path/to/local-marketplace` for a marketplace already on disk.

Private repos are supported; if a public lookup fails, VS Code falls back to cloning directly. Install a browsed plugin from the Extensions view (`@agentPlugins` → **Install**); the first install from a new marketplace shows a trust prompt.

### Copilot CLI

```bash
# Marketplaces
copilot plugin marketplace add OWNER/REPO
copilot plugin marketplace add /path/to/local
copilot plugin marketplace list
copilot plugin marketplace browse MARKETPLACE-NAME
copilot plugin marketplace remove MARKETPLACE-NAME

# Install a plugin from a registered marketplace
copilot plugin install PLUGIN-NAME@MARKETPLACE-NAME
```

Default Copilot CLI marketplaces (registered out of the box): `copilot-plugins`, `awesome-copilot`.

### Copilot CLI install layout

| Source | Path |
|--------|------|
| Marketplace install | `~/.copilot/installed-plugins/<MARKETPLACE>/<PLUGIN-NAME>/` |
| Direct install | `~/.copilot/installed-plugins/_direct/<SOURCE-ID>/` |

---

## Workspace recommendations

A project can recommend a marketplace and pre-enable plugins by configuring `.claude/settings.json` or `.github/copilot/settings.json`. VS Code surfaces these under `@agentPlugins @recommended` and prompts on the first chat message.

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

- **`extraKnownMarketplaces`**: registers additional marketplaces for the project; they appear when searching `@agentPlugins`.
- **`enabledPlugins`**: lists `plugin@marketplace` entries to enable by default.

---

## Updating

VS Code checks for updates on **Extensions: Check for Extension Updates** or automatically every 24 hours when `extensions.autoUpdate` is on; updating pulls changes from cloned marketplace repos. Plugins sourced from npm or PyPI never auto-update — they show an **Update** button. On the Copilot CLI, run `copilot plugin update PLUGIN-NAME` or `copilot plugin update --all`. Bump `version` in the plugin's `plugin.json` (and the marketplace entry) so update checks pick up changes.

---

## Troubleshooting

- **Manifest must live at a recognized path.** `.claude-plugin/marketplace.json`, `.github/plugin/marketplace.json`, root `marketplace.json`, or `.plugin/marketplace.json`. Elsewhere it is ignored.
- **Never `"source": "./"`.** It installs the entire repo instead of one plugin. Always point at a bounded subdirectory or a `github` source object.
- **Entry `name` must equal the plugin's `plugin.json` name.** A mismatch fails validation.
- **Keep component fields in the plugin.** `skills`, `agents`, `hooks`, `mcpServers`, `lspServers`, `commands`, `extensions` belong in each plugin's `plugin.json`, not the marketplace entry.
- **Kebab-case names are required.** Marketplace and plugin names: `[a-z0-9-]+`, max 64 chars. Invalid names silently fail.
- **Bump `version` for updates.** Update checks compare `version` in `plugin.json` (and the marketplace entry).
- **Trust boundaries.** Plugins can ship hooks and MCP servers that run code; the first install from a new marketplace prompts for trust. Review a marketplace source before adding it.

---

## Sources

See [sources.md](sources.md) for the full source list and verification date.
