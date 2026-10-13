---
summary: Live widget reports set_trajectory_summary as an unknown operation
issue: uibcdf/molsysviewer#239
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: medium
verification: reproduced
area: [trajectory, protocol, widget]
guard: molsysviewer/js/tests/e2e/panel-popup-welcome.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Live widget trajectory summary dispatch

**Reported:** uibcdf/pharmacophoremt#58, actual Jupyter/anywidget receiving on
c046fca1 and a later freshly built 76c8cee1 source runtime. The addon controls
passed, but the widget logged an unknown `set_trajectory_summary` operation.

## What

Python emits the trajectory summary on molecular loading. The live controller
must consume it consistently rather than log an unknown operation.

## How

The dispatch and `TrajectoryHandlers.applySummary` were implemented in c9471fe3,
after those reported sources. Current qualification uses the production widget
bootstrap, actual Python loading, Mol* rendering and a canvas popup. It requests
17 fps through `view.player.set_fps` and requires that exact received value in
both controllers, with no unknown-operation console warning.

## Why

Trajectory controls must reflect authoritative Python settings, including in a
connected popup, without starting another playback clock.

## What was refuted

The earlier fresh-runtime consumer evidence is retained; it was not dismissed
as a stale browser bundle. The current browser transport adapter is not a live
Jupyter-host or installed-package qualification.

## Resolution

The c9471fe3 dispatch correction is confirmed by the final production-widget/Mol* guard: Python changes fps to 17, both original and canvas-popup controllers consume that value, and neither logs the unknown operation. The original consumer Jupyter failures on c046fca1/76c8cee1 remain historical evidence. Local source receiving does not certify a live Jupyter host or an installed artifact.

Exact final-source hosted qualification is tracked separately in
[the receiving receipt](../addon_window_lifecycle_validation_20261013.json).
No candidate freeze or publication is inferred.
