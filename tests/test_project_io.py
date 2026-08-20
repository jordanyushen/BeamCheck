from __future__ import annotations

from beamcheck.core.loads import FullSpanUDL, PointLoad
from beamcheck.core.models import Beam, BeamType, CalculationInput, ProjectInfo
from beamcheck.utils.project_io import load_project, save_project


def test_project_round_trip_recalculable(tmp_path, steel, rectangle) -> None:
    original = CalculationInput(
        Beam(BeamType.SIMPLY_SUPPORTED, 4.0),
        steel,
        rectangle,
        (PointLoad(1000, 1.25), FullSpanUDL(500)),
        project=ProjectInfo("Bridge", "Check 01", "Engineer", "Local only"),
    )
    loaded = load_project(save_project(original, tmp_path / "case.beamcheck.json"))
    assert loaded == original
