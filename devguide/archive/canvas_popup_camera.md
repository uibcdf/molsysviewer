---
summary: Canvas popup camera diverges after focus, pointer release and automatic motion
issue: uibcdf/molsysviewer#234
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: high
verification: reproduced
area: [canvas, popup, camera]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Canvas popup camera diverges after focus, pointer release and automatic motion

**Reported:** 2026-10-13, maintainer-requested bidirectional mirror audit after uibcdf/molsysviewer#232. Real Python pentalanine structures [0, 8, 3], actual widget bootstrap/authority with adapted comm transport, and drawing Mol*/Chromium canvases. Development interpreter: `molsyssuite@uibcdf_3.14`.

## What

Focus All in either window, final pointer snapshots and Spin/Stop can leave different camera snapshots. A real notebook/Python/Mol* audit reproduced this after uibcdf/molsysviewer#232. Share the resolved camera and one motion authority, preserve bidirectional pointer input, prevent projection echoes, and verify focus/reset/drag/wheel/Spin/Swing in both directions.

## How

Camera sync gated notifications on a pressed pointer and used a debounce that could postpone automatic motion. Each endpoint also ran its own Spin/Swing clock. The shared CameraSync owner now relays changed drawn snapshots with a throttle, consumes matching incoming projections without echo and keeps local input priority. The popup retains motion settings but follows the original canvas clock.

## Why

The external canvas is a second endpoint of the same molecular session. Scientific scene changes must converge in both directions; window-local layout must follow an explicit symmetric rule. The controls guard for uibcdf/molsysviewer#232 did not qualify these behaviors.

## What was refuted

Passing shared-control tests and a matching initial scene are insufficient to establish continuing molecular-state convergence. This work does not qualify the separate experimental Qt popup (uibcdf/molsysviewer#51) or future package bytes. Publication remains paused.

## Resolution

Implemented in the shared owners. The browser guard moves both actual cameras through drag/wheel, focus/reset transitions, Spin/Stop and Swing/Stop, and asserts final snapshot convergence plus a disabled popup motion clock.

The bounded guard is `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`,
with the native scientific receiving scenario in `canvas-popup-mirror-scenarios.ts`.
Its build/core registration is checked offline by `tests/test_reporting_protocol.py`.
See the [maintained evidence receipt](../canvas_popup_mirror_validation_20261013.json)
and [current contract](../canvas_popup_contract.md) for results and scope.
Source checks do not qualify installed package bytes, the experimental Qt popup
or either paused 1.0 publication.
