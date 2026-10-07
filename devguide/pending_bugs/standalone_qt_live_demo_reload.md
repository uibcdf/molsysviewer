---
summary: In the standalone Qt host, replacing the loaded demo leaves the previous system on screen.
issue: uibcdf/molsysviewer#35
status: partial
opened: 2026-07-04
closed:
severity: high
verification: reproduced
area: [standalone, qt]
guard:
normative:
blocked_by: []
supersedes: []
---

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

Rechecked on 2026-08-09: the executor had only an SSH session. Although
`/tmp/.X11-unix/X0` existed, `DISPLAY=:0 glxinfo -B` failed with
`Authorization required, but no authorization protocol specified`; there was no
user-owned Xorg/Wayland desktop session to attach to. No virtual-display result
is substituted for the required visible human/GPU observation.

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

## Hosted Qt observation — 2026-10-07

Exact-head standard CI `37629258208` on Viewer `513391c1` fails
`tests/test_standalone.py::test_qt_live_model_smoke_real_window` at line 1951.
The bridge never becomes ready: the frontend reports an exported scene with no
WebGL canvas and cannot create a WebGL rendering context. The failing lane is
Xvfb/software WebGL; this is not the required visible native-GPU observation.
It therefore neither closes the reload defect nor establishes a reload regression:
startup failed before the replacement workflow. Qt remains experimental.

The compact Actions diagnostic selected nearby DBus stderr as its cause. Native
logs established the assertion above; that diagnostic limitation is reported in
uibcdf/gh-run-receptor#62. No DBus workaround, renderer change or blind rerun is
introduced. The original standard CI verdict remains failure even though its
scientific/lint jobs pass. Keep Qt admission/provider migration under #109/#113
and the existing workstation validation criteria separate.
