# Deprecated: rsync installer

> **Deprecated.** This repo is now a Copilot plugin marketplace. Install via plugins instead (see [README.md](README.md)). The `install.sh` rsync flow is kept for now but is no longer the recommended path and may be removed.

`install.sh` mirrors items from this repo straight into your local Copilot directories with `rsync`. It predates the marketplace and writes skills directly to `~/.copilot/skills/` instead of going through the plugin system.

## Usage

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

## Install location

Skills install into `~/.copilot/skills` by default. If your Copilot keeps skills somewhere else, point the installer at that directory with `COPILOT_SKILLS_DIR`:

```bash
COPILOT_SKILLS_DIR=~/.config/copilot/skills ./install.sh --apply
```

The variable applies to a single run (prefix it on the command, as above) or can be exported for the session. With `--host`, the path must be valid on the remote machine, not the local one.
