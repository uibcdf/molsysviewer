---
summary: Studio silently converts a missing annotation coordinate to zero
issue: uibcdf/molsysviewer#203
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [studio, frontend]
guard: molsysviewer/js/tests/e2e/studio-list-workflows.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Studio final review — coordinates

**Reported:** 2026-10-10, final Studio review with real pentalanine and Mol*/Chromium.

## What
In Annotations > Coordinates, clear X and enter annotation text: Create remains enabled and submits position=[0,0,0]. Missing input silently becomes a valid origin coordinate.

## How
Reproduced on the real Mol* Studio form. annotations-panel.ts uses Number(value) || 0.0 and only tests annotation text for coordinate creation readiness.

## Why
Coordinate annotations need explicit, finite coordinates. Keep missing/invalid values invalid, disable creation, show an inline explanation, validate the Python boundary, and guard recovery with explicit zero still accepted.

## What was refuted

Explicit zero is a valid coordinate. The defect is silently supplying zero for absent input, not positioning an annotation at the origin.

## Resolution

Coordinate fields retain missing values as invalid rather than zero. Creation is disabled with an inline hint until all three values are finite. The real browser guard checks missing X through a background repaint, explicit-zero recovery, pending form preservation and success clearing. tests/test_studio_creation_feedback.py rejects missing/nonfinite/malformed triples before mutation and verifies the nm-to-Angstrom boundary under both nm and Angstrom session policies.

**Executed:** 14/14 focused Python cases; TypeScript no-emit check; npm JS unit suite; real pentalanine/Mol*/Chromium Studio guard. These are source/development checks, not installed artifact qualification. The complete Python run and hosted gates retain their separate outcomes.
