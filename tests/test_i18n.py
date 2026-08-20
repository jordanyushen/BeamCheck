from __future__ import annotations

from beamcheck.core.loads import FullSpanUDL
from beamcheck.core.models import Beam, BeamType, CalculationInput
from beamcheck.core.solver import solve
from beamcheck.reporting.formula_trace import build_formula_trace
from beamcheck.reporting.report import export_pdf
from beamcheck.utils.i18n import LANGUAGES, translate


def test_all_supported_languages_have_distinct_navigation() -> None:
    assert set(LANGUAGES) == {"en", "fr", "de", "zh_CN"}
    labels = {translate(language, "settings") for language in LANGUAGES}
    assert len(labels) == 4
    assert translate("zh_CN", "calculate") == "计算"
    assert translate("fr", "calculate") == "Calculer"
    assert translate("de", "calculate") == "Berechnen"


def test_formula_trace_and_chinese_pdf_are_localized(tmp_path, steel, rectangle) -> None:
    result = solve(CalculationInput(Beam(BeamType.SIMPLY_SUPPORTED, 4), steel, rectangle, (FullSpanUDL(2000),)))
    assert "截面特性" in build_formula_trace(result, "zh_CN")
    assert "CARACTÉRISTIQUES DE SECTION" in build_formula_trace(result, "fr")
    assert "QUERSCHNITTSWERTE" in build_formula_trace(result, "de")
    path = export_pdf(result, tmp_path / "报告.pdf", "zh_CN")
    assert path.read_bytes().startswith(b"%PDF")
    assert path.stat().st_size > 10_000
