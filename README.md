# BeamCheck

BeamCheck is a local-first Windows desktop engineering calculation aid for basic beam strength and deflection checks. It is faster to set up than a spreadsheet, keeps a transparent calculation trail, and deliberately stays smaller in scope than finite-element software.

> BeamCheck is an engineering calculation aid. Results must be reviewed by a qualified user and checked against applicable standards, design requirements, and project conditions.

## MVP features

- Simply supported and cantilever beams
- A single point load, a full-span uniformly distributed load, or both together
- Solid rectangular, solid circular, RHS, and SHS sections
- S235, S275, S355, generic aluminium, and custom material properties
- English, French, German, and Simplified Chinese, switchable immediately under Settings → Language
- Reactions, shear, bending moment, elastic bending stress, deflection, and factor of safety
- Stress PASS/FAIL and L/180, L/250, L/300, L/360, or custom deflection checks
- Beam schematic, shear-force diagram, bending-moment diagram, and deflection curve
- Deterministic formula trace connected to the solver output
- Offline PDF calculation reports
- Local `.beamcheck.json` project files that store inputs only
- Rotating local diagnostic log at `logs/beamcheck.log`
- No login, cloud service, telemetry, or analytics

## Screenshot

The application opens with an input form on the left and Beam, Results, Shear, Moment, Deflection, and Calculation tabs on the right.

<!-- Add a release screenshot here after the first signed Windows build. -->

## Development setup

Python 3.12 is recommended.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe app.py
```

The default example is a 4 m simply supported beam with a 10 kN central point load and a 100 × 200 mm solid rectangular S355 section. Select **Calculate** to populate all result tabs.

Choose **Settings → Language** to switch immediately between English, Français, Deutsch, and 简体中文. BeamCheck remembers the selection for the next launch. Interface labels, result cards, charts, formula traces, dialogs, and newly exported PDF reports follow the active language; saved project input text is never translated or modified.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The benchmark suite includes the required textbook cases:

- Simply supported beam with a central point load
- Simply supported beam with a full-span UDL
- Cantilever with a free-end point load
- Cantilever with a full-span UDL

It also tests units, section properties, arbitrary point-load reactions, load superposition, stress and safety checks, validation, formula traces, PDF generation, and project-file round trips.

## Build the Windows distributable

From a clean environment with the requirements installed:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean BeamCheck.spec
```

The reliable one-folder build is written to `dist\BeamCheck\`. Run `dist\BeamCheck\BeamCheck.exe`; the target machine does not need Python or pip. One-folder mode is intentional for MVP reliability.

## Architecture

```text
app.py
beamcheck/
├── core/          # SI models, units, sections, loads, solver, deflection, checks
├── gui/           # PySide6 main window and shared matplotlib figures
├── reporting/     # deterministic formula trace and ReportLab PDF
└── utils/         # formatting, logging, and local JSON projects
tests/             # unit, benchmark, reporting, and persistence tests
```

The calculation engine has no GUI dependency. GUI screens, plots, the formula trace, and PDF reports all consume the same immutable solver result.

## Engineering assumptions

- Euler–Bernoulli beam theory
- Small deflection and linear-elastic behavior
- Constant cross-section; homogeneous, isotropic material
- Static, downward transverse loading
- SI units internally; display conversion occurs only at boundaries
- Bending about the section axis associated with the entered height

## Known limitations

- Only point loads and full-span UDLs are supported in MVP. Partial UDLs are not yet accepted.
- At most one point load and one UDL are exposed in the GUI, although the core uses a load tuple for future extension.
- Deflection values use validated analytical functions; the reported maximum location is selected from a dense numerical sampling that includes load and moment-extremum positions.
- The stress check covers elastic bending yield only. It does not cover shear resistance, stability, lateral-torsional buckling, local buckling, fatigue, dynamics, plasticity, connections, or load combinations from a design standard.
- Deflection criteria are user-selected serviceability limits, not code certification.
- Loads are treated as downward and non-negative in MVP.

## Roadmap

Near-term candidates are partial-span UDLs, multiple independently editable loads, richer project templates, signed Windows releases, and additional validated beam boundary/load cases. Broader calculation modules should retain the same workflow: deterministic inputs → solver → checks → trace → charts → report.
