# BeamCheck Verification Corpus

This directory is a versioned, machine-readable collection of BeamCheck calculation cases. It is separate from ordinary unit tests so inputs, expected quantities, tolerances, and independent references can be reviewed as data assets.

## Status model

- `draft` — the input is valid, but an owner-reviewed independent reference and expected quantities are not yet complete. Draft cases are discovered and reported, then skipped.
- `verified` — the case has an independent reference, declared expected quantities, and fixed tolerances. Verified cases must pass in pytest and `python -m beamcheck.verification`.

A case cannot be loaded as `verified` while its `reference.md` contains `STATUS: OWNER_REFERENCE_REQUIRED`, or while `expected.json` contains no quantities.

## Layout

```text
verification/
├── schema/
│   ├── verification_case.schema.json
│   └── verification_result.schema.json
└── cases/
    └── BC-NNNN/
        ├── case.json
        ├── expected.json
        └── reference.md
```

All numeric solver inputs in `case.json` use canonical SI units. JSON `NaN` and infinity values are rejected. Expected values are never rewritten by the runner.

## Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m beamcheck.verification
```

## Initial migration state

`BC-0001` through `BC-0004` preserve the input definitions of the existing textbook-form regression tests. They are intentionally `draft` because repository-owner-approved independent sources have not yet been supplied. They do not count as independently verified cases.
