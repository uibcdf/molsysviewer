---
summary: State identity can trust different atom associations and stale topology caches
issue: uibcdf/molsysviewer#147
status: resolved
opened: 2026-10-03
closed: 2026-10-07
severity: high
verification: measured
area: [state, identity, live_edit]
guard: tests/test_design_review_closure.py::test_announced_same_size_edit_invalidates_atom_identity_cache
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# State identity can trust different atom associations and stale topology caches

**Resolved — 2026-10-07:** Fingerprint schema 2 records ordered available hierarchy and atom identities independently of trajectory coordinates. Announced same-object/same-count edits invalidate both caches. Missing optional hierarchy remains explicit and old fingerprints conservatively re-resolve anchors.

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

The state fingerprint hashes only ordered atom names, whereas anchor identities include chain/group associations. Both caches use object identity and atom count, so an announced in-place topology edit preserving atom count can reuse stale identity data.

## How

Inspected viewer/state.py _structure_identity/_atom_identities and apply_system_edit. The same atom names with changed chain/group assignments can follow the index fast path incorrectly.

## Why

Avoid restoring plausible labels, measurements and selections onto different atoms. Strengthen the topology fingerprint while preserving frame-independent identity; invalidate caches at declared system edits.

## Acceptance

Real-demo guards for same-name/different-group systems, same-object/same-count metadata edits, frame independence and legacy state handling.

## What was refuted

Source inspection is recorded separately from runtime evidence. No new regression run is claimed at opening.

## Resolution

Implemented in the preserved working tree and locally qualified on 2026-10-03. Integration into a committed supported candidate remains pending. No closure or final release qualification is claimed.

Fingerprint schema 2 uses available ordered chain/group/atom identities and atom IDs/types. Missing hierarchy is represented explicitly through public has_attribute/get, never synthesized. Atom identity caches use the same missing-field semantics and are invalidated on load/announced edits even when object and size are unchanged. Exported identity dictionaries are detached. Legacy fingerprint records take the conservative re-resolution path. The first full run exposed 38 RDKit cases that lacked optional hierarchy; all 38 pass in the subsequent 90-case correction selection.

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

Guard: `tests/test_design_review_closure.py::test_announced_same_size_edit_invalidates_atom_identity_cache`. A real in-place group-ID edit keeps the same object and atom count while changing both the fingerprint and annotation identity. Detached exports cannot mutate the cached fingerprint; related cases verify changed associations and frame independence.

Normative contract: `devguide/scene_contracts.md`.
[Exact closure receipt](../design_contract_closure_20261007.json).
No production Python/TypeScript logic, runtime, tag or package is changed by this
closure. Standalone remains experimental; this record does not qualify Qt/GPU.
