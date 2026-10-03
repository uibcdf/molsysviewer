---
summary: Annotation coordinate anchors and callout options lack a coherent public lifecycle
issue: uibcdf/molsysviewer#146
status: partial
opened: 2026-10-03
closed:
severity: high
verification: measured
area: [annotations, state, rendering]
guard: tests/test_design_review_closure.py::test_coordinate_annotation_lifecycle
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Annotation coordinate anchors and callout options lack a coherent public lifecycle

**Reported:** 2026-10-03, final pre-1.0 design review and principal-maintainer authorization.

## What

Public annotations.add(position=...) exposes coordinate anchors, world/camera offsets and leader styles, but normal digestion accepts only layout corners. Coordinate anchors also fail state export through list(None), cannot be edited consistently and are dropped during scene transfer.

## How

Inspected annotations.py, the position digester, viewer/state.py, layers.Annotation and annotation-handlers.ts. Mol* label offsets are camera-space shader offsets; using them as world displacement cannot place a label at an absolute coordinate. No fresh runtime reproduction is claimed.

## Why

Close the already exposed Python and Studio contract before 1.0. Preserve atom anchors, implement coordinate anchors with explicit units across editing/history/state/session/copy/extract, and qualify or reject unsupported callout combinations before any scene mutation.

## Acceptance

Real-demo Python guards for both anchor kinds, units, edit transitions and scene transfer; real Mol* browser evidence for coordinate/world rendering and supported leader styles. Advanced MVS annotation machinery remains post-1.0.

## What was refuted

Source inspection is recorded separately from runtime evidence. No new regression run is claimed at opening.

## Resolution

Implemented in the preserved working tree and locally qualified on 2026-10-03. Integration into a committed supported candidate remains pending. No closure or final release qualification is claimed.

The public coordinate and offset digesters now support finite physical triples and their declared legacy nm input. set_style has an annotation-specific dictionary seam. State stores typed coordinate anchors with units; editing, history, session, extraction and same-system copying preserve them. Mol* callouts use actual world coordinates and camera-basis offsets, distinct leader geometry and retained hidden-state editing. The trajectory owner awaits callout updates and drains outstanding frame writes before playback stops. Browser evidence uses a real three-structure pentalanine fixture. Full MVS remains deferred.

Evidence: `devguide/final_design_closure_20261003.json` and its named test/browser artifacts.
