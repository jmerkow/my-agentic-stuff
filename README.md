# my-agentic-stuff

Personal source of truth for everything I've built around AI agents: skills, agents, prompts, MCP configs, and whatever else fits the category. Installs into the right Copilot directories by mirroring with `rsync` so this repo stays canonical.

## Install

```bash
./install.sh
```

Default behavior is an `rsync` dry-run preview. It resolves each selected item, runs `rsync -ain --delete`, and writes nothing. Results are grouped into `New installs:` and `Updates:` sections, where each update lists its changed files as `+` add, `~` update, `- delete`.

```bash
./install.sh --apply
```

Apply mode mirrors each valid item into the right target directory with `rsync -a --delete`, so stale files in the target are removed.

```bash
./install.sh --update          # preview updates to already-installed items only
./install.sh --apply --update  # update existing items, skip ones not installed yet
```

Update mode restricts the run to items that already exist in the target. Anything not yet installed is skipped (listed under `Skipped (not installed, --update)`) instead of being created. Combine with `--apply` to push updates without adding new items.

Use `--host <HOST>` to install to a remote machine over ssh. When `--host` is set and `COPILOT_SKILLS_DIR` is unset, the default remote base stays the literal `~/.copilot/skills` so the remote shell expands it.

Subset installs:

```bash
./install.sh skills                     # preview whole category
./install.sh --apply skills/build-deck  # apply one item by path
./install.sh build-deck                 # preview one item by name (searched in every category)
./install.sh --apply --host my-host skills/build-deck
```

### Install location

Skills install into `~/.copilot/skills` by default. If your Copilot keeps skills somewhere else, point the installer at that directory with `COPILOT_SKILLS_DIR`:

```bash
COPILOT_SKILLS_DIR=~/.config/copilot/skills ./install.sh --apply
```

The variable applies to a single run (prefix it on the command, as above) or can be exported for the session. With `--host`, the path must be valid on the remote machine, not the local one.

## Layout

```
my-agentic-stuff/
├── README.md
├── install.sh
└── skills/                  # → ~/.copilot/skills/
    ├── build-deck/          # each item has its own SKILL.md
    ├── slop-check/
    ├── diagram/
    └── ...                  # one directory per skill
```

Future categories (when needed): `agents/`, `prompts/`, `instructions/`, `mcp/`. Each gets a target-dir mapping in `install.sh` and a marker file convention.

## Adding stuff

1. Drop the new item under the right category dir (or create the category if it's the first of its kind).
2. Make sure it has the right marker file (`SKILL.md` for skills, TBD for other categories).
3. Run `./install.sh <category>/<name>` to preview it, then add `--apply` to apply the mirror.
4. Commit.

## Conventions

- One item per top-level directory inside its category; name = directory name.
- Items should be self-contained, with no cross-references between items in this repo (other than standard companion skills like `slop-check`, `diagram`).
- If an item ships scripts, put them at `<item>/scripts/`.
- If an item ships an example/test, put it at `<item>/example/` and make sure it works as a smoke test.
