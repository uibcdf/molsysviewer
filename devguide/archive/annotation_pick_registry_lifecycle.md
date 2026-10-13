---
summary: Annotation replacement retains deleted representation refs in the pick registry
issue: uibcdf/molsysviewer#243
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: medium
verification: reproduced
area: [annotations, canvas, lifecycle]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Annotation replacement retains deleted representation refs in the pick registry

**Reported:** 2026-10-13, real GPU pick/registry diagnostic while extending uibcdf/molsysviewer#236 and uibcdf/molsysviewer#241 to edited annotations.

## What

After `view.annotations["mirror-label"].set_text("Mirror revised")`, the drawing endpoint's annotation registry contains the deleted old transform and the new live representation. Repeated edits accumulate dead reference strings; lookup scans them before reaching live geometry.

## How

Annotation clear/replacement/drop removed transforms without unregistering their refs. Paired callbacks now invoke the existing StateHandlers.unregisterTaggedRef owner on per-tag clear, bulk clear and drop; live replacement registers its new ref normally.

## Why

Portable object picks need a current, bounded local representation registry. The defect affects the original and popup alike and is independent of scientific detection.

## What was refuted

A deleted ref is not another live label or a necessary selection ghost: the native diagnostic shows no data for it. Waiting for a draw resolves the separate stale GPU pick-image timing, but cannot remove a retained registry entry.

## Resolution

Implemented in the shared owners. After real text replacement, the browser guard checks that each annotation registry has exactly one ref and that it belongs to a live transform. A retained deleted ref fails this assertion even when picking eventually finds the new geometry.

The bounded guard is `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`,
with the native scientific receiving scenario in `canvas-popup-mirror-scenarios.ts`.
Its build/core registration is checked offline by `tests/test_reporting_protocol.py`.
See the [maintained evidence receipt](../canvas_popup_mirror_validation_20261013.json)
and [current contract](../canvas_popup_contract.md) for results and scope.
Source checks do not qualify installed package bytes, the experimental Qt popup
or either paused 1.0 publication.
