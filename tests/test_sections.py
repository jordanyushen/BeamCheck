from __future__ import annotations

from math import pi

import pytest

from beamcheck.core.sections import (
    CircularSection,
    HollowRectangularSection,
    RectangularSection,
    SquareHollowSection,
)


def test_rectangular_section_properties() -> None:
    section = RectangularSection(0.1, 0.2).properties()
    assert section.area == pytest.approx(0.02)
    assert section.second_moment == pytest.approx(0.1 * 0.2**3 / 12)
    assert section.extreme_fibre == pytest.approx(0.1)
    assert section.section_modulus == pytest.approx(0.1 * 0.2**2 / 6)


def test_circular_section_properties() -> None:
    section = CircularSection(0.1).properties()
    assert section.area == pytest.approx(pi * 0.1**2 / 4)
    assert section.second_moment == pytest.approx(pi * 0.1**4 / 64)
    assert section.section_modulus == pytest.approx(pi * 0.1**3 / 32)


def test_hollow_section_and_invalid_geometry() -> None:
    props = HollowRectangularSection(0.1, 0.2, 0.005).properties()
    assert props.area == pytest.approx(0.1 * 0.2 - 0.09 * 0.19)
    with pytest.raises(ValueError, match="positive inner"):
        HollowRectangularSection(0.1, 0.2, 0.05).properties()
    with pytest.raises(ValueError, match="must be equal"):
        SquareHollowSection(0.1, 0.11, 0.005).properties()
