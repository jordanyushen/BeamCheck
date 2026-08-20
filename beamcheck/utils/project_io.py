"""Local JSON project persistence. Inputs are stored in SI and recalculated on open."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from beamcheck.core.loads import FullSpanUDL, PointLoad
from beamcheck.core.materials import Material
from beamcheck.core.models import Beam, BeamType, CalculationInput, DeflectionCriterion, ProjectInfo
from beamcheck.core.sections import CircularSection, HollowRectangularSection, RectangularSection, SquareHollowSection


def input_to_dict(case: CalculationInput) -> dict[str, Any]:
    if isinstance(case.section, SquareHollowSection):
        section = {"type": "shs", "outer_width": case.section.outer_width, "outer_height": case.section.outer_height, "wall_thickness": case.section.wall_thickness}
    elif isinstance(case.section, HollowRectangularSection):
        section = {"type": "rhs", "outer_width": case.section.outer_width, "outer_height": case.section.outer_height, "wall_thickness": case.section.wall_thickness}
    elif isinstance(case.section, RectangularSection):
        section = {"type": "rectangular", "width": case.section.width, "height": case.section.height}
    elif isinstance(case.section, CircularSection):
        section = {"type": "circular", "diameter": case.section.diameter}
    else:
        raise ValueError("Unsupported section type for project storage.")

    loads: list[dict[str, Any]] = []
    for load in case.loads:
        if isinstance(load, PointLoad):
            loads.append({"type": "point", "magnitude": load.magnitude, "position": load.position})
        elif isinstance(load, FullSpanUDL):
            loads.append({"type": "full_span_udl", "magnitude": load.magnitude})

    return {
        "format": "beamcheck-project",
        "version": 1,
        "project": {
            "project_name": case.project.project_name,
            "calculation_title": case.project.calculation_title,
            "engineer": case.project.engineer,
            "notes": case.project.notes,
        },
        "beam": {"type": case.beam.beam_type.value, "length": case.beam.length},
        "material": {
            "name": case.material.name,
            "youngs_modulus": case.material.youngs_modulus,
            "yield_strength": case.material.yield_strength,
            "density": case.material.density,
        },
        "section": section,
        "loads": loads,
        "criterion": {"ratio": case.criterion.ratio, "custom_allowable": case.criterion.custom_allowable},
    }


def input_from_dict(data: dict[str, Any]) -> CalculationInput:
    if data.get("format") != "beamcheck-project" or data.get("version") != 1:
        raise ValueError("This is not a supported BeamCheck project file.")
    project_data = data["project"]
    beam_data = data["beam"]
    material_data = data["material"]
    section_data = data["section"]
    criterion_data = data["criterion"]

    section_type = section_data["type"]
    if section_type == "rectangular":
        section = RectangularSection(section_data["width"], section_data["height"])
    elif section_type == "circular":
        section = CircularSection(section_data["diameter"])
    elif section_type == "rhs":
        section = HollowRectangularSection(section_data["outer_width"], section_data["outer_height"], section_data["wall_thickness"])
    elif section_type == "shs":
        section = SquareHollowSection(section_data["outer_width"], section_data["outer_height"], section_data["wall_thickness"])
    else:
        raise ValueError("Project contains an unsupported section type.")

    loads = []
    for load_data in data["loads"]:
        if load_data["type"] == "point":
            loads.append(PointLoad(load_data["magnitude"], load_data["position"]))
        elif load_data["type"] == "full_span_udl":
            loads.append(FullSpanUDL(load_data["magnitude"]))
        else:
            raise ValueError("Project contains an unsupported load type.")

    case = CalculationInput(
        beam=Beam(BeamType(beam_data["type"]), beam_data["length"]),
        material=Material(material_data["name"], material_data["youngs_modulus"], material_data["yield_strength"], material_data["density"]),
        section=section,
        loads=tuple(loads),
        criterion=DeflectionCriterion(criterion_data.get("ratio"), criterion_data.get("custom_allowable")),
        project=ProjectInfo(**project_data),
    )
    case.validate()
    return case


def save_project(case: CalculationInput, destination: str | Path) -> Path:
    path = Path(destination)
    path.write_text(json.dumps(input_to_dict(case), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_project(source: str | Path) -> CalculationInput:
    path = Path(source)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read project file: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Project file must contain a JSON object.")
    return input_from_dict(data)
