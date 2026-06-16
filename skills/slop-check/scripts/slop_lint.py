#!/usr/bin/env python3
"""Slop linter — mechanically scans text files for AI slop patterns.

Usage:
    python slop_lint.py FILE [FILE ...]          # lint files
    python slop_lint.py --text "some text"       # lint inline text
    python slop_lint.py FILE --severity medium   # minimum severity (low|medium|high)
    python slop_lint.py FILE --format json       # output as JSON

Reads patterns from references/slop-words.yaml (relative to this script).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # fall back to built-in parser


# ── YAML loading ────────────────────────────────────────────────────────────────

def _parse_yaml_fallback(text: str) -> dict:
    """Minimal YAML-subset parser for the slop-words file when PyYAML is unavailable.

    Handles the specific structure: top-level keys (high/medium/low) each containing
    a list of mappings with pattern, suggestion, and optional note fields.
    """
    result: dict[str, list[dict]] = {}
    current_key: str | None = None
    current_item: dict | None = None
    items: list[dict] = []

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Top-level key like "high:" / "medium:" / "low:"
        if re.match(r"^[a-z]+:\s*$", stripped):
            if current_key and items:
                result[current_key] = items
            current_key = stripped.rstrip(":").strip()
            items = []
            current_item = None
            continue

        # List item start: "  - pattern: ..."
        m = re.match(r'^-\s+(\w+):\s+"(.*)"', stripped)
        if m:
            if current_item:
                items.append(current_item)
            current_item = {m.group(1): m.group(2)}
            continue

        # Continuation field: "    suggestion: ..." or "    note: ..."
        m = re.match(r'^(\w+):\s+"(.*)"', stripped)
        if m and current_item is not None:
            current_item[m.group(1)] = m.group(2)
            continue

    if current_item:
        items.append(current_item)
    if current_key and items:
        result[current_key] = items

    return result


def load_patterns(path: Path) -> dict[str, list[dict]]:
    text = path.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text)
    return _parse_yaml_fallback(text)


# ── Structural checks ──────────────────────────────────────────────────────────

SEVERITY_RANK = {"high": 4, "medium": 3, "low": 2, "info": 1}


def _structural_checks(lines: list[str]) -> list[dict]:
    """Flag structural slop patterns that regex word lists can't catch."""
    findings: list[dict] = []
    full_text = "\n".join(lines)
    word_count = len(full_text.split())

    # Count connector overuse in a sliding window
    connector_re = re.compile(r"\b(additionally|furthermore|moreover)\b", re.I)
    window = 5  # lines
    for i in range(len(lines)):
        chunk = lines[i : i + window]
        hits = []
        for j, line in enumerate(chunk):
            for m in connector_re.finditer(line):
                hits.append((i + j + 1, m.group()))
        if len(hits) >= 3:
            findings.append(
                {
                    "severity": "medium",
                    "line": hits[0][0],
                    "match": ", ".join(h[1] for h in hits),
                    "pattern": "(connector overuse)",
                    "suggestion": f"3+ transition connectors within {window} lines. Vary structure.",
                }
            )

    # Excessive bullet lists: >10 consecutive bullet lines
    bullet_run = 0
    run_start = 0
    for i, line in enumerate(lines):
        if re.match(r"^\s*[-*•]\s", line):
            if bullet_run == 0:
                run_start = i + 1
            bullet_run += 1
        else:
            if bullet_run > 10:
                findings.append(
                    {
                        "severity": "low",
                        "line": run_start,
                        "match": f"{bullet_run} consecutive bullet items",
                        "pattern": "(excessive list)",
                        "suggestion": "Consider using prose for some of these — long lists can be slop.",
                    }
                )
            bullet_run = 0

    # Catch trailing long list
    if bullet_run > 10:
        findings.append(
            {
                "severity": "low",
                "line": run_start,
                "match": f"{bullet_run} consecutive bullet items",
                "pattern": "(excessive list)",
                "suggestion": "Consider using prose for some of these — long lists can be slop.",
            }
        )

    # Exclamation mark overuse
    excl_lines = [(i + 1) for i, l in enumerate(lines) if l.count("!") >= 2]
    if len(excl_lines) >= 3:
        findings.append(
            {
                "severity": "low",
                "line": excl_lines[0],
                "match": f"{len(excl_lines)} lines with multiple exclamation marks",
                "pattern": "(exclamation overuse)",
                "suggestion": "Reduce exclamation marks — they signal unnatural enthusiasm.",
            }
        )

    # Fancy unicode characters — AI tells
    # Map of char → (name, ascii alternative)
    _unicode_chars = {
        "\u2013": ("en dash", "hyphen or 'to'"),
        "\u2192": ("right arrow →", "'->',  'to', or plain text"),
        "\u2190": ("left arrow ←", "'<-' or plain text"),
        "\u2022": ("bullet •", "'-' or '*'"),
        "\u2018": ("left single quote \u2018", "straight quote '"),
        "\u2019": ("right single quote \u2019", "straight quote '"),
        "\u201c": ("left double quote \u201c", 'straight quote "'),
        "\u201d": ("right double quote \u201d", 'straight quote "'),
        "\u2026": ("ellipsis \u2026", "'...'"),
        "\u2716": ("heavy multiplication \u2716", "'x' or '*'"),
        "\u2714": ("check mark \u2714", "plain text or markdown"),
        "\u2717": ("ballot x \u2717", "plain text or markdown"),
        "\u2728": ("sparkles \u2728", "remove or use plain text"),
        "\u2705": ("check box \u2705", "plain text or markdown"),
    }
    unicode_re = re.compile("[" + "".join(_unicode_chars.keys()) + "]")
    unicode_hits: dict[str, list[int]] = {}
    for i, line in enumerate(lines):
        for m in unicode_re.finditer(line):
            ch = m.group()
            unicode_hits.setdefault(ch, []).append(i + 1)

    for ch, line_nos in unicode_hits.items():
        name, alt = _unicode_chars[ch]
        for line_no in line_nos:
            findings.append(
                {
                    "severity": "info",
                    "line": line_no,
                    "match": ch,
                    "pattern": f"(unicode: {name})",
                    "suggestion": f"Fancy unicode. Consider {alt}. OK sparingly, avoid overuse.",
                }
            )
        # Escalate: 5+ hits, or >= 1 per 100 words
        density = len(line_nos) / max(word_count, 1)
        if len(line_nos) >= 5 or (word_count >= 50 and density >= 0.01):
            findings.append(
                {
                    "severity": "medium",
                    "line": line_nos[0],
                    "match": f"{len(line_nos)}x {name} in ~{word_count} words",
                    "pattern": f"(unicode overuse: {name})",
                    "suggestion": f"Heavy {name} usage is an AI writing tell. Replace most with {alt}.",
                }
            )

    # Em dashes and mid-line ` - ` — flag once per line for human review.
    # Acceptable: `**label** - details` (label-then-detail pattern).
    # Suspect: em dashes / ` - ` used as sentence punctuation. Linter doesn't
    # judge — it surfaces the line so the agent or human can evaluate.
    # Bullets (` - ` at line start) are skipped.
    em_dash_re = re.compile(r"\u2014")
    # No-space em dash: word—word (sneaky sentence punctuation that looks like
    # the acceptable bold-lead pattern but isn't). Flagged at medium.
    nospace_em_dash_re = re.compile(r"(?<=\w)\u2014(?=\w)")
    spaced_hyphen_re = re.compile(r"(?<=\S) - (?=\S)")
    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        # Skip pure bullet lines so list markers don't fire.
        is_bullet_line = bool(re.match(r"[-*+]\s", stripped))
        em_count = len(em_dash_re.findall(line))
        nospace_count = len(nospace_em_dash_re.findall(line))
        # On bullet lines, the leading "- " is the list marker; only count
        # ` - ` matches that occur after the bullet.
        if is_bullet_line:
            body = stripped[2:]  # strip "- " or "* " etc.
            hyphen_count = len(spaced_hyphen_re.findall(body))
        else:
            hyphen_count = len(spaced_hyphen_re.findall(line))

        # No-space em dashes get their own medium-severity finding.
        if nospace_count:
            findings.append(
                {
                    "severity": "medium",
                    "line": i,
                    "match": f"{nospace_count}× no-space em dash" if nospace_count > 1 else "no-space em dash",
                    "pattern": "(no-space em dash)",
                    "suggestion": (
                        "Em dash with no surrounding spaces (word\u2014word) is "
                        "sneaky sentence punctuation. Replace with comma, colon, "
                        "period, or parens."
                    ),
                }
            )
            # Subtract so the low-severity catch below doesn't double-report.
            em_count -= nospace_count

        if em_count or hyphen_count:
            parts = []
            if em_count:
                parts.append(f"{em_count}× em dash" if em_count > 1 else "em dash")
            if hyphen_count:
                parts.append(
                    f"{hyphen_count}× ` - `" if hyphen_count > 1 else "` - `"
                )
            findings.append(
                {
                    "severity": "low",
                    "line": i,
                    "match": " + ".join(parts),
                    "pattern": "(em dash / spaced hyphen)",
                    "suggestion": (
                        "Review this line. Acceptable for `**label** - details` "
                        "patterns; replace with comma/colon/period/parens when "
                        "used as sentence punctuation."
                    ),
                }
            )

    return findings


# ── Core linter ─────────────────────────────────────────────────────────────────


def lint_text(
    text: str,
    patterns: dict[str, list[dict]],
    min_severity: str = "low",
) -> list[dict]:
    """Lint text and return a list of findings sorted by line number."""
    min_rank = SEVERITY_RANK.get(min_severity, 1)
    lines = text.splitlines()
    findings: list[dict] = []

    for severity, entries in patterns.items():
        if SEVERITY_RANK.get(severity, 0) < min_rank:
            continue
        for entry in entries:
            try:
                rx = re.compile(entry["pattern"], re.IGNORECASE)
            except re.error:
                continue
            for i, line in enumerate(lines):
                for m in rx.finditer(line):
                    findings.append(
                        {
                            "severity": severity,
                            "line": i + 1,
                            "match": m.group(),
                            "pattern": entry["pattern"],
                            "suggestion": entry.get("suggestion", ""),
                            "note": entry.get("note", ""),
                        }
                    )

    # Add structural checks
    findings.extend(
        f for f in _structural_checks(lines) if SEVERITY_RANK.get(f["severity"], 0) >= min_rank
    )

    findings.sort(key=lambda f: (f["line"], -SEVERITY_RANK.get(f["severity"], 0)))
    return findings


# ── Formatting ──────────────────────────────────────────────────────────────────

_SEV_ICON = {"high": "🔴", "medium": "🟡", "low": "🔵", "info": "⚪"}


def format_text(findings: list[dict], filename: str = "") -> str:
    if not findings:
        return f"✅ {filename or 'text'}: No slop detected."

    header = f"{'─' * 60}\n{filename or 'text'} — {len(findings)} finding(s)\n{'─' * 60}"
    lines: list[str] = [header]
    for f in findings:
        icon = _SEV_ICON.get(f["severity"], "⚪")
        line_info = f"L{f['line']}" if f["line"] else ""
        note = f"  (note: {f['note']})" if f.get("note") else ""
        lines.append(f"  {icon} [{f['severity'].upper()}] {line_info}: \"{f['match']}\"")
        lines.append(f"     → {f['suggestion']}{note}")
    return "\n".join(lines)


def format_json(findings: list[dict], filename: str = "") -> str:
    return json.dumps({"file": filename, "findings": findings}, indent=2)


# ── Summary ─────────────────────────────────────────────────────────────────────


def summary_counts(all_findings: list[dict]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
    for f in all_findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    return counts


# ── CLI ─────────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint text for AI slop patterns.")
    parser.add_argument("files", nargs="*", help="Files to lint")
    parser.add_argument("--text", help="Inline text to lint")
    parser.add_argument(
        "--severity",
        choices=["info", "low", "medium", "high"],
        default="low",
        help="Minimum severity to report (default: low)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--patterns",
        help="Path to slop-words.yaml (default: auto-detected)",
    )
    args = parser.parse_args()

    if not args.files and not args.text:
        parser.error("Provide files or --text")

    # Locate patterns file
    if args.patterns:
        patterns_path = Path(args.patterns)
    else:
        patterns_path = Path(__file__).parent.parent / "references" / "slop-words.yaml"

    if not patterns_path.exists():
        print(f"Error: patterns file not found: {patterns_path}", file=sys.stderr)
        return 1

    patterns = load_patterns(patterns_path)
    all_findings: list[dict] = []
    outputs: list[str] = []

    if args.text:
        findings = lint_text(args.text, patterns, args.severity)
        all_findings.extend(findings)
        fmt = format_json if args.format == "json" else format_text
        outputs.append(fmt(findings, "<inline>"))

    for filepath in args.files or []:
        p = Path(filepath)
        if not p.exists():
            print(f"Warning: {filepath} not found, skipping", file=sys.stderr)
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        findings = lint_text(text, patterns, args.severity)
        all_findings.extend(findings)
        fmt = format_json if args.format == "json" else format_text
        outputs.append(fmt(findings, str(p)))

    print("\n\n".join(outputs))

    # Print summary
    if args.format == "text" and all_findings:
        counts = summary_counts(all_findings)
        print(f"\n{'─' * 60}")
        parts = [
            f"🔴 {counts['high']} high",
            f"🟡 {counts['medium']} medium",
            f"🔵 {counts['low']} low",
        ]
        if counts["info"]:
            parts.append(f"⚪ {counts['info']} info")
        print(f"TOTAL: {len(all_findings)} findings ({', '.join(parts)})")

    return 1 if any(f["severity"] == "high" for f in all_findings) else 0


if __name__ == "__main__":
    sys.exit(main())
