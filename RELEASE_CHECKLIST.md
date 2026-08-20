# BeamCheck Release Checklist

Use this checklist for the first public release and adapt it for later versions. The intended first tag is `v0.1.0` and the Windows asset name is `BeamCheck-v0.1.0-windows-x64.zip`.

## 1. Validate the release candidate

- [ ] Confirm the version and release scope.
- [ ] Start from a clean working tree and record the release commit SHA.
- [ ] Run `python -m pytest -q` and keep the result with the release notes.
- [ ] Verify the four benchmark beam cases and section/unit tests pass.
- [ ] Launch the app from source and from the packaged folder.
- [ ] Test English, French, German, and Simplified Chinese.
- [ ] Test project save/load using JSON.
- [ ] Export a PDF report and inspect every page.
- [ ] Check diagrams, calculation details, units, warnings, and error handling.
- [ ] Confirm the README limitations and disclaimer match the implemented scope.

## 2. Package Windows build

- [ ] Build with `.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean BeamCheck.spec`.
- [ ] Confirm `dist\BeamCheck\BeamCheck.exe` launches without a Python installation.
- [ ] Test the complete folder on a clean 64-bit Windows 10 or Windows 11 machine.
- [ ] Confirm no personal data, projects, PDFs, logs, or temporary files are included.
- [ ] ZIP the complete `dist\BeamCheck` folder as `BeamCheck-v0.1.0-windows-x64.zip`.
- [ ] Generate and record a SHA-256 checksum for the ZIP.
- [ ] Scan the release asset with current endpoint protection.
- [ ] Record whether the binary is code-signed; explain expected SmartScreen behaviour if it is not.

## 3. Review GitHub presentation

- [ ] Capture current real screenshots from the release candidate.
- [ ] Confirm all README links and images render on GitHub.
- [ ] Confirm the download instructions match the uploaded asset exactly.
- [ ] Set the repository description.
- [ ] Add relevant repository topics.
- [ ] Select and add a license only after owner approval.
- [ ] Review `CONTRIBUTING.md` and the issue templates.
- [ ] Confirm the test workflow passes on GitHub Actions.

Suggested repository metadata for owner review:

- Description: `Offline Windows beam strength and deflection calculator with transparent formulas, diagrams, PDF reports, and EN/FR/DE/ZH UI.`
- Topics: `beam-calculator`, `structural-engineering`, `civil-engineering`, `engineering-calculations`, `pyside6`, `python`, `windows`, `desktop-app`, `offline`, `pyinstaller`

## 4. Publish the GitHub release

- [ ] Create and push the annotated tag `v0.1.0` from the verified commit.
- [ ] Create the GitHub release with a concise change summary, supported platform, assumptions, limitations, and disclaimer.
- [ ] Upload `BeamCheck-v0.1.0-windows-x64.zip` and its SHA-256 checksum.
- [ ] Download the published asset and verify its checksum.
- [ ] Extract and launch the downloaded copy once more.
- [ ] Confirm the release is public and the README download link leads users to it.

Do not publish a release while any required validation item is unresolved. Document accepted exceptions in the release notes.
