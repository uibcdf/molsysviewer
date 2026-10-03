---
summary: Update the Mol* dependency after 1.0.
issue: uibcdf/molsysviewer#115
status: open
opened: 2026-09-28
closed:
verification: inspected
area: [dependency, frontend]
guard:
normative:
blocked_by: []
supersedes: []
---

# Update the Mol* dependency after 1.0

**Reported:** 2026-09-28, while defining the minimal pre-1.0 Interactions
slice in `uibcdf/molsysviewer#114`.

**Status:** Post-1.0 proposal. No target release has been selected or
installed by this report.

## What

Update the npm Mol* dependency to a published, tested release after 1.0.
The current package lock installs 5.4.1; the local upstream source checkout
is newer but is not the viewer's installed dependency. Newer Mol* capabilities
must not silently become 1.0 promises.

## How

Select an exact published version, inspect upstream changes affecting the
Mol* interfaces imported by the viewer, update package metadata and lockfile,
and rebuild the runtime. Validate structures, trajectories, picking, shapes,
measurements, Interactions, state reconstruction, export, and the supported
core browser lane. Record the tested version and any required compatibility
work. A `pull` in the separate Mol* source checkout is an inspection step,
not a dependency update.

## Why

MolSysViewer relies on Mol* APIs beyond its top-level viewer facade. Upstream
notes that less-used interfaces can change between minor versions. The
existing 5.4.1 package already includes `CustomInteractions` and
`InteractionsShape`, so the first Interactions slice does not require an
upgrade to be useful.

## What was refuted

- Pulling the local Mol* source checkout does not change the npm dependency.
- Treating the latest source-tree features as available in the installed
  runtime would overstate the viewer's current capability.

## Resolution

Deferred until after 1.0.
