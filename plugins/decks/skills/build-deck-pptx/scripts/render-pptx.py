#!/usr/bin/env python3

"""Render a PPTX to one PNG per slide using LibreOffice and Poppler."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def find_command(*names: str) -> str:
    """Return the first available command or raise a useful error."""
    for name in names:
        command = shutil.which(name)
        if command:
            return command
    raise RuntimeError(f"Required command not found: {' or '.join(names)}")


def slide_number(path: Path) -> int:
    """Return the numeric suffix from a Poppler slide image path."""
    return int(path.stem.rsplit("-", 1)[1])


def render_presentation(pptx_path: Path, output_dir: Path, dpi: int) -> list[Path]:
    """Render a presentation and return the generated PNG paths."""
    if not pptx_path.is_file():
        raise FileNotFoundError(f"Presentation does not exist: {pptx_path}")

    libreoffice = find_command("libreoffice", "soffice")
    pdftoppm = find_command("pdftoppm")
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / f"{pptx_path.stem}.pdf"
    pdf_path.unlink(missing_ok=True)
    for stale_slide in output_dir.glob("slide-*.png"):
        stale_slide.unlink()

    subprocess.run(
        [
            libreoffice,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(pptx_path.resolve()),
        ],
        check=True,
    )

    if not pdf_path.is_file():
        raise RuntimeError(f"LibreOffice did not create {pdf_path}")

    prefix = output_dir / "slide"
    subprocess.run(
        [pdftoppm, "-png", "-r", str(dpi), str(pdf_path), str(prefix)],
        check=True,
    )

    rendered_slides = sorted(output_dir.glob("slide-*.png"), key=slide_number)
    if not rendered_slides:
        raise RuntimeError("Poppler did not render any slides")

    normalized_slides = []
    width = max(2, len(str(len(rendered_slides))))
    for index, rendered_slide in enumerate(rendered_slides, start=1):
        normalized_slide = output_dir / f"slide-{index:0{width}d}.png"
        rendered_slide.rename(normalized_slide)
        normalized_slides.append(normalized_slide)
    return normalized_slides


def main() -> int:
    """Run the command-line renderer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path, help="Presentation to render")
    parser.add_argument("--output-dir", type=Path, default=Path("renders"))
    parser.add_argument("--dpi", type=int, default=144)
    arguments = parser.parse_args()

    try:
        rendered_slides = render_presentation(
            arguments.pptx,
            arguments.output_dir,
            arguments.dpi,
        )
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exception:
        print(f"ERROR: {exception}", file=sys.stderr)
        return 1

    for slide in rendered_slides:
        print(slide)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())