"""Material models and built-in engineering presets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    name: str
    youngs_modulus: float  # Pa
    yield_strength: float  # Pa
    density: float  # kg/m^3

    def validate(self) -> None:
        if self.youngs_modulus <= 0:
            raise ValueError("Young's modulus must be greater than zero.")
        if self.yield_strength <= 0:
            raise ValueError("Yield strength must be greater than zero.")
        if self.density <= 0:
            raise ValueError("Density must be greater than zero.")


MATERIAL_PRESETS: dict[str, Material] = {
    "S235": Material("S235 structural steel", 210e9, 235e6, 7850.0),
    "S275": Material("S275 structural steel", 210e9, 275e6, 7850.0),
    "S355": Material("S355 structural steel", 210e9, 355e6, 7850.0),
    "Aluminium": Material("Generic aluminium alloy", 69e9, 250e6, 2700.0),
}


def get_material(name: str) -> Material:
    try:
        return MATERIAL_PRESETS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown material preset: {name}") from exc
