#!/usr/bin/env python3
"""Validate .github/plugin/marketplace.json. Exit 0 if OK, 1 on any problem."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / ".github" / "plugin" / "marketplace.json"


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

        skills = plugin.get("skills") or []
        if not skills:
            errors.append(f"{name}: no skills listed")
        for rel in (plugin.get("source"), *skills):
            if isinstance(rel, str) and ".." in rel.split("/"):
                errors.append(f"{name}: path escapes root with '..': {rel}")

        for rel in skills:
            skill_md = ROOT / rel / "SKILL.md"
            if not skill_md.is_file():
                errors.append(f"{name}: missing SKILL.md at {rel}")
            elif (declared := skill_name(skill_md)) and declared != Path(rel).name:
                errors.append(f"{name}: SKILL.md name '{declared}' != dir '{Path(rel).name}'")

    for err in errors:
        print(f"  - {err}")
    print(f"FAIL: {len(errors)} problem(s)" if errors else f"ok: {len(plugins)} plugins")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
