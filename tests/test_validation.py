from __future__ import annotations

import pytest

from beamcheck.core.loads import FullSpanUDL
from beamcheck.core.materials import Material
from beamcheck.core.models import Beam, BeamType, CalculationInput
from beamcheck.core.sections import HollowRectangularSection
from beamcheck.core.solver import solve


def test_zero_length_and_impossible_hollow_section_rejected(steel) -> None:
    with pytest.raises(ValueError, match="length must be greater"):
        solve(CalculationInput(Beam(BeamType.CANTILEVER, 0), steel, HollowRectangularSection(0.1, 0.1, 0.005), (FullSpanUDL(1),)))
    with pytest.raises(ValueError, match="positive inner"):
        solve(CalculationInput(Beam(BeamType.CANTILEVER, 1), steel, HollowRectangularSection(0.1, 0.1, 0.05), (FullSpanUDL(1),)))


def test_invalid_material_rejected(rectangle) -> None:
    bad = Material("Bad", 0, 250e6, 7850)
    with pytest.raises(ValueError, match="Young's modulus"):
        solve(CalculationInput(Beam(BeamType.CANTILEVER, 1), bad, rectangle, (FullSpanUDL(1),)))
