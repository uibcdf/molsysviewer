---
summary: Movie interruption browser gate intermittently fails its camera drift assertion
issue: uibcdf/molsysviewer#177
status: partial
opened: 2026-10-07
closed:
severity: medium
verification: reproduced
area: [movie, ci, camera]
guard: molsysviewer/js/tests/e2e/movie-playback.e2e.ts
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Movie interruption browser gate intermittently fails its camera drift assertion

**Reported — 2026-10-07:** native logs of Python 3.14 source-pair run
`37602651230` on exact Viewer `513391c1`. No new local reproduction or correction
is claimed. Source reading is separate from the hosted observation.

## What

The Python 3.14 source-pair core browser gate failed on Viewer 513391c134b24c34969efae770015eab3f3f3fb2 in run 37602651230 at movie-playback. The interruption assertion observed camera drift 83.55 with remaining distance 0.00, from [60,0,0] to [0.9200000000031044,0,59.07999999999689]. Native logs retain the assertion and test stack. A separate core run 37629947438 succeeds on the same head; neither result cancels the other.

## How

Inspect the second playback's start/stop synchronization and camera-write completion in molsysviewer/js/tests/e2e/movie-playback.e2e.ts and its owning Movie/runtime camera tools. Determine whether the failure originates in product cancellation or test sampling before changing code. Preserve intermediate/final/interruption assertions and real Mol* rendering; no blind rerun, tolerance widening or WebGL skip establishes correction.

## Why

A repeatable final 1.0 gate must establish that stop_movie interrupts playback and does not continue the journey. This is separate from the final completion/draw correction in uibcdf/molsysviewer#172. The scientific Python suite and both annotation browser scenarios passed before the failing Movie assertion, so it does not refute their bounded evidence.

Run: https://github.com/uibcdf/molsysviewer/actions/runs/37602651230
Passing separate core: https://github.com/uibcdf/molsysviewer/actions/runs/37629947438

## What was refuted

The receptor's failure verdict is retained. A passing separate core run does not
prove the failing condition corrected. The source-pair run passed Python science
and both annotation scenarios before its Movie failure; its aggregate failure
cannot be presented as a passing complete gate. The observed atStop value equals
the previous playback's destination, but whether it is a stale test sample or a
product cancellation/write defect remains undiagnosed. Do not infer causality
from this coincidence.

## Acceptance

Diagnose the first incorrect boundary using the existing real Mol* scenario and
retain explicit playback-start, stop, camera-write and fresh-draw observations.
The guard must distinguish genuine continuing playback from an old sampled camera
without weakening interruption, interpolation or final-position semantics.
Qualify the affected exact-source/core lane and retain both old and new verdicts.
No tag, package or runtime rebuild is authorized by merely reporting this finding.

## Diagnosis and local correction — 2026-10-07

The subsequent core run `37675655282` reproduces the same boundary on `4bedcba9`:
stop reports `[60,0,0]`, then the camera moves 84.39 toward the next playback's
start. Its failure remains preserved. Independent source-pair run `37675655286`
passes on that head; this does not refute the failing condition.

The installed Mol* 5.4.1 source confirms Camera.SetSnapshot invokes the camera
manager's requestCameraReset; the reset is consumed during canvas commit/draw,
after its command promise returns. The local source checkout in
`/home/diego/repos@others/molstar` confirms the same separation. The configured
root `src_molstar` alias is absent here; no source/API upgrade is introduced.
Camera coordinates in these observations are in angstroms.

A diagnostic using real Chromium/Mol* pauses its native animation loop while
Movie's own rAF submits camera resets. After two rAF callbacks, Movie time is
361.20 ms and its command-promise set is empty. Stop returns while drawing remains
paused; restarting Mol* moves the observed camera from approximately
`[11.9462,13.3290,32.6629]` to `[24.0800,0,35.9200]`. An initial fixed-100-ms
probe observed no submitted tick and was inconclusive; awaiting actual rAF
callbacks established the missing boundary.

Movie now retains submitted-camera draw responsibility separately from pending
command promises. Stop drains commands, replaces pending resets with the observed
camera and awaits the shared fresh-draw tool. Natural completion clears that
responsibility only after its existing final draw; generation checks remain.
The browser guard waits for an applied intermediate second-playback camera,
adds the native paused-draw case and tightens post-stop drift to <1e-6. Original
interpolation and final-completion assertions remain.

Three targeted unit cases pass. An in-memory mutation restoring the old
promise-count condition fails the new unit case with “stop returned before the
camera was drawn”; production sources were never mutated for that control.
The real browser guard, normal JS unit command and TypeScript check pass. The
runtime is regenerated through build:runtime. Versioningit's configured writer
refreshes the ignored stale version file to the current development identity
before regeneration; package.json is unchanged. No published tag/package moves.
Full core/exact-source hosted qualification remains pending before closure.

[Exact local/hosted evidence](../movie_interruption_fix_20261007.json).
