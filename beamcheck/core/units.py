"""Unit conversion helpers.

All solver inputs are converted to SI before they reach the engineering logic.
"""

from __future__ import annotations

from dataclasses import dataclass


class UnitError(ValueError):
    """Raised when a unit is unknown or incompatible."""


_LENGTH_TO_M = {"m": 1.0, "mm": 1e-3}
_FORCE_TO_N = {"N": 1.0, "kN": 1e3}
_LINE_LOAD_TO_N_PER_M = {"N/m": 1.0, "kN/m": 1e3, "N/mm": 1e3}
_STRESS_TO_PA = {"Pa": 1.0, "MPa": 1e6, "GPa": 1e9}
_MOMENT_TO_NM = {"N·m": 1.0, "N*m": 1.0, "kN·m": 1e3, "kN*m": 1e3}


def _convert(value: float, unit: str, table: dict[str, float], quantity: str) -> float:
    try:
        return float(value) * table[unit]
    except KeyError as exc:
        raise UnitError(f"Unsupported {quantity} unit: {unit}") from exc


def length_to_si(value: float, unit: str) -> float:
    return _convert(value, unit, _LENGTH_TO_M, "length")


def force_to_si(value: float, unit: str) -> float:
    return _convert(value, unit, _FORCE_TO_N, "force")


def line_load_to_si(value: float, unit: str) -> float:
    return _convert(value, unit, _LINE_LOAD_TO_N_PER_M, "line load")


def stress_to_si(value: float, unit: str) -> float:
    return _convert(value, unit, _STRESS_TO_PA, "stress")


def moment_to_si(value: float, unit: str) -> float:
    return _convert(value, unit, _MOMENT_TO_NM, "moment")


def from_si(value: float, unit: str) -> float:
    """Convert an SI value to a supported display unit."""
    all_units = {
        **_LENGTH_TO_M,
        **_FORCE_TO_N,
        **_LINE_LOAD_TO_N_PER_M,
        **_STRESS_TO_PA,
        **_MOMENT_TO_NM,
    }
    try:
        return float(value) / all_units[unit]
    except KeyError as exc:
        raise UnitError(f"Unsupported display unit: {unit}") from exc


@dataclass(frozen=True)
class DisplayUnits:
    length: str = "mm"
    beam_length: str = "m"
    force: str = "kN"
    line_load: str = "kN/m"
    moment: str = "kN·m"
    stress: str = "MPa"
    modulus: str = "GPa"
