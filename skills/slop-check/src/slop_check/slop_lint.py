"""Phrase linter for AI slop patterns."""

import argparse
import re
import sys
from pathlib import Path

import yaml

from slop_check.common import (
    DEFAULT_FIX_TYPES_PATH,
    REFERENCES_DIR,
    YamlValue,
    format_findings_json,
    format_findings_text,
    load_fix_types,
    summary_counts,
    validate_level,
)


def load_patterns(path: Path, fix_types_path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    patterns = yaml.safe_load(text)
    fix_types = load_fix_types(fix_types_path)
    validate_patterns(patterns, path, fix_types)
    return patterns


def validate_patterns(patterns: YamlValue, path: Path, fix_types: dict[str, dict]) -> None:
    """Validate phrase rule metadata loaded from YAML."""
    if not isinstance(patterns, list):
        raise ValueError(f"Expected a list of rules in {path}")
    for index, entry in enumerate(patterns, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Rule #{index} in {path} must be a mapping")
        level = entry.get("level")
        rule_name = entry.get("rule", f"#{index}")
        validate_level(level, str(rule_name), path)
        fix_type = entry.get("fix_type")
        if fix_type not in fix_types:
            valid_values = ", ".join(sorted(fix_types))
            raise ValueError(
                f"Rule {rule_name!r} in {path} has missing or invalid fix_type "
                f"{fix_type!r}; expected one of: {valid_values}"
            )


def lint_text(
    text: str,
    patterns: list[dict],
) -> list[dict]:
    """Lint text and return a list of findings sorted by line number."""
    lines = text.splitlines()
    findings: list[dict] = []

    for entry in patterns:
        level = entry["level"]
        unless_rx = None
        unless_pat = entry.get("unless")
        if unless_pat:
            try:
                unless_rx = re.compile(unless_pat, re.IGNORECASE)
            except re.error:
                unless_rx = None
        try:
            rx = re.compile(entry["pattern"], re.IGNORECASE)
        except re.error:
            continue
        for line_index, line in enumerate(lines):
            if unless_rx and unless_rx.search(line):
                continue
            for match in rx.finditer(line):
                findings.append(
                    {
                        "rule": entry.get("rule", ""),
                        "level": level,
                        "fix_type": entry["fix_type"],
                        "line": line_index + 1,
                        "match": match.group(),
                        "pattern": entry["pattern"],
                        "suggestion": entry.get("suggestion", ""),
                        "note": entry.get("note", ""),
                    }
                )

    findings.sort(key=lambda finding: (finding["line"], -finding["level"]))
    return findings


def format_text(findings: list[dict], filename: str | None = None) -> str:
    return format_findings_text(findings, filename, empty_message="No slop detected.")


def format_json(findings: list[dict], filename: str | None = None) -> str:
    return format_findings_json(findings, filename)


def main() -> int:
    default_patterns_path = REFERENCES_DIR / "slop-words.yaml"

    parser = argparse.ArgumentParser(description="Lint text for AI slop patterns.")
    parser.add_argument("files", nargs="*", help="Files to lint")
    parser.add_argument("--text", help="Inline text to lint")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--patterns",
        type=Path,
        default=default_patterns_path,
        help="Path to slop-words.yaml (default: %(default)s)",
    )
    parser.add_argument(
        "--fix-types",
        type=Path,
        default=DEFAULT_FIX_TYPES_PATH,
        help="Path to slop-fix-types.yaml (default: %(default)s)",
    )
    args = parser.parse_args()

    if not args.files and not args.text:
        parser.error("Provide files or --text")

    patterns_path = args.patterns
    fix_types_path = args.fix_types

    if not patterns_path.exists():
        print(f"Error: patterns file not found: {patterns_path}", file=sys.stderr)
        return 1
    if not fix_types_path.exists():
        print(f"Error: fix types file not found: {fix_types_path}", file=sys.stderr)
        return 1

    patterns = load_patterns(patterns_path, fix_types_path)
    all_findings: list[dict] = []
    outputs: list[str] = []

    if args.text:
        findings = lint_text(args.text, patterns)
        all_findings.extend(findings)
        formatter = format_json if args.format == "json" else format_text
        outputs.append(formatter(findings, "<inline>"))

    for filepath in args.files:
        path = Path(filepath)
        if not path.exists():
            print(f"Warning: {filepath} not found, skipping", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        findings = lint_text(text, patterns)
        all_findings.extend(findings)
        formatter = format_json if args.format == "json" else format_text
        outputs.append(formatter(findings, str(path)))

    print("\n\n".join(outputs))

    if args.format == "text" and all_findings:
        counts = summary_counts(all_findings)
        print(f"\n{'─' * 60}")
        parts = [
            f"{counts[3]} level 3",
            f"{counts[2]} level 2",
            f"{counts[1]} level 1",
        ]
        if counts[0]:
            parts.append(f"{counts[0]} level 0")
        print(f"TOTAL: {len(all_findings)} findings ({', '.join(parts)})")

    return 1 if any(finding["level"] >= 3 for finding in all_findings) else 0


if __name__ == "__main__":
    sys.exit(main())
