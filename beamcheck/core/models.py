"""Public input and output models for the solver."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .loads import Load
from .materials import Material
from .sections import Section, SectionProperties


class BeamType(str, Enum):
    SIMPLY_SUPPORTED = "Simply supported"
    CANTILEVER = "Cantilever"


@dataclass(frozen=True)
class ProjectInfo:
    project_name: str = "Untitled project"
    calculation_title: str = "Beam calculation"
    engineer: str = ""
    notes: str = ""


@dataclass(frozen=True)
class Beam:
    beam_type: BeamType
    length: float  # m

    def validate(self) -> None:
        if self.length <= 0:
            raise ValueError("Beam length must be greater than zero.")


@dataclass(frozen=True)
class DeflectionCriterion:
    ratio: float | None = 250.0
    custom_allowable: float | None = None  # m

    def allowable(self, beam_length: float) -> float:
        if self.custom_allowable is not None:
            if self.custom_allowable <= 0:
                raise ValueError("Custom allowable deflection must be greater than zero.")
            return self.custom_allowable
        if self.ratio is None or self.ratio <= 0:
            raise ValueError("Deflection ratio must be greater than zero.")
        return beam_length / self.ratio


@dataclass(frozen=True)
class CalculationInput:
    beam: Beam
    material: Material
    section: Section
    loads: tuple[Load, ...]
    criterion: DeflectionCriterion = field(default_factory=DeflectionCriterion)
    project: ProjectInfo = field(default_factory=ProjectInfo)

    def validate(self) -> None:
        self.beam.validate()
        self.material.validate()
        self.section.validate()
        if not self.loads:
            raise ValueError("At least one load is required.")
        for load in self.loads:
            load.validate(self.beam.length)
        self.criterion.allowable(self.beam.length)


@dataclass(frozen=True)
class Reactions:
    left_vertical: float = 0.0
    right_vertical: float = 0.0
    fixed_vertical: float = 0.0
    fixed_moment: float = 0.0


@dataclass(frozen=True)
class CheckResult:
    calculated: float
    allowable: float
    passes: bool


@dataclass(frozen=True)
class CalculationResult:
    input: CalculationInput
    section_properties: SectionProperties
    reactions: Reactions
    x: tuple[float, ...]
    shear: tuple[float, ...]
    moment: tuple[float, ...]
    deflection: tuple[float, ...]
    max_abs_shear: float
    max_abs_moment: float
    max_bending_stress: float
    max_deflection: float
    deflection_location: float
    factor_of_safety: float
    stress_check: CheckResult
    deflection_check: CheckResult
