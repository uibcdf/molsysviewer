---
summary: Align Studio visibility wording and add concise workflow examples.
issue: uibcdf/molsysviewer#225
status: resolved
opened: 2026-10-10
closed: 2026-10-10
verification: inspected
area: [studio, interactions]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative:
blocked_by: []
supersedes: []
---

## What
Finish Studio visibility vocabulary and contextual form guidance before 1.0, as authorized after the final cross-surface review.

## How
Use visibility terminology for interaction representations, distinguish effective layer visibility, and add concise folded examples to specialized loading, interaction and geometry/persistence workflows. Preserve explicit calculation/display scopes, units, periodic limits and file ownership. Examples guide existing operations rather than claiming new detectors or automatic alignment.

## Why
Region enable/disable already has a distinct contract; interaction Show/Hide should not be described as enablement. Specialized forms benefit from concrete examples without expanding ordinary reading density.

## Resolution — 2026-10-10
Visible/Hidden/Hidden by layer replaces interaction enablement wording; counts respect layer visibility. Folded examples explain loading, structure coverage, geometry and persistence.

Guard: `molsysviewer/js/tests/e2e/studio-usability.e2e.ts`. The real Studio browser workflow additionally checks
coordinate focus, layer-hidden wording, JSON/MSV confirmation/retry/correlation,
PNG scale/alpha and unavailable exported-host actions. Focused Python file/action
checks pass 27/27; final figure/image checks pass 40/40. Local full-suite and
experimental Qt limitations remain in `studio_coverage_20261010.md`; no package
is qualified and no 1.0 publication is authorized by this closure.
