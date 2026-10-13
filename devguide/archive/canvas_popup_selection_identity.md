---
summary: Canvas popup selection loses selected scene object identity
issue: uibcdf/molsysviewer#236
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: high
verification: reproduced
area: [canvas, popup, selection_identity]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Canvas popup selection loses selected scene object identity

**Reported:** 2026-10-13, maintainer-requested bidirectional mirror audit after uibcdf/molsysviewer#232. Real Python pentalanine structures [0, 8, 3], actual widget bootstrap/authority with adapted comm transport, and drawing Mol*/Chromium canvases. Development interpreter: `molsyssuite@uibcdf_3.14`.

## What

A real-controller shape selection carries source_kind=shape and its tag immediately, then actual Python set_active_selection projections reduce it to element/atom_indices. Preserve serializable object/subelement identity across endpoints and rebuild local picking loci; do not transmit Mol* object references. The audit observed metadata loss, not native shape picking pixels. Extend real-browser guards to native shape/annotation picking and highlight in both directions.

## How

Python and popup bootstrap projected atoms without portable object identity. The private projection now retains whitelisted owner kind/tag, groups/instances and occurrence references; each endpoint resolves its own current Mol* loci. Incoming projections suppress another Python intent. State/history preserves the optional pick while retaining legacy atom-only support. An unchanged re-pick must also project: after an edit, its portable identity can be equal while its local geometry has changed.

## Why

The external canvas is a second endpoint of the same molecular session. Scientific scene changes must converge in both directions; window-local layout must follow an explicit symmetric rule. The controls guard for uibcdf/molsysviewer#232 did not qualify these behaviors.

## What was refuted

Passing shared-control tests and a matching initial scene are insufficient to establish continuing molecular-state convergence. This work does not qualify the separate experimental Qt popup (uibcdf/molsysviewer#51) or future package bytes. Publication remains paused.

## Resolution

Implemented in the shared owners. The real browser guard performs GPU picks of a sphere and an annotation from opposite endpoints, checks selected marker bits in both windows, edits the annotation and picks it again from the popup. It rejects occurrence refs from a different frame. Real-system Python guards cover detached popup snapshots, history/state restoration and unchanged re-pick projection without an extra history entry.

The bounded guard is `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`,
with the native scientific receiving scenario in `canvas-popup-mirror-scenarios.ts`.
Its build/core registration is checked offline by `tests/test_reporting_protocol.py`.
See the [maintained evidence receipt](../canvas_popup_mirror_validation_20261013.json)
and [current contract](../canvas_popup_contract.md) for results and scope.
Source checks do not qualify installed package bytes, the experimental Qt popup
or either paused 1.0 publication.
