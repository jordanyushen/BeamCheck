"""Typed models for verification cases and comparison results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from pathlib import Path

from beamcheck.core.models import CalculationInput


class VerificationStatus(str, Enum):
    DRAFT = "draft"
    VERIFIED = "verified"


class ToleranceType(str, Enum):
    ABSOLUTE = "absolute"
    RELATIVE = "relative"


@dataclass(frozen=True)
class Tolerance:
    type: ToleranceType
    value: float

    def __post_init__(self) -> None:
        if not isfinite(self.value) or self.value < 0:
            raise ValueError("Tolerance must be a finite, non-negative number.")


@dataclass(frozen=True)
class ExpectedQuantity:
    value: float
    tolerance: Tolerance

    def __post_init__(self) -> None:
        if not isfinite(self.value):
            raise ValueError("Expected values must be finite numbers.")
        if self.value == 0 and self.tolerance.type is ToleranceType.RELATIVE:
            raise ValueError("An expected value of zero requires an absolute tolerance.")


@dataclass(frozen=True)
class VerificationCase:
    schema_version: str
    case_id: str
    title: str
    status: VerificationStatus
    expected_reference_id: str
    calculation_input: CalculationInput
    expected: dict[str, ExpectedQuantity]
    case_directory: Path
    reference_text: str


@dataclass(frozen=True)
class QuantityComparison:
    case_id: str
    quantity: str
    expected: float
    actual: float
    tolerance: Tolerance
    absolute_difference: float
    relative_difference: float
    passed: bool

    def failure_message(self) -> str:
        return (
            f"{self.case_id} {self.quantity}: expected={self.expected:.17g}, "
            f"actual={self.actual:.17g}, tolerance={self.tolerance.type.value} "
            f"{self.tolerance.value:.17g}, absolute_difference={self.absolute_difference:.17g}, "
            f"relative_difference={self.relative_difference:.17g}"
        )


@dataclass(frozen=True)
class CaseRunResult:
    case_id: str
    status: str
    comparisons: tuple[QuantityComparison, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class VerificationSummary:
    discovered: int
    verified: int
    draft: int
    passed: int
    failed: int
    results: tuple[CaseRunResult, ...]

    @property
    def exit_code(self) -> int:
        return 1 if self.failed else 0
