---
summary: Replacement loading and system edit validation can mutate the scene before failing
issue: uibcdf/molsysviewer#148
status: resolved
opened: 2026-10-03
closed: 2026-10-07
severity: high
verification: measured
area: [load, live_edit]
guard: tests/test_design_review_closure.py::test_invalid_replacement_conversion_preserves_scene
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Replacement loading and system edit validation can mutate the scene before failing

**Resolved — 2026-10-07:** Replacement conversion and identity preparation, and conditional append accounting, complete before Viewer-owned mutation. Refused requests preserve system identity, overlays, source records, analyses, messages and history. Prior external mutations and arbitrary renderer failures are not covered by rollback.

The supported-public-package qualification boundary is complete in Viewer
0.24.0 build 1 / MolSysMT 0.23.0 ABI3 build 0. Earlier dated sections retain
their original observations; current hosted failures are recorded separately.

**Current qualification — 2026-10-06:** implementation is committed and
integrated in Viewer 0.24.0 build 1 with MolSysMT 0.23.0 ABI3 build 0. All
sixteen installed staging cells and 39 hosted core browser suites pass;
canonical-source Python 3.14 integration passes on all three native hosts,
with 25 documented notebooks passing on Linux. This report remains partial
for its public-provider/release qualification; staging evidence does not
close that gate. See the [current handoff](../checkpoints.md#resume-in-one-page)
and [exact candidate receipt](../stabilization_024_preparation_20261006.json).
Earlier dated sections retain their original scope.

**Reported:** 2026-10-03, final pre-1.0 design review and principal-maintainer authorization.

## What

load(mode='replace') clears the viewer before MolSysMT conversion succeeds. apply_system_edit(load_blocks='append') checks required appended_n_atoms only after replacing the system and rebuilding the scene.

## How

Inspected viewer/load.py and viewer/core.py. Conversion and joint argument validation need preparation before Viewer-owned mutations.

## Why

A failed load or invalid edit request must preserve the current scene. Existing external edits remain the caller's responsibility; no rollback of prior caller mutations is promised.

## Acceptance

Real-demo guards checking system identity, overlays, history and outgoing messages remain unchanged on invalid replacement/conversion and missing append accounting.

## What was refuted

Source inspection is recorded separately from runtime evidence. No new regression run is claimed at opening.

## Resolution

Implemented in the preserved working tree and locally qualified on 2026-10-03. Integration into a committed supported candidate remains pending. No closure or final release qualification is claimed.

The owning loader separates preparation (conversion, selected source maps and scale checks) from commit. Replacement resets only after preparation succeeds. Conditional append accounting is validated before analysis invalidation, assignment and rebuild. These guards protect conversion/argument failures, not a rollback of every renderer or external-provider mutation.

Evidence: `devguide/final_design_closure_20261003.json` and its named test/browser artifacts.

## Reviewed source integration — 2026-10-03

The accumulated source is reviewed, committed and pushed in `0dea171d`.
The final source regression passes 2,805 tests with 23 explicit skips in
`molsyssuite@uibcdf_3.14`; Ruff, TypeScript and runtime rebuild pass.
Earlier installed/browser observations retain their original inputs. This
internal integration used the existing deferred CI route and does not certify
an exact hosted or published-provider candidate. The report remains partial
for its existing supported-artifact/release qualification. See
[`integration_review_20261003.md`](../integration_review_20261003.md).

## Final closure evidence — 2026-10-07

The exact public pair passes sixteen installed cells in `37587631519`; published
producers and package bytes remain unchanged. Fresh isolated qualification passes
**27 tests, zero failures/errors/skips**, with both scientific imports verified
in site-packages: 13 design-review cases and 14 identity/loading cases. The local
qualification uses original staging files promoted unchanged; public-channel
availability is established separately by the verified sixteen-cell run.

All twelve labels-guide Python blocks execute against that installed pair. A
separate old atom-name-only fingerprint probe deliberately changes a saved index
and verifies identity re-resolution restores the intended atom with a mismatch
warning. The new coordinate/world-offset and reanchor examples name units
explicitly. The initial drafted active-selection call failed; it was corrected
to the existing public active_selection.set operation before publication.

At exact successor head `513391c1`, native source-pair logs retain both annotation
browser scenarios passing and 2,884 Linux Python tests passing (27 explicit skips).
That run's aggregate verdict is **failure**, from Movie interruption (#177).
Separate core `37629947438` passes. Standard CI `37629258208` remains **failure**
from Qt WebGL startup, retained under #35. Neither failure is erased or treated as
a full gate pass. They do not refute these separately observed bounded contracts;
final 1.0 recertification still requires its own complete gates.

Guard: `tests/test_design_review_closure.py::test_invalid_replacement_conversion_preserves_scene`. Loading a real invalid HDF5 file in replace mode raises before changing system identity, exported state or outgoing messages. Related real-provider cases additionally preserve sources, undo/redo and scientific analysis identities/signatures.

Normative contract: `devguide/scene_contracts.md`.
[Exact closure receipt](../design_contract_closure_20261007.json).
No production Python/TypeScript logic, runtime, tag or package is changed by this
closure. Standalone remains experimental; this record does not qualify Qt/GPU.
