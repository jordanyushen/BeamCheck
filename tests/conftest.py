from __future__ import annotations

import pytest

from beamcheck.core.materials import Material
from beamcheck.core.sections import RectangularSection


@pytest.fixture
def steel() -> Material:
    return Material("Test steel", 200e9, 250e6, 7850)


@pytest.fixture
def rectangle() -> RectangularSection:
    return RectangularSection(width=0.1, height=0.2)
