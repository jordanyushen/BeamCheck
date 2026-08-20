# Contributing to BeamCheck

Thank you for helping improve BeamCheck. Small, reviewable changes with clear validation are easiest to assess.

## Development setup

Use Python 3.12 on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe app.py
```

The core calculation modules are under `beamcheck/core/`; the PySide6 interface is in `beamcheck/gui/main_window.py`; regression and benchmark tests are under `tests/`.

## Before opening a pull request

- Keep the change focused and explain the problem it solves.
- Add or update automated tests for observable behaviour.
- Run the complete test suite locally.
- Update user-facing documentation and translations when behaviour or interface text changes.
- Do not include virtual environments, build output, logs, exported reports, or personal project data.
- Describe manual Windows checks when the change affects the UI, packaging, PDF export, or file handling.

## Engineering calculation changes

Changes to the solver, section properties, units, materials, or acceptance logic require extra care. A pull request must include:

- The physical assumptions and the exact formula being changed or added
- A traceable reference such as a recognized textbook, standard, or independently derived calculation
- Unit conventions and sign conventions
- At least one hand-checkable benchmark with expected values and justified tolerances
- Regression coverage for boundary cases and invalid inputs
- Any new limitation or warning needed in the interface, report, and README

Do not change a calculation merely to match an unexplained numeric output. If two references disagree, document the model assumptions and resolve the difference before implementation.

## Bug reports

Use the bug report template and remove confidential information from projects, PDFs, screenshots, and logs. For numerical discrepancies, include the smallest reproducible input set, the BeamCheck result, the expected result, units, and the independent reference calculation.

## Pull request review

Maintainers may ask for a smaller scope, additional references, or additional tests. Calculation-affecting changes should receive independent technical review before release.
