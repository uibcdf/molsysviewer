# Warnings (planned)

MolSysViewer should use warnings for user-facing situations that are not fatal.
You use warnings to make behavior explicit without breaking workflows.

This page is a placeholder.
The warning system described here is not implemented yet.

## Goals

- Make non-fatal problems visible (for example: partial feature support).
- Keep warnings filterable by category.
- Keep warning locations useful (`stacklevel` points to the caller).
- Avoid noisy repetition in notebooks (support “warn once” patterns).

## Proposed structure

- Define warning categories under `molsysviewer/warnings.py`.
- Use `warnings.warn(..., Category, stacklevel=2)` in public APIs.
- Provide optional helpers:
  - `warn(message, category=...)`
  - `warn_once(message, category=...)`

## Candidate categories

- `MolSysViewerWarning` (base)
- `ExportWarning` (HTML export and embedding limitations)
- `FrontendWarning` (Jupyter/frontend constraints)
- `SelectionWarning` (selection resolution ambiguities)
- `PerformanceWarning` (slow paths, large scenes)
- `DeprecationWarning` (API deprecations, with a clear horizon)

## What should warn (examples)

- HTML lite exports that cannot preserve an interactive widget output.
- Falling back to a slower path (for example: large marching cubes grids).
- Selection strings that match nothing or that are ambiguous (when applicable).
- Features that require WebGL/browser capabilities that are missing.

## Testing (planned)

- Unit tests assert that the correct warning category is emitted.
- Use `pytest.warns(...)` with the specific category.
- Avoid mocks when possible; prefer real demo systems from `molsysviewer.demo`.
