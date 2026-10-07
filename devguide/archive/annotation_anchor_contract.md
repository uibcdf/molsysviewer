---
summary: Annotation coordinate anchors and callout options lack a coherent public lifecycle
issue: uibcdf/molsysviewer#146
status: resolved
opened: 2026-10-03
closed: 2026-10-07
severity: high
verification: measured
area: [annotations, state, rendering]
guard: tests/test_design_review_closure.py::test_coordinate_annotation_lifecycle
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Annotation coordinate anchors and callout options lack a coherent public lifecycle

**Resolved — 2026-10-07:** Annotations now retain atom or explicit-unit coordinate anchors across add/reanchor/move, text/style edits, hidden state, history, copy/extraction and session/state restoration. World and camera offsets have distinct units and actual callout geometry; three leader styles are browser-observed.

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

Public annotations.add(position=...) exposes coordinate anchors, world/camera offsets and leader styles, but normal digestion accepts only layout corners. Coordinate anchors also fail state export through list(None), cannot be edited consistently and are dropped during scene transfer.

## How

Inspected annotations.py, the position digester, viewer/state.py, layers.Annotation and annotation-handlers.ts. Mol* label offsets are camera-space shader offsets; using them as world displacement cannot place a label at an absolute coordinate. No fresh runtime reproduction is claimed.

## Why

Close the already exposed Python and Studio contract before 1.0. Preserve atom anchors, implement coordinate anchors with explicit units across editing/history/state/session/copy/extract, and qualify or reject unsupported callout combinations before any scene mutation.

## Acceptance

Real-demo Python guards for both anchor kinds, units, edit transitions and scene transfer; real Mol* browser evidence for coordinate/world rendering and supported leader styles. Advanced MVS annotation machinery remains post-1.0.

## What was refuted

Source inspection is recorded separately from runtime evidence. No new regression run is claimed at opening.

## Resolution

Implemented in the preserved working tree and locally qualified on 2026-10-03. Integration into a committed supported candidate remains pending. No closure or final release qualification is claimed.

The public coordinate and offset digesters now support finite physical triples and their declared legacy nm input. set_style has an annotation-specific dictionary seam. State stores typed coordinate anchors with units; editing, history, session, extraction and same-system copying preserve them. Mol* callouts use actual world coordinates and camera-basis offsets, distinct leader geometry and retained hidden-state editing. The trajectory owner awaits callout updates and drains outstanding frame writes before playback stops. Browser evidence uses a real three-structure pentalanine fixture. Full MVS remains deferred.

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

Guard: `tests/test_design_review_closure.py::test_coordinate_annotation_lifecycle`. The real dialanine guard checks nm/angstrom conversion, the typed exported anchor, edits, undo/redo, copy/extraction, session restoration and transitions between both anchor kinds.

Normative contract: `devguide/scene_contracts.md`.
[Exact closure receipt](../design_contract_closure_20261007.json).
No production Python/TypeScript logic, runtime, tag or package is changed by this
closure. Standalone remains experimental; this record does not qualify Qt/GPU.
