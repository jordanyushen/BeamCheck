"""Consistent engineering-value formatting."""

from __future__ import annotations


def engineering(value: float, unit: str, digits: int = 4) -> str:
    return f"{value:.{digits}g} {unit}"


def pass_fail(value: bool) -> str:
    return "PASS" if value else "FAIL"
