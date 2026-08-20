"""Deterministic statics, stress and deflection solver."""

from __future__ import annotations

from .checks import bending_stress, deflection_check, safety_factor, stress_check
from .deflection import deflection_at
from .loads import FullSpanUDL, PointLoad
from .models import BeamType, CalculationInput, CalculationResult, Reactions


def calculate_reactions(case: CalculationInput) -> Reactions:
    case.validate()
    length = case.beam.length
    total_force = 0.0
    total_moment_about_origin = 0.0
    for load in case.loads:
        if isinstance(load, PointLoad):
            total_force += load.magnitude
            total_moment_about_origin += load.magnitude * load.position
        elif isinstance(load, FullSpanUDL):
            resultant = load.magnitude * length
            total_force += resultant
            total_moment_about_origin += resultant * length / 2.0

    if case.beam.beam_type is BeamType.SIMPLY_SUPPORTED:
        right = total_moment_about_origin / length
        return Reactions(left_vertical=total_force - right, right_vertical=right)
    return Reactions(fixed_vertical=total_force, fixed_moment=total_moment_about_origin)


def _shear_and_moment_at(
    case: CalculationInput, reactions: Reactions, x: float
) -> tuple[float, float]:
    if case.beam.beam_type is BeamType.SIMPLY_SUPPORTED:
        shear = reactions.left_vertical
        moment = reactions.left_vertical * x
    else:
        shear = reactions.fixed_vertical
        moment = -reactions.fixed_moment + reactions.fixed_vertical * x

    for load in case.loads:
        if isinstance(load, PointLoad) and x >= load.position:
            shear -= load.magnitude
            moment -= load.magnitude * (x - load.position)
        elif isinstance(load, FullSpanUDL):
            shear -= load.magnitude * x
            moment -= load.magnitude * x**2 / 2.0
    return shear, moment


def _sample_positions(case: CalculationInput, sample_count: int) -> tuple[float, ...]:
    if sample_count < 3:
        raise ValueError("At least three sample points are required.")
    length = case.beam.length
    positions = {length * index / (sample_count - 1) for index in range(sample_count)}
    point_positions = sorted(
        load.position for load in case.loads if isinstance(load, PointLoad)
    )
    positions.update(point_positions)

    # Moment extrema occur where shear is zero. Add exact roots in each load
    # interval so maximum moment is not dependent on plotting resolution.
    udl = sum(load.magnitude for load in case.loads if isinstance(load, FullSpanUDL))
    boundaries = [0.0, *point_positions, length]
    if udl > 0:
        for left, right in zip(boundaries, boundaries[1:]):
            probe = (left + right) / 2.0
            shear_at_probe, _ = _shear_and_moment_at(case, calculate_reactions(case), probe)
            root = probe + shear_at_probe / udl
            if left <= root <= right:
                positions.add(root)
    return tuple(sorted(positions))


def solve(case: CalculationInput, sample_count: int = 2001) -> CalculationResult:
    """Solve a supported MVP load case using SI units throughout."""
    case.validate()
    props = case.section.properties()
    reactions = calculate_reactions(case)
    positions = _sample_positions(case, sample_count)
    shear_values: list[float] = []
    moment_values: list[float] = []
    deflection_values: list[float] = []
    rigidity = case.material.youngs_modulus * props.second_moment

    for x in positions:
        shear, moment = _shear_and_moment_at(case, reactions, x)
        shear_values.append(shear)
        moment_values.append(moment)
        deflection_values.append(
            deflection_at(case.beam.beam_type, case.beam.length, case.loads, x, rigidity)
        )

    max_shear = max(abs(value) for value in shear_values)
    max_moment = max(abs(value) for value in moment_values)
    max_deflection_index = max(
        range(len(deflection_values)), key=lambda index: abs(deflection_values[index])
    )
    max_deflection = abs(deflection_values[max_deflection_index])
    max_stress = bending_stress(max_moment, props.section_modulus)
    allowable_deflection = case.criterion.allowable(case.beam.length)

    return CalculationResult(
        input=case,
        section_properties=props,
        reactions=reactions,
        x=positions,
        shear=tuple(shear_values),
        moment=tuple(moment_values),
        deflection=tuple(deflection_values),
        max_abs_shear=max_shear,
        max_abs_moment=max_moment,
        max_bending_stress=max_stress,
        max_deflection=max_deflection,
        deflection_location=positions[max_deflection_index],
        factor_of_safety=safety_factor(case.material.yield_strength, max_stress),
        stress_check=stress_check(max_stress, case.material.yield_strength),
        deflection_check=deflection_check(max_deflection, allowable_deflection),
    )
