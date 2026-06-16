#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///

"""Build a self-contained PowerPoint deck from the slide SVGs.

Strategy:
- Use the deck's template `.pptx` as a scaffold (provides slide master, theme,
  layouts, content types). The path is specified in `deck.yaml`.
- For each slide SVG listed in `deck.yaml` (or auto-discovered if not listed),
  inline any external <image href="..."> references as base64 data URIs so the
  SVG is fully self-contained.
- Drop one inlined SVG per slide into ppt/media/imageN.svg.
- Generate one ppt/slides/slideN.xml referencing that media file via rId2.
- Patch presentation.xml, presentation.xml.rels, and [Content_Types].xml.

The resulting .pptx contains pure vector SVG slides at 16:9 (12192000 x 6858000 EMU).

Usage:
    python build-pptx.py [deck-dir]

`deck-dir` defaults to the current working directory. `deck.yaml` is optional;
when present it pins slide order, template, and output path.
"""

from __future__ import annotations

import argparse
import base64
import re
import zipfile
from pathlib import Path

import yaml

SLIDE_PATTERN = "slide-*.svg"

# Default template ships with the skill at <skill>/templates/blank.pptx.
DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "blank.pptx"


def load_manifest(deck_dir: Path) -> dict:
    """Load deck.yaml from deck_dir; auto-discover slides if not listed.

    All keys are optional:
    - `output`:   defaults to `<deck-dirname>.pptx` in the deck dir
    - `template`: defaults to the skill's `templates/blank.pptx`
    - `slides`:   list of dicts with at least {"file": "slide-NN-name.svg"};
                  defaults to sorted glob `slide-*.svg` converted to dicts
    """
    manifest_path = deck_dir / "deck.yaml"
    manifest: dict = {}
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8") as f:
            manifest = yaml.safe_load(f) or {}

    if "output" not in manifest:
        manifest["output"] = f"{deck_dir.name}.pptx"

    if "template" not in manifest:
        manifest["template"] = str(DEFAULT_TEMPLATE)

    if not manifest.get("slides"):
        discovered = sorted(p.name for p in deck_dir.glob(SLIDE_PATTERN))
        if not discovered:
            raise ValueError(
                f"No 'slides' listed in {manifest_path} (or no manifest) and no "
                f"{SLIDE_PATTERN} found in {deck_dir}"
            )
        manifest["slides"] = [{"file": name} for name in discovered]

    return manifest


def inline_svg_images(svg_path: Path) -> str:
    """Replace ./assets/... and assets/... <image href> targets with base64 data URIs.

    Also strips the <?xml-stylesheet?> PI (external CSS that PowerPoint can't resolve;
    the theme is already inlined in <style>).
    """
    svg = svg_path.read_text()
    base = svg_path.parent

    # Strip xml-stylesheet PI
    svg = re.sub(r'<\?xml-stylesheet[^?]*\?>\s*', '', svg)

    def replace(match: re.Match) -> str:
        attr = match.group(1)  # 'href' or 'xlink:href'
        target = match.group(2)
        if target.startswith("data:") or target.startswith("http"):
            return match.group(0)
        target_path = (base / target).resolve()
        if not target_path.exists():
            print(f"  WARN missing: {target} (resolved: {target_path})")
            return match.group(0)
        suffix = target_path.suffix.lower().lstrip(".")
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "svg": "image/svg+xml"}.get(suffix, "application/octet-stream")
        data = base64.b64encode(target_path.read_bytes()).decode("ascii")
        return f'{attr}="data:{mime};base64,{data}"'

    # Match href="..." or xlink:href="..." inside <image ...> tags
    pattern = re.compile(r'(href|xlink:href)="([^"]+\.(?:png|jpg|jpeg|svg))"', re.IGNORECASE)
    return pattern.sub(replace, svg)


def slide_xml(picture_id: int, slide_index: int) -> str:
    """One full-bleed SVG picture filling the slide (12192000 x 6858000 EMU = 16:9)."""
    _ = slide_index
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:pic>
<p:nvPicPr>
<p:cNvPr id="{picture_id}" name="Slide SVG"/>
<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
<p:nvPr/>
</p:nvPicPr>
<p:blipFill>
<a:blip><a:extLst><a:ext uri="{{96DAC541-7B7A-43D3-8B79-37D633B846F1}}"><asvg:svgBlip xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" r:embed="rId2"/></a:ext></a:extLst></a:blip>
<a:stretch><a:fillRect/></a:stretch>
</p:blipFill>
<p:spPr>
<a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="6858000"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
</p:spPr>
</p:pic>
</p:spTree></p:cSld>
<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''


def slide_rels(svg_media_name: str, notes_slide_index: int | None = None) -> str:
    extra = ""
    if notes_slide_index is not None:
        extra = (
            f'<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" '
            f'Target="../notesSlides/notesSlide{notes_slide_index}.xml"/>'
        )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout2.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{svg_media_name}"/>
{extra}</Relationships>'''


NOTES_MASTER_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:notesMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld>
<p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>
<p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:sp>
<p:nvSpPr><p:cNvPr id="2" name="Notes Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="685800" y="1825625"/><a:ext cx="5486400" cy="3600450"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
<p:txBody><a:bodyPr vert="horz" lIns="91440" tIns="45720" rIns="91440" bIns="45720" rtlCol="0"><a:normAutofit/></a:bodyPr><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>
</p:sp>
</p:spTree>
</p:cSld>
<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
<p:notesStyle>
<a:lvl1pPr marL="0" indent="0" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">
<a:defRPr sz="1200" kern="1200"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill><a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr>
</a:lvl1pPr>
</p:notesStyle>
</p:notesMaster>'''

NOTES_MASTER_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>'''


def notes_slide_xml(notes_text: str) -> str:
    """Render a notesSlide containing the given notes. Each non-empty line becomes a paragraph."""
    paragraphs = []
    for line in notes_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip leading markdown bullets ('- ', '* ', '+ ')
        line = re.sub(r"^[-*+]\s+", "", line)
        # XML-escape
        line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        paragraphs.append(
            f'<a:p><a:r><a:rPr lang="en-US"/><a:t>{line}</a:t></a:r></a:p>'
        )
    if not paragraphs:
        paragraphs.append('<a:p><a:endParaRPr lang="en-US"/></a:p>')
    body = "\n".join(paragraphs)

    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:notes xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:sp>
<p:nvSpPr><p:cNvPr id="2" name="Notes Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>
<p:spPr/>
<p:txBody>
<a:bodyPr/><a:lstStyle/>
{body}
</p:txBody>
</p:sp>
</p:spTree></p:cSld>
<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:notes>'''


def notes_slide_rels(slide_index: int) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../slides/slide{slide_index}.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="../notesMasters/notesMaster1.xml"/>
</Relationships>'''


def build(deck_dir: Path, manifest: dict) -> Path:
    template_pptx = (deck_dir / manifest["template"]).resolve()
    output_pptx = (deck_dir / manifest["output"]).resolve()
    slides = manifest["slides"]

    assert template_pptx.exists(), f"Missing template: {template_pptx}"

    # Read all template parts that we'll keep as-is
    keep: dict[str, bytes] = {}
    with zipfile.ZipFile(template_pptx) as z:
        for name in z.namelist():
            keep[name] = z.read(name)

    # Drop template-specific slide files; we regenerate slide list.
    # Also drop any template notesMaster/notesSlides — we regenerate from scratch.
    for key in list(keep.keys()):
        if (key.startswith("ppt/slides/")
                or key.startswith("ppt/media/")
                or key.startswith("ppt/notesSlides/")
                or key.startswith("ppt/notesMasters/")):
            del keep[key]

    # Build per-slide content
    new_slides: dict[str, bytes] = {}
    n_slides = len(slides)
    notes_slide_indexes: list[int] = []  # 1-based indexes of slides with notes

    for i, slide_entry in enumerate(slides, start=1):
        svg_name = slide_entry["file"]
        svg_path = deck_dir / svg_name
        if not svg_path.exists():
            print(f"  SKIP missing slide: {svg_name}")
            continue

        notes_text = (slide_entry.get("notes") or "")
        has_notes = bool(notes_text.strip())
        suffix = " (+notes)" if has_notes else ""
        print(f"  packing {i:02d}: {svg_name}{suffix}")

        inlined = inline_svg_images(svg_path)
        new_slides[f"ppt/media/image{i}.svg"] = inlined.encode("utf-8")
        new_slides[f"ppt/slides/slide{i}.xml"] = slide_xml(picture_id=100 + i, slide_index=i).encode("utf-8")

        notes_idx = i if has_notes else None
        new_slides[f"ppt/slides/_rels/slide{i}.xml.rels"] = slide_rels(
            f"image{i}.svg", notes_slide_index=notes_idx
        ).encode("utf-8")

        if has_notes:
            new_slides[f"ppt/notesSlides/notesSlide{i}.xml"] = notes_slide_xml(notes_text).encode("utf-8")
            new_slides[f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels"] = notes_slide_rels(i).encode("utf-8")
            notes_slide_indexes.append(i)

    # If any slide has notes, also emit the notesMaster (referenced by every notesSlide).
    has_any_notes = bool(notes_slide_indexes)
    if has_any_notes:
        new_slides["ppt/notesMasters/notesMaster1.xml"] = NOTES_MASTER_XML.encode("utf-8")
        new_slides["ppt/notesMasters/_rels/notesMaster1.xml.rels"] = NOTES_MASTER_RELS.encode("utf-8")

    # Build presentation.xml.rels (slide masters + new slides + theme + props + optional notesMaster)
    # Preserve existing non-slide relationships, renumber slides
    pres_rels_template = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
{slide_rels}
<Relationship Id="rId{theme}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
<Relationship Id="rId{tableStyles}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles" Target="tableStyles.xml"/>
<Relationship Id="rId{presProps}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="presProps.xml"/>
<Relationship Id="rId{viewProps}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps" Target="viewProps.xml"/>
{notes_master}</Relationships>'''
    slide_rel_entries = "\n".join(
        f'<Relationship Id="rId{i + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i + 1}.xml"/>'
        for i in range(n_slides)
    )
    base_id = n_slides + 2  # 1=master, 2..n+1=slides, n+2..=other parts
    notes_master_entry = ""
    if has_any_notes:
        notes_master_entry = (
            f'<Relationship Id="rId{base_id + 4}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" '
            f'Target="notesMasters/notesMaster1.xml"/>'
        )
    pres_rels = pres_rels_template.format(
        slide_rels=slide_rel_entries,
        theme=base_id,
        tableStyles=base_id + 1,
        presProps=base_id + 2,
        viewProps=base_id + 3,
        notes_master=notes_master_entry,
    )
    keep["ppt/_rels/presentation.xml.rels"] = pres_rels.encode("utf-8")

    # Update presentation.xml sldIdLst (and add notesMasterIdLst if any notes exist)
    # rId1 is the slideMaster; slides start at rId2.
    pres = keep["ppt/presentation.xml"].decode()
    new_sldidlst = (
        "<p:sldIdLst>"
        + "".join(
            f'<p:sldId id="{256 + i}" r:id="rId{i + 2}"/>'
            for i in range(n_slides)
        )
        + "</p:sldIdLst>"
    )
    pres = re.sub(r"<p:sldIdLst>.*?</p:sldIdLst>", new_sldidlst, pres, count=1, flags=re.DOTALL)

    # Add or remove notesMasterIdLst based on whether we have notes
    pres = re.sub(r"<p:notesMasterIdLst>.*?</p:notesMasterIdLst>\s*", "", pres, flags=re.DOTALL)
    if has_any_notes:
        notes_master_rid = base_id + 4
        nmil = f'<p:notesMasterIdLst><p:notesMasterId r:id="rId{notes_master_rid}"/></p:notesMasterIdLst>'
        # Insert after </p:sldIdLst>
        pres = pres.replace("</p:sldIdLst>", "</p:sldIdLst>" + nmil, 1)

    keep["ppt/presentation.xml"] = pres.encode("utf-8")

    # Update [Content_Types].xml: ensure svg default + per-slide overrides + notes overrides
    ct = keep["[Content_Types].xml"].decode()
    # Strip existing slide / notes overrides
    ct = re.sub(r'<Override\s+PartName="/ppt/slides/slide\d+\.xml"[^>]*/>', "", ct)
    ct = re.sub(r'<Override\s+PartName="/ppt/notesSlides/notesSlide\d+\.xml"[^>]*/>', "", ct)
    ct = re.sub(r'<Override\s+PartName="/ppt/notesMasters/notesMaster1\.xml"[^>]*/>', "", ct)
    # Insert new slide overrides before </Types>
    slide_overrides = "".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, n_slides + 1)
    )
    notes_overrides = ""
    if has_any_notes:
        notes_overrides += '<Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"/>'
        for i in notes_slide_indexes:
            notes_overrides += (
                f'<Override PartName="/ppt/notesSlides/notesSlide{i}.xml" '
                f'ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>'
            )
    ct = ct.replace("</Types>", slide_overrides + notes_overrides + "</Types>")
    keep["[Content_Types].xml"] = ct.encode("utf-8")

    # Merge new slide files
    keep.update(new_slides)

    # Write the .pptx
    output_pptx.parent.mkdir(parents=True, exist_ok=True)
    output_pptx.unlink(missing_ok=True)
    with zipfile.ZipFile(output_pptx, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(keep.keys()):
            z.writestr(name, keep[name])

    return output_pptx


VIEWBOX_HEIGHT = 1080
OVERFLOW_MARGIN = 30  # warn if a text baseline is past (viewBox_height - this) px


def _approx_y_of_last_baseline(text_elem: str, parent_y: float, parent_font_size: float) -> float:
    """Walk tspan dy chain and compute the approximate y baseline of the last visible row.

    `dy="Nem"` advances by N * font_size. `dy="N"` (no unit) is treated as px.
    Other units fall back to 0 (best-effort heuristic).
    """
    y = parent_y
    fs = parent_font_size
    for m in re.finditer(r'<tspan\b([^>]*)>', text_elem):
        attrs = m.group(1)
        # Per-tspan font-size override
        fs_m = re.search(r'font-size="(\d+(?:\.\d+)?)"', attrs)
        if fs_m:
            fs = float(fs_m.group(1))
        dy_m = re.search(r'dy="(-?\d+(?:\.\d+)?)(em|px)?"', attrs)
        if not dy_m:
            continue
        value = float(dy_m.group(1))
        unit = dy_m.group(2) or "px"
        if unit == "em":
            y += value * fs
        else:
            y += value
    return y


def lint_source_svgs(deck_dir: Path, slide_files: list[str]) -> list[str]:
    """Heuristic checks on source SVGs before packaging. Returns a list of warnings.

    - Y-overflow: warn if any <text> element's baseline (after tspan dy advances) lands
      past viewBox height - OVERFLOW_MARGIN. Catches "I added one too many bullets."
    - X-bounds: warn if any <text> has x > 1820 (catches obvious off-slide labels).
    """
    warnings: list[str] = []
    text_block_re = re.compile(
        r'<text\b([^>]*?)>(.*?)</text>', re.DOTALL,
    )
    for svg_name in slide_files:
        path = deck_dir / svg_name
        if not path.exists():
            continue
        svg = path.read_text(errors="replace")
        for m in text_block_re.finditer(svg):
            attrs, body = m.group(1), m.group(2)
            y_m = re.search(r'\by="(-?\d+(?:\.\d+)?)"', attrs)
            if not y_m:
                continue
            y = float(y_m.group(1))
            fs_m = re.search(r'font-size="(\d+(?:\.\d+)?)"', attrs)
            fs = float(fs_m.group(1)) if fs_m else 22.0
            x_m = re.search(r'\bx="(-?\d+(?:\.\d+)?)"', attrs)
            x = float(x_m.group(1)) if x_m else 0.0

            # X overflow
            if x > 1820:
                warnings.append(f"{svg_name}: <text x={int(x)}> is past slide right edge (1920)")

            # Y overflow on parent baseline
            if y > VIEWBOX_HEIGHT - OVERFLOW_MARGIN:
                warnings.append(f"{svg_name}: <text y={int(y)}> is past slide bottom ({VIEWBOX_HEIGHT})")
                continue

            # Y overflow after tspan dy chain
            final_y = _approx_y_of_last_baseline(body, y, fs)
            if final_y > VIEWBOX_HEIGHT - OVERFLOW_MARGIN:
                warnings.append(
                    f"{svg_name}: <text y={int(y)}> bullet list spills to y≈{int(final_y)} (past {VIEWBOX_HEIGHT})"
                )
    return warnings


def verify(pptx_path: Path, expected_slide_count: int) -> list[str]:
    """Sanity-check a built pptx. Returns a list of problems (empty = OK).

    Catches issues that trigger PowerPoint's "found a problem with content,
    can attempt to repair" dialog:
      - duplicate slide overrides in [Content_Types].xml
      - phantom slide overrides for slides that don't exist
      - missing slide overrides
      - rId mismatch between presentation.xml sldIdLst and presentation.xml.rels
      - sldIdLst entries pointing at a rel that isn't a slide (e.g. slideMaster)
      - per-slide rels referencing missing media files
      - SVG media still containing <?xml-stylesheet?> PIs (external CSS refs)
      - SVG media with relative <image href> targets that aren't packaged
    """
    problems: list[str] = []
    with zipfile.ZipFile(pptx_path) as z:
        names = set(z.namelist())

        # --- Content_Types: slide overrides ---
        ct = z.read("[Content_Types].xml").decode()
        slide_overrides = re.findall(r'PartName="/ppt/slides/(slide\d+\.xml)"', ct)
        seen = set()
        for s in slide_overrides:
            if s in seen:
                problems.append(f"[Content_Types] duplicate slide override: {s}")
            seen.add(s)
        for s in seen:
            if f"ppt/slides/{s}" not in names:
                problems.append(f"[Content_Types] phantom slide override for missing part: {s}")
        for i in range(1, expected_slide_count + 1):
            if f"slide{i}.xml" not in seen:
                problems.append(f"[Content_Types] missing override for slide{i}.xml")

        # --- presentation rels vs sldIdLst ---
        pres_rels = z.read("ppt/_rels/presentation.xml.rels").decode()
        rid_target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', pres_rels))
        rid_type = dict(re.findall(r'Id="(rId\d+)"[^>]*Type="[^"]*relationships/(\w+)"', pres_rels))
        pres = z.read("ppt/presentation.xml").decode()
        sld_ids = re.findall(r'<p:sldId\s[^>]*r:id="(rId\d+)"', pres)
        if len(sld_ids) != expected_slide_count:
            problems.append(f"presentation.xml has {len(sld_ids)} sldId entries, expected {expected_slide_count}")
        for rid in sld_ids:
            if rid not in rid_target:
                problems.append(f"sldIdLst references {rid} but no matching rel")
                continue
            if rid_type.get(rid) != "slide":
                problems.append(f"sldIdLst {rid} points at type={rid_type.get(rid)!r}, not 'slide' (target={rid_target[rid]})")

        # --- per-slide rels: image targets must exist ---
        for n in sorted(names):
            if not n.startswith("ppt/slides/_rels/slide") or not n.endswith(".xml.rels"):
                continue
            rels = z.read(n).decode()
            for m in re.finditer(r'Target="([^"]+)"', rels):
                target = m.group(1)
                if target.startswith("http"):
                    continue
                # Resolve relative to ppt/slides/
                resolved = re.sub(r"^\.\./", "ppt/", target)
                if not resolved.startswith("ppt/"):
                    resolved = "ppt/slides/" + resolved
                if resolved not in names:
                    problems.append(f"{n}: rel target missing from package: {target}")

        # --- SVG media: stylesheet PIs + unresolved <image href> ---
        for n in sorted(names):
            if not n.startswith("ppt/media/") or not n.endswith(".svg"):
                continue
            svg = z.read(n).decode(errors="replace")
            if "<?xml-stylesheet" in svg:
                problems.append(f"{n}: contains <?xml-stylesheet?> (external CSS ref)")
            for m in re.finditer(r'<image[^>]+(?:xlink:)?href="([^"]+)"', svg):
                href = m.group(1)
                if href.startswith(("data:", "http:", "https:")):
                    continue
                # Relative href inside media/ — resolve against ppt/media/<svgdir>/
                svg_dir = "/".join(n.split("/")[:-1])  # e.g. ppt/media
                target = (svg_dir + "/" + href).replace("/./", "/")
                # Normalize ../
                parts = []
                for p in target.split("/"):
                    if p == "..":
                        if parts:
                            parts.pop()
                    elif p and p != ".":
                        parts.append(p)
                target = "/".join(parts)
                if target not in names:
                    problems.append(f"{n}: <image href={href!r}> points outside the package (would render broken in PowerPoint)")

    return problems


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a self-contained .pptx from a deck of SVG slides.",
    )
    parser.add_argument(
        "deck_dir",
        nargs="?",
        default=".",
        help="Path to the deck directory (default: cwd). Must contain SVG slides; deck.yaml is optional.",
    )
    parser.add_argument(
        "-o", "--output",
        help="Override the output .pptx path (relative to deck dir or absolute). "
             "Overrides deck.yaml 'output' and the default <deck-dirname>.pptx.",
    )
    args = parser.parse_args()

    deck_dir = Path(args.deck_dir).resolve()
    if not deck_dir.is_dir():
        raise SystemExit(f"Not a directory: {deck_dir}")

    manifest = load_manifest(deck_dir)
    if args.output:
        manifest["output"] = args.output

    print(f"Deck:     {deck_dir}")
    print(f"Template: {manifest['template']}")
    print(f"Output:   {manifest['output']}")
    print(f"Slides:   {len(manifest['slides'])}")
    print()

    out = build(deck_dir, manifest)
    print(f"\nWrote {out} ({out.stat().st_size / 1024:.1f} KB)")

    # Layout warnings (heuristic, not fatal)
    slide_files = [s["file"] for s in manifest["slides"]]
    layout_warnings = lint_source_svgs(deck_dir, slide_files)
    if layout_warnings:
        print(f"\nLayout warnings ({len(layout_warnings)}):")
        for w in layout_warnings:
            print(f"  - {w}")
        print("  ↑ heuristic only; render the PNG to confirm.")

    print("\nVerifying...")
    n_slides = sum(1 for s in manifest["slides"] if (deck_dir / s["file"]).exists())
    issues = verify(out, expected_slide_count=n_slides)
    if issues:
        print(f"  FAIL ({len(issues)} problems):")
        for p in issues:
            print(f"    - {p}")
        raise SystemExit(1)
    print("  OK")
