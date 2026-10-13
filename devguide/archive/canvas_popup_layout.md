---
summary: Studio popup layout is coupled to the notebook in only one direction
issue: uibcdf/molsysviewer#237
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: medium
verification: reproduced
area: [canvas, popup, layout]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Studio popup layout is coupled to the notebook in only one direction

**Reported:** 2026-10-13, maintainer-requested bidirectional mirror audit after uibcdf/molsysviewer#232. Real Python pentalanine structures [0, 8, 3], actual widget bootstrap/authority with adapted comm transport, and drawing Mol*/Chromium canvases. Development interpreter: `molsyssuite@uibcdf_3.14`.

## What

Notebook Studio Dock/ambient changes project into the canvas popup, while the same popup actions remain local. Define symmetric window-local layout for Dock, opacity/background lock, panel expansion/navigation and fullscreen, retaining shared canvas preferences. Opening a popup should inherit preferences and initial layout, then each window owns its layout. Test both directions and shared settings.

## How

The widget forwarded local shell layout while popup shell changes did not have an equivalent reverse projection. Dock/Float and ambient state now remain local in both directions; the declared canvas preference traits continue to synchronize. Initial layout inheritance remains explicit.

## Why

The external canvas is a second endpoint of the same molecular session. Scientific scene changes must converge in both directions; window-local layout must follow an explicit symmetric rule. The controls guard for uibcdf/molsysviewer#232 did not qualify these behaviors.

## What was refuted

Passing shared-control tests and a matching initial scene are insufficient to establish continuing molecular-state convergence. This work does not qualify the separate experimental Qt popup (uibcdf/molsysviewer#51) or future package bytes. Publication remains paused.

## Resolution

Implemented in the shared owners. The browser guard docks and floats each window separately and asserts the other stays floating. The existing controls scenario retains preference synchronization and Studio panel popout assertions.

The bounded guard is `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`,
with the native scientific receiving scenario in `canvas-popup-mirror-scenarios.ts`.
Its build/core registration is checked offline by `tests/test_reporting_protocol.py`.
See the [maintained evidence receipt](../canvas_popup_mirror_validation_20261013.json)
and [current contract](../canvas_popup_contract.md) for results and scope.
Source checks do not qualify installed package bytes, the experimental Qt popup
or either paused 1.0 publication.
