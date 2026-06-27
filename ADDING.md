# Adding to this marketplace

Steps to add or change a plugin. The manifest is [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json).

## Add a skill to the marketplace

1. Create the skill at `skills/<name>/SKILL.md`. The `name` field in the frontmatter must match the directory name.
2. Edit `.claude-plugin/marketplace.json` and either:
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
└── .claude-plugin/plugin.json   # the plugin's own definition (name, skills, agents, hooks, mcp...)
```

The `plugin.json` is read from `.claude-plugin/plugin.json` under the plugin source. Use this when a plugin carries more than skills (agents, hooks, MCP servers) or should be self-contained.

> [!CAUTION]
> Don't set `strict: false` on an entry whose `source` dir also has a component-declaring `plugin.json`. That combination is a load conflict. Inline entries use `strict: false`. Self-managed `plugin.json` entries omit it, so `strict` defaults to `true` and the `plugin.json` becomes the authority that the marketplace entry supplements.

## Add an external plugin submodule

1. Confirm the target branch exists, then add it under `catalog/<repo-name>/`:
  ```bash
  git ls-remote --heads https://github.com/<owner>/<repo> <branch>
  git submodule add -b <branch> https://github.com/<owner>/<repo> catalog/<repo-name>
  ```
2. Point the marketplace entry at the subdirectory that owns the plugin manifest:
  ```jsonc
  { "name": "<plugin-name>", "source": "./catalog/<repo-name>/<plugin-dir>" }
  ```
3. Validate with `python3 scripts/validate-marketplace.py`.
