"""Command-line runner for the versioned verification corpus."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TextIO

from beamcheck.core.solver import solve

from .compare import compare_case
from .loader import DEFAULT_CORPUS_ROOT, VerificationDataError, load_corpus
from .models import CaseRunResult, VerificationStatus, VerificationSummary


def run_verification(
    corpus_root: Path = DEFAULT_CORPUS_ROOT, stream: TextIO = sys.stdout
) -> VerificationSummary:
    cases = load_corpus(corpus_root)
    verified = sum(case.status is VerificationStatus.VERIFIED for case in cases)
    draft = len(cases) - verified
    results: list[CaseRunResult] = []

    print("BeamCheck Verification", file=stream)
    print(file=stream)
    print(f"Cases discovered: {len(cases)}", file=stream)
    print(f"Verified cases: {verified}", file=stream)
    print(f"Draft/unreferenced: {draft}", file=stream)
    print(file=stream)

    passed = 0
    failed = 0
    for case in cases:
        if case.status is VerificationStatus.DRAFT:
            reason = "owner reference required"
            print(f"SKIP {case.case_id} - {reason}", file=stream)
            results.append(CaseRunResult(case.case_id, "SKIP", reason=reason))
            continue
        try:
            comparisons = compare_case(case, solve(case.calculation_input))
            failures = tuple(comparison for comparison in comparisons if not comparison.passed)
            if failures:
                failed += 1
                print(f"FAIL {case.case_id}", file=stream)
                for failure in failures:
                    print(f"  {failure.failure_message()}", file=stream)
                results.append(
                    CaseRunResult(
                        case.case_id,
                        "FAIL",
                        comparisons=comparisons,
                        reason="one or more quantities exceeded tolerance",
                    )
                )
            else:
                passed += 1
                print(f"PASS {case.case_id}", file=stream)
                results.append(
                    CaseRunResult(case.case_id, "PASS", comparisons=comparisons)
                )
        except Exception as exc:
            failed += 1
            reason = f"{type(exc).__name__}: {exc}"
            print(f"FAIL {case.case_id} - {reason}", file=stream)
            results.append(CaseRunResult(case.case_id, "FAIL", reason=reason))

    print(file=stream)
    print(f"Verified passed: {passed}/{verified}", file=stream)
    if failed:
        print(f"Verified failed: {failed}", file=stream)
    return VerificationSummary(
        discovered=len(cases),
        verified=verified,
        draft=draft,
        passed=passed,
        failed=failed,
        results=tuple(results),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the BeamCheck verification corpus.")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS_ROOT,
        help="Path to the verification corpus root.",
    )
    args = parser.parse_args(argv)
    try:
        return run_verification(args.corpus).exit_code
    except VerificationDataError as exc:
        print(f"Verification data error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
