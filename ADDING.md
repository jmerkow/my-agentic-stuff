# Adding to this marketplace

Steps to add or change a plugin. The manifest is [.github/plugin/marketplace.json](.github/plugin/marketplace.json) (the `.claude-plugin/marketplace.json` symlink points at it, no need to touch that).

## Add a skill to the marketplace

1. Create the skill at `skills/<name>/SKILL.md`. The `name` field in the frontmatter must match the directory name.
2. Edit `.github/plugin/marketplace.json` and either:
   - **add it to an existing plugin**: append `"./skills/<name>"` to that plugin's `skills` array, or
   - **make it a new plugin**: add an entry to the `plugins` array:
     ```jsonc
     {
       "name": "<plugin-name>",
       "description": "<one line>",
       "source": "./",
       "strict": false,
       "skills": ["./skills/<name>"]
     }
     ```
3. Validate:
   ```bash
   python3 scripts/validate-marketplace.py
   ```
4. Test from a local clone (see [README.md](README.md#from-a-local-clone-fork--dev-work)), then commit.

> [!NOTE]
> A skill can be referenced by more than one plugin.

## Two ways to define a plugin

**Inline (default, what this repo uses).** The marketplace entry is the whole definition: `source: "./"` (repo root) plus a `skills` array pointing at shared `skills/`. Set `strict: false`. No per-plugin file. Best for skills-only plugins that share the top-level `skills/` folder.

**Self-managed `plugin.json`.** Point `source` at a plugin directory that owns its own `plugin.json`. The manifest entry just references it:

```jsonc
{ "name": "<plugin-name>", "source": "./plugins/<plugin-name>" }
```

```
plugins/<plugin-name>/
└── .github/plugin/plugin.json   # the plugin's own definition (name, skills, agents, hooks, mcp...)
```

The `plugin.json` is auto-detected at any of: `plugin.json`, `.plugin/plugin.json`, `.github/plugin/plugin.json`, `.claude-plugin/plugin.json`. Use this when a plugin carries more than skills (agents, hooks, MCP servers) or should be self-contained.

> [!CAUTION]
> Don't set `strict: false` on an entry whose `source` dir also has a component-declaring `plugin.json`. That combination is a load conflict. Inline entries use `strict: false`. Self-managed `plugin.json` entries omit it, so `strict` defaults to `true` and the `plugin.json` becomes the authority that the marketplace entry supplements.
