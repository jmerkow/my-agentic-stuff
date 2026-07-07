from collections import defaultdict
import json
from pathlib import Path

import yaml


SKILL_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_DIR = SKILL_ROOT / "references"
DEFAULT_FIX_TYPES_PATH = REFERENCES_DIR / "slop-fix-types.yaml"
YamlValue = dict[str, "YamlValue"] | list["YamlValue"] | str | int | float | bool | None

LEVEL_LABELS = {3: "high", 2: "medium", 1: "low", 0: "info"}
MATCH_DISPLAY_LIMIT = 60


def load_fix_types(path: Path) -> dict[str, dict]:
    fix_type_text = path.read_text(encoding="utf-8")
    fix_type_document = yaml.safe_load(fix_type_text)
    if not isinstance(fix_type_document, dict):
        raise ValueError(f"Expected a mapping in {path}")
    fix_types = fix_type_document.get("fix_types")
    if not isinstance(fix_types, dict) or not fix_types:
        raise ValueError(f"Expected non-empty fix_types mapping in {path}")
    for fix_type, definition in fix_types.items():
        if not isinstance(fix_type, str) or not fix_type:
            raise ValueError(f"Fix type keys in {path} must be non-empty strings")
        if not isinstance(definition, dict):
            raise ValueError(f"Fix type {fix_type!r} in {path} must be a mapping")
        description = definition.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"Fix type {fix_type!r} in {path} needs a description")
    return fix_types


def validate_level(level: YamlValue, rule_name: str, path: Path) -> None:
    if type(level) is not int or not 0 <= level <= 3:
        raise ValueError(
            f"Rule {rule_name!r} in {path} has missing or invalid level "
            f"{level!r}; expected an integer from 0 to 3"
        )


def _flatten_match(match: str, limit: int = MATCH_DISPLAY_LIMIT) -> str:
    """Collapse whitespace and truncate a matched span for compact display."""
    collapsed = " ".join(match.split())
    if len(collapsed) > limit:
        collapsed = collapsed[: limit - 1].rstrip() + "…"
    return collapsed


def format_findings_text(
    findings: list[dict],
    filename: str | None = None,
    empty_message: str = "No slop detected.",
) -> str:
    """Render findings as condensed text grouped by file, level, then rule.

    Within each rule, findings that share the same suggestion, fix type, and
    note are collapsed into a single advice block that lists every location.
    """
    label = filename or "text"
    if not findings:
        return f"✅ {label}: {empty_message}"

    header = f"{'─' * 60}\n{label} — {len(findings)} finding(s)\n{'─' * 60}"
    lines: list[str] = [header]

    by_level: dict[int, list[dict]] = defaultdict(list)
    for finding in findings:
        by_level[finding["level"]].append(finding)

    for level in sorted(by_level, reverse=True):
        level_findings = by_level[level]
        level_label = LEVEL_LABELS.get(level, str(level))
        lines.append(f"\nlevel {level} {level_label} — {len(level_findings)} finding(s)")

        by_rule: dict[str, list[dict]] = defaultdict(list)
        for finding in level_findings:
            by_rule[finding.get("rule", "")].append(finding)

        for rule_name in sorted(by_rule):
            rule_findings = by_rule[rule_name]
            lines.append(f"  [{rule_name}] {len(rule_findings)} finding(s)")

            advice_groups: dict[tuple, list[dict]] = defaultdict(list)
            for finding in rule_findings:
                key = (
                    finding.get("suggestion", ""),
                    finding.get("fix_type", ""),
                    finding.get("note", ""),
                )
                advice_groups[key].append(finding)

            for key in sorted(advice_groups, key=lambda k: min(f["line"] for f in advice_groups[k])):
                suggestion, fix_type, note = key
                group = sorted(advice_groups[key], key=lambda f: f["line"])
                fix_suffix = f" ({fix_type})" if fix_type else ""
                lines.append(f"    → {suggestion}{fix_suffix}")
                if note:
                    lines.append(f"      note: {note}")
                locations = " · ".join(f'L{f["line"]} "{_flatten_match(f["match"])}"' for f in group)
                lines.append(f"      {locations}")
    return "\n".join(lines)


def format_findings_json(findings: list[dict], filename: str | None = None) -> str:
    return json.dumps({"file": filename, "findings": findings}, indent=2)


def summary_counts(all_findings: list[dict]) -> dict[int, int]:
    counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for finding in all_findings:
        counts[finding["level"]] = counts.get(finding["level"], 0) + 1
    return counts
