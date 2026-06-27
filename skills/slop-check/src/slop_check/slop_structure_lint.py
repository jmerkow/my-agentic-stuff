"""Structure linter for formulaic AI-writing shapes."""

import argparse
from collections import defaultdict
import json
import re
import sys
from pathlib import Path

import yaml

from slop_check.common import DEFAULT_FIX_TYPES_PATH, REFERENCES_DIR, YamlValue, load_fix_types, validate_level

# ── YAML loading ────────────────────────────────────────────────────────────────


def load_rules(path: Path, fix_types_path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    rules = yaml.safe_load(text)
    fix_types = load_fix_types(fix_types_path)
    validate_rules(rules, path, fix_types)
    return rules


def validate_rules(rules: YamlValue, path: Path, fix_types: dict[str, dict]) -> None:
    """Validate structure rule metadata loaded from YAML."""
    if not isinstance(rules, list):
        raise ValueError(f"Expected a list of rules in {path}")
    for index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            raise ValueError(f"Rule #{index} in {path} must be a mapping")
        check_name = rule.get("check")
        if not isinstance(check_name, str) or not check_name:
            rule_name = rule.get("rule", f"#{index}")
            raise ValueError(f"Rule {rule_name!r} in {path} is missing required check")
        if check_name not in ALGORITHM_REGISTRY:
            rule_name = rule.get("rule", f"#{index}")
            valid_checks = ", ".join(sorted(ALGORITHM_REGISTRY))
            raise ValueError(
                f"Rule {rule_name!r} in {path} has unknown check {check_name!r}; "
                f"expected one of: {valid_checks}"
            )
        level = rule.get("level")
        rule_name = rule.get("rule", f"#{index}")
        validate_level(level, str(rule_name), path)
        fix_type = rule.get("fix_type")
        if fix_type not in fix_types:
            valid_values = ", ".join(sorted(fix_types))
            raise ValueError(
                f"Rule {rule_name!r} in {path} has missing or invalid fix_type "
                f"{fix_type!r}; expected one of: {valid_values}"
            )


# ── Text model ─────────────────────────────────────────────────────────────────


def split_paragraphs(text: str) -> list[dict]:
    """Split text into paragraphs with 1-based start lines."""
    paragraphs: list[dict] = []
    current_lines: list[str] = []
    start_line = 1

    for line_no, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            if not current_lines:
                start_line = line_no
            current_lines.append(line)
        elif current_lines:
            paragraphs.append({"text": "\n".join(current_lines), "line": start_line})
            current_lines = []

    if current_lines:
        paragraphs.append({"text": "\n".join(current_lines), "line": start_line})

    return paragraphs


def split_sentences(paragraph: str) -> list[str]:
    """Split a paragraph into rough sentences."""
    normalized = re.sub(r"\s+", " ", paragraph.strip())
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'’]+\b", text))


def sentence_start(sentence: str) -> str:
    return re.sub(r"^[^\w'’]+", "", sentence).strip().lower()


def first_words(sentence: str, count: int) -> str:
    words = re.findall(r"\b[\w'’]+\b", sentence.lower())
    return " ".join(words[:count])


def is_list_paragraph(paragraph: str, list_pattern: re.Pattern[str]) -> bool:
    lines = [line for line in paragraph.splitlines() if line.strip()]
    return bool(lines) and all(list_pattern.search(line) for line in lines)


# ── Findings ───────────────────────────────────────────────────────────────────


def make_finding(rule: dict, line: int, match: str, pattern: str | None = None) -> dict:
    return {
        "rule": rule.get("rule", ""),
        "level": rule["level"],
        "fix_type": rule["fix_type"],
        "line": line,
        "match": match,
        "pattern": pattern or "(structure)",
        "suggestion": rule.get("suggestion", ""),
        "note": rule.get("note", ""),
    }


# ── Rule checks ────────────────────────────────────────────────────────────────


def check_listicle_instinct(text: str, rule: dict) -> list[dict]:
    findings: list[dict] = []
    thresholds = rule.get("thresholds", {})
    item_counts = set(thresholds.get("item_counts", []))
    patterns = rule.get("patterns", {})
    bullet_pattern = patterns.get("bullet", r"^\s*[-*+]\s+")
    numbered_pattern = patterns.get("numbered", r"^\s*\d+[.)]\s+")
    item_re = re.compile(
        f"(?:{bullet_pattern})|(?:{numbered_pattern})",
        re.IGNORECASE,
    )

    run_count = 0
    run_start = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        if item_re.search(line):
            if run_count == 0:
                run_start = line_no
            run_count += 1
            continue
        if run_count in item_counts:
            findings.append(make_finding(rule, run_start, f"{run_count} item list", item_re.pattern))
        run_count = 0
    if run_count in item_counts:
        findings.append(make_finding(rule, run_start, f"{run_count} item list", item_re.pattern))

    return findings


def check_bold_first_bullets(text: str, rule: dict) -> list[dict]:
    pattern = rule.get("patterns", {}).get("bullet", r"^\s*[-*+]\s+\*\*[^*]+\*\*[:：]?")
    bullet_re = re.compile(pattern, re.IGNORECASE)
    findings = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = bullet_re.search(line)
        if match:
            findings.append(make_finding(rule, line_no, match.group().strip(), pattern))
    return findings


def check_question_then_answer(paragraphs: list[dict], rule: dict) -> list[dict]:
    findings: list[dict] = []
    max_answer_words = rule.get("thresholds", {}).get("max_answer_words", 12)
    question_pattern = rule.get("patterns", {}).get("question", r"\?\s+")
    question_re = re.compile(question_pattern, re.IGNORECASE)

    for paragraph in paragraphs:
        if not question_re.search(paragraph["text"]):
            continue
        sentences = split_sentences(paragraph["text"])
        for index, sentence in enumerate(sentences[:-1]):
            if sentence.endswith("?") and word_count(sentences[index + 1]) <= max_answer_words:
                match = f"{sentence} {sentences[index + 1]}"
                findings.append(make_finding(rule, paragraph["line"], match, question_pattern))
    return findings


def check_negation_countdown(paragraphs: list[dict], rule: dict) -> list[dict]:
    findings: list[dict] = []
    thresholds = rule.get("thresholds", {})
    min_run = thresholds.get("min_run", 2)
    max_sentence_words = thresholds.get("max_sentence_words", 8)
    pattern = rule.get("patterns", {}).get("sentence_start", r"^not\b")
    start_re = re.compile(pattern, re.IGNORECASE)

    for paragraph in paragraphs:
        sentences = split_sentences(paragraph["text"])
        run: list[str] = []
        for sentence in sentences + [""]:
            if start_re.search(sentence_start(sentence)) and word_count(sentence) <= max_sentence_words:
                run.append(sentence)
                continue
            if len(run) >= min_run:
                findings.append(make_finding(rule, paragraph["line"], " ".join(run), pattern))
            run = []
    return findings


def check_staccato_burst(paragraphs: list[dict], rule: dict) -> list[dict]:
    findings: list[dict] = []
    thresholds = rule.get("thresholds", {})
    min_run = thresholds.get("min_run", 3)
    max_sentence_words = thresholds.get("max_sentence_words", 7)
    list_pattern = rule.get("patterns", {}).get("list_line", r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
    list_re = re.compile(list_pattern, re.IGNORECASE)

    for paragraph in paragraphs:
        if is_list_paragraph(paragraph["text"], list_re):
            continue
        sentences = split_sentences(paragraph["text"])
        run: list[str] = []
        for sentence in sentences + [""]:
            if sentence and word_count(sentence) <= max_sentence_words:
                run.append(sentence)
                continue
            if len(run) >= min_run:
                findings.append(make_finding(rule, paragraph["line"], " ".join(run)))
            run = []
    return findings


def check_anaphora_abuse(paragraphs: list[dict], rule: dict) -> list[dict]:
    findings: list[dict] = []
    thresholds = rule.get("thresholds", {})
    min_run = thresholds.get("min_run", 3)
    opener_words = thresholds.get("opener_words", 1)

    for paragraph in paragraphs:
        sentences = split_sentences(paragraph["text"])
        previous_opener = ""
        run: list[str] = []
        for sentence in sentences + [""]:
            opener = first_words(sentence, opener_words) if sentence else ""
            if opener and opener == previous_opener:
                run.append(sentence)
                continue
            if len(run) >= min_run:
                findings.append(make_finding(rule, paragraph["line"], " ".join(run)))
            run = [sentence] if opener else []
            previous_opener = opener
    return findings


def check_gerund_litany(paragraphs: list[dict], rule: dict) -> list[dict]:
    findings: list[dict] = []
    thresholds = rule.get("thresholds", {})
    min_run = thresholds.get("min_run", 2)
    max_sentence_words = thresholds.get("max_sentence_words", 7)
    pattern = rule.get("patterns", {}).get("sentence_start", r"^[a-z]+ing\b")
    start_re = re.compile(pattern, re.IGNORECASE)

    for paragraph in paragraphs:
        sentences = split_sentences(paragraph["text"])
        run: list[str] = []
        for sentence in sentences + [""]:
            if start_re.search(sentence_start(sentence)) and word_count(sentence) <= max_sentence_words:
                run.append(sentence)
                continue
            if len(run) >= min_run:
                findings.append(make_finding(rule, paragraph["line"], " ".join(run), pattern))
            run = []
    return findings


def check_short_hook_paragraph(paragraphs: list[dict], rule: dict) -> list[dict]:
    findings: list[dict] = []
    thresholds = rule.get("thresholds", {})
    max_hook_words = thresholds.get("max_hook_words", 5)
    min_following_sentences = thresholds.get("min_following_sentences", 2)
    min_following_avg_words = thresholds.get("min_following_avg_words", 12)

    for paragraph in paragraphs:
        sentences = split_sentences(paragraph["text"])
        if len(sentences) < min_following_sentences + 1:
            continue
        following_counts = [word_count(sentence) for sentence in sentences[1:]]
        following_avg = sum(following_counts) / len(following_counts)
        if word_count(sentences[0]) <= max_hook_words and following_avg >= min_following_avg_words:
            findings.append(make_finding(rule, paragraph["line"], sentences[0]))
    return findings


def check_dramatic_fragment(paragraphs: list[dict], rule: dict) -> list[dict]:
    findings: list[dict] = []
    thresholds = rule.get("thresholds", {})
    min_words = thresholds.get("min_words", 1)
    max_words = thresholds.get("max_words", 4)
    patterns = rule.get("patterns", {})
    heading_re = re.compile(patterns.get("heading", r"^\s{0,3}#{1,6}\s+"), re.IGNORECASE)
    title_re = re.compile(patterns.get("title_like", r"^[A-Z].*$"))
    list_re = re.compile(patterns.get("list_line", r"^\s*(?:[-*+]\s+|\d+[.)]\s+)"), re.IGNORECASE)

    for paragraph in paragraphs:
        paragraph_text = paragraph["text"].strip()
        if "\n" in paragraph_text or heading_re.search(paragraph_text) or list_re.search(paragraph_text):
            continue
        if title_re.search(paragraph_text) and not re.search(r"[.!?]$", paragraph_text):
            continue
        words = word_count(paragraph_text)
        if min_words <= words <= max_words:
            findings.append(make_finding(rule, paragraph["line"], paragraph_text))
    return findings


ALGORITHM_REGISTRY = {
    "list_run": lambda text, paragraphs, rule: check_listicle_instinct(text, rule),
    "bold_first_bullets": lambda text, paragraphs, rule: check_bold_first_bullets(text, rule),
    "question_then_answer": lambda text, paragraphs, rule: check_question_then_answer(paragraphs, rule),
    "negation_countdown": lambda text, paragraphs, rule: check_negation_countdown(paragraphs, rule),
    "staccato_burst": lambda text, paragraphs, rule: check_staccato_burst(paragraphs, rule),
    "anaphora_abuse": lambda text, paragraphs, rule: check_anaphora_abuse(paragraphs, rule),
    "gerund_litany": lambda text, paragraphs, rule: check_gerund_litany(paragraphs, rule),
    "short_hook_paragraph": lambda text, paragraphs, rule: check_short_hook_paragraph(paragraphs, rule),
    "dramatic_fragment": lambda text, paragraphs, rule: check_dramatic_fragment(paragraphs, rule),
}


# ── Core linter ─────────────────────────────────────────────────────────────────


def lint_text(text: str, rules: list[dict]) -> list[dict]:
    """Lint text structure and return findings sorted by line number."""
    paragraphs = split_paragraphs(text)
    findings: list[dict] = []

    for rule in rules:
        check = ALGORITHM_REGISTRY[rule["check"]]
        findings.extend(check(text, paragraphs, rule))

    findings.sort(key=lambda f: (f["line"], -f["level"], f["rule"]))
    return findings


# ── Formatting ──────────────────────────────────────────────────────────────────


def format_text(findings: list[dict], filename: str | None = None) -> str:
    if not findings:
        return f"✅ {filename or 'text'}: No structural slop detected."

    header = f"{'─' * 60}\n{filename or 'text'} — {len(findings)} finding(s)\n{'─' * 60}"
    lines: list[str] = [header]

    groups: dict[str, list[dict]] = defaultdict(list)
    for finding in findings:
        groups[finding.get("rule", "")].append(finding)

    def group_sort_key(rule_name: str) -> tuple:
        max_level = max(finding["level"] for finding in groups[rule_name])
        return (-max_level, rule_name)

    for rule_name in sorted(groups.keys(), key=group_sort_key):
        rule_findings = groups[rule_name]
        level = rule_findings[0]["level"]
        lines.append(f"\n[{rule_name}] level {level}")
        for finding in rule_findings:
            note = f"\n       (note: {finding['note']})" if finding.get("note") else ""
            fix_type = f"\n       fix: {finding['fix_type']}" if finding.get("fix_type") else ""
            lines.append(f"  L{finding['line']}: \"{finding['match']}\"")
            lines.append(f"       → {finding['suggestion']}{fix_type}{note}")
    return "\n".join(lines)


def format_json(findings: list[dict], filename: str | None = None) -> str:
    return json.dumps({"file": filename, "findings": findings}, indent=2)


# ── Summary ─────────────────────────────────────────────────────────────────────


def summary_counts(all_findings: list[dict]) -> dict[int, int]:
    counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for finding in all_findings:
        counts[finding["level"]] = counts.get(finding["level"], 0) + 1
    return counts


# ── CLI ─────────────────────────────────────────────────────────────────────────


def main() -> int:
    default_rules_path = REFERENCES_DIR / "slop-structure.yaml"

    parser = argparse.ArgumentParser(description="Lint text for formulaic AI-writing structures.")
    parser.add_argument("files", nargs="*", help="Files to lint")
    parser.add_argument("--text", help="Inline text to lint")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=default_rules_path,
        help="Path to slop-structure.yaml (default: %(default)s)",
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

    rules_path = args.rules
    fix_types_path = args.fix_types

    if not rules_path.exists():
        print(f"Error: rules file not found: {rules_path}", file=sys.stderr)
        return 1
    if not fix_types_path.exists():
        print(f"Error: fix types file not found: {fix_types_path}", file=sys.stderr)
        return 1

    try:
        rules = load_rules(rules_path, fix_types_path)
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 1
    all_findings: list[dict] = []
    outputs: list[str] = []

    if args.text:
        findings = lint_text(args.text, rules)
        all_findings.extend(findings)
        formatter = format_json if args.format == "json" else format_text
        outputs.append(formatter(findings, "<inline>"))

    for filepath in args.files:
        path = Path(filepath)
        if not path.exists():
            print(f"Warning: {filepath} not found, skipping", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        findings = lint_text(text, rules)
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
