---
summary: All eight advanced Shapes examples disagree with public Python signatures
issue: uibcdf/molsysviewer#192
status: resolved
opened: 2026-10-09
closed: 2026-10-10
severity: medium
verification: reproduced
area: [studio]
guard: tests/test_studio_shape_examples.py
normative:
blocked_by: []
supersedes: []
---

# All eight advanced Shapes examples disagree with public Python signatures

**Reported:** 2026-10-09, second Studio review and authorized refinement.

## What

Signature binding rejects all eight snippets because positional inputs are sent to keyword-only methods; several examples also use obsolete data/option names.

## How

Correct every example and execute real minimal fixtures using current public owners, digesters and unit conventions.

## Why

The principal maintainer authorizes this refinement round before the next 0.25.0 candidate freeze. Both 1.0 publications remain paused. Consumer source: 01208af0 after the first Studio round. Implementation must retain real molecular/browser guards, native backend ownership and explicit qualification scope.

## What was refuted

Source signature inspection is not full scientific/artifact qualification. No publication is authorized by this implementation.

## Resolution — 2026-10-10

All eight previous supplied-geometry examples now use the actual keyword-only
public signatures and supported option names. Ring geometry adds a ninth guide
with explicit centers, dimensionless normals and length radii; it does not claim
aromaticity detection. Interaction sites use their current public method.
The guard extracts all nine snippets from the TypeScript catalogue and executes
them with real quantity arrays through digested public Python methods. It asserts
that each creates a shape, including the actual (n_triangles, 3, 3) triangle input.
All nine execute; the focused creation/catalogue/batch run passes 32/32.
