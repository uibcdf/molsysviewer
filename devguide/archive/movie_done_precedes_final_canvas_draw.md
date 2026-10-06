---
summary: Movie playback reports completion before its final camera reaches the canvas.
issue: uibcdf/molsysviewer#172
status: resolved
opened: 2026-10-06
closed: 2026-10-06
severity: medium
verification: reproduced
area: [movie]
guard: molsysviewer/js/tests/e2e/movie-playback.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Movie completion precedes the final camera draw

**Reported:** 2026-10-06 by staging core browser run `37538528770`, exact Viewer
`6c4ddba31c289a27f761576c07fa641603c4392e`. It passes 38 suites, then fails Movie:
the done event is present while the camera remains
`[57.353333333333346, 0, 2.646666666666654]` instead of `[60, 0, 0]`.

## How

Movie drains command promises and emits done. Mol*'s SetSnapshot handler only
requests a canvas camera reset; `resolveCameraReset()` applies it on the next
scene commit/draw. The promise describes command acceptance, not rendered state.
This is confirmed in the installed Mol* source and its local source checkout.

## Why

A caller can act on completion while the view still displays an intermediate
camera. This affects playback and the required core browser qualification.

## What was refuted

A larger fixed sleep and a relaxed final-position assertion hide the ordering
contract. MolSysMT detector/ABI3 behavior is unrelated to this camera-only case.
The separate experimental Qt WebGL failure remains under uibcdf/molsysviewer#109.

## Progress

`waitForCanvasDraw` extracts the existing exported-scene fresh-draw synchronization
as a reusable canvas tool. Export readiness and Movie use it; Movie awaits a fresh
draw after the final snapshot before emitting done, retaining the generation
check. The existing unit guard now delays render completion independently from
command completion. The real browser guard also records the camera inside the
completion callback, so a later correct draw cannot mask premature notification.
Focused unit/browser validation is recorded below.

## Resolution

**Resolved in source — 2026-10-06.** The two Movie unit cases pass, including the independently delayed draw. All three affected real Chrome/Mol* suites pass: movie-playback, export-replay and exported-page-framing. The playback browser assertion captures the camera at notification, rather than after a delay. The normal JS unit command passes. The bounded browser guard profile and source/workflow/report checks pass.
The next candidate uses a new source commit and Conda build 1. Build 0 and its
original failures remain preserved; no published tag or artifact is moved.
