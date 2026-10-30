---
summary: Qt persists expanded dimensions as the normal window size.
issue: uibcdf/molsysviewer#280
status: resolved
opened: 2026-10-30
closed: 2026-10-30
severity: medium
verification: reproduced
area: [standalone, qt, usability]
guard: tests/test_qt_window_polish.py::test_native_status_details_and_normal_geometry
normative:
blocked_by: []
supersedes: []
---

# Qt normal geometry restoration

## What

The native host saved current width/height when maximized/fullscreen and reused
them as ordinary startup dimensions. In a real Qt probe a 900x600 normal window
was persisted as 800x800 despite normalGeometry retaining the original size.
Saved dimensions also shadowed explicit launcher dimensions.

## How

`standalone_qt/geometry.py` captures normal geometry separately from maximized
state. The existing desktop metadata keeps legacy window_size and adds normal
geometry/screen/state. Startup never restores fullscreen. Explicit positive
width/height take precedence and start a normal window; omitted values restore
metadata with a 1440x960 fallback. Argument digesters admit None only at this
experimental Qt boundary. Geometry is clamped to available screen bounds;
Wayland global placement remains the compositor's responsibility.

## Why and receiving

Closing fullscreen must not redefine the user's normal window, and explicit
launch arguments must work. The actual-widget child checks normal/max/full
capture, saved metadata/readback, removed-screen/offscreen-coordinate fallback,
legacy dimensions and explicit overrides. This is widget policy evidence,
not physical multi-monitor or Windows/macOS qualification. See the
[receipt](../standalone_window_polish_receiving_20261030.json).

## Resolution — 2026-10-30

Implemented in `7900263691cd96fcf74840357cc2e7ca8ef62914`. The child receives real Qt normal/max/full geometry, writes/reads owned desktop metadata, restores legacy size, clamps offscreen coordinates and checks explicit dimensions. No physical multi-monitor/platform certification is inferred.

Local regression covers 3,318 distinct passing cases across the original run
and directed test-provenance recovery, with 21 skips retained; 332 JS units
and 44 core browser suites pass. This is not one clean full pytest run.
Hosted CI and the postponed maintainer visual review retain their own states
in the receiving record. Qt remains experimental; no publication follows.
