# Other Plugin Platforms (Orientation Only)

This skill targets **VS Code agent plugins for GitHub Copilot**. The agent plugin format is shared across several tools, so you may encounter plugin directories shaped for other hosts. Use this file to orient when reading those — not as a guide for authoring.

If a plugin is meant to run in VS Code + Copilot, see [agent-plugin-reference.md](agent-plugin-reference.md). Use this file only to identify and translate non-VS-Code plugin layouts.

---

## Plugin Format Detection

The shared plugin spec recognizes a `plugin.json` manifest in any of these locations. The location signals the intended primary host:

| Manifest path | Primary host |
|---------------|--------------|
| `plugin.json` (root) | Copilot / cross-tool default |
| `.github/plugin/plugin.json` | Copilot, repo-embedded |
| `.plugin/plugin.json` | OpenPlugin |
| `.claude-plugin/plugin.json` | Claude Code |

Marketplace manifests follow the same pattern: `marketplace.json`, `.github/plugin/marketplace.json`, `.plugin/marketplace.json`, `.claude-plugin/marketplace.json`.

VS Code can load a plugin from any of these layouts, but features that depend on host-specific tokens or files (below) will not all work.

---

## Claude Code Plugins

**Marker:** `.claude-plugin/plugin.json`, `.claude/agents/`, `.claude/skills/`, `hooks/hooks.json`.

Differences from the VS Code surface:

- **Plugin-root token:** `${CLAUDE_PLUGIN_ROOT}` is expanded in hook commands and MCP server config. VS Code recognizes this token in Claude-format plugins.
- **Hook config location:** `hooks/hooks.json` instead of root `hooks.json`.
- **Hook matchers:** Claude supports a `matcher` field (e.g. `"Edit|Write"`) on hook entries. VS Code parses these but ignores the matcher value — every event matches.
- **Tool name and case differences:** Claude tools use snake_case input properties (`tool_input.file_path`) and different tool names (`Write`, `Edit`). VS Code uses camelCase (`tool_input.filePath`) and names like `create_file`, `replace_string_in_file`. Hooks copied from Claude need translation.
- **Agent format:** `.claude/agents/<name>.md` (plain `.md`, not `.agent.md`) with frontmatter fields like `tools` as a comma-separated string instead of YAML array.

When you see one: it is portable to VS Code with caveats. Translate hook scripts before relying on them.

---

## OpenPlugin

**Marker:** `.plugin/plugin.json`.

- **Plugin-root token:** `${PLUGIN_ROOT}`.
- Otherwise mostly aligned with the cross-tool `plugin.json` schema.

---

## GitHub Copilot CLI Plugins

**Marker:** Same `plugin.json` schema. Installed via the `copilot plugin` CLI (`copilot plugin install OWNER/REPO`, `copilot plugin install ./local/path`).

Differences from the VS Code surface:

- **CLI-only fields in the schema:** `commands` and `lspServers` are documented in the CLI plugin reference; VS Code's behavior for these is underdocumented.
- **Marketplace registration via CLI:** `copilot plugin marketplace add ...` rather than `chat.plugins.marketplaces` in `settings.json`.
- **Install layout:** Marketplace installs land in `~/.copilot/installed-plugins/<MARKETPLACE>/<PLUGIN-NAME>/`; direct installs land in `~/.copilot/installed-plugins/_direct/<SOURCE-ID>/`.
- **Hook config:** `hooks.json` or `hooks/hooks.json`.
- **Precedence:** Agents and skills are first-found-wins; MCP servers are last-wins. Plugin components cannot override project-level or personal definitions of the same name.

A Copilot CLI plugin is generally also a valid VS Code agent plugin if it stays inside the shared schema.

---

## Sources

- https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference
- https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating
- https://code.claude.com/docs/en/plugin-marketplaces
- https://github.com/anthropics/skills
- https://code.visualstudio.com/docs/copilot/customization/agent-plugins (cross-tool compatibility section)
