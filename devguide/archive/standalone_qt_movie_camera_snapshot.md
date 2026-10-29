---
summary: Movie export in the Qt host fails because the camera snapshot is never mirrored back.
issue: uibcdf/molsysviewer#36
status: resolved
opened: 2026-07-04
closed: 2026-10-29
severity: low
verification: measured
area: [standalone, qt, movie]
guard: tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu
normative:
blocked_by: []
supersedes: []
---

# Standalone Qt movie export lacks a camera snapshot

**Status:** resolved in source on 2026-10-29; historical deferral retained below.

## Symptom

`Export → Export Movie (orbit)` fails with `"no camera snapshot available"`.

## Verified diagnosis

`movie.add_camera_orbit()` starts from the current camera state, but in the Qt
context `view._last_camera_snapshot` remains `None`. The request/response
round-trip is incomplete:

```text
request_camera_snapshot
→ frontend camera_snapshot event
→ Qt event transport
→ persistent MolSysView._handle_frontend_event
→ _last_camera_snapshot
```

## Resolution plan

1. Prove the minimal snapshot round-trip without starting a movie.
2. Verify that the event reaches the persistent view and updates the snapshot.
3. Make the Qt export action request a fresh snapshot and wait cooperatively,
   processing Qt events with an observable timeout.
4. Build the orbit only after a valid response.
5. Add response, timeout, and non-blocking tests, then validate the complete
   export in a real Qt/WebGL window.

Do not use a silent default-camera fallback. It would export a viewpoint other
than the one the user asked to preserve.

## Closure criteria

- The received snapshot matches the visible camera.
- Orbit export produces the expected frames.
- The GUI remains responsive.
- A missing response terminates with a diagnosed timeout.

## Resolution — 2026-10-29

The shared frontend handles camera/image requests for the live Qt connector.
Python waits cooperatively process Qt events, and the native movie action asks
for a fresh camera before constructing the orbit. It does not fall back to a
silent default viewpoint. The shared movie frame export also waits for drawing
under uibcdf/molsysviewer#273.

The native GPU guard receives the visible camera, exports three requested raw
frames into a nonempty animated GIF with visibly different opposite viewpoints,
observes a live Qt timer throughout, and verifies a missing reply terminates.
See [the review](../standalone_review_20261029.md) for exact source/environment
scope. This closes the camera-return/export defect, not standalone certification.
