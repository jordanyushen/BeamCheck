"""Matplotlib figures shared by the GUI and PDF report."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Literal

from matplotlib.font_manager import FontProperties
from matplotlib.figure import Figure
from matplotlib.patches import Polygon, Rectangle

from beamcheck.core.loads import FullSpanUDL, PointLoad
from beamcheck.core.models import BeamType, CalculationResult
from beamcheck.utils.i18n import translate


NAVY = "#183153"
BLUE = "#2563eb"
RED = "#dc2626"
TEAL = "#0f766e"
GRID = "#dbe4ee"


def _localized_font(language: str) -> FontProperties | None:
    if language != "zh_CN":
        return None
    for path in (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf")):
        if path.exists():
            return FontProperties(fname=str(path))
    return None


def _base_figure(height: float = 3.5) -> Figure:
    figure = Figure(figsize=(8.2, height), dpi=110, constrained_layout=True)
    figure.patch.set_facecolor("white")
    return figure


def beam_schematic(result: CalculationResult, language: str = "en") -> Figure:
    figure = _base_figure(3.2)
    axis = figure.add_subplot(111)
    length = result.input.beam.length
    axis.plot([0, length], [0, 0], color=NAVY, linewidth=6, solid_capstyle="round")

    if result.input.beam.beam_type is BeamType.SIMPLY_SUPPORTED:
        support_height = max(length * 0.055, 0.12)
        for x in (0.0, length):
            triangle = Polygon(
                [[x, -0.02], [x - support_height / 2, -support_height], [x + support_height / 2, -support_height]],
                closed=True,
                facecolor="#94a3b8",
                edgecolor=NAVY,
            )
            axis.add_patch(triangle)
    else:
        wall_height = max(length * 0.22, 0.5)
        axis.add_patch(Rectangle((-length * 0.018, -wall_height / 2), length * 0.018, wall_height, facecolor="#94a3b8", edgecolor=NAVY))
        for y in [(-wall_height / 2) + index * wall_height / 7 for index in range(8)]:
            axis.plot([-length * 0.055, 0], [y - wall_height / 12, y], color="#64748b", linewidth=1)

    load_scale = max(length * 0.16, 0.35)
    for load in result.input.loads:
        if isinstance(load, PointLoad):
            axis.annotate(
                "",
                xy=(load.position, 0.04),
                xytext=(load.position, load_scale),
                arrowprops={"arrowstyle": "-|>", "color": RED, "lw": 2.2},
            )
            axis.text(load.position, load_scale * 1.06, f"{load.magnitude / 1000:g} kN", ha="center", va="bottom", color=RED, fontsize=9)
        elif isinstance(load, FullSpanUDL):
            arrow_count = 9
            for index in range(arrow_count):
                x = length * index / (arrow_count - 1)
                axis.annotate(
                    "",
                    xy=(x, 0.04),
                    xytext=(x, load_scale * 0.72),
                    arrowprops={"arrowstyle": "-|>", "color": BLUE, "lw": 1.4},
                )
            axis.plot([0, length], [load_scale * 0.72] * 2, color=BLUE, linewidth=1.5)
            axis.text(length / 2, load_scale * 0.82, f"{load.magnitude / 1000:g} kN/m", ha="center", color=BLUE, fontsize=9)

    dimension_y = -max(length * 0.13, 0.28)
    axis.annotate("", xy=(0, dimension_y), xytext=(length, dimension_y), arrowprops={"arrowstyle": "<->", "color": "#475569", "lw": 1})
    axis.text(length / 2, dimension_y * 1.08, f"L = {length:g} m", ha="center", va="top", color="#334155")
    margin = max(length * 0.1, 0.2)
    axis.set_xlim(-margin, length + margin)
    axis.set_ylim(dimension_y * 1.55, load_scale * 1.35)
    axis.set_title(translate(language, "beam_schematic"), loc="left", color=NAVY, fontweight="bold", fontproperties=_localized_font(language))
    axis.axis("off")
    return figure


def result_diagram(
    result: CalculationResult,
    kind: Literal["shear", "moment", "deflection"],
    language: str = "en",
) -> Figure:
    figure = _base_figure()
    axis = figure.add_subplot(111)
    localized_font = _localized_font(language)
    x_values = result.x
    if kind == "shear":
        values = [value / 1000 for value in result.shear]
        ylabel, title, color = translate(language, "shear_axis"), translate(language, "shear_diagram"), BLUE
    elif kind == "moment":
        values = [value / 1000 for value in result.moment]
        ylabel, title, color = translate(language, "moment_axis"), translate(language, "moment_diagram"), RED
    else:
        values = [value * 1000 for value in result.deflection]
        ylabel, title, color = translate(language, "deflection_axis"), translate(language, "deflection_curve"), TEAL

    axis.plot(x_values, values, color=color, linewidth=2)
    axis.fill_between(x_values, values, 0, color=color, alpha=0.12)
    axis.axhline(0, color="#64748b", linewidth=0.8)
    axis.set_xlabel(translate(language, "position_axis"), fontproperties=localized_font)
    axis.set_ylabel(ylabel, fontproperties=localized_font)
    axis.set_title(title, loc="left", color=NAVY, fontweight="bold", fontproperties=localized_font)
    axis.grid(True, color=GRID, linewidth=0.7)
    axis.margins(x=0)
    return figure


def figure_png(figure: Figure, dpi: int = 160) -> BytesIO:
    stream = BytesIO()
    figure.savefig(stream, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    stream.seek(0)
    return stream
