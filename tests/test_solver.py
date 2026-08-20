from __future__ import annotations

import pytest

from beamcheck.core.checks import bending_stress, safety_factor
from beamcheck.core.loads import FullSpanUDL, PointLoad
from beamcheck.core.models import Beam, BeamType, CalculationInput, DeflectionCriterion
from beamcheck.core.solver import solve


def test_arbitrary_point_reactions(steel, rectangle) -> None:
    case = CalculationInput(
        Beam(BeamType.SIMPLY_SUPPORTED, 5.0), steel, rectangle, (PointLoad(12_000, 2.0),)
    )
    result = solve(case)
    assert result.reactions.left_vertical == pytest.approx(7200)
    assert result.reactions.right_vertical == pytest.approx(4800)
    assert result.max_abs_moment == pytest.approx(14_400)


def test_superposition_equilibrium(steel, rectangle) -> None:
    case = CalculationInput(
        Beam(BeamType.SIMPLY_SUPPORTED, 4.0),
        steel,
        rectangle,
        (PointLoad(10_000, 1.0), FullSpanUDL(2_000)),
    )
    result = solve(case)
    assert result.reactions.left_vertical + result.reactions.right_vertical == pytest.approx(18_000)
    assert result.moment[0] == pytest.approx(0.0, abs=1e-10)
    assert result.moment[-1] == pytest.approx(0.0, abs=1e-10)


def test_stress_factor_and_checks(steel, rectangle) -> None:
    stress = bending_stress(10_000, rectangle.properties().section_modulus)
    assert stress == pytest.approx(15e6)
    assert safety_factor(steel.yield_strength, stress) == pytest.approx(250 / 15)
    case = CalculationInput(
        Beam(BeamType.CANTILEVER, 1.0),
        steel,
        rectangle,
        (PointLoad(1000, 1.0),),
        DeflectionCriterion(ratio=250),
    )
    result = solve(case)
    assert result.stress_check.passes
    assert result.deflection_check.passes


def test_bad_inputs_are_plainly_rejected(steel, rectangle) -> None:
    with pytest.raises(ValueError, match="position must lie"):
        solve(
            CalculationInput(
                Beam(BeamType.SIMPLY_SUPPORTED, 2.0),
                steel,
                rectangle,
                (PointLoad(100, 3.0),),
            )
        )
