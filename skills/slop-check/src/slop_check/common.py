from pathlib import Path

import yaml


SKILL_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_DIR = SKILL_ROOT / "references"
DEFAULT_FIX_TYPES_PATH = REFERENCES_DIR / "slop-fix-types.yaml"
YamlValue = dict[str, "YamlValue"] | list["YamlValue"] | str | int | float | bool | None


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
