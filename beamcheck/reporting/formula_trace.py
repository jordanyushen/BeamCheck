"""Deterministic, solver-connected calculation trail."""

from __future__ import annotations

from beamcheck.core.loads import FullSpanUDL, PointLoad
from beamcheck.core.models import BeamType, CalculationResult
from beamcheck.utils.i18n import translate


def _status(value: bool, language: str) -> str:
    return translate(language, "pass" if value else "fail")


def build_formula_trace(result: CalculationResult, language: str = "en") -> str:
    """Return a human-readable trace without generated or duplicated results."""
    case = result.input
    length = case.beam.length
    props = result.section_properties
    lines = [
        translate(language, "trace_section_properties"),
        f"I = {props.second_moment:.6g} m^4",
        f"c = {props.extreme_fibre:.6g} m",
        "Z = I / c",
        f"Z = {props.second_moment:.6g} / {props.extreme_fibre:.6g}",
        f"Z = {props.section_modulus:.6g} m^3",
        "",
        translate(language, "trace_reactions"),
    ]

    if case.beam.beam_type is BeamType.SIMPLY_SUPPORTED:
        lines.extend(
            [
                "ΣM_A = 0: R_B L = Σ(P a) + Σ(w L · L/2)",
                f"R_A = {result.reactions.left_vertical / 1000:.6g} kN",
                f"R_B = {result.reactions.right_vertical / 1000:.6g} kN",
            ]
        )
    else:
        lines.extend(
            [
                "V_fixed = ΣP + Σ(w L)",
                "M_fixed = Σ(P a) + Σ(w L²/2)",
                f"V_fixed = {result.reactions.fixed_vertical / 1000:.6g} kN",
                f"M_fixed = {result.reactions.fixed_moment / 1000:.6g} kN·m",
            ]
        )

    lines.extend(["", translate(language, "trace_load_result")])
    if len(case.loads) == 1:
        load = case.loads[0]
        if isinstance(load, FullSpanUDL):
            w = load.magnitude / 1000
            if case.beam.beam_type is BeamType.SIMPLY_SUPPORTED:
                lines.extend(
                    [
                        "M_max = w L² / 8",
                        f"M_max = {w:.6g} × {length:.6g}² / 8",
                        f"M_max = {result.max_abs_moment / 1000:.6g} kN·m",
                        "δ_max = 5 w L⁴ / (384 E I)",
                    ]
                )
            else:
                lines.extend(
                    [
                        "M_max = w L² / 2",
                        f"M_max = {w:.6g} × {length:.6g}² / 2",
                        f"M_max = {result.max_abs_moment / 1000:.6g} kN·m",
                        "δ_max = w L⁴ / (8 E I)",
                    ]
                )
        elif isinstance(load, PointLoad):
            p = load.magnitude / 1000
            if case.beam.beam_type is BeamType.SIMPLY_SUPPORTED and abs(load.position - length / 2) < 1e-12:
                lines.extend(
                    [
                        translate(language, "trace_central_point"),
                        f"M_max = {p:.6g} × {length:.6g} / 4",
                        f"M_max = {result.max_abs_moment / 1000:.6g} kN·m",
                        "δ_max = P L³ / (48 E I)",
                    ]
                )
            elif case.beam.beam_type is BeamType.CANTILEVER and abs(load.position - length) < 1e-12:
                lines.extend(
                    [
                        translate(language, "trace_free_end_point"),
                        f"M_max = {p:.6g} × {length:.6g}",
                        f"M_max = {result.max_abs_moment / 1000:.6g} kN·m",
                        "δ_max = P L³ / (3 E I)",
                    ]
                )
            else:
                lines.extend(
                    [
                        translate(language, "trace_arbitrary_point"),
                        f"M_max = {result.max_abs_moment / 1000:.6g} kN·m",
                    ]
                )
    else:
        lines.extend(
            [
                translate(language, "trace_superposition"),
                f"M_max = {result.max_abs_moment / 1000:.6g} kN·m",
            ]
        )

    lines.extend(
        [
            f"δ_max = {result.max_deflection * 1000:.6g} mm — {translate(language, 'trace_at', x=result.deflection_location)}",
            "",
            translate(language, "trace_bending_stress"),
            "σ_max = M_max / Z",
            f"σ_max = {result.max_abs_moment:.6g} / {props.section_modulus:.6g}",
            f"σ_max = {result.max_bending_stress / 1e6:.6g} MPa",
            f"f_y = {case.material.yield_strength / 1e6:.6g} MPa",
            f"FoS = f_y / σ_max = {result.factor_of_safety:.4g}",
            translate(language, "trace_stress_check", status=_status(result.stress_check.passes, language)),
            "",
            translate(language, "trace_deflection_check"),
            f"{translate(language, 'trace_calculated')} = {result.max_deflection * 1000:.6g} mm",
            f"{translate(language, 'trace_allowable')} = {result.deflection_check.allowable * 1000:.6g} mm",
            translate(language, "trace_deflection_status", status=_status(result.deflection_check.passes, language)),
        ]
    )
    return "\n".join(lines)
