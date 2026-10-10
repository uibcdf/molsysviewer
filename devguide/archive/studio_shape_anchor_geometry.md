---
summary: Studio atom-anchored displacement vectors fail and ignore the visible structure
issue: uibcdf/molsysviewer#190
status: resolved
opened: 2026-10-09
closed: 2026-10-10
severity: medium
verification: reproduced
area: [studio]
guard: tests/test_studio_shape_creation.py::test_shape_centers_use_all_unique_atoms_and_visible_structure
normative:
blocked_by: []
supersedes: []
---

# Studio atom-anchored displacement vectors fail and ignore the visible structure

**Reported:** 2026-10-09, second Studio review and authorized refinement.

## What

Creating a vector on real pentalanine raises AttributeError for view._msm. The route hardcodes structure 0 and silently uses the first atom from a staged set.

## How

Resolve validated atom-set centers from view.molsys in the visible structure, document snapshot geometry, preserve explicit coordinates and test units/current-frame semantics.

## Why

The principal maintainer authorizes this refinement round before the next 0.25.0 candidate freeze. Both 1.0 publications remain paused. Consumer source: 01208af0 after the first Studio round. Implementation must retain real molecular/browser guards, native backend ownership and explicit qualification scope.

## What was refuted

Source signature inspection is not full scientific/artifact qualification. No publication is authorized by this implementation.

## Resolution — 2026-10-10

Validated atom sets now resolve their unique atoms' geometric centers from
`view.molsys` at `view.player.index`. Links and arrows are fixed geometry in nm,
passed as explicit quantities and converted to the Å wire format. Atom-anchored
spheres retain moving anchors. The guard compares actual centers/endpoints in a
nonconsecutive three-structure pentalanine selection under both nm and angstrom
standardization policies; changing the visible structure does not move a snapshot.
The focused creation/catalogue/batch run passes 32/32 cases.
