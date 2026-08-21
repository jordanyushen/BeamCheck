"""Compare solver results with independently supplied expected quantities."""

from __future__ import annotations

from collections.abc import Callable
from math import inf, isfinite

from beamcheck.core.models import CalculationResult

from .models import QuantityComparison, ToleranceType, VerificationCase


QuantityAccessor = Callable[[CalculationResult], float]


QUANTITY_ACCESSORS: dict[str, QuantityAccessor] = {
    "left_reaction_n": lambda result: result.reactions.left_vertical,
    "right_reaction_n": lambda result: result.reactions.right_vertical,
    "fixed_vertical_n": lambda result: result.reactions.fixed_vertical,
    "fixed_moment_nm": lambda result: result.reactions.fixed_moment,
    "max_shear_n": lambda result: result.max_abs_shear,
    "max_moment_nm": lambda result: result.max_abs_moment,
    "max_bending_stress_pa": lambda result: result.max_bending_stress,
    "max_deflection_m": lambda result: result.max_deflection,
    "deflection_location_m": lambda result: result.deflection_location,
    "factor_of_safety": lambda result: result.factor_of_safety,
    "allowable_deflection_m": lambda result: result.deflection_check.allowable,
}


def compare_case(
    case: VerificationCase, result: CalculationResult
) -> tuple[QuantityComparison, ...]:
    comparisons: list[QuantityComparison] = []
    for quantity, expected in case.expected.items():
        try:
            actual = float(QUANTITY_ACCESSORS[quantity](result))
        except KeyError as exc:
            raise ValueError(f"Unsupported expected quantity: {quantity}") from exc
        if not isfinite(actual):
            raise ValueError(f"Solver produced a non-finite value for {quantity}.")

        absolute_difference = abs(actual - expected.value)
        relative_difference = (
            absolute_difference / abs(expected.value) if expected.value != 0 else inf
        )
        if expected.tolerance.type is ToleranceType.ABSOLUTE:
            passed = absolute_difference <= expected.tolerance.value
        else:
            passed = relative_difference <= expected.tolerance.value
        comparisons.append(
            QuantityComparison(
                case_id=case.case_id,
                quantity=quantity,
                expected=expected.value,
                actual=actual,
                tolerance=expected.tolerance,
                absolute_difference=absolute_difference,
                relative_difference=relative_difference,
                passed=passed,
            )
        )
    return tuple(comparisons)
