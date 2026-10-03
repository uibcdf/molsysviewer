---
summary: Extraction drops interaction display coverage for repeated structures.
issue: uibcdf/molsysviewer#156
status: resolved
opened: 2026-10-03
closed: 2026-10-03
severity: medium
verification: reproduced
area: [interactions, extraction, state]
guard: tests/test_scene_transfer.py::test_extraction_retains_interaction_filter_for_every_repeated_structure
normative:
blocked_by: []
supersedes: []
---

# Repeated structures lose interaction display coverage

## What

`view.extract(structure_indices=[2, 0, 2])` retains both scientific copies of
an observation from structure 2, but a visual set filtered to `[2]` becomes
filtered to `[2]` in the destination. The correct destination filter is `[0, 2]`.
Structure 0 incorrectly reports `excluded` despite containing the observation.

## How

The integration review reproduced this on a real pentalanine three-structure
view with a named sparse hydrogen-bond fixture evaluated at local structure 2.
The extracted analysis has two occurrences, but its visual statuses are
`excluded`, `excluded`, `evaluated`. No scientific method was mocked.

The canonical scene transfer builds a scalar original-to-destination structure
dictionary. Repeated source structures overwrite earlier destinations.

## Correction

Map a visual structure filter to every matching destination in extraction
order. A scalar current frame uses the first retained copy of its source frame.
Scientific analysis remapping remains with MolSysMT. Source correspondence and
trajectory event transfer retain their existing handling of repeated structures.

## Verification

Guard: `tests/test_scene_transfer.py::test_extraction_retains_interaction_filter_for_every_repeated_structure`.
It checks both projected copies, the excluded unrelated frame, scientific
occurrence coverage, original-source correspondence, current frame and a complete
MSV session round trip. All seven scene-transfer guards pass in
`molsyssuite@uibcdf_3.14` (Python 3.14.7), with the editable provider.
The final once-run source regression passes 2,805 tests with 23 explicit skips
in 510.35 s. The reviewed fix and guard are committed and pushed at
`0dea171db750c289e6b1f85c2407f91f3ce58f4a`. This closes the source-transfer defect;
compatible published-provider and exact release-artifact qualification remain
separate under #114/#140. No new hosted or complete installed result is claimed.

The first guard attempt assigned the read-only `player.index` property and
stopped at its setup. The corrected guard uses `player.go_to_structure(2)`;
the setup failure is not additional evidence about the product defect.
