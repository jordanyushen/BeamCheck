"""Professional, offline PDF calculation report generation."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from beamcheck.core.loads import FullSpanUDL, PointLoad
from beamcheck.core.models import BeamType, CalculationResult
from beamcheck.gui.plots import beam_schematic, figure_png, result_diagram
from beamcheck.reporting.formula_trace import build_formula_trace
from beamcheck.utils.i18n import translate


DISCLAIMER = (
    "BeamCheck is an engineering calculation aid. Results must be reviewed by a qualified "
    "user and checked against applicable standards, design requirements, and project conditions. "
    "This report is not code-compliance certification and is not a replacement for professional "
    "engineering review."
)


def _pdf_fonts(language: str) -> tuple[str, str]:
    if language != "zh_CN":
        return "Helvetica", "Helvetica-Bold"
    if "BeamCheckCJK" in pdfmetrics.getRegisteredFontNames():
        return "BeamCheckCJK", "BeamCheckCJK"
    candidates = (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    )
    for font_path in candidates:
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("BeamCheckCJK", str(font_path)))
                return "BeamCheckCJK", "BeamCheckCJK"
            except Exception:
                continue
    return "Helvetica", "Helvetica-Bold"


def _table(
    rows: list[list[str]],
    widths: tuple[float, float] = (72 * mm, 92 * mm),
    regular_font: str = "Helvetica",
    bold_font: str = "Helvetica-Bold",
) -> Table:
    table = Table(rows, colWidths=list(widths), hAlign="LEFT", repeatRows=1 if rows else 0)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#183153")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), bold_font),
                ("FONTNAME", (0, 1), (0, -1), bold_font),
                ("FONTNAME", (1, 1), (-1, -1), regular_font),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _plot_image(figure, width: float = 164 * mm) -> Image:
    image = Image(figure_png(figure), width=width, height=width * 0.44)
    return image


def _footer(canvas, document, language: str, regular_font: str) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
    canvas.line(20 * mm, 15 * mm, 190 * mm, 15 * mm)
    canvas.setFont(regular_font, 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(20 * mm, 10 * mm, translate(language, "report_footer"))
    canvas.drawRightString(190 * mm, 10 * mm, translate(language, "page", page=document.page))
    canvas.restoreState()


def export_pdf(result: CalculationResult, destination: str | Path, language: str = "en") -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title=result.input.project.calculation_title,
        author=result.input.project.engineer or "BeamCheck",
    )
    styles = getSampleStyleSheet()
    regular_font, bold_font = _pdf_fonts(language)
    for base_style in ("Normal", "BodyText", "Title", "Heading1", "Heading2", "Code"):
        styles[base_style].fontName = regular_font
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName=bold_font, textColor=colors.HexColor("#183153"), fontSize=25, leading=30, alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName=bold_font, textColor=colors.HexColor("#183153"), fontSize=14, leading=18, spaceBefore=10, spaceAfter=7))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontName=regular_font, fontSize=8.5, leading=11, textColor=colors.HexColor("#475569")))
    styles.add(ParagraphStyle(name="Trace", parent=styles["Code"], fontName=regular_font if language == "zh_CN" else "Courier", fontSize=7.5, leading=10, leftIndent=5 * mm, borderColor=colors.HexColor("#cbd5e1"), borderWidth=0.5, borderPadding=7, backColor=colors.HexColor("#f8fafc")))

    case = result.input
    props = result.section_properties
    story = [
        Spacer(1, 18 * mm),
        Paragraph("BeamCheck", styles["ReportTitle"]),
        Paragraph(case.project.calculation_title, styles["Heading1"]),
        Spacer(1, 8 * mm),
        _table(
            [
                [translate(language, "project_information"), translate(language, "value")],
                [translate(language, "project"), case.project.project_name],
                [translate(language, "engineer_author"), case.project.engineer or "—"],
                [translate(language, "notes"), case.project.notes or "—"],
            ], regular_font=regular_font, bold_font=bold_font
        ),
        Spacer(1, 12 * mm),
        Paragraph(translate(language, "disclaimer"), styles["Small"]),
        PageBreak(),
        Paragraph(translate(language, "report_beam_definition"), styles["Section"]),
        _table(
            [
                [translate(language, "beam_group"), translate(language, "value")],
                [translate(language, "support_condition"), translate(language, "simply_supported" if case.beam.beam_type is BeamType.SIMPLY_SUPPORTED else "cantilever")],
                [translate(language, "length"), f"{case.beam.length:.6g} m"],
                [translate(language, "section"), translate(language, {"Solid rectangular": "rectangular", "Solid circular": "circular", "Rectangular hollow": "rhs", "Square hollow": "shs"}.get(case.section.name, "section"))],
                [translate(language, "material"), case.material.name],
                [translate(language, "youngs_modulus"), f"{case.material.youngs_modulus / 1e9:.6g} GPa"],
                [translate(language, "yield_strength"), f"{case.material.yield_strength / 1e6:.6g} MPa"],
            ], regular_font=regular_font, bold_font=bold_font
        ),
        Spacer(1, 5 * mm),
        _plot_image(beam_schematic(result, language)),
        Paragraph(translate(language, "report_section_properties"), styles["Section"]),
        _table(
            [
                [translate(language, "property"), translate(language, "calculated_value")],
                [translate(language, "area"), f"{props.area:.6g} m²"],
                [translate(language, "second_moment"), f"{props.second_moment:.6g} m⁴"],
                [translate(language, "extreme_fibre"), f"{props.extreme_fibre:.6g} m"],
                [translate(language, "section_modulus"), f"{props.section_modulus:.6g} m³"],
            ], regular_font=regular_font, bold_font=bold_font
        ),
        Paragraph(translate(language, "report_applied_loads"), styles["Section"]),
    ]
    load_rows = [[translate(language, "load"), translate(language, "definition")]]
    for load in case.loads:
        if isinstance(load, PointLoad):
            load_rows.append([translate(language, "point_load"), translate(language, "point_load_definition", p=load.magnitude / 1000, x=load.position)])
        elif isinstance(load, FullSpanUDL):
            load_rows.append([translate(language, "full_span_udl"), translate(language, "udl_definition", w=load.magnitude / 1000, length=case.beam.length)])
    story.extend([_table(load_rows, regular_font=regular_font, bold_font=bold_font), PageBreak(), Paragraph(translate(language, "report_reactions"), styles["Section"])])

    if case.beam.beam_type is BeamType.SIMPLY_SUPPORTED:
        reaction_rows = [[translate(language, "reaction"), translate(language, "value")], [translate(language, "left_reaction"), f"{result.reactions.left_vertical / 1000:.6g} kN"], [translate(language, "right_reaction"), f"{result.reactions.right_vertical / 1000:.6g} kN"]]
    else:
        reaction_rows = [[translate(language, "reaction"), translate(language, "value")], [translate(language, "fixed_vertical"), f"{result.reactions.fixed_vertical / 1000:.6g} kN"], [translate(language, "fixed_end_moment"), f"{result.reactions.fixed_moment / 1000:.6g} kN·m"]]
    story.extend([_table(reaction_rows, regular_font=regular_font, bold_font=bold_font), Spacer(1, 4 * mm)])
    for kind in ("shear", "moment", "deflection"):
        story.append(_plot_image(result_diagram(result, kind, language)))

    stress_status = translate(language, "pass" if result.stress_check.passes else "fail")
    deflection_status = translate(language, "pass" if result.deflection_check.passes else "fail")
    story.extend(
        [
            PageBreak(),
            Paragraph(translate(language, "report_summary"), styles["Section"]),
            _table(
                [
                    [translate(language, "result"), translate(language, "value")],
                    [translate(language, "maximum_absolute_shear"), f"{result.max_abs_shear / 1000:.6g} kN"],
                    [translate(language, "maximum_absolute_moment"), f"{result.max_abs_moment / 1000:.6g} kN·m"],
                    [translate(language, "maximum_bending_stress"), f"{result.max_bending_stress / 1e6:.6g} MPa — {stress_status}"],
                    [translate(language, "fos_yield"), f"{result.factor_of_safety:.4g}"],
                    [translate(language, "maximum_deflection"), f"{result.max_deflection * 1000:.6g} mm — {translate(language, 'trace_at', x=result.deflection_location)}"],
                    [translate(language, "allowable_deflection"), f"{result.deflection_check.allowable * 1000:.6g} mm — {deflection_status}"],
                ], regular_font=regular_font, bold_font=bold_font
            ),
            Paragraph(translate(language, "report_formula_trace"), styles["Section"]),
            Paragraph(build_formula_trace(result, language).replace("&", "&amp;").replace("<", "&lt;").replace("\n", "<br/>"), styles["Trace"]),
            Paragraph(translate(language, "report_assumptions"), styles["Section"]),
            Paragraph(translate(language, "assumptions_text"), styles["BodyText"]),
            Spacer(1, 5 * mm),
            KeepTogether([Paragraph(translate(language, "disclaimer_heading"), styles["Section"]), Paragraph(translate(language, "disclaimer"), styles["Small"])])
        ]
    )
    footer = lambda canvas, doc: _footer(canvas, doc, language, regular_font)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return path
