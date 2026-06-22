# my-agentic-stuff

Personal source of truth for everything I've built around AI agents: skills, agents, prompts, MCP configs, and whatever else fits the category. This repo is an **agent plugin marketplace**. The plugin format is shared across tools, so the same marketplace works in VS Code, the GitHub Copilot CLI, and Claude Code.

## Plugins

| Plugin | Skills | What it's for |
|---|---|---|
| `authoring` | agent-refiner, skill-creator, plugin-creator | Author and refine Copilot customizations |
| `decks` | build-deck | Build presentation decks as SVG slides packaged into `.pptx` |
| `eng-ops` | engdirs-status, worktree-setup | Git worktree and `.eng/` repo-state tooling |
| `sessions` | chronicle-collect | Inspect and query Copilot session history |
| `code-review` | code-review | Local dual sub-agent code review, no PR |
| `pandoc-docx` | pandoc-docx | Convert markdown to styled `.docx` |
| `slop-check` | slop-check | Detect and fix AI slop in text |
| `visual-design` | visual-design | Judge and improve visual design of static artifacts |
| `work-search` | work-search | Search M365, internal eng knowledge, and MS docs |

`decks` uses `visual-design` and `slop-check` if they're installed, but doesn't require them.

## Install

> [!WARNING]
> **Back up your private config first.** Installing a plugin writes into your Copilot directories and can overwrite existing skills or config under `~/.copilot/`. If you keep private or local-only customizations there, copy them somewhere safe before installing:
> ```bash
> cp -r ~/.copilot ~/.copilot.bak
> ```
> This is a file-overwrite risk, not a code-execution one: every plugin here is skills-only (markdown, model-invoked) and ships no hooks, MCP servers, or scripts, so installing runs no code.

There are two ways in, depending on what you want.

### Direct from GitHub (just use it)

If you only want to install and use the plugins, pull straight from GitHub. Untracked local files are excluded, so you get exactly what's committed.

**Copilot CLI:**

```bash
copilot plugin marketplace add jmerkow/my-agentic-stuff
copilot plugin marketplace browse my-agentic-stuff
copilot plugin install slop-check@my-agentic-stuff
```

**VS Code** — add the repo to `chat.plugins.marketplaces` in `settings.json`, then install plugins from the Chat plugin picker:

```jsonc
"chat.plugins.marketplaces": [
  "jmerkow/my-agentic-stuff"
]
```

### From a local clone (fork + dev work)

If you want to edit skills, add new ones, or develop against the marketplace, fork and clone the repo, then register the **local path** as the source. Installs reflect your working tree, so changes show up without pushing.

**Copilot CLI:**

```bash
git clone https://github.com/<you>/my-agentic-stuff
cd my-agentic-stuff
copilot plugin marketplace add "$PWD"
copilot plugin install slop-check@my-agentic-stuff
```

**VS Code** — point `chat.plugins.marketplaces` at the local path:

```jsonc
"chat.plugins.marketplaces": [
  "/absolute/path/to/my-agentic-stuff"
]
```

To iterate: edit a skill, then re-run `copilot plugin update` (CLI) or reinstall from the picker (VS Code).

### Install individual plugins

Each plugin installs by name: `copilot plugin install <plugin>@my-agentic-stuff`. Bundles (`authoring`, `eng-ops`) install all their skills at once; the rest install a single skill.

> The old `rsync` installer (`install.sh`) is **deprecated**. It still works for mirroring skills directly into `~/.copilot/skills/`, but plugins are the supported path now. See [INSTALL-RSYNC.md](INSTALL-RSYNC.md).

## Layout

```
my-agentic-stuff/
├── README.md
├── INSTALL-RSYNC.md                 # deprecated rsync installer docs
├── install.sh                       # deprecated
├── .github/plugin/marketplace.json  # marketplace manifest (9 plugins)
├── .claude-plugin/marketplace.json  # symlink → above, for Claude Code
└── skills/                          # canonical skills, shared across plugins
    ├── build-deck/                  # each item has its own SKILL.md
    ├── slop-check/
    └── ...                          # one directory per skill
```

Every plugin entry uses `source: "./"` and references its skills in place (`./skills/<name>`), so skills live canonically under `skills/` and any plugin can pull one in without copying it. The `.claude-plugin/marketplace.json` symlink lets Claude Code read the same manifest VS Code and the Copilot CLI use.

Future categories (when needed): `agents/`, `prompts/`, `instructions/`, `mcp/`. Per-plugin extras (agents, hooks, MCP configs) go under `plugins/<name>/`, added lazily the first time a plugin needs one.

## Adding stuff

1. Drop the new skill under `skills/<name>/` with a `SKILL.md` (`name` field must match the directory name).
2. Add or extend a plugin entry in [.github/plugin/marketplace.json](.github/plugin/marketplace.json) pointing at `./skills/<name>`. Reuse an existing bundle if it fits, or add a standalone entry.
3. Validate the manifest:
   ```bash
   python3 -c "import json,os; m=json.load(open('.github/plugin/marketplace.json')); bad=[s for p in m['plugins'] for s in p['skills'] if not os.path.isfile(os.path.join(s,'SKILL.md'))]; print('MISSING:',bad) if bad else print('ok,',len(m['plugins']),'plugins')"
   ```
4. Test from a local clone (see above), then commit.

## Conventions

- One item per top-level directory inside its category; name = directory name.
- Items should be self-contained, with no hard cross-references between items (companion skills like `slop-check` and `visual-design` are used only if present).
- If an item ships scripts, put them at `<item>/scripts/`.
- If an item ships an example/test, put it at `<item>/example/` and make sure it works as a smoke test.
