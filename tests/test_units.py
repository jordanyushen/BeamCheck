from __future__ import annotations

import pytest

from beamcheck.core.units import (
    UnitError,
    force_to_si,
    from_si,
    length_to_si,
    line_load_to_si,
    stress_to_si,
)


def test_engineering_units_convert_to_si() -> None:
    assert length_to_si(2500, "mm") == pytest.approx(2.5)
    assert force_to_si(3.5, "kN") == pytest.approx(3500)
    assert line_load_to_si(2.0, "N/mm") == pytest.approx(2000)
    assert stress_to_si(355, "MPa") == pytest.approx(355e6)
    assert from_si(2.52e3, "kN·m") == pytest.approx(2.52)


def test_unknown_unit_is_rejected() -> None:
    with pytest.raises(UnitError):
        length_to_si(1, "inch")
