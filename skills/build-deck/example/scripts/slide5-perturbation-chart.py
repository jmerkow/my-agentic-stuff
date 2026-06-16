"""Slide 5 — Matplotlib chart example.

Horizontal bar chart of (synthetic) perturbation impact on a score.
Palette pulled from the light-classic theme so the chart blends into
the slide.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


# Palette → theme classes:
#   FIGURE_BG → .bg          fill
#   AXES_BG   → .surface-alt fill
#   TEXT      → .text        fill
#   MUTED     → .text-muted  fill
#   SPINE     → .border      stroke
#   BAR       → .accent      fill
FIGURE_BG = "#ffffff"
AXES_BG = "#fafbfc"
TEXT = "#1a1a1a"
MUTED = "#666666"
SPINE = "#e5e7eb"
BAR = "#0078d4"

# Synthetic data — eight perturbations sorted by impact.
DATA = [
    ("truncation", 0.105),
    ("unicode_lookalikes", 0.101),
    ("whitespace_pad", 0.097),
    ("drop_indication", 0.091),
    ("punctuation_strip", 0.086),
    ("lowercase", 0.045),
    ("drop_impression", 0.019),
    ("whitespace_collapse", 0.013),
]


def format_tick(value, _):
    if abs(value) < 1e-12:
        return "0"
    return f"{value:.2f}"


def build():
    out_dir = Path(__file__).resolve().parent.parent / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "slide5-perturbation-chart.png"

    labels = [item[0] for item in DATA]
    values = [item[1] for item in DATA]
    y_positions = list(range(len(DATA)))

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Liberation Sans", "Arial"]

    fig, ax = plt.subplots(figsize=(11, 6.0), dpi=100, facecolor=FIGURE_BG)
    ax.set_facecolor(AXES_BG)

    ax.barh(y_positions, values, color=BAR, height=0.7)

    ax.set_xlim(0, 0.12)
    ax.set_xticks([0.00, 0.03, 0.06, 0.09, 0.12])
    ax.xaxis.set_major_formatter(FuncFormatter(format_tick))
    ax.set_xlabel("Δ score (lower is better; positive = damage)",
                  fontsize=12, color=MUTED, labelpad=10)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=14, color=MUTED)
    ax.invert_yaxis()

    ax.set_axisbelow(True)
    ax.grid(axis="x", color=SPINE, linewidth=1)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(SPINE)
    ax.tick_params(axis="x", colors=MUTED)
    ax.tick_params(axis="y", colors=MUTED, length=0)

    fig.tight_layout(pad=0.5)
    fig.savefig(out_path, dpi=100, bbox_inches="tight", facecolor=FIGURE_BG)
    plt.close(fig)
    print(out_path)


if __name__ == "__main__":
    build()
