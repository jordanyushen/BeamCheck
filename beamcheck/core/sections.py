"""Cross-section models and elastic section properties."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Protocol


@dataclass(frozen=True)
class SectionProperties:
    area: float  # m^2
    second_moment: float  # m^4 about the centroidal bending axis
    extreme_fibre: float  # m
    section_modulus: float  # m^3


class Section(Protocol):
    name: str

    def properties(self) -> SectionProperties: ...

    def validate(self) -> None: ...


@dataclass(frozen=True)
class RectangularSection:
    width: float  # m
    height: float  # m, bending depth
    name: str = "Solid rectangular"

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Rectangular section width and height must be greater than zero.")

    def properties(self) -> SectionProperties:
        self.validate()
        area = self.width * self.height
        inertia = self.width * self.height**3 / 12.0
        c = self.height / 2.0
        return SectionProperties(area, inertia, c, inertia / c)


@dataclass(frozen=True)
class CircularSection:
    diameter: float  # m
    name: str = "Solid circular"

    def validate(self) -> None:
        if self.diameter <= 0:
            raise ValueError("Circular section diameter must be greater than zero.")

    def properties(self) -> SectionProperties:
        self.validate()
        area = pi * self.diameter**2 / 4.0
        inertia = pi * self.diameter**4 / 64.0
        c = self.diameter / 2.0
        return SectionProperties(area, inertia, c, inertia / c)


@dataclass(frozen=True)
class HollowRectangularSection:
    outer_width: float  # m
    outer_height: float  # m
    wall_thickness: float  # m
    name: str = "Rectangular hollow"

    def validate(self) -> None:
        if self.outer_width <= 0 or self.outer_height <= 0 or self.wall_thickness <= 0:
            raise ValueError("Hollow section dimensions and wall thickness must be greater than zero.")
        if 2 * self.wall_thickness >= min(self.outer_width, self.outer_height):
            raise ValueError("Wall thickness must leave positive inner width and height.")

    def properties(self) -> SectionProperties:
        self.validate()
        inner_width = self.outer_width - 2 * self.wall_thickness
        inner_height = self.outer_height - 2 * self.wall_thickness
        area = self.outer_width * self.outer_height - inner_width * inner_height
        inertia = (
            self.outer_width * self.outer_height**3 - inner_width * inner_height**3
        ) / 12.0
        c = self.outer_height / 2.0
        return SectionProperties(area, inertia, c, inertia / c)


@dataclass(frozen=True)
class SquareHollowSection(HollowRectangularSection):
    name: str = "Square hollow"

    def validate(self) -> None:
        super().validate()
        tolerance = 1e-12 * max(self.outer_width, self.outer_height, 1.0)
        if abs(self.outer_width - self.outer_height) > tolerance:
            raise ValueError("SHS outer width and outer height must be equal.")
