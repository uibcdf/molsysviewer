---
summary: Active selection retains an old atom subset within the same group
issue: uibcdf/molsysviewer#235
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: high
verification: reproduced
area: [canvas, popup, selection_membership]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Active selection retains an old atom subset within the same group

**Reported:** 2026-10-13, maintainer-requested bidirectional mirror audit after uibcdf/molsysviewer#232. Real Python pentalanine structures [0, 8, 3], actual widget bootstrap/authority with adapted comm transport, and drawing Mol*/Chromium canvases. Development interpreter: `molsyssuite@uibcdf_3.14`.

## What

Replacing atom indices [0,1,2] with [4,5] in the first group of the real pentalanine demo immediately retains [0,1,2]. ActiveSelection.signature and sameItems omit membership. Distinguish item toggle identity from complete selected membership; cover partial atom and shape subelement replacements, canonical projections and undo/redo.

## How

ActiveSelectionController.sameItems compared coarse group signatures and retained the old item values. Replacement now installs the new membership and local loci, independently of the signature used for Shift toggles.

## Why

The external canvas is a second endpoint of the same molecular session. Scientific scene changes must converge in both directions; window-local layout must follow an explicit symmetric rule. The controls guard for uibcdf/molsysviewer#232 did not qualify these behaviors.

## What was refuted

Passing shared-control tests and a matching initial scene are insufficient to establish continuing molecular-state convergence. This work does not qualify the separate experimental Qt popup (uibcdf/molsysviewer#51) or future package bytes. Publication remains paused.

## Resolution

Implemented in the shared owners. The real authority/browser guard replaces [0, 1, 2] with [4, 5] within the same molecular group from opposite endpoints, then applies [0, 1] from Python; both atom subsets converge exactly. JS units cover membership and subelement replacement.

The bounded guard is `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`,
with the native scientific receiving scenario in `canvas-popup-mirror-scenarios.ts`.
Its build/core registration is checked offline by `tests/test_reporting_protocol.py`.
See the [maintained evidence receipt](../canvas_popup_mirror_validation_20261013.json)
and [current contract](../canvas_popup_contract.md) for results and scope.
Source checks do not qualify installed package bytes, the experimental Qt popup
or either paused 1.0 publication.
