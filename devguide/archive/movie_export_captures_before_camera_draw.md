---
summary: Movie frame export captures before the requested camera has been drawn.
issue: uibcdf/molsysviewer#273
status: resolved
opened: 2026-10-29
closed: 2026-10-29
severity: high
verification: measured
area: [movie, rendering, standalone]
guard: tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu
normative:
blocked_by: []
supersedes: []
---

# Movie export captures before its camera draw

## What

exportFrames awaits applyStateForExport but immediately reads the image.
The camera command's completion does not mean Mol* consumed its reset.
Playback/stop already wait for drawing under #172; export omits that barrier.

## How

MovieHandlers.setCameraSnapshot delegates to the queued camera command.
Canvas3D consumes the pending reset during rendering; its didDraw signal marks
that completed draw. MovieContext already exposes waitForDraw for this reason.
Use it after applying each export state and before obtaining the image.

## Why

A frame must depict its requested keyframe time in every host, including Qt.
The native review observed a three-frame GIF with coalesced viewpoints; that
alone does not establish the cause, so the initial verification is inspected.
Do not change interpolation, coordinates, FPS or the requested camera recipe.

## Acceptance

Native export delivers the expected three frame events and nonempty images;
the requested half orbit differs from the initial image. The GUI timer continues
running during synchronous Python export. Retain existing playback completion,
stopping and visibility semantics and qualify the shared handler in JS/browser
checks as well as the native window. GIF encoding may coalesce identical frames.

## Resolution — 2026-10-29

MovieHandlers.exportFrames now awaits the existing draw barrier after applying
each requested state and before capturing its image. This reuses the shared
MovieContext contract; interpolation, scientific data and playback policy do
not change.

The real Qt guard captures three raw frames and checks the first and half-orbit
images differ (mean absolute channel difference 3.9928). The encoded GIF has
at least two nonempty frames; endpoint coalescing is permitted. This guard
checks actual requested viewpoints rather than only counting emitted frames. Existing core movie contracts
and browser playback retain their independent scope.

Native Linux source evidence: canonical PySide6/Qt 6.11.2, Python 3.14.7,
NVIDIA Quadro M2000. The guard passes with the frozen MolSysMT runtime matching
71fbe4f4. See [the review](../standalone_review_20261029.md) for scope and
retained failed attempts. This does not qualify a published artifact, other
native platforms or the standalone 1.0 support promise.
