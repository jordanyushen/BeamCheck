"""Euler-Bernoulli elastic deflection functions.

Returned values are positive downward. Solutions assume a prismatic beam,
small deflection, linear elasticity and static loading.
"""

from __future__ import annotations

from .loads import FullSpanUDL, Load, PointLoad
from .models import BeamType


def point_load_deflection(
    beam_type: BeamType,
    length: float,
    load: PointLoad,
    x: float,
    flexural_rigidity: float,
) -> float:
    p = load.magnitude
    a = load.position
    if beam_type is BeamType.SIMPLY_SUPPORTED:
        b = length - a
        if x <= a:
            return p * b * x * (length**2 - b**2 - x**2) / (6 * length * flexural_rigidity)
        distance_from_right = length - x
        return (
            p
            * a
            * distance_from_right
            * (length**2 - a**2 - distance_from_right**2)
            / (6 * length * flexural_rigidity)
        )

    # Cantilever point load at arbitrary position. Beyond the load the beam
    # continues along the tangent because curvature is zero there.
    if x <= a:
        return p * x**2 * (3 * a - x) / (6 * flexural_rigidity)
    return p * a**2 * (3 * x - a) / (6 * flexural_rigidity)


def full_span_udl_deflection(
    beam_type: BeamType,
    length: float,
    load: FullSpanUDL,
    x: float,
    flexural_rigidity: float,
) -> float:
    w = load.magnitude
    if beam_type is BeamType.SIMPLY_SUPPORTED:
        return w * x * (length**3 - 2 * length * x**2 + x**3) / (24 * flexural_rigidity)
    return w * x**2 * (6 * length**2 - 4 * length * x + x**2) / (24 * flexural_rigidity)


def deflection_at(
    beam_type: BeamType,
    length: float,
    loads: tuple[Load, ...],
    x: float,
    flexural_rigidity: float,
) -> float:
    if flexural_rigidity <= 0:
        raise ValueError("Flexural rigidity must be greater than zero.")
    total = 0.0
    for load in loads:
        if isinstance(load, PointLoad):
            total += point_load_deflection(beam_type, length, load, x, flexural_rigidity)
        else:
            total += full_span_udl_deflection(beam_type, length, load, x, flexural_rigidity)
    return total
