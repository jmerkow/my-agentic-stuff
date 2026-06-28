#!/usr/bin/env python3
"""Validate marketplace entries and their plugin.json manifests."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / ".claude-plugin" / "marketplace.json"
ENTRY_COMPONENT_FIELDS = {
    "agents",
    "commands",
    "extensions",
    "hooks",
    "lspServers",
    "mcpServers",
    "rules",
    "skills",
}


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def skill_name(skill_md):
    front = skill_md.read_text(encoding="utf-8").split("---", 2)
    if len(front) < 3:
        return None
    m = re.search(r"^name:\s*(.+?)\s*$", front[1], re.MULTILINE)
    return m.group(1).strip("\"'") if m else None


def as_string_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return None


def path_escapes_root(rel):
    path = Path(rel)
    return path.is_absolute() or ".." in path.parts


def source_is_external(source):
    return source.removeprefix("./").startswith("catalog/")


def validate_skill_paths(plugin_name, plugin_dir, skills, errors):
    skill_paths = as_string_list(skills)
    if skill_paths is None:
        errors.append(f"{plugin_name}: plugin.json `skills` must be a string or string array")
        return
    if not skill_paths:
        errors.append(f"{plugin_name}: plugin.json must list at least one skill path")
        return
    for rel in skill_paths:
        if path_escapes_root(rel):
            errors.append(f"{plugin_name}: plugin.json skill path escapes plugin root: {rel}")
            continue
        skill_dir = plugin_dir / rel
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{plugin_name}: missing SKILL.md at {skill_md.relative_to(ROOT)}")
            continue
        declared = skill_name(skill_md)
        if declared and declared != skill_dir.resolve().name:
            errors.append(f"{plugin_name}: SKILL.md name '{declared}' != dir '{skill_dir.resolve().name}'")


def main():
    errors, seen = [], set()
    try:
        plugins = load_json(MANIFEST).get("plugins") or []
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1
    if not plugins:
        return print("FAIL: no `plugins` array") or 1

    for i, plugin in enumerate(plugins):
        name = plugin.get("name") or f"plugins[{i}]"
        if not plugin.get("name"):
            errors.append(f"{name}: missing `name`")
        if name in seen:
            errors.append(f"{name}: duplicate plugin name")
        seen.add(name)

        source = plugin.get("source")
        if not source:
            errors.append(f"{name}: missing `source`")
        elif path_escapes_root(source):
            errors.append(f"{name}: source path escapes marketplace root: {source}")
            continue

        entry_components = sorted(ENTRY_COMPONENT_FIELDS.intersection(plugin))
        if entry_components:
            fields = ", ".join(entry_components)
            errors.append(f"{name}: move marketplace component fields into source plugin.json: {fields}")

        if not source:
            continue
        source_dir = ROOT / source
        plugin_json = source_dir / "plugin.json"
        if not source_dir.is_dir():
            errors.append(f"{name}: source directory not found: {source}")
            continue
        if not plugin_json.is_file():
            errors.append(f"{name}: missing plugin.json at {plugin_json.relative_to(ROOT)}")
            continue
        try:
            plugin_manifest = load_json(plugin_json)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue
        declared = plugin_manifest.get("name")
        if declared != name:
            errors.append(f"{name}: plugin.json name '{declared}' != marketplace name")
        if not source_is_external(source):
            validate_skill_paths(name, source_dir, plugin_manifest.get("skills"), errors)

    for err in errors:
        print(f"  - {err}")
    print(f"FAIL: {len(errors)} problem(s)" if errors else f"ok: {len(plugins)} plugins")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
