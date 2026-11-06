---
summary: Measurement visibility cycles retain deleted renderer references
issue: uibcdf/molsysviewer#313
status: resolved
opened: 2026-11-06
closed: 2026-11-06
severity: medium
verification: reproduced
area: [measurements, lifecycle, picking]
guard: molsysviewer/js/tests/e2e/coordinate-edits.e2e.ts
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Resolved: measurement reference lifecycle

The first complete core run for #308–#312 passes seven suites, then the new
renamed-measure context assertion fails. Geometry/value receiving itself is
correct. The test helper chose the first registered ref, which was deleted
by an earlier hide; it must use the production live-loci resolver instead.

There is also genuine registry debt: the measurement manager removes rendered
objects without unregistering their refs from StateHandlers. Repeated show/hide
cycles retain dead refs and rename carries those forward. Annotation #243
already has this lifetime callback, but measurements do not. Picking's live
resolver skips missing cells, so this is not a disappearing-measure claim.

The scoped fix mirrors the existing unregister callback on hide/clear/drop.
The real pentalanine/Mol* guard additionally cycles both atomic/native and
centroid measures three times, requiring an empty registry while hidden and
only the original number of live refs on show, then checks the actual shape's
production context owner before/after rename. The first failed core run is
retained at `/tmp/msv-measurement-core-e2e-20261106.log` (496.02 s); no later
local or hosted gate may describe it as passing. The final affected browser
lane passes in 81.97 s, including the new production-owner assertions.

A separate real-Mol* probe reconstructs the pre-#313 measurement handler and
controller from the staged index. Three visibility cycles grow centroid refs
from one to four and atomic refs from two to eight, retaining deleted cells.
The identical probe after the fix keeps one/two live refs and none while hidden.
Its expected failing baseline and passing correction are retained in
`/tmp/msv-measurement-ref-before-20261106.log` and
`/tmp/msv-measurement-ref-after-20261106.log`. The production live-loci resolver
also replaces the test helper's incorrect first-ref assumption. No numerical
or renamed-owner assertion is removed.

Final evidence and remaining gate scope are in the
[measurement receiving receipt](../measurement_geometry_receiving_20261106.json).
