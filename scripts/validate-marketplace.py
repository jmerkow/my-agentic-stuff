#!/usr/bin/env python3
"""Validate .claude-plugin/marketplace.json. Exit 0 if OK, 1 on any problem."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / ".claude-plugin" / "marketplace.json"


def skill_name(skill_md):
    front = skill_md.read_text(encoding="utf-8").split("---", 2)
    if len(front) < 3:
        return None
    m = re.search(r"^name:\s*(.+?)\s*$", front[1], re.MULTILINE)
    return m.group(1).strip("\"'") if m else None


def main():
    errors, seen = [], set()
    plugins = json.loads(MANIFEST.read_text(encoding="utf-8")).get("plugins") or []
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

        skills = plugin.get("skills") or []
        for rel in (source, *skills):
            if isinstance(rel, str) and ".." in rel.split("/"):
                errors.append(f"{name}: path escapes root with '..': {rel}")

        if skills:
            for rel in skills:
                skill_md = ROOT / rel / "SKILL.md"
                if not skill_md.is_file():
                    errors.append(f"{name}: missing SKILL.md at {rel}")
                elif (declared := skill_name(skill_md)) and declared != Path(rel).name:
                    errors.append(f"{name}: SKILL.md name '{declared}' != dir '{Path(rel).name}'")
        elif source:
            source_dir = ROOT / source
            plugin_json = next(
                (source_dir / rel for rel in (".claude-plugin/plugin.json", "plugin.json") if (source_dir / rel).is_file()),
                None,
            )
            if not plugin_json:
                errors.append(f"{name}: no skills listed and no plugin.json under source")
            elif plugin.get("strict") is False:
                errors.append(f"{name}: strict false conflicts with source plugin.json")
            else:
                declared = json.loads(plugin_json.read_text(encoding="utf-8")).get("name")
                if declared and declared != name:
                    errors.append(f"{name}: plugin.json name '{declared}' != marketplace name")

    for err in errors:
        print(f"  - {err}")
    print(f"FAIL: {len(errors)} problem(s)" if errors else f"ok: {len(plugins)} plugins")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
