---
summary: Canvas popup playback needs frame convergence with derived scene objects
issue: uibcdf/molsysviewer#238
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: high
verification: measured
area: [canvas, popup, playback]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Canvas popup playback needs frame convergence with derived scene objects

**Reported:** 2026-10-13, maintainer-requested bidirectional mirror audit after uibcdf/molsysviewer#232. Real Python pentalanine structures [0, 8, 3], actual widget bootstrap/authority with adapted comm transport, and drawing Mol*/Chromium canvases. Development interpreter: `molsyssuite@uibcdf_3.14`.

## What

A loaded real scene with Buch hbonds had original frame 0 and popup frame 1 after both reported stopped. An isolated stop converged after transport drain and settling, so persistence under loaded geometry remains unqualified. Diagnose clocks and final frame projections; verify stop after applied geometry in both directions, interactions/frame correspondence and absence of delayed updates. Existing step guards do not cover this case.

## How

Both canvases could run competing playback clocks. The popup now follows absolute applied original-canvas frames; play/stop controls await their local operation before sending the authority intent. Stop drains pending frame and derived-geometry work before final projection. Python sends the stopped authoritative frame without adding a replay/history command. FPS/step summaries update controls without moving the renderer or starting another clock; changing FPS while playing preserves playback.

## Why

The external canvas is a second endpoint of the same molecular session. Scientific scene changes must converge in both directions; window-local layout must follow an explicit symmetric rule. The controls guard for uibcdf/molsysviewer#232 did not qualify these behaviors.

## What was refuted

Passing shared-control tests and a matching initial scene are insufficient to establish continuing molecular-state convergence. This work does not qualify the separate experimental Qt popup (uibcdf/molsysviewer#51) or future package bytes. Publication remains paused.

## Resolution

Implemented in the shared owners. The real browser guard starts and stops from both windows with calculated Buch hbonds present, changes FPS through Python, and checks displayed frames, frame-specific interaction geometry and no later frame drift. The authority guard confirms runtime-only final reconciliation.

The bounded guard is `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`,
with the native scientific receiving scenario in `canvas-popup-mirror-scenarios.ts`.
Its build/core registration is checked offline by `tests/test_reporting_protocol.py`.
See the [maintained evidence receipt](../canvas_popup_mirror_validation_20261013.json)
and [current contract](../canvas_popup_contract.md) for results and scope.
Source checks do not qualify installed package bytes, the experimental Qt popup
or either paused 1.0 publication.
