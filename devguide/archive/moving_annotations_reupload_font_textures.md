---
summary: Moving callouts reupload unchanged font textures and delay frame projections.
issue: uibcdf/molsysviewer#340
status: resolved
opened: 2026-11-08
closed: 2026-11-08
severity: medium
verification: reproduced
area: [annotations, trajectory, performance, capture]
guard: molsysviewer/js/tests/e2e/annotations-interaction.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Moving callouts reupload font textures

## What

A passive CPU/native-stage diagnostic receives the unchanged real-pentalanine
moving guard under #319. Both actual canvases retain their own V8 profile;
4 ms sampling and duration observations change no molecular or rendering
operation, assertion or operation deadline. The run fails popup-state after
75.50 s, with 4,330 selected inputs unchanged, all thirteen owned processes
closed and no resource interruption. The diagnostic is not release acceptance.

`texImage2D` under render-item updates accounts for about 41.4 s in the primary
profile and 39.3 s in the popup profile. These are sampled wall-time attributions,
not a generalized CPU benchmark. Annotation/tree updates repeatedly take
hundreds of milliseconds. Exact Mol* 5.4.1 source shows `Text.update` incrementing
the font texture ValueCell along with the position buffers whenever Viewer's
callout builder rebuilds its text geometry. A changed anchor need not change
the glyph atlas.

## How

Receive a real native regression in the existing annotation browser entry.
Coordinate-only updates must retain the unchanged font texture while updating
all actual glyph centres and their bounds. Changed text and background geometry
must retain rebuild behavior. Preserve leader geometry, camera-relative
presentation, picking and image export. Use the native geometry/ValueCell
contracts from the Viewer-owned representation; no dependency or `node_modules`
patch is proposed.

## Why

Repeatedly uploading an unchanged atlas can occupy the render thread while
current-frame interactions and dynamic regions wait. This is independently
undesirable even if other capture delays remain. A successful optimization
must still receive the unchanged popup/detached moving saves; it cannot close
#319 by inference. #325's GPU-pick receiving remains a separate finding.

## Evidence and next receiving

The private `A5-native-profile-20261108/endpoint-after-01` directory retains the
profiles, stage observations, failure, command, source hashes and cleanup.
The complete issue inventory has pages 100/100/100/38; no equivalent was found.
The first annotation attempt exposes a pre-existing sampling defect: shallow
copies retain mutable presentation positions and camera changes are read before
a completed draw. The guard now detaches its data and waits for real completed
draws, keeping every original assertion. The next before-control fails exactly
because an unchanged 3287 × 3286 font texture advances from version zero to one
after movement (12.25 s; 4,331 unchanged selected inputs; thirteen owned processes
closed).

The Viewer-owned correction keeps a weak layout record for each native Text
geometry. When text and representation properties match, it updates every
active quad centre through ValueCell; the native geometry hash recalculates
bounds without touching font/layout buffers. Other changes retain TextBuilder.
No font image bytes, quality or scientific result are altered. Strict frontend
builds and all 428 canonical Node cases pass. The expanded annotation guard
then exits zero in 12.27 s, including centre/bounds, font identity/version,
text/background rebuilding and all earlier controls, with 4,331 unchanged
selected inputs and complete owned-process cleanup. These directed durations
are not a comparative performance benchmark.

The next full unchanged moving-state entry, without the profiler, passes primary
state/session and captures a popup state, then rejects its missing region
geometry under #341. This run exits one in 42.06 s, preserves all 4,330 selected
inputs and closes all thirteen owned processes. It is not a full moving pass.
The #341 lifecycle correction has its own passing native before/after control;
combined full moving receiving is in progress. Presentation/picking/image and
all seven format/origin/empty-frame cases must be inspected before claiming
that gate.
Protocol 2,
packages, tags and both 1.0 publications remain unadvertised or paused.

## Resolution — 2026-11-08

Resolved in reviewed source. Coordinate-only callouts retain native font/layout buffers and update centres/bounds. The real before/after annotation guard and final seven-case native moving/presentation/image/picking entry pass. This is a Viewer representation fix, not a Mol* dependency patch or a universal performance claim. The [final source receipt](../moving_capture_font_and_region_receiving_20261108.json) records commands, exact input witnesses, retained failures, resource limits and cleanup. Public capture capabilities remain v1; publication stays paused.
