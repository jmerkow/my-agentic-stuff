# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Read-only validator for a my-workspace workspace index."""

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

import yaml


def find_workspace_root(start_arg: str | None) -> Path | None:
    """Return the given root, or walk up from cwd until my-workspace.yaml is found."""
    if start_arg:
        return Path(start_arg).resolve()
    start = Path.cwd().resolve()
    for current in (start, *start.parents):
        if (current / "my-workspace.yaml").exists():
            return current
    return None


def load_index(index_path: Path) -> dict[str, object]:
    """Load my-workspace.yaml as a mapping of root entries."""
    loaded = yaml.safe_load(index_path.read_text())
    return loaded if isinstance(loaded, dict) else {}


def emit_error(message: str, root: Path | None, as_json: bool) -> int:
    """Report a fatal error, as JSON when requested, and return exit code 1."""
    if as_json:
        payload = {
            "root": str(root) if root else None,
            "status": "ERROR",
            "error": message,
            "issues": {},
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"ERROR: {message}")
    return 1


def main() -> int:
    """Validate the workspace root against my-workspace.yaml."""
    parser = argparse.ArgumentParser(description="Validate a my-workspace index (read-only).")
    parser.add_argument("root", nargs="?", help="workspace root (default: search upward from cwd)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    root = find_workspace_root(args.root)
    if root is None or not (root / "my-workspace.yaml").exists():
        return emit_error("not a my-workspace workspace (no my-workspace.yaml found)", root, args.json)

    try:
        index = load_index(root / "my-workspace.yaml")
    except (OSError, yaml.YAMLError) as exc:
        return emit_error(f"could not read my-workspace.yaml: {exc}", root, args.json)
    issues: defaultdict[str, set[str]] = defaultdict(set)

    # Every index entry must be a mapping with a non-empty description.
    for name, entry in sorted(index.items()):
        description = entry.get("description") if isinstance(entry, dict) else None
        if not isinstance(description, str) or not description.strip():
            issues[name].add("ERROR: malformed index entry (needs a description)")

    # Single pass over the root: collect dirs, flag loose files and unindexed dirs.
    try:
        root_names = sorted(os.listdir(root))
    except OSError as exc:
        return emit_error(f"could not list workspace root: {exc}", root, args.json)
    top_level_index = {name for name in index if "/" not in name}
    root_dirs: list[str] = []
    for name in root_names:
        if name == "my-workspace.yaml":
            continue
        if (root / name).is_dir():
            root_dirs.append(name)
            if name not in top_level_index:
                issues[name].add("ERROR: not indexed (add to my-workspace.yaml)")
        elif name not in index:
            issues[name].add("ERROR: loose file (move it or add an index entry)")

    # Validate every index entry plus every root dir (indexed or not). Flags
    # accumulate per dir: an unindexed non-git dir gets both ERRORs (index it +
    # git init); an unindexed dir that already has .git only needs indexing.
    for name in sorted(set(index) | set(root_dirs)):
        path = root / name
        entry = index.get(name)
        if not path.exists():
            issues[name].add("WARN: indexed path not found on disk")
        elif path.is_file():
            continue
        elif isinstance(entry, dict) and entry.get("vc_exception"):
            continue
        elif not (path / ".git").exists():
            issues[name].add("ERROR: not under git (run git init or set vc_exception)")

    has_error = any(flag.startswith("ERROR") for flags in issues.values() for flag in flags)

    if args.json:
        payload = {
            "root": str(root),
            "status": "FAIL" if has_error else "PASS",
            "issues": {name: sorted(issues[name]) for name in sorted(issues)},
        }
        print(json.dumps(payload, indent=2))
        return 1 if has_error else 0

    print(f"root: {root}")
    for name in sorted(issues):
        suffix = "/" if (root / name).is_dir() else ""
        print(f"{name}{suffix}:")
        for flag in sorted(issues[name]):
            print(f"  - {flag}")
    if not issues:
        print("PASS — nothing to fix")
    elif has_error:
        print(f"FAIL — {len(issues)} path(s) flagged")
    else:
        print(f"PASS — {len(issues)} path(s) flagged (warnings only)")
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
