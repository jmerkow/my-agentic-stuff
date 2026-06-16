#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///

"""Parse slide-spec.md into a deck.yaml manifest.

The spec is markdown with one ## Slide N — <title> header per slide. This script:

1. Parses all slide metadata in one pass (load_spec).
2. Runs lint checks on the parsed data (lint) — no duplicate parsing.
3. On clean lint, writes deck.yaml with per-slide objects and optional inline notes.
4. With --lint-only, only runs lint and exits (no writes).

Finding format: E3 (Slide 3 — Title): <message>
Errors block writes and exit 1. Warnings print to stderr, don't block.

Usage:
    python parse-spec.py [--lint-only] [deck-dir]

`deck-dir` defaults to cwd. Must contain slide-spec.md.
"""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

import yaml


# ─── Regexes ─────────────────────────────────────────────────────────────────

SLIDE_HEADER_RE = re.compile(r"^## Slide\s+(\S+?)\s*[—\-]\s*(.+?)\s*$", re.MULTILINE)
FILE_FIELD_RE = re.compile(r"^- \*\*File:\*\*\s*`?([^`\s]+\.svg)`?", re.MULTILINE)
# Top-level field keys only (0-indent lines): "- **FieldName:**"
FIELD_RE = re.compile(r"^- \*\*([^*]+?):\*\*", re.MULTILINE)

# ─── Constants ────────────────────────────────────────────────────────────────

KNOWN_FIELDS = {
    "Layout",
    "Headline",
    "Subtitle",
    "Headline / subtitle",
    "Footer",
    "Content blocks",
    "Visuals",
    "Artifact sources",
    "Talking points",
    "Speaker notes",
    "Status",
    "File",
    "Reference",
}

STATUS_VALUES = {"✅", "⚠️", "❌"}


# ─── Data model ──────────────────────────────────────────────────────────────

@dataclass
class SlideInfo:
    slide_id: str
    title: str
    body: str
    explicit_file: str | None = None    # from "- **File:**" field
    resolved_file: str | None = None    # resolved SVG filename (may be None)
    talking_points: str = ""            # extracted talking points, stripped
    speaker_notes: str = ""             # extracted speaker notes, stripped
    fields: list[str] = field(default_factory=list)   # all top-level field keys
    status: str | None = None           # value after "Status:"
    visuals: list[str] = field(default_factory=list)  # paths from "Visuals:"


# ─── Parsing primitives ──────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert a title to a lowercase hyphen-slug for filename matching."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text


def resolve_filename(deck_dir: Path, slide_id: str, title: str, body: str,
                     fallback_index: int) -> str | None:
    """Pick the SVG filename for a slide. Returns None if no match found."""
    # 1. Explicit File field.
    m = FILE_FIELD_RE.search(body)
    if m:
        return m.group(1)

    # 2. Slugified title with zero-padded ID prefix.
    slug = slugify(title)
    id_part = slide_id
    if id_part.isdigit():
        id_part = id_part.zfill(2)
    elif re.match(r"^\d+[a-z]$", id_part):
        n, suf = re.match(r"^(\d+)([a-z])$", id_part).groups()
        id_part = f"{int(n):02d}{suf}"
    candidate = f"slide-{id_part}-{slug}.svg"
    if (deck_dir / candidate).exists():
        return candidate

    # 3. Glob: slide-<id>-*.svg with any suffix.
    matches = sorted(deck_dir.glob(f"slide-{id_part}-*.svg"))
    if matches:
        return matches[0].name

    # 4. Fall back to sorted index position.
    all_slides = sorted(deck_dir.glob("slide-*.svg"))
    if fallback_index < len(all_slides):
        return all_slides[fallback_index].name

    return None


def extract_block(body: str, header_name: str) -> str:
    """Return the stripped body for a top-level markdown field block."""
    pattern = re.compile(
        rf"^- \*\*{re.escape(header_name)}:\*\*\s*$(.*?)(?=^- \*\*|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if not match:
        return ""
    return textwrap.dedent(match.group(1)).strip()


def extract_status(body: str) -> str | None:
    m = re.search(r"^- \*\*Status:\*\*\s*(.+)$", body, re.MULTILINE)
    return m.group(1).strip() if m else None


def extract_visuals(body: str) -> list[str]:
    """Parse `- **Visuals:** ...` and return a list of asset paths."""
    m = re.search(r"^- \*\*Visuals:\*\*\s*(.+)$", body, re.MULTILINE)
    if not m:
        return []
    text = m.group(1).strip()
    # Prefer backtick-quoted paths.
    paths = re.findall(r"`([^`]+\.[a-zA-Z]{2,4})`", text)
    if paths:
        return paths
    # Fallback: first token that looks like a path.
    first = text.split()[0].strip("`'\"")
    if "." in first:
        return [first]
    return []


def parse_asset_checklist(spec_text: str) -> list[tuple[str, str]]:
    """Loosely parse the Asset checklist table. Returns [(asset_name, slide_id), ...]."""
    result = []
    m = re.search(r"## Asset checklist(.+?)(?=^##|\Z)", spec_text, re.MULTILINE | re.DOTALL)
    if not m:
        return result
    for row in m.group(1).splitlines():
        row = row.strip()
        if not row.startswith("|") or "---" in row or row.startswith("| Asset"):
            continue
        cols = [c.strip().strip("`") for c in row.split("|") if c.strip()]
        if len(cols) >= 2:
            asset, slide_ref = cols[0].strip(), cols[1].strip()
            if asset and slide_ref:
                result.append((asset, slide_ref))
    return result


# ─── load_spec ───────────────────────────────────────────────────────────────

def load_spec(deck_dir: Path) -> tuple[list[SlideInfo], str]:
    """Parse slide-spec.md once. Returns (slides, raw_spec_text).

    All per-slide data (file resolution, notes extraction, field extraction,
    status, visuals) is gathered here. lint() and to_manifest() consume the
    result — no re-parsing.
    """
    spec_path = deck_dir / "slide-spec.md"
    if not spec_path.exists():
        raise FileNotFoundError(f"No slide-spec.md at {spec_path}")
    spec_text = spec_path.read_text()

    header_matches = list(SLIDE_HEADER_RE.finditer(spec_text))
    slides: list[SlideInfo] = []
    for i, m in enumerate(header_matches):
        slide_id = m.group(1)
        title = m.group(2).strip()
        # Skip the Asset checklist pseudo-header (rare edge case).
        if slide_id.lower() in {"asset", "checklist"}:
            continue
        start = m.end()
        end = header_matches[i + 1].start() if i + 1 < len(header_matches) else len(spec_text)
        body = spec_text[start:end]

        explicit_file_m = FILE_FIELD_RE.search(body)
        explicit_file = explicit_file_m.group(1) if explicit_file_m else None
        resolved = resolve_filename(deck_dir, slide_id, title, body, len(slides))
        talking_points = extract_block(body, "Talking points")
        speaker_notes = extract_block(body, "Speaker notes")
        fields = FIELD_RE.findall(body)
        status = extract_status(body)
        visuals = extract_visuals(body)

        slides.append(SlideInfo(
            slide_id=slide_id,
            title=title,
            body=body,
            explicit_file=explicit_file,
            resolved_file=resolved,
            talking_points=talking_points,
            speaker_notes=speaker_notes,
            fields=fields,
            status=status,
            visuals=visuals,
        ))

    return slides, spec_text


# ─── lint ────────────────────────────────────────────────────────────────────

def _f(code: str, slide: SlideInfo | None, msg: str) -> str:
    """Format a finding with slide context if available."""
    if slide:
        return f"{code} (Slide {slide.slide_id} — {slide.title}): {msg}"
    return f"{code}: {msg}"


def lint(slides: list[SlideInfo], spec_text: str, deck_dir: Path) -> tuple[list[str], list[str]]:
    """Validate parsed spec data. Returns (errors, warnings).

    Errors: block writes, exit 1.
    Warnings: print to stderr, don't block.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # E1 — every ## Slide header line must parse (has dash separator + non-empty title).
    for line in spec_text.splitlines():
        if line.startswith("## Slide "):
            if not SLIDE_HEADER_RE.match(line):
                errors.append(
                    f"E1: Header does not parse (missing dash separator or empty title): {line!r}"
                )

    # E2 — slide IDs unique.
    seen_ids: dict[str, int] = {}
    for slide in slides:
        if slide.slide_id in seen_ids:
            errors.append(_f("E2", slide, f"duplicate ID '{slide.slide_id}' (first at position {seen_ids[slide.slide_id] + 1})"))
        else:
            seen_ids[slide.slide_id] = slides.index(slide)

    # E3 — every slide resolves to an SVG.
    for slide in slides:
        if slide.resolved_file is None:
            errors.append(_f("E3", slide, "no matching SVG file found in deck dir"))

    # E4 — if explicit File field present, the SVG must exist.
    for slide in slides:
        if slide.explicit_file and not (deck_dir / slide.explicit_file).exists():
            errors.append(_f("E4", slide, f"explicit File field '{slide.explicit_file}' does not exist"))

    # E6 — Status field required.
    for slide in slides:
        if not slide.status:
            errors.append(_f("E6", slide, "missing required '- **Status:**' field"))

    # W1 — sequential IDs (gaps flagged).
    numeric_ids = []
    for slide in slides:
        m = re.match(r"^(\d+)[a-z]?$", slide.slide_id)
        if m:
            numeric_ids.append((int(m.group(1)), slide.slide_id))
    if numeric_ids:
        expected = 1
        for num, sid in sorted(numeric_ids):
            if num > expected:
                warnings.append(f"W1: Slide ID gap — expected {expected}, got {sid}")
                expected = num + 1
            elif num == expected:
                expected += 1

    # W2 — unknown field keys.
    for slide in slides:
        for f_key in slide.fields:
            f_norm = f_key.strip()
            if f_norm not in KNOWN_FIELDS:
                warnings.append(_f("W2", slide, f"unknown field '**{f_norm}:**' (not in documented schema)"))

    # W3 — Status value not one of ✅ / ⚠️ / ❌.
    for slide in slides:
        if slide.status and slide.status not in STATUS_VALUES:
            warnings.append(_f("W3", slide, f"Status value {slide.status!r} is not one of ✅/⚠️/❌"))

    # W4 / W5 — asset checklist cross-checks (tolerate missing/empty checklist).
    try:
        checklist = parse_asset_checklist(spec_text)
    except Exception:
        checklist = []

    checklist_assets = {Path(a).name for a, _ in checklist}
    slide_ids_set = {s.slide_id for s in slides}

    # W4 — visual referenced in spec but absent from checklist.
    for slide in slides:
        for visual in slide.visuals:
            vname = Path(visual).name
            if vname not in checklist_assets:
                warnings.append(_f("W4", slide, f"visual '{visual}' is not in the Asset checklist table"))

    # W5 — checklist row references a slide ID that doesn't exist.
    for asset, slide_ref in checklist:
        if slide_ref and slide_ref not in slide_ids_set:
            warnings.append(f"W5: Asset checklist row '{asset}' references slide ID '{slide_ref}' which doesn't exist")

    # W6: empty Talking points block (stub the author forgot to fill).
    for slide in slides:
        if "Talking points" in slide.fields and not slide.talking_points:
            warnings.append(_f("W6", slide, "Talking points header present but block is empty (forgotten stub?)"))

    # W7: empty Speaker notes block (stub the author forgot to fill).
    for slide in slides:
        if "Speaker notes" in slide.fields and not slide.speaker_notes:
            warnings.append(_f("W7", slide, "Speaker notes header present but block is empty (forgotten stub?)"))

    return errors, warnings


# ─── to_manifest / write_manifest ────────────────────────────────────────────

class _LiteralDumper(yaml.Dumper):
    """YAML dumper that uses | block scalars for multiline strings."""


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_LiteralDumper.add_representer(str, _str_representer)


def to_manifest(slides: list[SlideInfo], existing: dict | None = None) -> dict:
    """Build the deck.yaml dict from parsed slide data.

    Preserves `output` and `template` from an existing deck.yaml if present.
    """
    manifest: dict = {}
    if existing:
        for key in ("output", "template"):
            if key in existing:
                manifest[key] = existing[key]

    slide_objects = []
    for slide in slides:
        if slide.resolved_file is None:
            continue
        obj: dict = {"file": slide.resolved_file}
        if slide.speaker_notes.strip():
            obj["notes"] = slide.speaker_notes + "\n"
        slide_objects.append(obj)
    manifest["slides"] = slide_objects
    return manifest


def write_manifest(manifest: dict, deck_dir: Path) -> Path:
    """Serialize manifest to deck.yaml using literal block scalars for notes."""
    manifest_path = deck_dir / "deck.yaml"
    with manifest_path.open("w", encoding="utf-8") as f:
        yaml.dump(manifest, f, Dumper=_LiteralDumper, default_flow_style=False,
                  allow_unicode=True, sort_keys=False)
    return manifest_path


# ─── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lint slide-spec.md and write deck.yaml with inline speaker notes.",
    )
    parser.add_argument(
        "deck_dir",
        nargs="?",
        default=".",
        help="Path to the deck directory containing slide-spec.md (default: cwd)",
    )
    parser.add_argument(
        "--lint-only",
        action="store_true",
        help="Run lint checks only — do not write deck.yaml. Exits 0 if clean, 1 if errors.",
    )
    args = parser.parse_args()

    deck_dir = Path(args.deck_dir).resolve()
    if not deck_dir.is_dir():
        raise SystemExit(f"Not a directory: {deck_dir}")

    slides, spec_text = load_spec(deck_dir)
    if not slides:
        raise SystemExit(f"No '## Slide N — <title>' headers found in {deck_dir / 'slide-spec.md'}")

    errors, warnings = lint(slides, spec_text, deck_dir)
    for w in warnings:
        print(w, file=sys.stderr)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)

    if args.lint_only:
        sys.exit(0)

    # Load existing deck.yaml to preserve output/template if present.
    existing_path = deck_dir / "deck.yaml"
    existing: dict | None = None
    if existing_path.exists():
        with existing_path.open(encoding="utf-8") as f:
            existing = yaml.safe_load(f)

    manifest = to_manifest(slides, existing)
    manifest_path = write_manifest(manifest, deck_dir)
    print(f"Wrote {manifest_path} ({len(manifest['slides'])} slides)")


if __name__ == "__main__":
    main()
