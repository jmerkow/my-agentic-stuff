# Adding to this marketplace

Steps to add or change a plugin. The marketplace manifest is [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json). Each plugin source directory owns a top-level `plugin.json`.

## Add a skill plugin

Use this for a genuinely single-skill plugin that should stay under `skills/`.

1. Create the skill at `skills/<name>/SKILL.md`. The `name` field in the frontmatter must match the directory name.
2. Add `skills/<name>/plugin.json`:
   ```jsonc
   {
     "name": "<name>",
     "description": "<one line>",
     "skills": ["./"]
   }
   ```
3. Add an entry to `.claude-plugin/marketplace.json`:
   ```jsonc
   {
     "name": "<name>",
     "description": "<one line>",
     "source": "./skills/<name>"
   }
   ```
4. Validate:
   ```bash
   python3 scripts/validate-marketplace.py
   ```
5. Test from a local clone (see [README.md](README.md#from-a-local-clone-fork--dev-work)), then commit.

## Add a multi-component plugin

Create a real plugin directory that owns its manifest, then point the marketplace entry at that directory. Keep component paths in `plugin.json` relative to that plugin directory.

```text
plugins/<plugin-name>/
├── plugin.json
└── skills/
  └── <skill-name>/
    └── SKILL.md
```

```jsonc
{
  "name": "<plugin-name>",
  "description": "<one line>",
  "source": "./plugins/<plugin-name>"
}
```

## Add an external plugin

1. Confirm the target repo, plugin path, and ref.
2. Add a marketplace entry with a GitHub source object:
  ```jsonc
  {
    "name": "<plugin-name>",
    "source": {
      "source": "github",
      "repo": "<owner>/<repo>",
      "path": "<plugin-dir>",
      "ref": "<branch-or-tag>"
    }
  }
  ```
3. Validate with `python3 scripts/validate-marketplace.py`.
