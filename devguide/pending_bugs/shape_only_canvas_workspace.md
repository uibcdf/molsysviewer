---
summary: Shape-only views keep the welcome card and hide addon workspaces until a molecular structure is loaded
issue: uibcdf/molsysviewer#240
status: open
opened: 2026-10-13
closed:
severity: high
verification: reproduced
area: [canvas, addons, welcome]
guard:
normative:
blocked_by: []
supersedes: []
---

# Shape-only canvas cannot reach addon workspaces

**Reported:** 2026-10-13 by the consumer under uibcdf/pharmacophoremt#58.
The maintainer requested review after the scientific popup corrections.
The existing owning issue was read before creating this record; no duplicate
issue or intermediate issue comment was added.

## What

`MolSysView()` accepts an absolute native sphere and an enabled PharmacophoreMT
addon without a molecular system. Its workspace is registered, but the welcome
card remains and Add-ons is hidden. The consumer's fresh live Jupyter evidence
on Viewer `76c8cee1` confirms the normal workspace click cannot complete.

The current `c9471fe3` runtime still reproduces this premise: the real Python
API creates the sphere and addon summary; the real Mol*/Chromium controller
contains a live visible sphere and the workspace, but reports one welcome card,
`addonsVisible=false`, `addonsExpanded=false`, and a workspace button of zero
width/height after the normal controller panel-toggle operation. See the
[bounded review receipt](../shape_only_canvas_workspace_review_20261013.json).

## How

`viewer-controller.ts::updateWelcomeState` checks only `getStructureData()`,
which reads the molecular hierarchy. `captureCurrentStructure` reveals the
addon panel only when that hierarchy contains a structure. Shape creation and
addon registration do not establish that condition. Panel-only endpoints have
an explicit exception, but the original canvas and its canvas popup do not.

## Why

Absolute shapes and addon lifecycle/workspace APIs already work without atoms.
Requiring a dummy molecular system to reach their UI is a host prerequisite
mismatch. A molecular scene and the fully empty quick-start case remain valid
independent scenarios. This is pre-1.0 host work; PHMT's calculations and renderer
do not need a local workaround for it.

## What was refuted

The first consumer execution used an old checkout; its later fresh `76c8cee1`
execution and this current-source DOM reproduction remove that ambiguity.
The workspace metadata and native sphere exist, so registration or absent
geometry does not explain the hidden controls. The popup camera/selection fixes
do not change these availability conditions.

This local probe qualifies the controller's prerequisite failure, not a complete
live Jupyter/PHMT control campaign or the public 0.24.0 package. The consumer's
live-widget evidence retains its own scope under uibcdf/pharmacophoremt#58.

## Proposed resolution

Separate molecular-data availability, managed scene content and workspace
availability. Keep Studio/Add-ons reachable without atoms; only operations that
require molecular data should carry that prerequisite. Hide the welcome card
for a nonempty managed scene and prevent it from covering an explicitly opened
workspace; retain quick-start guidance for a truly empty canvas. Use a generic
host rule, with no PharmacophoreMT-specific branch or dummy system.

Before closure, receive real controls for empty, shape-only, addon-first and
molecular scenes, Render/Clear/remount and caller-owned shape preservation,
including canvas/panel popup behavior. Implementation and its closing guard
remain pending. No API or runtime code was changed during this review.
