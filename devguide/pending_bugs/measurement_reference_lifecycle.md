---
summary: Measurement visibility cycles retain deleted renderer references
issue: uibcdf/molsysviewer#313
status: active
opened: 2026-11-06
closed:
severity: high
verification: reproduced
area: [measurements, lifecycle, picking]
guard: molsysviewer/js/tests/e2e/coordinate-edits.e2e.ts
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Reopened: measurement reference lifecycle

The complete core run on `1187fc18` passes 24 suites, then fails in
`measures-subpanel`: its old hide assertion expects dead refs to remain
registered. Replacing that expectation with an empty registry **and absence
of the actual old Mol* nodes** reveals a real deletion-order regression.
`dropTag()` unregisters refs before `StateHandlers.deleteLayer()` obtains
them, so deletion can leave unregistered geometry alive. The annotation
retirement path has the same ordering risk.

The correction snapshots physical refs before retiring the handler's identity,
then awaits removal of those nodes. Early retirement still prevents later
rebuilds. Guards inspect the actual state cells after hide and delete, rebuild
on show and restore on undo; the panel fixture now loads real pentalanine
structures `[0, 8, 3]` with independent frame-value oracles.

The failed complete run is retained in
`/tmp/msv-measurement-final-core-receipt-20261106.json`: exit 1, 812.146 s,
1,139 selected input hashes and both source heads unchanged. Its remaining
19 suites did not run. The stronger panel reproduction fails before the fix
in `/tmp/msv-measures-panel-lifecycle-receiving-20261106.log`. A complete
corrected core run and updated hosted evidence remain pending.

The correction passes the four affected actual-browser suites (annotations,
managed coordinate edits and live measurements, measurement panel, scene-object
panel roundtrip), including real widget/canvas/Studio popups. The measurement
panel additionally uses nonbonded atoms `[0, 5]`, with independently calculated
display values `0.277`, `0.312`, `0.322 nm`; a fixture assertion requires the
first two displayed values to differ. This prevents a fixed covalent distance
from making a stale frame value unobservable. Complete-gate receiving remains
separate; see the [followup receipt](../measurement_geometry_receiving_20261106.json).

## Initial closure and retained evidence

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
