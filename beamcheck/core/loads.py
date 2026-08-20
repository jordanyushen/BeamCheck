"""Load models. Positive magnitudes act downward."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PointLoad:
    magnitude: float  # N, downward positive
    position: float  # m from left/fixed origin

    def validate(self, beam_length: float) -> None:
        if self.magnitude < 0:
            raise ValueError("Point load magnitude cannot be negative.")
        if not 0 <= self.position <= beam_length:
            raise ValueError("Point load position must lie on the beam.")


@dataclass(frozen=True)
class FullSpanUDL:
    magnitude: float  # N/m, downward positive

    def validate(self, beam_length: float) -> None:
        if beam_length <= 0:
            raise ValueError("Beam length must be greater than zero.")
        if self.magnitude < 0:
            raise ValueError("UDL magnitude cannot be negative.")


Load = PointLoad | FullSpanUDL
