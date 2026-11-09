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

**Inspected 2026-11-08:** #344's font-upload investigation receives an
independent real-WebGL probe of current upstream master
`6682cc94a230c851e13dbbc6f35fc9d486c0bbdb`. Its v6 source already supplies
shared versioned atlases and dirty-row uploads, unlike the installed 5.4.1
route. The current v5 branch was inspected separately, not executed as a new
dependency. This finding neither selects v6 for Viewer nor changes the
post-1.0 migration decision. Follow the
[owning investigation](../../pending_bugs/jupyter_moving_capture_residual_uploads.md)
for the bounded probe, the withdrawn new-bug draft and distinct integration
failures; a source mechanism is not installed Viewer compatibility.

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

### Follow the first published font-atlas correction

The maintainer requested explicit issue-board follow-up on 2026-11-08; #115
now includes this acceptance checklist. At dependency/release review checkpoints:

- Identify the first published release that actually contains shared,
  content-versioned font textures and the applicable upload correction. Do not
  infer inclusion from the next version number or current upstream master.
- Record the exact version, tag/source commit and npm artifact identity/integrity,
  then inspect the published artifact to confirm the relevant implementation.
- Review its actual package/API migration scope before selecting the dependency.
- Receive unchanged-text updates, new glyphs and actual GPU pixels,
  font/style/quality changes, disposal and context restoration, alongside the
  applicable trajectory, camera, measurement, capture and popup gates.
- Remove any temporary Viewer compatibility adaptation only after those native
  controls pass; otherwise record why it still remains necessary.

The migration stays post-1.0. The separate pre-1.0 #344 consumer work remains
open; this follow-up changes neither the dependency nor the publication scope.

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
