# my-agentic-stuff

Personal collection of skills I've built for AI coding agents, packaged as a plugin marketplace. The plugin format is shared across tools, so the same marketplace works in VS Code, the GitHub Copilot CLI, and Claude Code.

## Plugins

| Plugin | Skills | What it's for |
|---|---|---|
| `authoring` | agent-refiner, skill-creator, plugin-creator | Author and refine Copilot customizations |
| `decks` | build-deck | Build presentation decks as SVG slides packaged into `.pptx` |
| `eng-ops` | engdirs-status, worktree-setup | Git worktree and `.eng/` repo-state tooling |
| `engflow` | EngAgent external plugin | Engineering workflow agents and skills |
| `sessions` | chronicle-collect | Inspect and query Copilot session history |
| `code-review` | code-review | Local dual sub-agent code review, no PR |
| `pandoc-docx` | pandoc-docx | Convert markdown to styled `.docx` |
| `slop-check` | slop-check | Detect and fix AI slop in text |
| `visual-design` | visual-design | Judge and improve visual design of static artifacts |
| `work-search` | work-search | Search M365, internal eng knowledge, and MS docs |

`decks` uses `visual-design` and `slop-check` if they're installed, but doesn't require them.

## Install

> [!WARNING]
> **Back up your config first.** Installing a plugin writes into `~/.copilot/`, and a skill that shares a name with one you already have can overwrite it. If you keep local-only customizations there, copy them somewhere safe first:
> ```bash
> cp -r ~/.copilot ~/.copilot.bak
> ```

Two ways in:

### Direct from GitHub

If you only want to install and use the plugins, pull straight from GitHub. Untracked local files are excluded, so you get exactly what's committed.

**Copilot CLI:**

```bash
copilot plugin marketplace add jmerkow/my-agentic-stuff
copilot plugin marketplace browse my-agentic-stuff
copilot plugin install slop-check@my-agentic-stuff
```

**VS Code**: add the repo to `chat.plugins.marketplaces` in `settings.json`, then install plugins from the Chat plugin picker:

```jsonc
"chat.plugins.marketplaces": [
  "jmerkow/my-agentic-stuff"
]
```

### From a local clone (fork + dev work)

Fork and clone the repo, then register the **local path** as the source. Installs reflect your working tree, so edits show up without pushing.

**Copilot CLI:**

```bash
git clone https://github.com/<you>/my-agentic-stuff
cd my-agentic-stuff
git submodule update --init --recursive  # needed for submodule-backed plugins like engflow
copilot plugin marketplace add "$PWD"
copilot plugin install slop-check@my-agentic-stuff
```

**VS Code**: point `chat.plugins.marketplaces` at the local path:

```jsonc
"chat.plugins.marketplaces": [
  "/absolute/path/to/my-agentic-stuff"
]
```

To iterate: edit a skill, then re-run `copilot plugin update` (CLI) or reinstall from the picker (VS Code).

### Install individual plugins

Each plugin installs by name: `copilot plugin install <plugin>@my-agentic-stuff`. Bundles (`authoring`, `eng-ops`) install all their skills at once. `engflow` installs the external EngAgent plugin. The remaining entries install a single skill.

> The old `rsync` installer (`install.sh`) is **deprecated**. It still works for mirroring skills directly into `~/.copilot/skills/`, but plugins are the supported path now. See [INSTALL-RSYNC.md](INSTALL-RSYNC.md).

## Layout

```
my-agentic-stuff/
├── README.md
├── ADDING.md
├── INSTALL-RSYNC.md                 # deprecated rsync installer docs
├── install.sh                       # deprecated
├── scripts/validate-marketplace.py  # manifest validator
├── .claude-plugin/marketplace.json  # Claude marketplace manifest
├── catalog/                         # external plugin submodules
│   └── EngAgent/                    # provides the engflow plugin
└── skills/                          # canonical skills, shared across plugins
    ├── build-deck/                  # each has its own SKILL.md
    ├── slop-check/
    └── ...                          # one directory per skill
```

Most plugin entries use `source: "./"` and reference their skills in place (`./skills/<name>`), so a skill lives once under `skills/` and any plugin can pull it in without copying. External plugins can live under `catalog/` as submodules and point `source` at the plugin directory they provide. The authoritative marketplace manifest is `.claude-plugin/marketplace.json`.

## Adding stuff

See [ADDING.md](ADDING.md) for the steps to add a skill or plugin to the marketplace.

## Conventions

- One directory per skill under `skills/`. The `name` in `SKILL.md` matches the directory name.
- Skills should be self-contained. Companion skills like `slop-check` and `visual-design` are used only if present.
- Skill scripts go in `<skill>/scripts/`.
- A skill's example or smoke test goes in `<skill>/example/`.
