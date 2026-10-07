---
summary: Movie interruption browser gate intermittently fails its camera drift assertion
issue: uibcdf/molsysviewer#177
status: open
opened: 2026-10-07
closed:
severity: medium
verification: reproduced
area: [movie, ci, camera]
guard:
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
