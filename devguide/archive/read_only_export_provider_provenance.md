---
summary: Preserve the selected scientific provider in the read-only export guard.
issue: uibcdf/molsysviewer#282
status: resolved
opened: 2026-10-30
closed: 2026-10-30
severity: low
verification: reproduced
area: [tests, export, dependencies]
guard: tests/test_headless_export_resources.py::test_real_png_export_from_read_only_package
normative:
blocked_by: []
supersedes: []
---

# Read-only export subprocess provider provenance

## What

The Qt polish full regression passes 3,317 cases and fails this guard before
Chromium: the child imports the development ChemicalStates branch although
the parent deliberately selects source 71fbe4f46. The missing topology.bonds
belongs to the separate #269 transition, not the #228 resource repair.

## How

The fixture overwrote PYTHONPATH with the installed Viewer copy only. Preserve
that copy first, then the selected parent's MolSysMT root and inherited search
path. The actual child now asserts both the isolated Viewer path and exact
provider file, retaining the read-only permissions, real browser PNG dimensions
and nonuniform pixels, workspace cleanup and caller output.

## Resolution — 2026-10-30

The changed file passes all three real tests in 17.70 seconds. The original
full-run failure remains in the [receipt](../standalone_window_polish_receiving_20261030.json):
3,318 distinct passing cases are covered across attempts, with 21 skips; this
is not one clean green full run. The selected guard fails if provider
provenance is lost or if the installed/read-only export behavior breaks.
No scientific implementation, core API or dependency floor changes.
