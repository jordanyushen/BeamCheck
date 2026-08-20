from __future__ import annotations

import pytest

from beamcheck.core.loads import FullSpanUDL, PointLoad
from beamcheck.core.models import Beam, BeamType, CalculationInput
from beamcheck.core.solver import solve


LENGTH = 4.0
POINT_LOAD = 10_000.0
UDL = 2_000.0


def make_case(beam_type, load, steel, rectangle):
    return CalculationInput(Beam(beam_type, LENGTH), steel, rectangle, (load,))


def test_case_a_simply_supported_central_point_load(steel, rectangle) -> None:
    result = solve(make_case(BeamType.SIMPLY_SUPPORTED, PointLoad(POINT_LOAD, LENGTH / 2), steel, rectangle))
    ei = steel.youngs_modulus * result.section_properties.second_moment
    assert result.reactions.left_vertical == pytest.approx(POINT_LOAD / 2, rel=1e-12)
    assert result.reactions.right_vertical == pytest.approx(POINT_LOAD / 2, rel=1e-12)
    assert result.max_abs_moment == pytest.approx(POINT_LOAD * LENGTH / 4, rel=1e-12)
    assert result.max_deflection == pytest.approx(POINT_LOAD * LENGTH**3 / (48 * ei), rel=1e-12)


def test_case_b_simply_supported_full_span_udl(steel, rectangle) -> None:
    result = solve(make_case(BeamType.SIMPLY_SUPPORTED, FullSpanUDL(UDL), steel, rectangle))
    ei = steel.youngs_modulus * result.section_properties.second_moment
    assert result.reactions.left_vertical == pytest.approx(UDL * LENGTH / 2, rel=1e-12)
    assert result.reactions.right_vertical == pytest.approx(UDL * LENGTH / 2, rel=1e-12)
    assert result.max_abs_moment == pytest.approx(UDL * LENGTH**2 / 8, rel=1e-12)
    assert result.max_deflection == pytest.approx(5 * UDL * LENGTH**4 / (384 * ei), rel=1e-12)


def test_case_c_cantilever_free_end_point_load(steel, rectangle) -> None:
    result = solve(make_case(BeamType.CANTILEVER, PointLoad(POINT_LOAD, LENGTH), steel, rectangle))
    ei = steel.youngs_modulus * result.section_properties.second_moment
    assert result.reactions.fixed_vertical == pytest.approx(POINT_LOAD, rel=1e-12)
    assert result.reactions.fixed_moment == pytest.approx(POINT_LOAD * LENGTH, rel=1e-12)
    assert result.max_abs_shear == pytest.approx(POINT_LOAD, rel=1e-12)
    assert result.max_abs_moment == pytest.approx(POINT_LOAD * LENGTH, rel=1e-12)
    assert result.max_deflection == pytest.approx(POINT_LOAD * LENGTH**3 / (3 * ei), rel=1e-12)


def test_case_d_cantilever_full_span_udl(steel, rectangle) -> None:
    result = solve(make_case(BeamType.CANTILEVER, FullSpanUDL(UDL), steel, rectangle))
    ei = steel.youngs_modulus * result.section_properties.second_moment
    assert result.reactions.fixed_vertical == pytest.approx(UDL * LENGTH, rel=1e-12)
    assert result.reactions.fixed_moment == pytest.approx(UDL * LENGTH**2 / 2, rel=1e-12)
    assert result.max_abs_shear == pytest.approx(UDL * LENGTH, rel=1e-12)
    assert result.max_abs_moment == pytest.approx(UDL * LENGTH**2 / 2, rel=1e-12)
    assert result.max_deflection == pytest.approx(UDL * LENGTH**4 / (8 * ei), rel=1e-12)
