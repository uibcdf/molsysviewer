---
summary: Shape-only views keep the welcome card and hide addon workspaces until a molecular structure is loaded
issue: uibcdf/molsysviewer#240
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: high
verification: reproduced
area: [canvas, addons, welcome]
guard: molsysviewer/js/tests/e2e/panel-popup-welcome.e2e.ts
normative: devguide/addon_panel_widget_contract.md
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

## Resolution — 2026-10-13

Studio/Add-ons availability no longer follows the molecular hierarchy. Core Studio
remains reachable for loading, absolute shapes and settings; non-core workspaces
keep their existing panel navigation. Removing a molecular system does not hide
Add-ons. `StateHandlers.hasSceneContent` reads live Mol* representation cells,
including hidden and untagged geometry, without reading atoms or trajectories;
metadata/deleted refs alone do not suppress guidance. The controller updates
Welcome after scene operations, including rings, alpha spheres and clear-by-tag,
and after explicit panel open/close. Molecular loading still suppresses transient
Welcome. A genuinely empty, closed canvas keeps its quick start; an open workspace
and every panel-only endpoint are unobstructed. There is no provider-specific
branch or new scientific/API prerequisite.

The registered closing guard uses an actual `AddonPanelWidget` and public
`view.shapes` operations, real Mol*/Chromium, the AnyWidget bootstrap and production
popup snapshots. It receives empty original/canvas popup guidance, normal Studio
opening/closing, disabled molecular interaction creation, visible/hidden/deleted
absolute geometry, addon-first Render/Clear/remount, caller-owned sphere protection,
Clear from the panel popup, Render from the canvas popup's W navigation, and
subsequent real dialanine loading in both canvases. Navigation remains local to
each window; the guard uses each window's normal workspace controls.

The specific shared-runner guard passes. JS units pass after updating the existing
summary-routing seam to exclude its absent DOM; the guard above receives real
workspace behavior. Regression integration and exact-source hosted campaigns
retain separate status in [the validation receipt](../shape_only_canvas_workspace_validation_20261013.json).
This is source/runtime evidence, not installed package qualification or a complete
live Jupyter/PharmacophoreMT campaign. Consumer confirmation under
uibcdf/pharmacophoremt#58 can exercise this host correction without a dummy system.

The retained development attempts caught fixture errors (an unsupported AddonSpec
title, molecular-only camera observation, controls hidden while a floating panel
is open, and assumptions about local popup navigation). Each was diagnosed before
a targeted rerun. No force-click, fake molecular system, synthetic scene or
skipped browser failure was used to obtain the final passing guard.
