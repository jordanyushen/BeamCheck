from __future__ import annotations

import io
import json
import shutil
from dataclasses import replace

import pytest
from jsonschema import Draft202012Validator

from beamcheck.core.solver import solve
from beamcheck.verification.compare import compare_case
from beamcheck.verification.loader import (
    DEFAULT_CORPUS_ROOT,
    VerificationDataError,
    load_corpus,
)
from beamcheck.verification.models import (
    ExpectedQuantity,
    Tolerance,
    ToleranceType,
    VerificationStatus,
)
from beamcheck.verification.runner import run_verification


def _synthetic_verified_corpus(tmp_path, expected_moment: float):
    corpus = tmp_path / "verification"
    shutil.copytree(DEFAULT_CORPUS_ROOT, corpus)
    case_directory = corpus / "cases" / "BC-0001"
    case_path = case_directory / "case.json"
    case_data = json.loads(case_path.read_text(encoding="utf-8"))
    case_data["status"] = "verified"
    case_data["expected_reference_id"] = "REF-SYNTHETIC-UNIT-TEST"
    case_path.write_text(json.dumps(case_data), encoding="utf-8")
    expected_path = case_directory / "expected.json"
    expected_data = json.loads(expected_path.read_text(encoding="utf-8"))
    expected_data["expected"] = {
        "max_moment_nm": {
            "value": expected_moment,
            "tolerance": {"type": "absolute", "value": 0.0},
        }
    }
    expected_path.write_text(json.dumps(expected_data), encoding="utf-8")
    reference_path = case_directory / "reference.md"
    reference_path.write_text(
        "# Synthetic unit-test reference\n\n"
        "Reference ID: REF-SYNTHETIC-UNIT-TEST\n\n"
        "This temporary file tests runner behavior and is not corpus evidence.\n",
        encoding="utf-8",
    )
    return corpus


def test_versioned_corpus_is_loadable_and_drafts_are_explicit() -> None:
    cases = load_corpus()
    assert [case.case_id for case in cases] == [
        "BC-0001",
        "BC-0002",
        "BC-0003",
        "BC-0004",
    ]
    assert all(case.status is VerificationStatus.DRAFT for case in cases)
    assert all(not case.expected for case in cases)
    assert all("STATUS: OWNER_REFERENCE_REQUIRED" in case.reference_text for case in cases)


def test_corpus_schemas_are_valid_draft_2020_12_documents() -> None:
    for schema_path in sorted((DEFAULT_CORPUS_ROOT / "schema").glob("*.json")):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_all_verified_corpus_cases_use_the_production_solver() -> None:
    verified_cases = [
        case for case in load_corpus() if case.status is VerificationStatus.VERIFIED
    ]
    failures: list[str] = []
    for case in verified_cases:
        comparisons = compare_case(case, solve(case.calculation_input))
        failures.extend(
            comparison.failure_message()
            for comparison in comparisons
            if not comparison.passed
        )
    assert not failures, "\n".join(failures)


def test_runner_reports_drafts_without_counting_them_as_verified() -> None:
    output = io.StringIO()
    summary = run_verification(stream=output)
    assert summary.discovered == 4
    assert summary.verified == 0
    assert summary.draft == 4
    assert summary.passed == 0
    assert summary.failed == 0
    assert summary.exit_code == 0
    assert "Verified passed: 0/0" in output.getvalue()
    assert "SKIP BC-0001 - owner reference required" in output.getvalue()


def test_verified_status_rejects_empty_expected_data(tmp_path) -> None:
    corpus = tmp_path / "verification"
    shutil.copytree(DEFAULT_CORPUS_ROOT, corpus)
    case_path = corpus / "cases" / "BC-0001" / "case.json"
    data = json.loads(case_path.read_text(encoding="utf-8"))
    data["status"] = "verified"
    case_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(VerificationDataError, match="must declare expected quantities"):
        load_corpus(corpus)


def test_verified_status_rejects_owner_reference_placeholder(tmp_path) -> None:
    corpus = tmp_path / "verification"
    shutil.copytree(DEFAULT_CORPUS_ROOT, corpus)
    case_path = corpus / "cases" / "BC-0001" / "case.json"
    case_data = json.loads(case_path.read_text(encoding="utf-8"))
    case_data["status"] = "verified"
    case_path.write_text(json.dumps(case_data), encoding="utf-8")
    expected_path = corpus / "cases" / "BC-0001" / "expected.json"
    expected_data = json.loads(expected_path.read_text(encoding="utf-8"))
    expected_data["expected"] = {
        "max_moment_nm": {
            "value": 10000.0,
            "tolerance": {"type": "relative", "value": 1e-10},
        }
    }
    expected_path.write_text(json.dumps(expected_data), encoding="utf-8")

    with pytest.raises(VerificationDataError, match="owner-reference placeholder"):
        load_corpus(corpus)


def test_loader_rejects_non_finite_json_numbers(tmp_path) -> None:
    corpus = tmp_path / "verification"
    shutil.copytree(DEFAULT_CORPUS_ROOT, corpus)
    case_path = corpus / "cases" / "BC-0001" / "case.json"
    text = case_path.read_text(encoding="utf-8").replace('"length_m": 4.0', '"length_m": NaN')
    case_path.write_text(text, encoding="utf-8")

    with pytest.raises(VerificationDataError, match="Non-finite JSON number"):
        load_corpus(corpus)


def test_comparison_failure_contains_auditable_details() -> None:
    draft = load_corpus()[0]
    result = solve(draft.calculation_input)
    synthetic = replace(
        draft,
        status=VerificationStatus.VERIFIED,
        expected={
            "max_moment_nm": ExpectedQuantity(
                value=result.max_abs_moment + 1.0,
                tolerance=Tolerance(ToleranceType.ABSOLUTE, 0.0),
            )
        },
    )
    comparison = compare_case(synthetic, result)[0]

    assert not comparison.passed
    message = comparison.failure_message()
    assert "BC-0001" in message
    assert "max_moment_nm" in message
    assert "expected=" in message
    assert "actual=" in message
    assert "tolerance=absolute" in message
    assert "absolute_difference=" in message
    assert "relative_difference=" in message


def test_runner_returns_nonzero_when_verified_quantity_exceeds_tolerance(tmp_path) -> None:
    corpus = _synthetic_verified_corpus(tmp_path, expected_moment=9999.0)

    output = io.StringIO()
    summary = run_verification(corpus, output)

    assert summary.verified == 1
    assert summary.failed == 1
    assert summary.exit_code == 1
    assert "FAIL BC-0001" in output.getvalue()
    assert "expected=" in output.getvalue()
    assert "actual=" in output.getvalue()


def test_runner_passes_a_synthetic_verified_case(tmp_path) -> None:
    corpus = _synthetic_verified_corpus(tmp_path, expected_moment=10000.0)

    output = io.StringIO()
    summary = run_verification(corpus, output)

    assert summary.verified == 1
    assert summary.passed == 1
    assert summary.failed == 0
    assert summary.exit_code == 0
    assert "PASS BC-0001" in output.getvalue()
    assert "Verified passed: 1/1" in output.getvalue()
