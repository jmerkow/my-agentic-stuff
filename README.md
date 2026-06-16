# my-agentic-stuff

Personal source of truth for everything I've built around AI agents — skills, agents, prompts, MCP configs, and whatever else fits the category. Installs into the right Copilot directories via symlinks so this repo is canonical.

## Install

```bash
./install.sh
```

Walks each category dir and symlinks every valid item into the right place. Idempotent — re-runs replace stale symlinks but never touch a real directory.

Subset installs:

```bash
./install.sh skills              # whole category
./install.sh skills/build-deck   # one item by path
./install.sh build-deck          # one item by name (searched in every category)
```

Override the install target by setting `COPILOT_SKILLS_DIR` (and equivalents as they're added).

## Layout

```
my-agentic-stuff/
├── README.md
├── install.sh
└── skills/                  # → ~/.copilot/skills/
    └── build-deck/          # see skills/build-deck/SKILL.md
```

Future categories (when needed): `agents/`, `prompts/`, `instructions/`, `mcp/`. Each gets a target-dir mapping in `install.sh` and a marker file convention.

## Adding stuff

1. Drop the new item under the right category dir (or create the category if it's the first of its kind).
2. Make sure it has the right marker file (`SKILL.md` for skills, TBD for other categories).
3. Run `./install.sh <category>/<name>` to symlink it.
4. Commit.

## Conventions

- One item per top-level directory inside its category; name = directory name.
- Items should be self-contained — no cross-references between items in this repo (other than standard companion skills like `slop-check`, `diagram`).
- If an item ships scripts, put them at `<item>/scripts/`.
- If an item ships an example/test, put it at `<item>/example/` and make sure it works as a smoke test.
