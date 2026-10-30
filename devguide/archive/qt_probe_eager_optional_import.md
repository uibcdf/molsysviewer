---
summary: Keep optional Qt imports out of child-helper collection.
issue: uibcdf/molsysviewer#283
status: resolved
opened: 2026-10-30
closed: 2026-10-30
severity: medium
verification: reproduced
area: [tests, qt, dependencies]
guard: tests/test_qt_window_polish.py::test_qt_child_collection_without_optional_dependencies
normative:
blocked_by: []
supersedes: []
---

# Optional Qt imports during core doctest collection

## What

The polish helper introduced in 79002636 eagerly imported PySide6. The core
suite's doctest collection imports helpers before marker deselection, so
macOS without optional Qt reports collection exit 2 at `_qt_window_polish.py`.
Direct job log 124219876361 in run 41101687711 establishes the missing PySide6;
the run/step summaries did not expose that evidence. This is a newly introduced
test regression, distinct from the old public-provider Pandas4Warning baseline.

## Resolution — 2026-10-30

All optional Viewer/Qt imports now live inside the child's main function,
following the existing workbench child pattern. The new guard executes actual
`python -I -S` without site packages, asserts PySide6 is absent and imports the
helper through runpy without running main. It fails on the original eager
imports. The actual Qt widget child remains selected under qt_runtime.

Both the genuine dependency-absence guard and the real-widget guard pass in
3.15 seconds. No production code, dependency floor or test skip is changed.
The broader original failures, subsequent source identities and hosted states
remain in the [receipt](../standalone_window_polish_receiving_20261030.json).
