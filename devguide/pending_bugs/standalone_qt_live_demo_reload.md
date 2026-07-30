# Standalone Qt — live demo replacement does not update the scene

**Status:** fix implemented and protected; visible-window validation pending.

The interactive backend was validated in a real Qt/GPU environment on
2026-07-04. Rendering, transport, the persistent `MolSysView`, context menus,
and camera interaction worked. Replacing the loaded system did not.

The camera/movie defect formerly recorded beside this one is explicitly
post-1.0 and now lives in
[`post_1.0/standalone_qt_movie_camera_snapshot.md`](post_1.0/standalone_qt_movie_camera_snapshot.md).

## Symptom

In the real Qt window, `File → Load Demo → <another system>` leaves the previous
system on screen. The old scene is not even cleared.

## Root cause and fix

The Python side emitted the expected `clear_all` and
`load_molsys_payload`. Two Qt transport defects prevented reliable delivery:

1. `runJavaScript()` returned `{accepted: true}`, but real PySide/QWebEngine did
   not consistently convert that JavaScript object to a Python `dict`. The
   bridge treated an accepted message as rejected and retried it up to the Q2
   ceiling. Delivery now returns the scalar sentinel
   `molsysviewer-message-accepted`, while retaining compatibility with the old
   object result.
2. `molsysviewer-payload://` allowed Fetch and CORS but was not registered as a
   local scheme. A `file://` Qt host could not fetch the second-generation
   payload, so the scheme handler served nothing. The payload scheme now also
   has `LocalScheme`.

Both mechanisms are covered independently:

- a unit regression rejects a mutation that ignores the scalar sentinel;
- a real offscreen Qt WebEngine regression sends two generations, serves two
  distinct payload IDs, parses different atom counts, and receives both
  terminal `structure_ready` events;
- a Chrome/WebGL E2E loads real dialanine and replaces it with the first frame
  of real pentalanine, asserting that Mol* retains exactly one structure and
  changes from 22 to 62 atoms.

The Qt regression fails when `LocalScheme` is removed, and the sentinel test
fails when scalar acceptance is ignored.

## Remaining validation

This executor has no X11/Wayland display and cannot create an EGL/Vulkan
context in Qt offscreen mode. It can validate the real bridge and scheme
handlers, while Chrome/SwiftShader validates Mol*, but it cannot observe the
integrated visible Qt window.

On a supported Qt/WebGL workstation:

1. alternate two visually distinguishable demos at least ten times;
2. confirm each replacement displays only the requested system;
3. confirm status reaches `Ready.` and no failed deliveries accumulate;
4. record the environment and result here.

Temporary diagnostics must remain runtime-only. They do not enter scene history,
state, replay, or export.

## Closure criteria

- Ten visible-window replacements display only the most recently requested
  system.
- Status reaches `Ready.` with no failed deliveries or stale payloads.
- Python and the rendered scene identify the same loaded system after every
  replacement.
