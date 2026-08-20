from __future__ import annotations

from beamcheck.core.loads import FullSpanUDL
from beamcheck.core.models import Beam, BeamType, CalculationInput
from beamcheck.core.solver import solve
from beamcheck.reporting.formula_trace import build_formula_trace
from beamcheck.reporting.report import export_pdf


def test_formula_trace_is_solver_connected(steel, rectangle) -> None:
    result = solve(CalculationInput(Beam(BeamType.SIMPLY_SUPPORTED, 4), steel, rectangle, (FullSpanUDL(2000),)))
    trace = build_formula_trace(result)
    assert "M_max = w L² / 8" in trace
    assert "M_max = 4 kN·m" in trace
    assert "Stress check: PASS" in trace


def test_pdf_export(tmp_path, steel, rectangle) -> None:
    result = solve(CalculationInput(Beam(BeamType.CANTILEVER, 2), steel, rectangle, (FullSpanUDL(1000),)))
    path = export_pdf(result, tmp_path / "report.pdf")
    assert path.read_bytes().startswith(b"%PDF")
    assert path.stat().st_size > 10_000
