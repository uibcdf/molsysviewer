---
summary: Explicit-position and callout annotation text is not pickable in the canvas
issue: uibcdf/molsysviewer#241
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: medium
verification: reproduced
area: [annotations, canvas, popup]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Explicit-position and callout annotation text is not pickable in the canvas

**Reported:** 2026-10-13, native GPU pick in the real notebook/popup mirror guard for uibcdf/molsysviewer#236.

## What

A visible label at `[0, 30, 0]` angstrom has correct geometry and ownership but its text render object reports `pickable: false`. Neither canvas can pick its visible text. The leader line remains pickable when present.

## How

Mol* Text.updateRenderableState sets pickable=false, including during creation. The managed callout representation now explicitly enables picking after both createOrUpdate paths. Structure-anchored tooltip labels retain their existing route.

## Why

Managed annotations are context-menu targets and must preserve native object selection in both endpoints. A correct portable identity cannot compensate for an object the renderer refuses to pick.

## What was refuted

The label has the intended position, owner, visible representation and background. Increasing its size did not help; inspecting the native render state established the non-pickable default. No synthetic loci or mocked calculation was used for the failing native pick.

## Resolution

Implemented in the shared owners. The native GPU guard finds visible callout text, selects it from the original canvas, verifies its selected marker in both windows, edits its text and picks the new geometry from the popup. It waits for a real GPU hit rather than substituting synthetic loci or a summary-only check.

The bounded guard is `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`,
with the native scientific receiving scenario in `canvas-popup-mirror-scenarios.ts`.
Its build/core registration is checked offline by `tests/test_reporting_protocol.py`.
See the [maintained evidence receipt](../canvas_popup_mirror_validation_20261013.json)
and [current contract](../canvas_popup_contract.md) for results and scope.
Source checks do not qualify installed package bytes, the experimental Qt popup
or either paused 1.0 publication.
