# Standalone Qt movie export lacks a camera snapshot

**Status:** confirmed, deferred until after 1.0.

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
