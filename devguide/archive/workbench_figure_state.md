---
summary: Preserve workbench figure settings across state/session restoration.
issue: uibcdf/molsysviewer#227
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: low
verification: reproduced
area: [studio, export, state]
guard: tests/test_workbench_figure_state.py::test_workbench_recipe_survives_file_roundtrip
normative:
blocked_by: []
supersedes: []
---

## What
The real Studio persistence guard restores a 1.5× figure recipe as 2×. State
JSON omits the workbench recipe, and frontend Whole projection resets its
controls independently of the Python recipe. The PNG background can reset too.

## How
Persist preset/scale/background as an optional additive state-v2 field. Validate
it before mutation and restore through the existing `set_figure_spec` owner.
Whole representation projection preserves configured figure values; explicit
viewer reset still clears them. Old documents without the field remain accepted.
Export-only width/height and camera overrides are not stored by the workbench
setter and are not promised by this field.

## Why
State/session restoration must retain the visible PNG configuration. Guard real
JSON/MSV roundtrips, finite positive scale, invalid metadata without mutation,
legacy documents and actual browser controls/pixels.

## Implementation
FigureSpec owns finite positive scale validation, so normal construction and
state import reject booleans, NaN and infinity consistently. The state importer
validates the optional field before mutation and ignores unknown extra fields.
The final focused figure/image-export run passes 40/40.

## Resolution — 2026-10-10
Optional state-v2 workbench figure settings prevalidate and restore through the FigureSpec owner; Whole preserves the existing recipe and explicit reset clears it.

Guard: `tests/test_workbench_figure_state.py::test_workbench_recipe_survives_file_roundtrip`. The real Studio browser workflow additionally checks
coordinate focus, layer-hidden wording, JSON/MSV confirmation/retry/correlation,
PNG scale/alpha and unavailable exported-host actions. Focused Python file/action
checks pass 27/27; final figure/image checks pass 40/40. Local full-suite and
experimental Qt limitations remain in `studio_coverage_20261010.md`; no package
is qualified and no 1.0 publication is authorized by this closure.
