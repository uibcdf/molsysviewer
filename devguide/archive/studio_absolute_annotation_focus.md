---
summary: Studio cannot focus annotations anchored at absolute coordinates.
issue: uibcdf/molsysviewer#223
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: low
verification: reproduced
area: [studio, camera]
guard: tests/test_studio_work_persistence.py::test_coordinate_annotation_focus_uses_live_owner_and_rejects_missing_tag
normative:
blocked_by: []
supersedes: []
---

## What
Studio disables an annotation's Focus button whenever it has no associated atoms. The public Annotation.focus() already supports absolute coordinate anchors as well as live molecular centroids.

## How
AnnotationsPanel calls an atom-list callback and disables Focus on empty atomIndices. Route tagged annotation focus through the existing annotation owner, with truthful availability for broken anchors and supported exported hosts.

## Why
The final cross-surface review found a working public operation missing from the same object's Studio controls. The principal maintainer authorizes closing this before 1.0. Verify real coordinate-anchored and atom-anchored annotations and preserve selection.

## Resolution — 2026-10-10
Live tagged annotation Focus uses Annotation.focus, including absolute coordinates; broken anchors and exported-host availability remain explicit.

Guard: `tests/test_studio_work_persistence.py::test_coordinate_annotation_focus_uses_live_owner_and_rejects_missing_tag`. The real Studio browser workflow additionally checks
coordinate focus, layer-hidden wording, JSON/MSV confirmation/retry/correlation,
PNG scale/alpha and unavailable exported-host actions. Focused Python file/action
checks pass 27/27; final figure/image checks pass 40/40. Local full-suite and
experimental Qt limitations remain in `studio_coverage_20261010.md`; no package
is qualified and no 1.0 publication is authorized by this closure.
