# BeamCheck — MVP Development Specification

## 1. Project Goal

Build a **local-first Windows desktop engineering calculation tool** called **BeamCheck**.

BeamCheck is NOT intended to compete with full FEA software.

Its positioning is:

> Faster than spreadsheets, clearer than hand calculations, simpler than FEA.

The MVP should allow a user to define a basic beam problem, calculate reactions / shear / bending / stress / deflection, visualize the results, and export a professional calculation report.

The first version must be deterministic, testable, and engineering-oriented.

---

# 2. MVP Scope

The MVP must support:

## Beam Types

- Simply supported beam
- Cantilever beam

## Load Types

- Single point load
- Uniformly distributed load (UDL)

For MVP v1, support at least:
- one point load
- one UDL

The architecture should make it possible to support multiple loads later.

## Cross Sections

- Solid rectangular
- Solid circular
- Rectangular hollow section (RHS)
- Square hollow section (SHS)

## Materials

Include built-in presets for:

### Steel
- S235
- S275
- S355

### Aluminium
- Generic aluminium alloy preset

Material properties should include at least:

- Young's modulus, E
- Yield strength, fy
- Density

The material system must allow custom values.

---

# 3. Required Inputs

The GUI must allow the user to define:

## Project

- Project name
- Calculation title
- Engineer / author name (optional)
- Notes (optional)

## Beam

- Beam type
- Length
- Unit

## Material

- Material preset
- Young's modulus
- Yield strength

## Section

Depending on section type:

### Rectangular

- Width
- Height

### Circular

- Diameter

### RHS / SHS

- Outer width
- Outer height
- Wall thickness

## Loads

### Point Load

- Magnitude
- Position from beam origin

### UDL

- Load magnitude per unit length
- Start position
- End position

For MVP, if partial UDL adds unnecessary complexity, full-span UDL may be implemented first, but the code architecture must allow partial UDL later.

---

# 4. Units

The application must have a consistent unit system.

Recommended internal SI units:

- Length: m
- Force: N
- Moment: N·m
- Stress: Pa

The GUI should support convenient engineering display units:

- mm
- m
- N
- kN
- N/mm
- kN/m
- MPa
- GPa

All calculations must convert inputs into a single internal unit system before solving.

Never mix display units directly in calculation logic.

Create a dedicated unit conversion module.

---

# 5. Engineering Calculations

The calculation engine must be deterministic and independent of the GUI.

Create a dedicated solver layer.

At minimum calculate:

## Section Properties

- Area
- Second moment of area, I
- Distance to extreme fibre, c
- Section modulus, Z = I / c

## Beam Reactions

For supported configurations:

- Left reaction
- Right reaction
- Fixed-end reaction where applicable
- Fixed-end moment for cantilever where applicable

## Internal Results

Across the beam length calculate:

- Shear force V(x)
- Bending moment M(x)

Use numerical sampling where useful for plotting, but analytical formulas should be used where practical.

## Key Results

Calculate:

- Maximum absolute shear force
- Maximum absolute bending moment
- Maximum bending stress
- Maximum deflection
- Deflection location
- Factor of safety against yield

Bending stress:

sigma = M / Z

or equivalently:

sigma = M*c/I

Factor of safety:

FoS = fy / sigma_max

---

# 6. Deflection

For MVP, implement validated deflection solutions for supported cases.

At minimum:

## Simply Supported Beam

- Central or arbitrary point load if practical
- Full-span UDL

## Cantilever Beam

- Point load
- Full-span UDL

If arbitrary point-load position is implemented, ensure formulas are validated carefully.

The solver must NOT silently return an approximation without indicating it.

If a load case is not supported, show a clear message.

---

# 7. Engineering Checks

The application should perform simple checks.

## Stress Check

Compare maximum bending stress with yield strength.

Display:

- Calculated stress
- Yield strength
- Factor of safety
- PASS / FAIL

For MVP:

PASS if:

sigma_max <= fy

## Deflection Check

Allow the user to choose a basic allowable deflection criterion:

- L / 180
- L / 250
- L / 300
- L / 360
- Custom

Display:

- Maximum calculated deflection
- Allowable deflection
- PASS / FAIL

Important:

Do NOT present these simple checks as code-compliance certification.

The report must contain a disclaimer stating that engineering judgment and applicable standards remain the user's responsibility.

---

# 8. Diagrams

The application must display:

## Beam Schematic

Show:

- Beam
- Supports
- Point load arrow
- UDL arrows
- Basic dimensions

## Shear Force Diagram

Plot V(x).

## Bending Moment Diagram

Plot M(x).

## Deflection Curve

Plot deflection y(x).

Use matplotlib.

The plots must:

- Have axis labels
- Show units
- Use engineering-friendly formatting
- Be readable in exported reports

Do not use seaborn.

---

# 9. Formula Trace

One important product feature is a transparent calculation trail.

For supported cases, display key calculation steps.

Example structure:

Maximum bending moment

M_max = w L^2 / 8

Substitution:

M_max = 3.5 × 2.4^2 / 8

Result:

M_max = 2.52 kN·m

Then:

Bending stress

sigma = M / Z

Substitution

Result

Check:

sigma_max < fy

PASS

Do not use AI to generate formulas.

Formula trace must come from deterministic templates connected directly to the calculation engine.

---

# 10. PDF Calculation Report

Export a professional PDF report.

Recommended structure:

1. Cover / Header
2. Project Information
3. Beam Definition
4. Material Properties
5. Section Properties
6. Applied Loads
7. Reaction Forces
8. Shear Force Diagram
9. Bending Moment Diagram
10. Deflection Curve
11. Stress Calculation
12. Deflection Check
13. Factor of Safety
14. Calculation Summary
15. Assumptions and Limitations
16. Disclaimer

The PDF should show:

- Input values
- Units
- Important formulas
- Numerical substitutions
- Results
- PASS / FAIL badges or text
- Diagrams

Preferred PDF approach:

- ReportLab

Alternative libraries are acceptable if they simplify layout and packaging.

The report must NOT depend on a remote service.

---

# 11. GUI

Build a clean desktop GUI.

Preferred:

- PySide6

Fallback:

- tkinter

PySide6 is preferred because the final application should look like a real engineering tool.

Suggested layout:

## Left Panel

Input form:

- Project
- Beam type
- Material
- Section
- Loads
- Deflection criterion

## Main Area

Tabs:

### Tab 1 — Beam

Beam schematic

### Tab 2 — Results

Summary cards / values

### Tab 3 — Shear

SFD

### Tab 4 — Moment

BMD

### Tab 5 — Deflection

Deflection curve

### Tab 6 — Calculation

Formula trace

Bottom actions:

- Calculate
- Reset
- Export PDF

---

# 12. Validation

Input validation is critical.

Examples:

- Beam length > 0
- Load magnitude valid
- Load position within beam length
- Section dimensions > 0
- Wall thickness physically valid
- Young's modulus > 0
- Yield strength > 0
- Inner dimensions of hollow section > 0

Do not allow physically impossible RHS/SHS geometry.

Errors should be presented in plain language.

The app should never crash because of normal bad user input.

---

# 13. Software Architecture

Use a modular structure.

Suggested:

```text
beamcheck/
│
├── app.py
├── requirements.txt
├── README.md
│
├── beamcheck/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── models.py
│   │   ├── units.py
│   │   ├── materials.py
│   │   ├── sections.py
│   │   ├── loads.py
│   │   ├── solver.py
│   │   ├── deflection.py
│   │   └── checks.py
│   │
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── input_panel.py
│   │   ├── results_panel.py
│   │   └── plots.py
│   │
│   ├── reporting/
│   │   ├── report.py
│   │   └── formula_trace.py
│   │
│   └── utils/
│       ├── validation.py
│       └── formatting.py
│
└── tests/
    ├── test_sections.py
    ├── test_units.py
    ├── test_reactions.py
    ├── test_moments.py
    ├── test_deflection.py
    └── test_known_cases.py
```

Do not put all engineering logic inside the GUI.

The solver must be usable independently from the interface.

---

# 14. Testing Requirements

Engineering correctness is more important than UI polish.

Use pytest.

Create unit tests for:

- Unit conversions
- Section properties
- Reactions
- Maximum moment
- Shear
- Bending stress
- Deflection
- Safety factor

Create benchmark tests against textbook analytical cases.

At minimum validate:

## Case A

Simply supported beam, central point load.

Expected:

R_A = R_B = P / 2

M_max = P L / 4

delta_max = P L^3 / (48 E I)

## Case B

Simply supported beam, full-span UDL.

Expected:

R_A = R_B = w L / 2

M_max = w L^2 / 8

delta_max = 5 w L^4 / (384 E I)

## Case C

Cantilever with point load at free end.

Expected:

V_max = P

M_max = P L

delta_max = P L^3 / (3 E I)

## Case D

Cantilever with full-span UDL.

Expected:

V_max = w L

M_max = w L^2 / 2

delta_max = w L^4 / (8 E I)

Use tight numerical tolerances.

---

# 15. Engineering Assumptions

The MVP must document its assumptions clearly.

Unless specifically extended:

- Euler-Bernoulli beam theory
- Small deflection
- Linear elastic material behaviour
- Constant cross-section
- Homogeneous isotropic material
- Static loading
- No lateral torsional buckling
- No local buckling
- No shear deformation correction
- No fatigue
- No dynamic loading
- No plastic analysis
- No connection design
- No code certification

These limitations must be visible in the application and report.

---

# 16. Product Safety / Claims

Do NOT describe BeamCheck as:

- certified
- code compliant
- approved
- a replacement for professional engineering review

Use language such as:

> BeamCheck is an engineering calculation aid. Results must be reviewed by a qualified user and checked against applicable standards, design requirements, and project conditions.

---

# 17. Data Storage

MVP should be local-first.

No:

- login
- account
- server
- cloud database
- telemetry
- analytics SDK

Optional local project saving may use JSON.

Suggested file extension:

```text
.beamcheck.json
```

The project file should store inputs only and recalculate outputs when opened.

---

# 18. Packaging

Target:

- Windows 10
- Windows 11

Use PyInstaller.

Final goal:

```text
BeamCheck.exe
```

The user should NOT need:

- Python
- pip
- developer tools

The project must include:

- build instructions
- dependency file
- PyInstaller configuration if needed

If one-file mode causes reliability problems, a one-folder distributable is acceptable for MVP.

Reliability is more important than forcing a single executable.

---

# 19. Logging

Create local logs for debugging.

Example:

```text
logs/beamcheck.log
```

Log:

- startup
- calculations
- validation failures
- export failures
- unexpected exceptions

Do not log sensitive user information unnecessarily.

---

# 20. README

README should contain:

- What BeamCheck is
- MVP feature list
- Screenshots placeholder
- Installation for development
- How to run
- How to test
- How to build Windows executable
- Engineering assumptions
- Known limitations
- Roadmap

---

# 21. MVP Non-Goals

DO NOT implement these in v1:

- Finite element analysis
- Arbitrary frame analysis
- Trusses
- 3D CAD
- Beam optimization
- AI assistant
- Natural language input
- Cloud sync
- User accounts
- Payment system
- License server
- Online material database
- Eurocode / AISC / BS full compliance
- Mobile app
- Web app
- Multi-language support

Avoid scope creep.

---

# 22. Future Architecture Considerations

Code should make it possible to add future modules such as:

- Column buckling
- Shaft design
- Bearing life
- Bolt calculations
- Gear calculations
- Pressure drop
- Heat transfer

The common future workflow should be:

```text
Inputs
  ↓
Deterministic engineering solver
  ↓
Checks
  ↓
Formula trace
  ↓
Charts
  ↓
Calculation report
```

Do not implement these modules now.

---

# 23. Development Sequence

Implement in this order:

## Phase 1 — Core Engineering Engine

1. Data models
2. Unit conversion
3. Section properties
4. Materials
5. Load models
6. Beam reactions
7. Shear / moment calculations
8. Stress calculation
9. Deflection
10. Checks

Run tests before continuing.

## Phase 2 — Plotting

Implement:

- beam schematic
- SFD
- BMD
- deflection plot

## Phase 3 — Formula Trace

Generate deterministic calculation steps.

## Phase 4 — GUI

Connect GUI to solver.

## Phase 5 — PDF Export

Generate report using calculation results and plots.

## Phase 6 — Packaging

Create Windows build.

---

# 24. Coding Rules

- Use Python 3.12 where practical.
- Use type hints.
- Use dataclasses or Pydantic-style models where useful.
- Keep calculation functions pure where possible.
- Separate UI state from engineering state.
- Avoid global variables.
- Do not duplicate formulas across GUI, report, and solver.
- Solver outputs should feed both GUI and reports.
- All engineering formulas need comments describing assumptions.
- Use SI units internally.
- Write tests before adding major complexity.

---

# 25. Required First Deliverable

Start by creating the repository structure and implementing ONLY:

- unit system
- material model
- rectangular section
- circular section
- simply supported beam
- cantilever beam
- point load
- full-span UDL
- reactions
- shear
- bending moment
- bending stress
- deflection
- benchmark tests

Do NOT start GUI work until these benchmark tests pass.

After the core solver passes tests, continue with plots, GUI, formula trace, and PDF export.

---

# 26. Codex Working Instructions

You are the primary developer for this project.

Do not just explain what code should look like.

You should:

1. Create the files.
2. Implement the code.
3. Run the code.
4. Run the tests.
5. Inspect failures.
6. Fix failures.
7. Repeat until the core benchmark tests pass.
8. Continue through the MVP phases.
9. Keep README updated.
10. Avoid unnecessary dependencies and scope creep.

When an engineering formula is uncertain:

- do not guess;
- isolate it;
- add a TODO;
- clearly report the uncertainty.

Correctness is more important than feature count.

At the end, provide:

- final project structure
- implemented features
- test results
- known limitations
- exact command to run the app
- exact command to build the Windows distributable
