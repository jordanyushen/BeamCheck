"""Strict loading of versioned verification data assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from beamcheck.core.loads import FullSpanUDL, PointLoad
from beamcheck.core.materials import Material
from beamcheck.core.models import (
    Beam,
    BeamType,
    CalculationInput,
    DeflectionCriterion,
    ProjectInfo,
)
from beamcheck.core.sections import (
    CircularSection,
    HollowRectangularSection,
    RectangularSection,
    SquareHollowSection,
)

from .models import (
    ExpectedQuantity,
    Tolerance,
    ToleranceType,
    VerificationCase,
    VerificationStatus,
)


DATASET_SCHEMA_VERSION = "1.0"
DEFAULT_CORPUS_ROOT = Path(__file__).resolve().parents[2] / "verification"


class VerificationDataError(ValueError):
    """Raised when corpus data is malformed or semantically inconsistent."""


def _reject_json_constant(token: str) -> None:
    raise VerificationDataError(f"Non-finite JSON number is not allowed: {token}")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant
        )
    except VerificationDataError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationDataError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationDataError(f"Top-level JSON value must be an object: {path}")
    return value


def _validate_schema(data: dict[str, Any], schema_path: Path, data_path: Path) -> None:
    schema = _read_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(data),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise VerificationDataError(
            f"Schema validation failed for {data_path} at {location}: {error.message}"
        )


def _build_input(data: dict[str, Any], case_id: str, title: str) -> CalculationInput:
    beam_data = data["beam"]
    beam_type = {
        "simply_supported": BeamType.SIMPLY_SUPPORTED,
        "cantilever": BeamType.CANTILEVER,
    }[beam_data["type"]]
    beam = Beam(beam_type=beam_type, length=float(beam_data["length_m"]))

    material_data = data["material"]
    material = Material(
        name=material_data["name"],
        youngs_modulus=float(material_data["youngs_modulus_pa"]),
        yield_strength=float(material_data["yield_strength_pa"]),
        density=float(material_data["density_kg_m3"]),
    )

    section_data = data["section"]
    section_type = section_data["type"]
    if section_type == "rectangular":
        section = RectangularSection(
            width=float(section_data["width_m"]),
            height=float(section_data["height_m"]),
        )
    elif section_type == "circular":
        section = CircularSection(diameter=float(section_data["diameter_m"]))
    elif section_type == "rectangular_hollow":
        section = HollowRectangularSection(
            outer_width=float(section_data["outer_width_m"]),
            outer_height=float(section_data["outer_height_m"]),
            wall_thickness=float(section_data["wall_thickness_m"]),
        )
    else:
        outer_size = float(section_data["outer_size_m"])
        section = SquareHollowSection(
            outer_width=outer_size,
            outer_height=outer_size,
            wall_thickness=float(section_data["wall_thickness_m"]),
        )

    loads = []
    for load_data in data["loads"]:
        if load_data["type"] == "point":
            loads.append(
                PointLoad(
                    magnitude=float(load_data["magnitude_n"]),
                    position=float(load_data["position_m"]),
                )
            )
        else:
            loads.append(FullSpanUDL(magnitude=float(load_data["magnitude_n_per_m"])))

    criterion_data = data["criterion"]
    if criterion_data["type"] == "span_ratio":
        criterion = DeflectionCriterion(ratio=float(criterion_data["ratio"]))
    else:
        criterion = DeflectionCriterion(
            ratio=None,
            custom_allowable=float(criterion_data["allowable_deflection_m"]),
        )

    calculation_input = CalculationInput(
        beam=beam,
        material=material,
        section=section,
        loads=tuple(loads),
        criterion=criterion,
        project=ProjectInfo(project_name=case_id, calculation_title=title),
    )
    calculation_input.validate()
    return calculation_input


def load_case(case_directory: Path, corpus_root: Path = DEFAULT_CORPUS_ROOT) -> VerificationCase:
    case_path = case_directory / "case.json"
    expected_path = case_directory / "expected.json"
    reference_path = case_directory / "reference.md"
    schema_root = corpus_root / "schema"

    case_data = _read_json(case_path)
    expected_data = _read_json(expected_path)
    _validate_schema(case_data, schema_root / "verification_case.schema.json", case_path)
    _validate_schema(
        expected_data, schema_root / "verification_result.schema.json", expected_path
    )

    try:
        reference_text = reference_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise VerificationDataError(f"Cannot read reference file {reference_path}: {exc}") from exc

    if case_data["schema_version"] != DATASET_SCHEMA_VERSION:
        raise VerificationDataError(
            f"Unsupported case schema version in {case_path}: {case_data['schema_version']}"
        )
    if expected_data["schema_version"] != DATASET_SCHEMA_VERSION:
        raise VerificationDataError(
            f"Unsupported expected schema version in {expected_path}: "
            f"{expected_data['schema_version']}"
        )
    if case_data["case_id"] != expected_data["case_id"]:
        raise VerificationDataError(
            f"case_id mismatch between {case_path} and {expected_path}."
        )
    if case_data["case_id"] != case_directory.name:
        raise VerificationDataError(
            f"case_id {case_data['case_id']} must match directory {case_directory.name}."
        )
    if case_data["expected_reference_id"] not in reference_text:
        raise VerificationDataError(
            f"Reference file for {case_data['case_id']} must contain expected_reference_id "
            f"{case_data['expected_reference_id']}."
        )

    try:
        status = VerificationStatus(case_data["status"])
        expected = {
            name: ExpectedQuantity(
                value=float(quantity["value"]),
                tolerance=Tolerance(
                    type=ToleranceType(quantity["tolerance"]["type"]),
                    value=float(quantity["tolerance"]["value"]),
                ),
            )
            for name, quantity in expected_data["expected"].items()
        }
        calculation_input = _build_input(
            case_data, case_data["case_id"], case_data["title"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise VerificationDataError(
            f"Invalid verification semantics in {case_directory}: {exc}"
        ) from exc

    if status is VerificationStatus.VERIFIED:
        if not expected:
            raise VerificationDataError(
                f"Verified case {case_data['case_id']} must declare expected quantities."
            )
        if "STATUS: OWNER_REFERENCE_REQUIRED" in reference_text:
            raise VerificationDataError(
                f"Verified case {case_data['case_id']} cannot use an owner-reference placeholder."
            )
        if "OWNER-REQUIRED" in case_data["expected_reference_id"]:
            raise VerificationDataError(
                f"Verified case {case_data['case_id']} must use a reviewed reference ID."
            )

    return VerificationCase(
        schema_version=case_data["schema_version"],
        case_id=case_data["case_id"],
        title=case_data["title"],
        status=status,
        expected_reference_id=case_data["expected_reference_id"],
        calculation_input=calculation_input,
        expected=expected,
        case_directory=case_directory,
        reference_text=reference_text,
    )


def load_corpus(corpus_root: Path = DEFAULT_CORPUS_ROOT) -> tuple[VerificationCase, ...]:
    cases_root = corpus_root / "cases"
    if not cases_root.is_dir():
        raise VerificationDataError(f"Verification cases directory does not exist: {cases_root}")
    case_directories = sorted(
        path for path in cases_root.iterdir() if path.is_dir() and path.name.startswith("BC-")
    )
    if not case_directories:
        raise VerificationDataError(f"No verification cases found in {cases_root}")
    cases = tuple(load_case(path, corpus_root) for path in case_directories)
    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise VerificationDataError("Verification corpus contains duplicate case IDs.")
    return cases
