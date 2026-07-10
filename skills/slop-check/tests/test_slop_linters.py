import json
from pathlib import Path
import subprocess
import sys

import pytest

from slop_check import slop_lint, slop_structure_lint
from slop_check.common import format_findings_text, load_fix_types


SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCES_DIR = SKILL_ROOT / "references"
WORDS_PATH = REFERENCES_DIR / "slop-words.yaml"
STRUCTURE_PATH = REFERENCES_DIR / "slop-structure.yaml"
FIX_TYPES_PATH = REFERENCES_DIR / "slop-fix-types.yaml"


def rule_names(findings: list[dict]) -> set[str]:
    return {finding["rule"] for finding in findings}


@pytest.fixture(scope="module")
def phrase_linter():
    return slop_lint, slop_lint.load_patterns(WORDS_PATH, FIX_TYPES_PATH)


@pytest.fixture(scope="module")
def structure_linter():
    return slop_structure_lint, slop_structure_lint.load_rules(STRUCTURE_PATH, FIX_TYPES_PATH)


def finding_for_rule(findings: list[dict], rule_name: str) -> dict:
    return next(finding for finding in findings if finding["rule"] == rule_name)


def test_word_rules_load_with_valid_schema(phrase_linter):
    module, patterns = phrase_linter
    fix_types = load_fix_types(FIX_TYPES_PATH)

    assert patterns
    for pattern in patterns:
        assert isinstance(pattern["level"], int)
        assert 0 <= pattern["level"] <= 3
        assert pattern["fix_type"] in fix_types


def test_structure_rules_load_with_known_check_selectors(structure_linter):
    module, rules = structure_linter

    assert rules
    for rule in rules:
        assert rule["check"] in module.ALGORITHM_REGISTRY


@pytest.mark.parametrize(
    ("yaml_text", "error_text"),
    [
        ("- rule: bad-rule\n  level: 1\n  pattern: bad\n", "fix_type"),
        ("- rule: bad-rule\n  level: 1\n  fix_type: invent\n  pattern: bad\n", "invalid fix_type"),
    ],
)
def test_phrase_rule_invalid_or_missing_fix_type_raises_clear_error(phrase_linter, tmp_path, yaml_text, error_text):
    module, _patterns = phrase_linter
    patterns_path = tmp_path / "slop-words.yaml"
    patterns_path.write_text(yaml_text, encoding="utf-8")

    with pytest.raises(ValueError, match=error_text):
        module.load_patterns(patterns_path, FIX_TYPES_PATH)


def test_structure_rule_invalid_fix_type_raises_clear_error(structure_linter, tmp_path):
    module, _rules = structure_linter
    rules_path = tmp_path / "slop-structure.yaml"
    rules_path.write_text(
        "- rule: bad-rule\n  check: list_run\n  level: 1\n  fix_type: invent\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid fix_type"):
        module.load_rules(rules_path, FIX_TYPES_PATH)


@pytest.mark.parametrize(
    ("text", "rule_name", "expected_level", "expected_fix_type"),
    [
        ("It's important to note that speed matters.", "filler-hedge", 3, "delete"),
        ("Experts agree this is ready.", "fake-authority", 3, "substantiate"),
        ("This is a robust design.", "vague-descriptor", 2, "rewrite"),
        ("We deliver a world-class platform.", "empty-superlative", 2, "substantiate"),
        ("This will empower teams.", "hype-verb", 2, "rewrite"),
        ("We leverage the toolchain.", "corporate-buzzword", 2, "replace"),
        ("In an era of constant churn, teams need clarity.", "era-opener", 3, "delete"),
    ],
)
def test_phrase_linter_positive_cases(phrase_linter, text, rule_name, expected_level, expected_fix_type):
    module, patterns = phrase_linter
    finding = finding_for_rule(module.lint_text(text, patterns), rule_name)

    assert finding["level"] == expected_level
    assert finding["fix_type"] == expected_fix_type


def test_em_dash_bold_lead_in_label_is_exempt(phrase_linter):
    module, patterns = phrase_linter

    findings = module.lint_text("**Decision** — keep this", patterns)

    assert "em-dash-prose" not in rule_names(findings)


@pytest.mark.parametrize(
    ("text", "rule_name"),
    [
        ("What does this mean? It means speed matters.", "question-then-answer"),
        ("- **One**: keep scope tight.", "bold-first-bullets"),
        ("- one\n- two\n- three", "listicle-instinct"),
        ("Not speed. Not scale.", "negation-countdown"),
    ],
)
def test_structure_linter_positive_cases(structure_linter, text, rule_name):
    module, rules = structure_linter

    findings = module.lint_text(text, rules)

    assert rule_name in rule_names(findings)


def test_staccato_burst_ignores_pure_bullet_list_paragraph(structure_linter):
    module, rules = structure_linter

    findings = module.lint_text("- fast\n- safe\n- clear", rules)

    assert "staccato-burst" not in rule_names(findings)


@pytest.mark.parametrize(
    ("module_name", "text", "expected_rule", "expected_exit_code"),
    [
        ("slop_check.slop_lint", "This is a robust design.", "vague-descriptor", 0),
        ("slop_check.slop_structure_lint", "What does this mean? It means speed matters.", "question-then-answer", 0),
    ],
)
def test_cli_json_text_smoke(module_name, text, expected_rule, expected_exit_code):
    completed_process = subprocess.run(
        [sys.executable, "-m", module_name, "--format", "json", "--text", text],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed_process.returncode == expected_exit_code
    payload = json.loads(completed_process.stdout)
    assert payload["file"] == "<inline>"
    assert expected_rule in rule_names(payload["findings"])

def test_format_findings_text_empty_uses_custom_message():
    output = format_findings_text([], "notes.md", empty_message="Nothing here.")

    assert output == "✅ notes.md: Nothing here."


def test_format_findings_text_groups_by_level_then_rule():
    findings = [
        {"rule": "beta", "level": 2, "fix_type": "rewrite", "line": 5, "match": "b", "suggestion": "fix b", "note": ""},
        {"rule": "alpha", "level": 3, "fix_type": "delete", "line": 2, "match": "a", "suggestion": "fix a", "note": ""},
    ]

    output = format_findings_text(findings, "doc.md")

    assert "doc.md — 2 finding(s)" in output
    assert output.index("level 3 high") < output.index("level 2 medium")
    assert output.index("[alpha]") < output.index("[beta]")
    assert 'L2 "a"' in output
    assert "fix a (delete)" in output


def test_format_findings_text_collapses_shared_suggestion_into_one_block():
    findings = [
        {"rule": "em-dash-prose", "level": 0, "fix_type": "rewrite", "line": 3, "match": "—", "suggestion": "rephrase", "note": ""},
        {"rule": "em-dash-prose", "level": 0, "fix_type": "rewrite", "line": 9, "match": "—", "suggestion": "rephrase", "note": ""},
    ]

    output = format_findings_text(findings, "doc.md")

    assert output.count("→ rephrase (rewrite)") == 1
    assert 'L3 "—" · L9 "—"' in output


def test_format_findings_text_truncates_long_match():
    long_match = "word " * 40
    findings = [
        {"rule": "staccato-burst", "level": 1, "fix_type": "rewrite", "line": 1, "match": long_match, "suggestion": "s", "note": ""},
    ]

    output = format_findings_text(findings, "doc.md")

    assert "…" in output
