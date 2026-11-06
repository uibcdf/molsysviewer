---
summary: Centroid measurements render bounding-sphere centers instead of geometric means
issue: uibcdf/molsysviewer#308
status: resolved
opened: 2026-11-06
closed: 2026-11-06
severity: high
verification: reproduced
area: [measurements, rendering, trajectory]
guard: molsysviewer/js/tests/e2e/coordinate-edits.e2e.ts
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Resolved: centroid measurement rendering

The Python/Studio centroid contract computes arithmetic means, including repeated
atom occurrences. The previous adapter passed complete structure loci to Mol*'s
measurement manager, whose distance/angle/dihedral representations use
bounding-sphere centers. This is a Viewer adapter defect; the post-1.0 dependency
upgrade in #115 is separate. It was found while preparing Analysis-to-scene
adoption under #264 / uibcdf/molsysmt#421.

## Reproduction

With real pentalanine structures `[0, 8, 3]`, the first endpoint `[0, 2, 4]`
and second `[5]` give **2.2465548711 Å** from independent coordinates and
Python. The actual Mol* 5.4.1/Chromium shape label instead reads **1.91 Å**;
its text anchor implies 1.9127484374 Å and an endpoint displaced by
0.41908 Å. The first dash is not an endpoint oracle because dash spacing
can offset it. Source inspection identifies the same boundary for angles
and dihedrals, which require independent numerical receiving.

Initial evidence: `/tmp/msv-centroid-render-probe-20261106.json`,
`/tmp/msv-centroid-render-probe-20261106.mjs` and
`/tmp/msv-centroid-render-before-20261106.json`; source profile Viewer
`a994f89c` (public/runtime code `737f9bc3`, JS `2e17ee6f`), owner contribution
`7c7b92a7c`, native MolSysMT `ed09f6453`, PyUnitWizard `02d0015`, Python 3.14.
The complete four-page inventory (278 issues / 306 items including PRs)
had no equivalent report at opening.

## Correction and acceptance

Keep Mol*'s distance/angle/dihedral visual factories, supplying zero-radius
point loci at the effective geometric means. Bind the transform to the
molecular structure so Mol* updates geometry with its dependency tree before
trajectory/coordinate completion. Keep the original atom occurrences as
parameters, preserve participant identity and use the existing native route
for atomic/representative endpoints. Do not change molecular coordinates.

Receive real asymmetric populations for all three measurement kinds against
independent coordinate oracles, including repeated occurrences, units,
frame/coordinate changes, visibility/rename/history/replay and popup hosts.
No source correction qualifies public packages or closes broader scientific
session receiving. Human Jupyter/Qt review remains postponed.

Final scope, original diagnostics and retained source hashes are in the
[measurement receiving receipt](../measurement_geometry_receiving_20261106.json).
Source correction does not qualify public artifacts or postponed human review.
