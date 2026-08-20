"""Simple non-code-certifying engineering checks."""

from __future__ import annotations

from math import inf

from .models import CheckResult


def bending_stress(moment: float, section_modulus: float) -> float:
    if section_modulus <= 0:
        raise ValueError("Section modulus must be greater than zero.")
    return abs(moment) / section_modulus


def safety_factor(yield_strength: float, stress: float) -> float:
    if yield_strength <= 0:
        raise ValueError("Yield strength must be greater than zero.")
    return inf if stress == 0 else yield_strength / stress


def stress_check(stress: float, yield_strength: float) -> CheckResult:
    return CheckResult(stress, yield_strength, stress <= yield_strength)


def deflection_check(deflection: float, allowable: float) -> CheckResult:
    return CheckResult(abs(deflection), allowable, abs(deflection) <= allowable)
